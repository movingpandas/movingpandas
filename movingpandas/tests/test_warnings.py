# -*- coding: utf-8 -*-

import warnings

import pytest

from movingpandas.tools._warnings import deprecated


@deprecated
def _deprecated_example():
    """A deprecated function used only for testing the decorator."""
    return 42


def test_deprecated_still_emits_warning():
    # The decorated function should still raise a DeprecationWarning
    # and still return its original result.
    with pytest.warns(DeprecationWarning, match="deprecated function"):
        result = _deprecated_example()
    assert result == 42


def test_deprecated_does_not_mutate_global_filter():
    # Calling a deprecated function should not alter the global
    # warnings filter configured by the user.
    with warnings.catch_warnings():
        warnings.resetwarnings()
        warnings.simplefilter("ignore")
        filters_before = list(warnings.filters)

        _deprecated_example()

        assert warnings.filters == filters_before
