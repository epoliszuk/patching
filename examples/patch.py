"""
Example file for the Patching class of the patching module.
"""

from pprint import pprint

### pylint: disable-next=import-error
from src.patching import Patching

# initialize the class
Patch = Patching("Testing")


#################################
# explicit, immediate patching. #
#################################


### pylint: disable-next=missing-function-docstring
def test_one(string: str) -> str:
    string = list(string)
    string.sort()

    return string

### pylint: disable-next=missing-function-docstring
def prefix_one(args, _) -> str:
    print(f"`string` argument: {args[0]}")

# prefix with an elementary method
# the same as a simple monkeypatch prefix
# basic patch, simple logging of arguments.
test_one = Patch.elementary_prefix(test_one, prefix_one)

print(test_one("This is a String!"))
# `string` argument: This is a String!
# [' ', ' ', ' ', '!', 'S', 'T', 'a', 'g', 'h', 'i', 'i', 'i', 'n', 'r', 's', 's', 't']


### pylint: disable-next=missing-function-docstring
def test_two(integer: int, shift: int = 2) -> int:
    integer += 10
    integer <<= shift

    return integer

### pylint: disable-next=missing-function-docstring
def postfix_one(args, kwargs, result) -> int:
    pprint(f"`integer` argument: {args[0]}")
    pprint(f"passed kwargs: {kwargs}")
    pprint(f"Return value: {result}")

    return result

# postfix with an elementary method
# the same as a simple monkeypatch postfix
# basic patch, simple logging of arguments and return value.
test_two = Patch.elementary_postfix(test_two, postfix_one)

pprint(test_two(5))
# '`integer` argument: 5'
# 'passed kwargs: {}'
# 'Return value: 60'
# 60

pprint(test_two(5, shift=3))
# '`integer` argument: 5'
# "passed kwargs: {'shift': 3}"
# 'Printed : Return value: 120'
# 120


######################
# proactive patching #
######################


# TODO: This whole section.
