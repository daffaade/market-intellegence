"""
Tests must never spend Sectors credits (hard limit per team). Every Sectors
HTTP call is blocked unless RUN_LIVE_SECTORS=1 is set explicitly.
"""
import os

import pytest


@pytest.fixture(autouse=True)
def _block_sectors_api(monkeypatch):
    if os.environ.get("RUN_LIVE_SECTORS") == "1":
        return
    from data_processing.data_sectors.dataminer import SectorsDataMiner

    def blocked(self, endpoint):
        return None  # same as an unavailable endpoint: callers fall back to yfinance

    monkeypatch.setattr(SectorsDataMiner, "_get", blocked)
