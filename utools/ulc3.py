from array import array
from collections.abc import Iterable
from enum import IntEnum, IntFlag, auto
from io import BytesIO
from types import TracebackType
from typing import Protocol, TextIO


class MemoryMappedDevice(Protocol):
    def __enter__(self) -> None:
        ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        ...


def sign_extend(value: int, bits: int) -> int:
    # https://stackoverflow.com/a/32031543
    sign_bit = 1 << (bits - 1)
    return (value & (sign_bit - 1)) - (value & sign_bit)


def zero_fill(size: int):
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


class Memory:
    SIZE = 1 << 16
    __slots__ = ("memory", "mmio")

    def __init__(self):
        self.mmio: dict[int, MemoryMappedDevice] = {}
        self.memory = array("H", zero_fill(self.SIZE))

    def __getitem__(self, position: int) -> int:
        if position in self.mmio:
            with self.mmio[position]:
                return self.memory[position]
        return self.memory[position]

    def __setitem__(self, position: int, value: int):
        self.memory[position] = value

    def add_device(self, address: int, device: MemoryMappedDevice):
        self.mmio[address] = device

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
    NREGISTERS = 10
    __slots__ = ("registers",)

    def __init__(self):
        self.registers = array("H", zero_fill(self.NREGISTERS))

    def __getitem__(self, register: int) -> int:
        return self.registers[register]

    def __setitem__(self, register: int, value: int):
        self.registers[register] = value & 0xFFFF

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
        value = self.registers[register]
        if value == 0:
            self.cond = Flag.ZERO
        elif value >> 15:  # left-most bit indicates negative
            self.cond = Flag.NEGATIVE
        else:
            self.cond = Flag.POSITIVE


PROGRAM_START = 0x3000


def lc3_trap(
    vector: int, registers: Registers, memory: Memory, stdin: TextIO, stdout: TextIO
) -> bool:
    match TrapVector(vector):
        case TrapVector.GETC:
            registers[0] = ord(stdin.read(1)) & 0xFF

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
            c = stdin.read(1)
            stdout.write(c)
            stdout.flush()
            registers[0] = ord(c) & 0xFF

        case TrapVector.PUTSP:
            start = registers[0]
            index = 0
            while (c := memory[start + index]) != 0x00:
                stdout.write(chr(c & 0xFF))
                stdout.write(chr(c >> 8))
                index += 1
            stdout.flush()

        case TrapVector.HALT:
            return True

    return False


def lc3(registers: Registers, memory: Memory, stdin: TextIO, stdout: TextIO):  # noqa: PLR0915
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
                registers.update_flags(dr)

            case OpCode.AND:
                dr = (instruction >> 9) & 0x7
                sr1 = (instruction >> 6) & 0x7
                if (instruction >> 5) & 0x1:
                    imm5 = sign_extend(instruction & 0x1F, 5)
                    registers[dr] = registers[sr1] & imm5
                else:
                    sr2 = instruction & 0x7
                    registers[dr] = registers[sr1] & registers[sr2]
                registers.update_flags(dr)

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
                registers.update_flags(dr)

            case OpCode.LDI:
                dr = (instruction >> 9) & 0x7
                pc_offset_9 = sign_extend(instruction & 0x1FF, 9)
                address = memory[registers.pc + pc_offset_9]
                registers[dr] = memory[address]
                registers.update_flags(dr)

            case OpCode.LDR:
                dr = (instruction >> 9) & 0x7
                br = (instruction >> 6) & 0x7
                offset_6 = sign_extend(instruction & 0x3F, 6)
                registers[dr] = memory[registers[br] + offset_6]
                registers.update_flags(dr)

            case OpCode.LEA:
                dr = (instruction >> 9) & 0x7
                pc_offset_9 = sign_extend(instruction & 0x1FF, 9)
                registers[dr] = registers.pc + pc_offset_9
                registers.update_flags(dr)

            case OpCode.NOT:
                dr = (instruction >> 9) & 0x7
                sr = (instruction >> 6) & 0x7
                registers[dr] = ~registers[sr]
                registers.update_flags(dr)

            case OpCode.RES:  # intentionally blank
                pass

            case OpCode.RTI:  # not implemented
                pass

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
                if lc3_trap(vector, registers, memory, stdin, stdout):
                    break


if __name__ == "__main__":
    import argparse
    import contextlib
    import select
    import sys
    import termios
    import tty

    parser = argparse.ArgumentParser(description="LC3 emulator")
    parser.add_argument("image", type=argparse.FileType("rb"))
    args = parser.parse_args()

    @contextlib.contextmanager
    def cbreak_terminal(stdin: TextIO):
        if stdin.isatty():
            settings = termios.tcgetattr(stdin)
            try:
                tty.setcbreak(stdin)
                yield stdin
            finally:
                termios.tcsetattr(stdin, termios.TCSADRAIN, settings)
        else:
            yield stdin

    class Keyboard:
        KBSR = 0xFE00
        KBDR = 0xFE02

        def __init__(self, memory: Memory, stdin: TextIO):
            self.memory = memory
            self.stdin = stdin

        def __enter__(self):
            # only works when the terminal is in raw or cbreak mode
            waiting, _, _ = select.select([sys.stdin], [], [], 0)
            if len(waiting) > 0:
                self.memory[self.KBSR] = 1 << 15
                self.memory[self.KBDR] = ord(self.stdin.read(1))

        def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_value: BaseException | None,
            traceback: TracebackType | None,
        ) -> None:
            self.memory[self.KBSR] = 0

    registers = Registers()
    memory = Memory()

    with (
        contextlib.suppress(KeyboardInterrupt),
        cbreak_terminal(sys.stdin) as stdin,
    ):
        memory.add_device(Keyboard.KBSR, Keyboard(memory, stdin))
        memory.fromfile(args.image)
        lc3(registers, memory, stdin, sys.stdout)
