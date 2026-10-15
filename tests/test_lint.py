import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
import lint  # noqa: E402


def test_lint_en():
    errs = lint.lint("en")
    assert not errs, "\n".join(errs)
