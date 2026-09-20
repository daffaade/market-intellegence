import os
import sys
import re
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union, Tuple

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


class NormalizationStatus:
    NORMALIZED = "NORMALIZED"
    NORMALIZATION_ERROR = "NORMALIZATION_ERROR"


class YFinanceDataNormalizer:
    """
    Normalizes validated Yahoo Finance data into standard, consistent format
    for storage and Machine Learning / Intelligence Engines.

    Rules applied (based on datanormalise.md):
    1. Field Name: snake_case, no leading/trailing symbols, no special symbols, spaces to '_'
    2. Data Type: standard int/float/str/bool/None/list/dict
    3. Numeric: clean numeric conversions & proper typing
    4. Percentage: standard decimal representations [0.0 - 1.0] with 6 decimal precision
    5. DateTime: ISO 8601 (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ)
    6. Currency: strip symbols (Rp, IDR, $, USD), convert to float/int
    7. Nulls: standard None for missing/empty/"N/A"/"-"/nan
    8. Categorical & Text: trimmed, clean whitespace, readable
    9. Precision: sensible rounding for prices (2 decimals), ratios (4 decimals), percentages (6 decimals)
    """

    NULL_STRINGS = {"", "n/a", "na", "null", "none", "-", "--", "nil", "nan"}
    CURRENCY_REGEX = re.compile(r'^(rp|idr|\$|usd|eur|sgd|jpy)[\s.]*', re.IGNORECASE)

    @classmethod
    def normalize_field_name(cls, key: str) -> str:
        """
        Converts any field name into standard format:
        - lowercase
        - blankspaces converted to '_'
        - camelCase / PascalCase converted to snake_case
        - special symbols removed
        - no symbol at the end of the line
        """
        if not isinstance(key, str):
            key = str(key)

        # Convert camelCase / PascalCase to snake_case (e.g. forwardPE -> forward_pe)
        s1 = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', key)
        s2 = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', s1).lower()

        # Replace spaces, hyphens, dots, and slashes with underscore
        s3 = re.sub(r'[\s\-\./\\]+', '_', s2)

        # Remove any non-alphanumeric characters except underscore
        s4 = re.sub(r'[^a-z0-9_]', '', s3)

        # Collapse consecutive underscores and strip leading/trailing underscores
        s5 = re.sub(r'_+', '_', s4).strip('_')

        return s5 or "field"

    @classmethod
    def is_null_value(cls, val: Any) -> bool:
        """Determines if a value represents a null/missing/nan value."""
        if val is None:
            return True
        if isinstance(val, float) and (str(val) == "nan" or str(val) == "inf" or str(val) == "-inf"):
            return True
        if isinstance(val, str) and val.strip().lower() in cls.NULL_STRINGS:
            return True
        return False

    @classmethod
    def normalize_text(cls, text: str) -> Optional[str]:
        """Trims whitespace, removes non-printable characters, collapses spaces."""
        if cls.is_null_value(text):
            return None
        cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', str(text))
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned if cleaned else None

    @classmethod
    def normalize_date(cls, val: Any) -> Optional[str]:
        """Converts date/datetime/timestamp into standard ISO 8601 string (YYYY-MM-DD)."""
        if cls.is_null_value(val):
            return None

        # Handle unix timestamps in seconds or milliseconds
        if isinstance(val, (int, float)) and val > 100000000:
            ts = val / 1000.0 if val > 1e11 else float(val)
            try:
                dt = datetime.fromtimestamp(ts, tz=timezone.utc)
                return dt.strftime("%Y-%m-%d")
            except Exception:
                pass

        val_str = str(val).strip()
        if re.match(r'^\d{4}-\d{2}-\d{2}$', val_str):
            return val_str

        # ISO and standard timestamp formats
        formats = [
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S%z",
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%Y/%m/%d"
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(val_str, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue

        # Regex fallback for strings starting with YYYY-MM-DD
        date_match = re.match(r'^(\d{4}-\d{2}-\d{2})', val_str)
        if date_match:
            return date_match.group(1)

        return val_str

    @classmethod
    def normalize_percentage(cls, val: Any) -> Optional[float]:
        """
        Converts percentage representation to standard decimal fraction (0.0 to 1.0)
        with 6 decimal places of precision.
        """
        if cls.is_null_value(val):
            return None

        if isinstance(val, str):
            val_clean = val.strip().replace("%", "").replace(",", ".")
            try:
                num = float(val_clean)
                if "%" in val or num > 1.0:
                    return round(num / 100.0, 6)
                return round(num, 6)
            except ValueError:
                return None

        if isinstance(val, (int, float)):
            # If percentage scale is > 1 (e.g. 6.02 meaning 6.02%), convert to decimal
            if val > 1.0:
                return round(float(val) / 100.0, 6)
            return round(float(val), 6)

        return None

    @classmethod
    def normalize_numeric(cls, val: Any, precision: int = 4) -> Optional[Union[int, float]]:
        """Cleans and standardizes numeric values."""
        if cls.is_null_value(val):
            return None

        if isinstance(val, bool):
            return val

        if isinstance(val, (int, float)):
            if isinstance(val, int):
                return val
            if val.is_integer():
                return int(val)
            return round(val, precision)

        if isinstance(val, str):
            cleaned = cls.CURRENCY_REGEX.sub('', val.strip())
            cleaned = cleaned.replace(",", "").strip()
            try:
                if "." in cleaned or "e" in cleaned.lower():
                    return round(float(cleaned), precision)
                return int(cleaned)
            except ValueError:
                return val

        return val

    @classmethod
    def normalize_value(cls, key: str, val: Any) -> Any:
        """Context-aware value normalization based on key hints and value types."""
        if cls.is_null_value(val):
            return None

        if isinstance(val, dict):
            return cls.normalize_dict(val)

        if isinstance(val, list):
            return [cls.normalize_value(key, item) for item in val]

        key_lower = key.lower()

        # Date / Timestamp field normalization
        if any(d in key_lower for d in ["date", "time", "updated_at", "created_at", "ex_dividend"]):
            return cls.normalize_date(val)

        # Percentage fields
        is_percentage_field = (
            "percentage" in key_lower or
            "percent" in key_lower or
            "pct" in key_lower or
            "yield" in key_lower or
            key_lower.endswith("_chg") or
            key_lower.endswith("_growth")
        ) and not any(non_pct in key_lower for non_pct in ["amount", "count", "num", "value", "price", "share_amount", "volume", "pay"])

        if is_percentage_field:
            return cls.normalize_percentage(val)

        # Financial / Valuation / Price numeric normalization
        if any(n in key_lower for n in [
            "price", "open", "high", "low", "close", "pe", "pb", "ps", "pcf", "peg",
            "market_cap", "revenue", "income", "assets", "liabilities", "equity",
            "volume", "amount", "value", "dividend", "forecast", "estimate", "expense",
            "num", "split", "splits", "shares", "pay"
        ]):
            if any(p in key_lower for p in ["price", "close", "open", "high", "low", "target"]):
                return cls.normalize_numeric(val, precision=2)
            elif any(r in key_lower for r in ["pe", "pb", "ps", "pcf", "peg", "ratio"]):
                return cls.normalize_numeric(val, precision=4)
            else:
                return cls.normalize_numeric(val, precision=2)

        # General Text
        if isinstance(val, str):
            return cls.normalize_text(val)

        return val

    @classmethod
    def normalize_dict(cls, d: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively normalizes all dictionary keys and values."""
        normalized = {}
        for k, v in d.items():
            norm_k = cls.normalize_field_name(k)
            norm_v = cls.normalize_value(norm_k, v)
            normalized[norm_k] = norm_v
        return normalized

    @classmethod
    def normalize_category_name(cls, category: str) -> str:
        """Standardizes category names from mining module to standard schema keys."""
        mapping = {
            "Valuation": "valuation",
            "Peer": "peer",
            "Future Forecast": "future_forecast",
            "Institutional Transactions": "institutional_transactions",
            "Executive Shareholdings": "executive_shareholdings",
            "Major Shareholders": "major_shareholders",
            "Shareholder Composition": "shareholder_composition",
            "Dividend": "dividend",
            "Executives": "executives",
            "Historical Price": "historical_price"
        }
        return mapping.get(category, cls.normalize_field_name(category))

    @classmethod
    def normalize_dataset(cls, dataset: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Normalizes full mined dataset.

        Returns:
            Tuple of (normalized_data, normalization_metadata)
        """
        normalized_data = {}
        transformed_categories = []
        errors = []

        try:
            for category, content in dataset.items():
                std_category_key = cls.normalize_category_name(category)
                if isinstance(content, dict):
                    norm_content = cls.normalize_dict(content)
                elif isinstance(content, list):
                    norm_content = [cls.normalize_value(std_category_key, item) for item in content]
                else:
                    norm_content = cls.normalize_value(std_category_key, content)

                normalized_data[std_category_key] = norm_content
                transformed_categories.append(std_category_key)

            status = NormalizationStatus.NORMALIZED
        except Exception as e:
            status = NormalizationStatus.NORMALIZATION_ERROR
            errors.append(str(e))

        metadata = {
            "status": status,
            "total_categories": len(normalized_data),
            "categories": transformed_categories,
            "errors": errors
        }

        return normalized_data, metadata


def display_normalization(original_data: dict, normalized_data: dict, meta: dict):
    """Displays clean overview of normalization results."""
    print("=" * 75)
    print("✨ YFINANCE DATA NORMALIZATION RESULT")
    print("=" * 75)

    for cat_name, content in normalized_data.items():
        print(f"\n🏷️  [{cat_name}]")
        print(json.dumps(content, indent=2, ensure_ascii=False))

    print("\n" + "=" * 75)
    print(f"📊 Normalization Status : {'✅ ' + meta['status'] if meta['status'] == 'NORMALIZED' else '❌ ' + meta['status']}")
    print(f"📦 Total Categories     : {meta['total_categories']}")
    if meta.get("errors"):
        print(f"⚠️  Errors               : {meta['errors']}")
    print("=" * 75)


if __name__ == "__main__":
    from data_processing.y_finance_data.datamineryfinance import YFinanceDataMiner

    target_symbol = sys.argv[1] if len(sys.argv) > 1 else "BBCA.JK"
    print(f"🔍 Mining Yahoo Finance data for {target_symbol}...")
    miner = YFinanceDataMiner()
    mined_data, val_report = miner.mine_sample_data(target_symbol, validate=True)

    print(f"⚙️  Normalizing mined data...")
    normalizer = YFinanceDataNormalizer()
    normalized_data, meta = normalizer.normalize_dataset(mined_data)

    display_normalization(mined_data, normalized_data, meta)
