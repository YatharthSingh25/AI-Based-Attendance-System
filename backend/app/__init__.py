"""Application package.

Load environment files before submodules read configuration. Platform-provided
environment variables take precedence because ``override`` is disabled.
"""

from pathlib import Path

from dotenv import load_dotenv

_BACKEND_DIR = Path(__file__).resolve().parent.parent

load_dotenv(_BACKEND_DIR / ".env")
load_dotenv(_BACKEND_DIR.parent / ".env")
