"""Smoke tests — verify the package imports cleanly and version is set."""

from __future__ import annotations


def test_package_imports() -> None:
    """The quantlab package must import without errors."""
    import quantlab

    assert quantlab.__version__


def test_all_subpackages_import() -> None:
    """Every declared subpackage must import without errors."""
    from quantlab import (  # noqa: F401
        data,
        execution,
        features,
        labels,
        lenses,
        models,
        portfolio,
        regime,
        research,
        validation,
    )
