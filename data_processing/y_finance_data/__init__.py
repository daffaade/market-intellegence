"""
y_finance_data subpackage
"""
from pathlib import Path
import sys

_SUB_DIR = Path(__file__).resolve().parent
_PKG_DIR = _SUB_DIR.parent
_ROOT_DIR = _PKG_DIR.parent

for _p in [str(_SUB_DIR), str(_PKG_DIR), str(_ROOT_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)
