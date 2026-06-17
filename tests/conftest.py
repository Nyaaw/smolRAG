import os
import re
import subprocess
from pathlib import Path

import pytest

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "java-sample"


@pytest.fixture
def fixture_project() -> str:
    """Absolute path to the java-sample fixture project."""
    return str(FIXTURE_DIR.resolve())


def _java_available() -> bool:
    """Return True if Java 17+ is available via JAVA_HOME."""
    java_home = os.environ.get("JAVA_HOME")
    if not java_home:
        return False
    java = Path(java_home) / "bin" / "java"
    try:
        result = subprocess.run(
            [str(java), "-version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except Exception:
        return False
    for line in (result.stderr + result.stdout).splitlines():
        m = re.search(r'"(\d+)', line)
        if m and int(m.group(1)) >= 17:
            return True
    return False


@pytest.fixture
def require_lsp() -> None:
    """Skip the test if Java 17+ is not available."""
    if not _java_available():
        pytest.skip("Java 17+ not available (set JAVA_HOME)")
