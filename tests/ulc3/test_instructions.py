from io import StringIO

import pytest

from utools.ulc3 import Flag, Memory, OpCode, Registers, lc3


class Bits:
    def __init__(self, value: int, size: int):
        self.size = size
        self.value = value if value >= 0 else (-value) | (2**size - 1) - 1

    def __truediv__(self, other: "Bits") -> "Bits":
        return Bits(
            (self.value << other.size) | other.value,
            self.size + other.size,
        )

    def as_int(self) -> int:
        return self.value


class VM:
    START = 0x3000

    def __init__(self):
        self.memory = Memory()
        self.registers = Registers()
        self.stdin = StringIO()
        self.stdout = StringIO()

    def run(self, code: list[Bits]) -> "VM":
        self.memory.fromiter(self.START, (ins.as_int() for ins in code))
        self.registers.pc = self.START
        lc3(self.registers, self.memory, self.stdin, self.stdout)
        return self


@pytest.fixture
def vm():
    return VM()


# fmt: off
def op(value: int) -> Bits: return Bits(value, 4)
def br(value: int) -> Bits: return Bits(value, 3)
def dr(value: int) -> Bits: return Bits(value, 3)
def sr(value: int) -> Bits: return Bits(value, 3)
def imm5(value: int) -> Bits: return Bits(value, 5)
def imm8(value: int) -> Bits: return Bits(value, 5)
def imm9(value: int) -> Bits: return Bits(value, 9)
def val(value: int) -> int : return Bits(value, 16).as_int()
# fmt: on

INS_HALT = op(OpCode.TRAP) / Bits(0, 4) / Bits(0x25, 8)


def test_add_imm(vm: VM):
    def run(a: int, b: int) -> int:
        ins = op(OpCode.ADD) / dr(3) / sr(1) / Bits(1, 1) / imm5(b)
        vm.registers[1] = val(a)
        vm.run([ins, INS_HALT])
        return vm.registers[3]

    assert run(1, 1) == val(2)
    assert vm.registers.cond == Flag.POSITIVE

    assert run(-1, -1) == val(-2)
    assert vm.registers.cond == Flag.NEGATIVE

    assert run(-1, 1) == val(0)
    assert vm.registers.cond == Flag.ZERO


def test_add_reg(vm: VM):
    def run(a: int, b: int) -> int:
        ins = op(OpCode.ADD) / dr(3) / sr(1) / Bits(0, 3) / sr(2)
        vm.registers[1] = val(a)
        vm.registers[2] = val(b)
        vm.run([ins, INS_HALT])
        return vm.registers[3]

    assert run(1, 1) == val(2)
    assert vm.registers.cond == Flag.POSITIVE

    assert run(-1, -1) == val(-2)
    assert vm.registers.cond == Flag.NEGATIVE

    assert run(-1, 1) == val(0)
    assert vm.registers.cond == Flag.ZERO


def test_and_imm(vm: VM):
    def run(a: int, b: int) -> int:
        ins = op(OpCode.AND) / dr(3) / sr(1) / Bits(1, 1) / imm5(b)
        vm.registers[1] = val(a)
        vm.run([ins, INS_HALT])
        return vm.registers[3]

    assert run(1, 1) == val(1)
    assert vm.registers.cond == Flag.POSITIVE

    assert run(-1, -1) == val(-1)
    assert vm.registers.cond == Flag.NEGATIVE

    assert run(0, 0) == val(0)
    assert vm.registers.cond == Flag.ZERO


def test_and_reg(vm: VM):
    def run(a: int, b: int) -> int:
        ins = op(OpCode.AND) / dr(3) / sr(1) / Bits(0, 3) / sr(2)
        vm.registers[1] = val(a)
        vm.registers[2] = val(b)
        vm.run([ins, INS_HALT])
        return vm.registers[3]

    assert run(1, 1) == val(1)
    assert vm.registers.cond == Flag.POSITIVE

    assert run(-1, -1) == val(-1)
    assert vm.registers.cond == Flag.NEGATIVE

    assert run(0, 0) == val(0)
    assert vm.registers.cond == Flag.ZERO


@pytest.mark.parametrize(
    "flag",
    [
        Flag.ZERO,
        Flag.NEGATIVE,
        Flag.POSITIVE,
        Flag.ZERO | Flag.NEGATIVE,
        Flag.ZERO | Flag.POSITIVE,
        Flag.NEGATIVE | Flag.POSITIVE,
    ],
)
def test_br(vm: VM, flag):
    def run(cond: int) -> int:
        ins = op(OpCode.BR) / Bits(cond, 3) / imm9(2)
        vm.run([ins, INS_HALT, INS_HALT])
        return vm.registers.pc

    vm.registers.cond = flag
    assert run(flag) == 0x3002

    vm.registers.cond = ~flag
    assert run(flag) == 0x3001  # noqa: PLR2004


def test_ld(vm: VM):
    def run(a: int) -> int:
        ins = op(OpCode.LD) / dr(3) / Bits(0x30F0 - vm.START, 9)
        vm.memory[0x30F0] = val(a)
        vm.run([ins, INS_HALT])
        return vm.registers[3]

    assert run(1) == val(1)
    assert vm.registers.cond == Flag.POSITIVE

    assert run(-1) == val(-1)
    assert vm.registers.cond == Flag.NEGATIVE

    assert run(0) == val(0)
    assert vm.registers.cond == Flag.ZERO


def test_ldi(vm: VM):
    def run(a: int) -> int:
        ins = op(OpCode.LDI) / dr(3) / Bits(0x30F0 - vm.START, 9)
        vm.memory[0x30F0] = 0x4000
        vm.memory[0x4000] = val(a)
        vm.run([ins, INS_HALT])
        return vm.registers[3]

    assert run(1) == val(1)
    assert vm.registers.cond == Flag.POSITIVE

    assert run(-1) == val(-1)
    assert vm.registers.cond == Flag.NEGATIVE

    assert run(0) == val(0)
    assert vm.registers.cond == Flag.ZERO


def test_ldr(vm: VM):
    def run(a: int) -> int:
        ins = op(OpCode.LDR) / dr(3) / br(4) / Bits(0, 6)
        vm.memory[0x30F0] = val(a)
        vm.registers[4] = 0x30F0
        vm.run([ins, INS_HALT])
        return vm.registers[3]

    assert run(1) == val(1)
    assert vm.registers.cond == Flag.POSITIVE

    assert run(-1) == val(-1)
    assert vm.registers.cond == Flag.NEGATIVE

    assert run(0) == val(0)
    assert vm.registers.cond == Flag.ZERO


def test_lea(vm: VM):
    def run(a: int) -> int:
        ins = op(OpCode.LEA) / dr(1) / imm9(5)
        vm.run([ins, INS_HALT])
        return vm.registers[1]

    assert run(5) == vm.START + 5
    assert vm.registers.cond == Flag.POSITIVE


def test_not(vm: VM):
    def run(a: int) -> int:
        ins = op(OpCode.NOT) / dr(3) / sr(1) / Bits(0b111111, 6)
        vm.registers[1] = val(a)
        vm.run([ins, INS_HALT])
        return vm.registers[3]

    assert run(0xFFF0) == val(0xF)
    assert vm.registers.cond == Flag.POSITIVE

    assert run(0x0FFF) == val(0xF000)
    assert vm.registers.cond == Flag.NEGATIVE

    assert run(0xFFFF) == val(0)
    assert vm.registers.cond == Flag.ZERO


def test_st(vm: VM):
    def run(a: int) -> int:
        ins = op(OpCode.ST) / sr(3) / Bits(0x30F0 - vm.START, 9)
        vm.registers[3] = val(a)
        vm.run([ins, INS_HALT])
        return vm.memory[0x30F0]

    assert run(1) == val(1)
    assert run(-1) == val(-1)
    assert run(0) == val(0)


def test_sti(vm: VM):
    def run(a: int) -> int:
        ins = op(OpCode.STI) / sr(3) / Bits(0x30F0 - vm.START, 9)
        vm.memory[0x30F0] = 0x4000
        vm.registers[3] = val(a)
        vm.run([ins, INS_HALT])
        return vm.memory[0x4000]

    assert run(1) == val(1)
    assert run(-1) == val(-1)
    assert run(0) == val(0)


def test_str(vm: VM):
    def run(a: int) -> int:
        ins = op(OpCode.STR) / sr(3) / br(4) / Bits(0, 6)
        vm.registers[3] = val(a)
        vm.registers[4] = 0x30F0
        vm.run([ins, INS_HALT])
        return vm.memory[0x30F0]

    assert run(1) == val(1)
    assert run(-1) == val(-1)
    assert run(0) == val(0)


# jmp, jsr
# trap
# rti, res
# test overflow semantics
