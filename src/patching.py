#     Copyright (C) 2024  Ellis Poliszuk
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
A module to simplify the process of patching functions and methods.

Contains:
    - ``Static``: A helper class to make certain classes 'static'.
    - ``OutVar``: A class to patch functions and methods to return the final state of parameters \
upon return.
        - ``patch``: A method to patch a function or method for returning specified out variables.
        - ``unpatch``: A method to unpatch a function or method. Undoes patch.
        - ``get_info``: A method to get the out var patch information of a function or method.
        - ``get_capture``: A method to get the captured parameters (out vars) of the function \
or method.
        - ``get_original``: A method to get the original function or method, pre-patch.
        - ``is_patched``: A method to check if a function or method is patched for out variables.
    - ``Patching``: A class to patch functions and methods in modules.
        - ``elementary_prefix``: A method to create a prefix wrapper.
        - ``elementary_postfix``: A method to create a postfix wrapper.
        - ``prefix``: A method to prefix a function or method from a module.
        - ``postfix``: A method to postfix a function or method in a module.
"""

### pylint: disable=method-hidden, not-callable, expression-not-assigned, too-few-public-methods
### pylint: disable=multiple-statements

import inspect
from types import FunctionType, ModuleType
from typing import Any, TypeVar, TypeAlias
from copy import copy
from collections.abc import Iterable, Callable
from functools import partial, update_wrapper

import bytecode.bytecode as bc
import bytecode


class _Helper:
    CallableT: TypeAlias = Callable
    T = TypeVar('T')


class Static:
    """
    Use as a decorator on a class definition to make the class 'static'.

    Despite the name, this does not decorate each method with ``@staticmethod``.
    This class is meant for use with classes that only require a single shared instance.

    Will error if:
        - The input to Static is not a class or not instantiatable.
        - The class takes additional parameters in its __init__ method.
    """

    def __init__(self, cls: type):
        if not inspect.isclass(cls):
            raise TypeError(
                f"Failed to make static the input class '{cls.__name__}'. " +
                "The input to Static must be a class, not an instance.")

        try:
            self.cls = cls()

        except TypeError as exc:
            raise TypeError(
                f"Failed to make static the input class '{cls.__name__}'. " +
                "The input to Static must be a class, not an instance. " + 
                "Additionally, the class must not take additional parameters in __init__.") from exc

        self.props = {}

        for prop in dir(cls):
            if prop.startswith("__") and prop.endswith("__"):
                continue

            setattr(self, prop, partial(getattr(cls, prop), self.cls))
            update_wrapper(getattr(self, prop), self.cls)

        self.__doc__ = self.cls.__doc__


    def __getattr__(self, name: str):
        if name in self.props:
            return self.props[name]

        return getattr(self.cls, name)


@Static
class OutVar:
    """
    A class that patches functions and methods to return the final state of parameters upon return.

    Contains:
        - ``patch``: A method to patch a function or method for returning specified out variables.
        - ``unpatch``: A method to unpatch a function or method.
        - ``get_info``: A method to get the out var patch information of a function or method.
        - ``get_capture``: A method to get the captured parameters (out vars) of the function or \
method.
        - ``get_original``: A method to get the original function or method, pre-patch.
        - ``is_patched``: A method to check if a function or method is patched for out variables.
    """

    def patch(self, func: _Helper.CallableT, names: str | Iterable[str] = None) \
            -> _Helper.CallableT:
        """
        Used to wrap a function and return the final state of parameters upon return.
        Will patch the original function as well as returning it.

        Args:
            func (CallableT): The function or method to patch.
            names (str | Iterable[str], optional): The names of the parameters to return. \
Defaults to None.

        Returns:
            CallableT: Returns the original function after the successful patching.
        """

        # if run as a decorator or without a names argument, capture all parameters
        if names is None:
            names = func.__code__.co_varnames

        # if names is just a single parameter, make it a tuple
        if names.__class__ is str:
            names = (names,)

        # if no names are provided, return the original function
        # no need to capture any params
        if len(names) == 0:
            return func

        oldfunc = None

        # if the function is already patched, get the original function
        # repatch the original function with the new params
        if self.is_patched(func):
            if not self.get_capture(func) is None:
                names += self.get_capture(func)

            # get the original function
            oldfunc = self.get_original(func)

        # if the original function has been accessed, operate on that code
        # if not, use the function from arguments
        newcode = bc.Bytecode.from_code(oldfunc.__code__ if not oldfunc is None else func.__code__)

        # aliasing
        Instr = bytecode.Instr

        ind = 0
        for instr in copy(newcode):
            # we want to change the return value of the function
            # continue when the opcode isn't returning from the function.
            if instr.name != "RETURN_VALUE": continue

            # get the line number of the return value
            # the new instructions should inherit this
            ln = instr.lineno

            # place all of the captured parameters in the stack
            # after the original return value
            [newcode.insert(ind - 1, Instr('LOAD_FAST', x, lineno=ln)) for x in names]
            # build a tuple with all of the necessary arguments.
            newcode.insert(ind - 1, Instr('BUILD_TUPLE', len(names) + 1, lineno=ln))

            # keep track of the actual index we should insert at
            ind += len(names) + 1

        # build the old function from parts, as a deepcopy

        ### pylint: disable-next=invalid-name
        OLD_FUNC = FunctionType(
            func.__code__,
            func.__globals__,
            func.__name__,
            func.__defaults__,
            func.__closure__
        )

        # replace the original functions code with the patched code
        func.__code__ = newcode.to_code()
        # set a property on the newly patched function to store information about the patch
        func.OUTPATCHINFO = {
            "captured": names,
            "original": oldfunc if not oldfunc is None else OLD_FUNC
        }

        return func

    def unpatch(self, func: _Helper.CallableT) -> _Helper.CallableT:
        """Reverts a function patched with ``OutVar.patch`` to its original state.

        Args:
            func (_Helper.CallableT): The function or method to unpatch.

        Returns:
            _Helper.CallableT: The original function or method.
        """
        if not self.is_patched(func):
            return func

        func.__code__ = self.get_original(func).__code__

        return func

    def get_info(self, func: Callable) -> dict:
        """Get information about a function that has been patched with ``OutVar.patch``.

        Args:
            func (Callable): The function to get info for.

        Returns:
            dict: The information about the patch.
        """
        if not self.is_patched(func):
            return None

        return func.OUTPATCHINFO

    def get_capture(self, func: Callable) -> tuple:
        """Get the captured parameters / out vars of a function patched with ``OutVar.patch``.

        Args:
            func (Callable): The function to get the captured parameters for.

        Returns:
            tuple: The captured parameters / out vars.
        """
        if not self.is_patched(func):
            return None

        return func.OUTPATCHINFO["captured"]

    def get_original(self, func: Callable) -> Callable:
        """Get the original function or method of a function patched with ``OutVar.patch``.

        Args:
            func (Callable): The function to return the original of.

        Returns:
            Callable: The function or method before the patch.
        """
        if not self.is_patched(func):
            return None

        return func.OUTPATCHINFO["original"]

    def is_patched(self, func: Callable) -> bool:
        """Returns whether or not a function or method has been patched with ``OutVar.patch``.

        Args:
            func (Callable): The function or method to check.

        Returns:
            bool: Whether or not the function or method has been patched.
        """
        return hasattr(func, 'OUTPATCHINFO')


class Patching:
    """
    A class to patch functions and methods in modules.

    Contains:
        - ``elementary_prefix``: A method to create a prefix wrapper.
        - ``elementary_postfix``: A method to create a postfix wrapper.
        - ``prefix``: A method to prefix a function or method from a module.
        - ``postfix``: A method to postfix a function or method in a module.
    """

    def __init__(self, name: str):
        ### pylint: disable-next=invalid-name
        self._PATCH_INFO = {}
        self.name = name

        self.prefix = self._patch__import__(self.prefix)
        self.postfix = self._patch__import__(self.postfix)

    def _patch__import__(self, func: _Helper.CallableT) -> _Helper.CallableT:
        """Patches the import builtin for the running module to allow for proactive patching.

        Args:
            func (Callable): The function that should ensure __import__ is patched.

        Returns:
            Callable: The origin function.
        """

        def _wrapper(*args, **kwargs) -> Any:
            """A wrapper used in the patching of the __import__ builtin.

            Returns:
                Any: The result of the original function.
            """

            builtins = inspect.currentframe().f_back.f_globals["__builtins__"]

            if hasattr(builtins.__import__, "PATCH") and builtins.__import__.PATCH.get(self.name):
                return func(*args, **kwargs)

            def process_imports(_, __, result: 'ModuleType') -> None:
                """
                Function that is monkeypatched to the end of the __import__ builtin to \
                process imports.

                Args:
                    _ (Any): Positional needed for patching. Ignored.
                    __ (Any): Positional needed for patching. Ignored.
                    result ('ModuleType'): The result of the import.
                """

                #print(f"""Intercepted import of {result.__name__}.""")

                if result.__name__ in self._PATCH_INFO:
                    for tup in copy(self._PATCH_INFO[result.__name__]):
                        patch_type, name, prefix = tup

                        if patch_type == "prefix":
                            self._prefix_atom(result, name, prefix)

                        if patch_type == "postfix":
                            self._postfix_atom(result, name, prefix)

                        self._PATCH_INFO[result.__name__].remove(tup)

            builtins.__import__ = self.elementary_postfix(
                builtins.__import__,
                process_imports
            )

            if not hasattr(builtins.__import__, "PATCH"):
                builtins.__import__.PATCH = {}

            builtins.__import__.PATCH[self.name] = True

            return func(*args, **kwargs)

        return _wrapper

    def _prefix_atom(self, base: 'ModuleType', name: str, prefix: Callable) -> None:
        """Patches a function or method in a module to have a prefix.

        Prefix functions should have 3 parameters: ``args``, ``kwargs``, and ``_result``.

        The return value of the prefix function determines whether or not the original \
        function is called.
        
        If the prefix function return a truthy value, the rest of the original function will \
        run and be returned.
        If the prefix function returns a falsy value, the original function will not run and \
        ``_result`` is returned instead.

        Args:
            base (ModuleType): The module containing the target function.
            name (str): The name of the function to patch.
            prefix (Callable): The prefix function to apply.

        Raises:
            AttributeError: If the target function is not found in the module.
        """
        if name in dir(base):
            # the function to patch
            this_func = getattr(base, name)

            # wrapper for the prefix
            def _wrapper(*args, **kwargs):
                """Wrapper function for ``Patching._prefix_atom``.

                Returns:
                    Any: Either the return value of the function or prefix.
                """
                nonlocal prefix
                _result = None

                OutVar.patch(prefix, '_result')
                prefix_out = prefix(args, kwargs, _result)
                _result = prefix_out[1]

                if prefix_out[0] is True:
                    return this_func(*args, **kwargs)
                else:
                    return _result

            setattr(base, name, _wrapper)

        else: raise AttributeError(f"{name} not found in {base}.")

    def _postfix_atom(self, base: 'ModuleType', name: str, postfix: Callable) -> None:
        """Patches a function or method in a module to have a postfix.

        Postfix functions should have 3 parameters: ``args``, ``kwargs``, and ``_result``.

        ``_result`` is initialized to the return value of the original function.

        ``_result`` can be set to a new value in the postfix function, which will be returned \
        instead of the original return value.
        If ``_result`` is falsy, return the prefix return value.

        Args:
            base (ModuleType): The module containing the target function.
            name (str): The name of the function to patch.
            postfix (Callable): The postfix function to apply.

        Raises:
            AttributeError: If the target function is not found in the module.
        """

        if name in dir(base):
            this_func = getattr(base, name)

            def _wrapper(*args, **kwargs):
                nonlocal postfix

                _result = this_func(*args, **kwargs)

                postfix = OutVar.patch(postfix, '_result')
                postfix_out = postfix(args, kwargs, _result)
                _result = postfix_out[1]

                return _result or postfix_out[0]

            setattr(base, name, _wrapper)

        else: raise AttributeError(f"{name} not found in {base}.")

    def elementary_prefix(self, func: Callable[..., _Helper.T], prefix: Callable[..., _Helper.T]) \
        -> Callable[..., _Helper.T]:
        """Creates a basic monkeypatch prefix wrapper for a function.

        Prefix functions should have 2 parameters: ``args`` and ``kwargs``.

        Args:
            func (Callable[..., _Helper.T]): The function to prefix.
            prefix (Callable[..., _Helper.T]): The prefix function to apply.

        Returns:
            Callable[..., _Helper.T]: The prefix wrapper.
        """

        def _prefix_wrapper(*args, **kwargs):
            prefix(args, kwargs)
            return func(args, kwargs)

        return _prefix_wrapper

    def elementary_postfix(self, func: Callable[..., _Helper.T], prefix: Callable[..., _Helper.T]) \
        -> Callable[..., _Helper.T]:
        """Creates a basic monkeypatch postfix wrapper for a function.

        Postfix functions should have 3 parameters: ``args``, ``kwargs``, and ``result``.
        ``result`` is initialized to the return value of the original function.

        The return value of the postfix is returned as the return value of the patched function.

        Args:
            func (Callable[..., _Helper.T]): The function to postfix.
            postfix (Callable[..., _Helper.T]): The postfix function to apply.

        Returns:
            Callable[..., _Helper.T]: The postfix wrapper.
        """

        def _postfix_wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            return prefix(args, kwargs, result)

        return _postfix_wrapper

    def prefix(self, module: str, name: str, prefix: Callable) -> None:
        """A function that simplifies the process of prefixing a function or method.

        If a module and the corresponding function name are found in the current global scope, \
        the function will be prefixed immediately.

        If a module and the corresponding function name are *not* found in the current global \
        scope, add the current patch to a queue that awaits the importing of the given module.

        Prefix functions should have 3 parameters: ``args``, ``kwargs``, and ``_result``.

        The return value of the prefix function determines whether or not the original function \
        is called.
        
        If the prefix function return a truthy value, the rest of the original function will run \
        and be returned.
        If the prefix function returns a falsy value, the original function will not run and \
        ``_result`` is returned instead. 

        Args:
            module (str): The name of the module containing the target function.
            name (str): The name of the target function.
            prefix (Callable): The prefix function to apply.
        """

        last_frame_globals = inspect.currentframe().f_back.f_globals

        if module in last_frame_globals \
                and last_frame_globals[module].__class__ is ModuleType:

            module = last_frame_globals[module]

            self._prefix_atom(module, name, prefix)

        else:
            if not module in self._PATCH_INFO:
                self._PATCH_INFO[module] = set()

            self._PATCH_INFO[module].add(("prefix", name, prefix))

    def postfix(self, module: str, name: str, postfix: Callable) -> None:
        """A function that simplifies the process of postfixing a function or method.

        If a module and the corresponding function name are found in the current global scope,
        the function will be postfixed immediately.

        If a module and the corresponding function name are *not* found in the current global
        scope, add the current patch to a queue that awaits the importing of the given module.

        Postfix functions should have 3 parameters: ``args``, ``kwargs``, and ``_result``.

        ``_result`` is initialized to the return value of the original function.

        ``_result`` can be set to a new value in the postfix function, which will be returned
        instead of the original return value.
        If ``_result`` is falsy, return the prefix return value.


        Args:
            module (str): The name of the module containing the target function.
            name (str): The name of the target function.
            postfix (Callable): The postfix function to apply.
        """
        last_frame_globals = inspect.currentframe().f_back.f_globals

        if module in last_frame_globals \
                and last_frame_globals[module].__class__ is ModuleType:

            module = last_frame_globals[module]

            self._postfix_atom(module, name, postfix)

        else:
            if not module in self._PATCH_INFO:
                self._PATCH_INFO[module] = set()

            self._PATCH_INFO[module].add(("postfix", name, postfix))
