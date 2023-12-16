from typing import Any, Literal

A = "A"
B = "B"
C = "C"
D = "D"
E = "E"
F = "F"
G = "G"
H = "H"
Z = "Z"

AB = "AB"
AC = "AC"
BC = "BC"
ABC = "ABC"

L_01 = Literal[0, 1]
L_ab = Literal["a", "b"]

S_AB = Literal["A", "B"]
S_AC = Literal["A", "B", "C"]
S_AD = Literal["A", "B", "C", "D"]
S_AE = Literal["A", "B", "C", "D", "E"]
S_AF = Literal["A", "B", "C", "D", "E", "F"]
S_AG = Literal["A", "B", "C", "D", "E", "F", "G"]
S_AH = Literal["A", "B", "C", "D", "E", "F", "G", "H"]


def fz(*args: Any):
    return frozenset(args)
