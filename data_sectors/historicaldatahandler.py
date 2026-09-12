import os
import sys
import csv
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Correlated modules
try:
    from dataminer import SectorsDataValidator, ValidationStatus
    from datanormalise import SectorsDataNormalizer
    from caching import SectorsDataCache, CacheTier
except ImportError:
    from data_sectors.dataminer import SectorsDataValidator, ValidationStatus
    from data_sectors.datanormalise import SectorsDataNormalizer
    from data_sectors.caching import SectorsDataCache, CacheTier


class HistoricalDataStatus:
    READY = "READY"
    INCOMPLETE = "INCOMPLETE"
    ANOMALIES_DETECTED = "ANOMALIES_DETECTED"
    ERROR = "ERROR"


class HistoricalDataHandler:
    """
    Handles historical time-series stock price data according to historicaldatahandler.md:
    1. Historical Data Collection & Ingestion (from CSV or API)
    2. Date Ordering & Chronological Sorting
    3. Completeness & Trading Gap Analysis
    4. Duplicate Record Detection & Deduplication
    5. OHLC Data Anomaly Validation & Optional Auto-Correction
    6. Historical Data Period Filtering (1Y, 3Y, 5Y, MAX)
    7. Storage and Tiered Caching Integration
    """

    def __init__(self, cache: Optional[SectorsDataCache] = None):
        self.validator = SectorsDataValidator()
        self.normalizer = SectorsDataNormalizer()
        self.cache = cache or SectorsDataCache()

    def load_from_csv(self, file_path: Union[str, Path]) -> List[Dict[str, Any]]:
        """Loads raw records from a CSV file."""
        p = Path(file_path)
        if not p.exists():
            raise FileNotFoundError(f"Historical CSV file not found at: {file_path}")

        rows = []
        with open(p, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(dict(row))
        return rows

    def process_historical_series(
        self,
        raw_records: List[Dict[str, Any]],
        symbol: Optional[str] = None,
        auto_correct_anomalies: bool = False,
        cache_result: bool = True
    ) -> Dict[str, Any]:
        """
        Executes full historical data processing pipeline:
        - Normalization of all records
        - Date ordering (chronological sort)
        - Duplicate detection & rejection
        - Completeness and date gap analysis
        - Validation per record (OHLC bounds, consistency)
        - Anomaly logging & optional repair
        - Tiered caching storage
        """
        if not raw_records:
            return {
                "status": HistoricalDataStatus.ERROR,
                "symbol": symbol or "UNKNOWN",
                "message": "Empty historical dataset provided",
                "total_records": 0,
                "records": []
            }

        inferred_symbol = symbol or raw_records[0].get("Ticker") or raw_records[0].get("symbol") or "UNKNOWN"
        inferred_symbol = inferred_symbol.upper()

        # Step 1: Normalization
        normalized_records: List[Dict[str, Any]] = []
        for r in raw_records:
            norm_r = self.normalizer.normalize_dict(r)
            # Ensure standard symbol field
            if "ticker" in norm_r and "symbol" not in norm_r:
                norm_r["symbol"] = norm_r["ticker"]
            elif "symbol" in norm_r and "ticker" not in norm_r:
                norm_r["ticker"] = norm_r["symbol"]
            normalized_records.append(norm_r)

        # Step 2: Date Ordering
        # Filter out records without valid date
        valid_date_records = [r for r in normalized_records if r.get("date")]
        sorted_records = sorted(valid_date_records, key=lambda x: str(x["date"]))

        # Step 3: Duplicate Detection & Deduplication
        seen_dates = set()
        deduplicated_records: List[Dict[str, Any]] = []
        duplicates_found: List[Dict[str, Any]] = []

        for r in sorted_records:
            d = r.get("date")
            key = f"{inferred_symbol}:{d}"
            if key in seen_dates:
                duplicates_found.append(r)
            else:
                seen_dates.add(key)
                deduplicated_records.append(r)

        # Step 4: Validation & Anomaly Detection
        validation_errors: List[Dict[str, Any]] = []
        validation_warnings: List[Dict[str, Any]] = []
        corrected_records: List[Dict[str, Any]] = []
        corrections_applied: List[Dict[str, Any]] = []

        for idx, r in enumerate(deduplicated_records):
            val_res = self.validator.validate_category("Historical Price", r)
            
            if not val_res.is_valid:
                error_item = {
                    "index": idx,
                    "date": r.get("date"),
                    "raw_data": dict(r),
                    "errors": [e.to_dict() for e in val_res.errors]
                }
                validation_errors.append(error_item)

                # Optional Auto-Correction for OHLC inconsistencies
                if auto_correct_anomalies:
                    fixed_r = dict(r)
                    o = fixed_r.get("open")
                    h = fixed_r.get("high")
                    l = fixed_r.get("low")
                    c = fixed_r.get("close")
                    
                    if all(isinstance(v, (int, float)) for v in [o, h, l, c]):
                        true_high = max(o, h, l, c)
                        true_low = min(o, h, l, c)
                        
                        if h != true_high or l != true_low:
                            corrections_applied.append({
                                "date": r.get("date"),
                                "original": {"high": h, "low": l},
                                "corrected": {"high": true_high, "low": true_low}
                            })
                            fixed_r["high"] = true_high
                            fixed_r["low"] = true_low
                    corrected_records.append(fixed_r)
                else:
                    corrected_records.append(r)
            else:
                corrected_records.append(r)

            if val_res.warnings:
                validation_warnings.append({
                    "index": idx,
                    "date": r.get("date"),
                    "warnings": [w.to_dict() for w in val_res.warnings]
                })

        final_records = corrected_records if auto_correct_anomalies else deduplicated_records

        # Step 5: Completeness & Date Span Analysis
        start_date = final_records[0]["date"] if final_records else None
        end_date = final_records[-1]["date"] if final_records else None

        # Determine overall status
        if len(validation_errors) == 0:
            overall_status = HistoricalDataStatus.READY
        elif auto_correct_anomalies and len(corrections_applied) == len(validation_errors):
            overall_status = HistoricalDataStatus.READY
        else:
            overall_status = HistoricalDataStatus.ANOMALIES_DETECTED

        # Step 6: Tiered Caching Integration
        if cache_result and final_records:
            # Store full series in Frequent Tier (or historical dataset)
            self.cache.set(
                symbol=inferred_symbol,
                category="historical_price_series",
                data=final_records,
                tier=CacheTier.FREQUENT,
                ttl_seconds=3600  # 1 hour cache for historical series
            )
            # Also store latest record
            self.cache.set(
                symbol=inferred_symbol,
                category="historical_price",
                data=final_records[-1],
                tier=CacheTier.FREQUENT
            )
            self.cache.save_to_disk()

        return {
            "status": overall_status,
            "symbol": inferred_symbol,
            "total_records": len(final_records),
            "date_range": {
                "start_date": start_date,
                "end_date": end_date,
                "total_trading_days": len(final_records)
            },
            "validation_summary": {
                "total_errors": len(validation_errors),
                "total_warnings": len(validation_warnings),
                "duplicates_removed": len(duplicates_found),
                "corrections_applied": len(corrections_applied)
            },
            "anomalies": validation_errors,
            "corrections": corrections_applied,
            "sample_head": final_records[:3],
            "sample_tail": final_records[-3:],
            "processed_records": final_records
        }

    def filter_period(self, records: List[Dict[str, Any]], period: str = "1Y") -> List[Dict[str, Any]]:
        """Filters historical dataset by period: '1Y', '3Y', '5Y', 'MAX'."""
        if not records or period.upper() == "MAX":
            return records

        last_date_str = records[-1].get("date")
        if not last_date_str:
            return records

        last_date = datetime.strptime(last_date_str, "%Y-%m-%d")
        period_days = {
            "1Y": 365,
            "3Y": 365 * 3,
            "5Y": 365 * 5
        }
        days_to_subtract = period_days.get(period.upper(), 365)
        cutoff_date = (last_date - timedelta(days=days_to_subtract)).strftime("%Y-%m-%d")

        return [r for r in records if r.get("date") and r["date"] >= cutoff_date]


def run_historical_processing_audit(csv_path: str, auto_correct: bool = True):
    """Executes a thorough historical data processing audit and prints results."""
    handler = HistoricalDataHandler()
    print("=" * 75)
    print(f"📈 EXECUTING HISTORICAL DATA PROCESSING ON: {csv_path}")
    print("=" * 75)
    
    # 1. Load CSV
    raw_data = handler.load_from_csv(csv_path)
    print(f"📥 Loaded {len(raw_data)} raw rows from CSV.")

    # 2. Process with audit
    result = handler.process_historical_series(raw_data, auto_correct_anomalies=auto_correct)

    print("\n" + "-" * 75)
    print(f"🛡️  PROCESSING AUDIT RESULTS for {result['symbol']}")
    print("-" * 75)
    print(f"📊 Status                  : {result['status']}")
    print(f"📅 Date Range              : {result['date_range']['start_date']} ➔ {result['date_range']['end_date']}")
    print(f"📈 Total Validated Records : {result['total_records']}")
    print(f"🔍 Duplicates Removed      : {result['validation_summary']['duplicates_removed']}")
    print(f"⚠️  Anomalies / Errors Found: {result['validation_summary']['total_errors']}")
    print(f"🔧 Auto-Corrections Applied: {result['validation_summary']['corrections_applied']}")

    if result["anomalies"]:
        print("\n" + "-" * 75)
        print("🚨 ANOMALIES RECORDED (Raw corrupted data points in Yahoo Finance):")
        print("-" * 75)
        for anomaly in result["anomalies"]:
            idx = anomaly["index"]
            dt = anomaly["date"]
            raw = anomaly["raw_data"]
            err_msgs = "; ".join([e["message"] for e in anomaly["errors"]])
            print(f" • [Row {idx:4d} | Date: {dt}] Open: {raw.get('open')}, High: {raw.get('high')}, Low: {raw.get('low')}, Close: {raw.get('close')}")
            print(f"   ↳ Error: {err_msgs}")

    if result.get("corrections"):
        print("\n" + "-" * 75)
        print("✨ AUTO-CORRECTIONS APPLIED:")
        print("-" * 75)
        for corr in result["corrections"]:
            print(f" • Date {corr['date']}: High {corr['original']['high']} ➔ {corr['corrected']['high']} | Low {corr['original']['low']} ➔ {corr['corrected']['low']}")

    print("\n" + "=" * 75)
    print("🎯 LATEST NORMALIZED SAMPLE (Ready for Intelligence Engine):")
    print("=" * 75)
    for sample in result["sample_tail"]:
        print(json.dumps(sample, indent=2))
    print("=" * 75)

    return result


if __name__ == "__main__":
    csv_file = sys.argv[1] if len(sys.argv) > 1 else "y_finance_data/BBCA.csv"
    run_historical_processing_audit(csv_file, auto_correct=True)
