"""
data_processing package
Unified data processing combining Sectors API and yFinance API pipelines.
"""

from pathlib import Path
import sys

_PACKAGE_DIR = Path(__file__).resolve().parent
_ROOT_DIR = _PACKAGE_DIR.parent

for _p in [str(_PACKAGE_DIR), str(_ROOT_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from data_processing.endpoint_finaldata import get_api_data, get_final_data, get_section_data
from data_processing.unified_pipeline import UnifiedPipeline
from data_processing.cachingunified import UnifiedDataCache, UnifiedCacheTier
from data_processing.getunified import UnifiedDataProvider

__all__ = [
    "get_api_data",
    "get_final_data",
    "get_section_data",
    "UnifiedPipeline",
    "UnifiedDataCache",
    "UnifiedCacheTier",
    "UnifiedDataProvider",
]
