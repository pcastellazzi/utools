from typing import Any, Literal

A = "A"
B = "B"
C = "C"
D = "D"
E = "E"
Z = "Z"

AB = "AB"
AC = "AC"
BC = "BC"
ABC = "ABC"

L_01 = Literal[0, 1]

S_AB = Literal["A", "B"]
S_AC = Literal["A", "B", "C"]
S_AD = Literal["A", "B", "C", "D"]
S_AE = Literal["A", "B", "C", "D", "E"]


def fz(*args: Any):
    return frozenset(args)
