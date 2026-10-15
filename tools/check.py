"""One-command check (the pre-commit hook runs this): tests + text lint."""
import subprocess, sys
sys.exit(subprocess.call([sys.executable, "-X", "utf8", "-m", "pytest", "-q", "tests"]))
