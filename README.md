# Patching

## Introduction

Patching is a Python module to simplify and expand the capabilities of [monkeypatching](https://en.wikipedia.org/wiki/Monkey_patch). It aims to emulate in part the functionality of [Harmony](https://harmony.pardeike.net/) for C#.

## Content

### Source

The source consists of the file ``patching.py``. This file contains 2 important classes, ``OutVar`` and ``Patching``. Further information on both of these can be found in [Documentation](#documentation).

Information/infrastructure for building will come in the future.

### Documentation

Missing external documentation at the moment. Functions all have docstrings, however, and ``OutVar.patch`` is explained further in comments. Two example files are also present, see: [Examples](#examples).

### Examples

Two files exist as examples at the moment. [outvar.py](/tree/master/examples/outvar.py) and [patch.py](/tree/master/examples/patch.py). ``outvar.py`` gives examples for usage of the ``OutVar`` class, and ``patch.py`` gives examples for usage of the ``Patching`` class.