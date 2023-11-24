from array import array
from io import BytesIO
from types import TracebackType

from utools.ulc3 import Flag, Memory, Registers, sign_extend, zero_fill


def test_sign_extend():
    assert sign_extend(0b001010, 16), 0b0000_0000_0000_1010
    assert sign_extend(0b100101, 16), 0b1111_1111_1110_0101


def test_zero_fill():
    assert array("H", zero_fill(3)) == array("H", [0, 0, 0])
    assert bytes(zero_fill(3)) == b"\0\0\0"
    assert list(zero_fill(3)) == [0, 0, 0]


def test_memory():
    data = bytes(i % 2 for i in range(10))
    mem = Memory()
    mem.frombytes(0x0000, data)
    assert mem[0] == 1
    assert mem[4] == 1
    assert mem[5] == 0

    data = [1 for _ in range(10)]
    mem = Memory()
    mem.fromiter(0x0000, data)
    assert mem[0] == 1
    assert mem[9] == 1
    assert mem[10] == 0

    data = BytesIO(b"\x30\00\0T\0e\0s\0t")
    mem = Memory()
    mem.fromfile(data)

    expected = [84, 101, 115, 116, 0]
    for i, e in enumerate(expected):
        assert mem[0x3000 + i] == e


def test_memory_device():
    class FakeDevice:
        def __init__(self, memory: Memory):
            self.memory = memory

        def __enter__(self) -> None:
            self.memory[0] = 1
            self.memory[1] = 1

        def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_value: BaseException | None,
            traceback: TracebackType | None,
        ) -> None:
            self.memory[2] = 1

    mem = Memory()
    mem.add_device(0x0000, FakeDevice(mem))

    assert mem[0] == 1
    assert mem[1] == 1
    assert mem[2] == 1


def test_registers():
    reg = Registers()
    assert reg[0] == 0
    assert reg[7] == 0
    assert reg.pc == 0
    assert reg.cond == 0

    reg[0] = 0x1111
    reg.update_flags(0)
    assert reg.cond & Flag.POSITIVE

    reg[0] = 0
    reg.update_flags(0)
    assert reg.cond & Flag.ZERO

    reg[0] = 0xFFFF
    reg.update_flags(0)
    assert reg.cond & Flag.NEGATIVE
