"""
Example file for the patching module.
"""

from pprint import pprint

### pylint: disable-next=import-error
from src.patching import OutVar as O

# patching with a decorator
# returns all parameters
@O.patch
### pylint: disable-next=missing-function-docstring
def test_one(string1: str, string2: str) -> str:
    string2 = (string2 + " Local String!").replace('t','1')
    return string1 + string2[-7:]

# to be patched more explicitly

### pylint: disable-next=missing-function-docstring
def test_two(int1: int, int2: int) -> int:
    return int1 + int2 * 5

# returns only the int1 parameter
O.patch(test_two, "int1")

pprint(test_one("Hello, this is a ", "test! Will this work?"))
# ('Hello, this is a S1ring!', 'Hello, this is a ', '1es1! Will 1his work? Local S1ring!')
# The first value in the tuple is the return value of test_one.
# The second value in the tuple is the final state of the parameter "string1".
# The third value in the tuple is the final state of the parameter "string2".

O.unpatch(test_one)

pprint(test_one)
