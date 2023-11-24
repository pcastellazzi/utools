from array import array
from collections.abc import Iterable, Iterator
from enum import IntEnum, IntFlag, auto
from io import BytesIO
from termios import TCSAFLUSH, tcgetattr, tcsetattr
from tty import setcbreak
from typing import TextIO


def getch(stdin: TextIO) -> str:
    # https://stackoverflow.com/a/72825322
    if not stdin.isatty():
        return stdin.read(1)

    fd = stdin.fileno()
    old = tcgetattr(fd)

    try:
        setcbreak(fd)
        return stdin.read(1)
    finally:
        tcsetattr(fd, TCSAFLUSH, old)


def sign_extend(value: int, bits: int) -> int:
    # https://stackoverflow.com/a/32031543
    sign_bit = 1 << (bits - 1)
    return (value & (sign_bit - 1)) - (value & sign_bit)


def zero_fill(size: int):
    assert size > 0, "at least 1 item must be generated"
    return (0 for _ in range(size))


class Flag(IntFlag):
    POSITIVE = auto()
    ZERO = auto()
    NEGATIVE = auto()


class OpCode(IntEnum):
    BR = 0b0000  # conditional branch
    ADD = 0b0001  # addition
    LD = 0b0010  # load
    ST = 0b0011  # store
    JSR = 0b0100  # jump to subroutine
    AND = 0b0101  # bit-wise logical and
    LDR = 0b0110  # load base + offset
    STR = 0b0111  # store indirect
    RTI = 0b1000  # return from interrupt
    NOT = 0b1001  # bit-wise complement
    LDI = 0b1010  # load indirect
    STI = 0b1011  # store base + offset
    JMP = 0b1100  # jump / return from subroutine
    RES = 0b1101  # reserved / unused
    LEA = 0b1110  # load effective address
    TRAP = 0b1111  # system call


class TrapVector(IntEnum):
    GETC = 0x20
    OUT = 0x21
    PUTS = 0x22
    IN = 0x23
    PUTSP = 0x24
    HALT = 0x25
    DEBUG = 0x99


class Memory:
    SIZE = 1 << 16
    __slots__ = ("memory",)

    def __init__(self):
        self.memory = array("H", zero_fill(self.SIZE))

    def __getitem__(self, position: int) -> int:
        return self.memory[position]

    def __setitem__(self, position: int, value: int):
        self.memory[position] = value

    def debug(self, address: int, output: TextIO) -> None:
        assert 0 <= address < Memory.SIZE
        width = 16
        padding = width * 3 - 1
        dump = self.memory[address : address + 128].tobytes()

        def blocks() -> Iterator[bytes]:
            quotient, remainder = divmod(len(dump), width)
            for index in range(quotient):
                yield dump[index * width : (index + 1) * width]
            if remainder:
                yield dump[quotient * width :]

        for offset, block in enumerate(blocks()):
            text = "".join(chr(b) if 0x20 <= b <= 0x7B else "." for b in block)
            print(
                f"{address + (offset* width):08x}  {block.hex(' '):{padding}}  {text}",
                file=output,
            )

    def frombytes(self, start_address: int, data: bytes):
        memory = array("H")
        memory.frombytes(data)
        memory.byteswap()  # LC3 is big endian
        self.fromiter(start_address, memory)

    def fromiter(self, start_address: int, data: Iterable[int]):
        memory = array("H", data)
        self.memory[start_address : start_address + len(memory) - 1] = memory

    def fromfile(self, fd: BytesIO):
        start_address = int.from_bytes(fd.read(2), "big")
        data = fd.read()
        self.frombytes(start_address, data)


class Registers:
    GREGISTERS = 8
    NREGISTERS = 10

    __slots__ = ("registers",)

    def __init__(self):
        self.registers = array("H", zero_fill(self.NREGISTERS))

    def __getitem__(self, register: int) -> int:
        assert 0 <= register < self.GREGISTERS, "only GPRs are indexable"
        return self.registers[register]

    def __setitem__(self, register: int, value: int):
        assert 0 <= register < self.GREGISTERS, "only GPRs are indexable"
        assert 0 <= value < (1 << 16), "value must be UINT16"
        self.registers[register] = value
        self.update_flags(register)

    def __str__(self):
        return ",  ".join(
            [
                f"pc: {self.pc:04x}",
                f"cond: {self.cond:04x}",
                f"r0: {self[0]:04x}",
                f"r4: {self[4]:04x}",
                f"r1: {self[1]:04x}",
                f"r5: {self[5]:04x}",
                f"r2: {self[2]:04x}",
                f"r5: {self[6]:04x}",
                f"r3: {self[3]:04x}",
                f"r5: {self[7]:04x}",
            ]
        )

    @property
    def cond(self):
        return self.registers[-2]

    @cond.setter
    def cond(self, value: Flag):
        self.registers[-2] = value

    @property
    def pc(self):
        return self.registers[-1]

    @pc.setter
    def pc(self, value: int):
        self.registers[-1] = value

    def update_flags(self, register: int):
        assert 0 <= register <= self.GREGISTERS, "only GPRs can update flags"
        value = self.registers[register]
        if value == 0:
            self.cond = Flag.ZERO
        elif value >> 15:  # left-most bit indicates negative
            self.cond = Flag.NEGATIVE
        else:
            self.cond = Flag.POSITIVE


PROGRAM_START = 0x3000


def lc3_trap(
    vector: int,
    registers: Registers,
    memory: Memory,
    stdin: TextIO,
    stdout: TextIO,
    stderr: TextIO,
):
    match TrapVector(vector):
        case TrapVector.GETC:
            registers[0] = ord(getch(stdin)) & 0xFF

        case TrapVector.OUT:
            sys.stdout.write(chr(registers[0] & 0xFF))
            sys.stdout.flush()

        case TrapVector.PUTS:
            start = registers[0]
            index = 0
            while (c := memory[start + index]) != 0x00:
                stdout.write(chr(c & 0xFF))
                index += 1
            stdout.flush()

        case TrapVector.IN:
            stdout.write("Waiting for input: ")
            c = getch(stdin)
            stdout.write(c)
            registers[0] = ord(getch(stdin)) & 0xFF

        case TrapVector.PUTSP:
            start = registers[0]
            index = 0
            while (c := memory[start + index]) != 0x00:
                stdout.write(chr(c & 0xFF))
                stdout.write(chr(c >> 8))
                index += 1
            stdout.flush()

        case TrapVector.HALT:
            sys.exit()

        case TrapVector.DEBUG:
            print(registers, file=stderr)
            memory.debug(registers.pc, stderr)
            sys.exit()


def lc3(
    registers: Registers, memory: Memory, stdin: TextIO, stdout: TextIO, stderr: TextIO
):
    registers.cond = Flag.ZERO
    registers.pc = PROGRAM_START

    while True:
        instruction = memory[registers.pc]
        registers.pc += 1

        match OpCode(instruction >> 12):
            case OpCode.BR:
                cond = (instruction >> 9) & 0x7
                if cond & registers.cond:
                    pc_offset_9 = sign_extend(instruction & 0x1FF, 9)
                    registers.pc += pc_offset_9

            case OpCode.ADD:
                dr = (instruction >> 9) & 0x7
                sr1 = (instruction >> 6) & 0x7
                if (instruction >> 5) & 0x1:
                    imm5 = sign_extend(instruction & 0x1F, 5)
                    registers[dr] = registers[sr1] + imm5
                else:
                    sr2 = instruction & 0x7
                    registers[dr] = registers[sr1] + registers[sr2]

            case OpCode.AND:
                dr = (instruction >> 9) & 0x7
                sr1 = (instruction >> 6) & 0x7
                if (instruction >> 5) & 0x1:
                    imm5 = sign_extend(instruction & 0x1F, 5)
                    registers[dr] = registers[sr1] & imm5
                else:
                    sr2 = instruction & 0x7
                    registers[dr] = registers[sr1] & registers[sr2]

            case OpCode.JMP:
                br = (instruction >> 6) & 0x7
                registers.pc = registers[br]

            case OpCode.JSR:
                registers[7] = registers.pc
                if (instruction >> 11) & 0x1:
                    pc_offset_11 = sign_extend(instruction & 0x7FF, 11)
                    registers.pc += pc_offset_11
                else:
                    br = (instruction >> 6) & 0x7
                    registers.pc = registers[br]

            case OpCode.LD:
                dr = (instruction >> 9) & 0x7
                pc_offset_9 = sign_extend(instruction & 0x1FF, 9)
                registers[dr] = memory[registers.pc + pc_offset_9]

            case OpCode.LDI:
                dr = (instruction >> 9) & 0x7
                pc_offset_9 = sign_extend(instruction & 0x1FF, 9)
                address = memory[registers.pc + pc_offset_9]
                registers[dr] = memory[address]

            case OpCode.LDR:
                dr = (instruction >> 9) & 0x7
                br = (instruction >> 6) & 0x7
                offset_6 = sign_extend(instruction & 0x3F, 6)
                registers[dr] = memory[registers[br] + offset_6]

            case OpCode.LEA:
                dr = (instruction >> 9) & 0x7
                pc_offset_9 = sign_extend(instruction & 0x1FF, 9)
                registers[dr] = registers.pc + pc_offset_9

            case OpCode.NOT:
                dr = (instruction >> 9) & 0x7
                sr = (instruction >> 6) & 0x7
                registers[dr] = ~registers[sr]

            case OpCode.ST:
                sr = (instruction >> 9) & 0x7
                pc_offset_9 = sign_extend(instruction & 0x1FF, 9)
                memory[registers.pc + pc_offset_9] = registers[sr]

            case OpCode.STI:
                sr = (instruction >> 9) & 0x7
                pc_offset_9 = sign_extend(instruction & 0x1FF, 9)
                address = memory[registers.pc + pc_offset_9]
                memory[address] = registers[sr]

            case OpCode.STR:
                sr = (instruction >> 9) & 0x7
                br = (instruction >> 6) & 0x7
                offset_6 = sign_extend(instruction & 0x3F, 6)
                memory[registers[br] + offset_6] = registers[sr]

            case OpCode.TRAP:
                registers[7] = registers.pc
                vector = instruction & 0xFF
                lc3_trap(vector, registers, memory, stdin, stdout, stderr)

            case _ as opcode:
                err = f"0b{opcode:04b}({opcode:d}) is not supported"
                raise RuntimeError(err)


if __name__ == "__main__":
    import argparse
    import contextlib
    import sys

    parser = argparse.ArgumentParser(description="LC3 emulator")
    parser.add_argument("image", type=argparse.FileType("rb"))
    args = parser.parse_args()

    registers = Registers()
    memory = Memory()

    with contextlib.suppress(KeyboardInterrupt):
        memory.fromfile(args.image)
        memory.debug(0x3000, sys.stdout)
        sys.exit()
        lc3(registers, memory, sys.stdin, sys.stdout, sys.stderr)
