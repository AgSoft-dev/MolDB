import sys
import io

# PyInstaller sets stdout/stderr to None in windowed mode
# Uvicorn's logging formatter calls .isatty() on them and crashes
if sys.stdout is None:
    sys.stdout = io.StringIO()
if sys.stderr is None:
    sys.stderr = io.StringIO()