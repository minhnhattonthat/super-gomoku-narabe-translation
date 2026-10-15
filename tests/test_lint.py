import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
import lint  # noqa: E402


import pytest


@pytest.mark.parametrize("lang", ["en", "vi"])
def test_lint(lang):
    errs = lint.lint(lang)
    assert not errs, "\n".join(errs)
