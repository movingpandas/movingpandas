"""Custom skipper if a module succeeds in importing

Most to make it a bit easier to ensure the hvplot raises an import error later
on so that can be tested.
"""
from typing import Optional
import sys

from _pytest.outcomes import Skipped


def importthenskip(modname: str, minversion: Optional[str] = None, reason: Optional[str] = None) -> None:
    """Import the requested module and skip if successful.

    :param str modname:
        The name of the module to import.
    :param str minversion:
        If given and the import succeeds then the test is skipped if the the
        imported module's ``__version__`` is at least this value
    :param str reason:
        If given, this reason is shown as the message when the module is imported

    Example::

        importthenskip("docutils")
    """
    import warnings

    __tracebackhide__ = True
    compile(modname, "", "eval")  # to catch syntaxerrors

    with warnings.catch_warnings():
        # Make sure to ignore ImportWarnings that might happen because
        # of existing directories with the same name we're trying to
        # import but without a __init__.py file.
        warnings.simplefilter("ignore")
        try:
            __import__(modname)
        except ImportError:
            return
    mod = sys.modules[modname]
    if minversion is None:
        if reason is None:
            reason = "imported {!r}".format(modname)
        raise Skipped(reason, allow_module_level=True)

    verattr = getattr(mod, "__version__", None)
    if minversion is not None:
        # Imported lazily to improve start-up time.
        from packaging.version import Version

        if verattr is None or Version(verattr) >= Version(minversion):
            raise Skipped(
                "module {!r} has __version__ {!r}, at least: {!r}".format(modname, verattr, minversion), allow_module_level=True,
            )
