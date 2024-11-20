"""
Example file for the OutVar class of the patching module.
"""

from pprint import pprint
from math import trunc

### pylint: disable-next=import-error
from src.patching import OutVar as O

### pylint: disable=missing-function-docstring

# patching with a decorator
# returns all parameters

@O.patch
def test_one(string1: str, string2: str) -> str:
    string2 = (string2 + " Local String!").replace('t','1')
    return string1 + string2[-7:]

pprint(test_one("Hello, this is a ", "test! Will this work?"))
# >>> ('Hello, this is a S1ring!', 'Hello, this is a ', '1es1! Will 1his work? Local S1ring!')
# The first value in the tuple is the return value of test_one.
# The second value in the tuple is the final state of the parameter "string1".
# The third value in the tuple is the final state of the parameter "string2".

O.unpatch(test_one)

pprint(test_one("Hello, this is a ", "test! Will this work?"))
# Successfully unpatched, returns just 'Hello, this is a S1ring!'
# Looking back to before the unpatch, this is the same return value (index zero in the tuple).


# to be patched more explicitly

def test_two(int1: int, int2: int) -> int:
    int1 += 20
    int1 >>= 2
    return int1 + int2 * 5

# patches for returning the int1 parameter
O.patch(test_two, "int1")

pprint(test_two(13, 4))
# >>> (28, 8)
# The first value in the tuple is the return value of test_two.
# The second value in the tuple is the final state of the parameter "int1".

# unpatches test_two and repatches, adding this new out variable.
O.patch(test_two, "int2")

pprint(test_two(13, 4))
# >>> (28, 4, 8)
# The first value in the tuple is the return value of test_two.
# The second value in the tuple is the final state of the parameter **"int2"**.
# ^ The reason int2 is first is because it was the most recent parameter patched.


def test_three(int1: int, int2: int, float1: float) -> float:
    int2 <<= 1

    if int2 * float1 == trunc(int2 * float1):
        float1 = 2.54
        return (int1 + int2) * float1

    int1 = trunc(int2 * float1)

    return (int1 - int2) * float1

# patches for returning the float1 parameter
O.patch(test_three, "float1")

pprint(test_three(13, 4, 3.14))
# >>> (53.38, 3.14)
# The first value in the tuple is the return value of test_three.
# The second value in the tuple is the final state of the parameter "float1".

# unpatch test_three, patch with new out variable ordering.
O.unpatch(test_three)
O.patch(test_three, ["int2", "float1"])

pprint(test_three(12, 2, .5))
# >>> (40.64, 4, 2.54)
# The first value in the tuple is the return value of test_three.
# The second value in the tuple is the final state of the parameter "int2".
# The third value in the tuple is the final state of the parameter "float1".
