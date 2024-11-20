"""
Example file for the Patching class of the patching module.
"""

from pprint import pprint

### pylint: disable-next=import-error
from src.patching import Patching

# initialize the class
Patch = Patching("Testing")


### pylint: disable=missing-function-docstring, wrong-import-position, wrong-import-order


#################################
# explicit, immediate patching. #
#################################


def test_one(string: str) -> str:
    string = list(string)
    string.sort()

    return string

def prefix_one(args, _) -> str:
    print(f"`string` argument: {args[0]}")

# prefix with an elementary method
# the same as a simple monkeypatch prefix
# basic patch, simple logging of arguments.
test_one = Patch.elementary_prefix(test_one, prefix_one)

print(test_one("This is a String!"))
# >>> `string` argument: This is a String!
# >>> [' ', ' ', ' ', '!', 'S', 'T', 'a', 'g', 'h', 'i', 'i', 'i', 'n', 'r', 's', 's', 't']


def test_two(integer: int, shift: int = 2) -> int:
    integer += 10
    integer <<= shift

    return integer

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
# >>> '`integer` argument: 5'
# >>> 'passed kwargs: {}'
# >>> 'Return value: 60'
# >>> 60

pprint(test_two(5, shift=3))
# >>> '`integer` argument: 5'
# >>> "passed kwargs: {'shift': 3}"
# >>> 'Printed : Return value: 120'
# >>> 120


######################
# proactive patching #
######################


# immediate fulfillment #

def test_three(string: str) -> str:
    print("This runs first!")

    return string

def prefix_two(_, __, ___) -> None:
    print("Successfully prefixed!")

print(test_three("This is a String!"))
# >>> This runs first!
# >>> This is a String!

Patch.prefix('__main__', 'test_three', prefix_two)

print(test_three("This is a String!"))
# >>> Successfully prefixed!
# >>> This runs first!
# >>> This is a String!


def test_four(int1: int, int2: int) -> int:
    print("Running function..")
    print("This prints last!")

    return int1 ** int2 - int2

def postfix_two(_, __, ___) -> None:
    print("Successfully postfixed!")

test_four(2, 3)
# >>> Running function..
# >>> This prints last!

Patch.postfix('__main__', 'test_four', postfix_two)

test_four(2, 3)
# >>> Running function..
# >>> This prints first!
# >>> Successfully postfixed!


# actual proactive patching #


# note that os is not imported yet.
Patch.prefix("os", "listdir", prefix_two) # see previous prefix function

import os

print(os.listdir("/"))
# >>> Successfully prefixed!
# >>> ['lib64', 'sys', 'sbin', 'dev', ...]


def postfix_three(_, __, _result) -> None:
    print(_result)

# note that math is not imported yet.
Patch.postfix("math", "cos", postfix_three)

import math

math.cos(3)
# >>> -0.9899924966004454
# ^ still prints a value because of the postfix!


# prefix flow control #


def potentially_dangerous() -> None:
    print("This function will error...")

    raise ValueError(":(")

def prefix_three(_, __, _result) -> None:
    # Uses out var functionality. See outvar.py
    # the value contained in this _result name is used.
    _result = "Exited safely!"

    # by returning False, the original function will not run
    # _result is returned instead.
    return False

Patch.prefix('__main__', 'potentially_dangerous', prefix_three)

print(potentially_dangerous())
# >>> Exited safely!

# as you can see, the function didn't error, and the value of
# _result in the prefix function was returned.

# we can even go as far as to do the following:

def prefix_four(_, __, ___) -> bool:
    return False

Patch.prefix("sys", "exit", prefix_four)

import sys

sys.exit(0)
# no output, but our code still runs. lets continue.

### pylint: disable=unreachable


# postfix return control #


def postfix_four(_, __, _result) -> int:
    print(_result)

    _result += 12

    return 5

Patch.postfix("math", "sin", postfix_four)

print(math.sin(3))
# >>> 0.1411200080598672
# >>> 12.141120008059866
