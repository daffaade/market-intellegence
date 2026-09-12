import os
import sys
import json
import re
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def load_env(env_path: str = ".env") -> dict:
    """Load environment variables from a .env file if available."""
    env_vars = {}
    possible_paths = [
        Path(env_path),
        Path(__file__).resolve().parent / ".env",
        Path(__file__).resolve().parent.parent / ".env"
    ]
    for path in possible_paths:
        if path.is_file():
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        env_vars[k.strip()] = v.strip().strip("\"'")
            break
            
    for k, v in os.environ.items():
        if k not in env_vars:
            env_vars[k] = v
            
    return env_vars


# =====================================================================
# DATA VALIDATION MODULE
# =====================================================================

class ValidationStatus:
    VALID = "VALID"
    WARNING = "WARNING"
    INVALID = "INVALID"


class ValidationIssue:
    def __init__(self, level: str, field: str, message: str, value: Any = None):
        self.level = level  # "ERROR" or "WARNING"
        self.field = field
        self.message = message
        self.value = value

    def to_dict(self) -> dict:
        return {
            "level": self.level,
            "field": self.field,
            "message": self.message,
            "value": self.value
        }

    def __repr__(self) -> str:
        return f"[{self.level}] {self.field}: {self.message} (value={self.value})"


class ValidationResult:
    def __init__(self, data: Any = None):
        self.data = data
        self.issues: List[ValidationIssue] = []

    def add_error(self, field: str, message: str, value: Any = None):
        self.issues.append(ValidationIssue("ERROR", field, message, value))

    def add_warning(self, field: str, message: str, value: Any = None):
        self.issues.append(ValidationIssue("WARNING", field, message, value))

    @property
    def is_valid(self) -> bool:
        return not any(issue.level == "ERROR" for issue in self.issues)

    @property
    def status(self) -> str:
        if any(issue.level == "ERROR" for issue in self.issues):
            return ValidationStatus.INVALID
        if any(issue.level == "WARNING" for issue in self.issues):
            return ValidationStatus.WARNING
        return ValidationStatus.VALID

    @property
    def errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.level == "ERROR"]

    @property
    def warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.level == "WARNING"]

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "is_valid": self.is_valid,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "issues": [i.to_dict() for i in self.issues]
        }


class SectorsDataValidator:
    """
    Validates mined sectors data against schemas, data types, ranges,
    duplicates, datetimes, and cross-field logic.
    """

    @staticmethod
    def is_valid_date(date_str: str) -> bool:
        """Checks if a string is a valid ISO date (YYYY-MM-DD or ISO datetime)."""
        if not isinstance(date_str, str):
            return False
        # Remove trailing Z or timezone offset for basic parse
        clean_date = re.sub(r'([+-]\d{2}:\d{2}|Z)$', '', date_str.strip())
        for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"):
            try:
                datetime.strptime(clean_date, fmt)
                return True
            except ValueError:
                continue
        return False

    @classmethod
    def validate_category(cls, category: str, data: Any) -> ValidationResult:
        """Validates a single category record based on its domain rules."""
        result = ValidationResult(data)

        if data is None:
            result.add_error(category, "Data is null/empty for category")
            return result

        if not isinstance(data, (dict, list)):
            result.add_error(category, f"Expected dict or list, got {type(data).__name__}", data)
            return result

        # Dispatch to specific validator
        validator_map = {
            "Valuation": cls._validate_valuation,
            "Peer": cls._validate_peer,
            "Future Forecast": cls._validate_future_forecast,
            "Institutional Transactions": cls._validate_institutional_transactions,
            "Executive Shareholdings": cls._validate_executive_shareholdings,
            "Major Shareholders": cls._validate_major_shareholders,
            "Shareholder Composition": cls._validate_shareholder_composition,
            "Dividend": cls._validate_dividend,
            "Executives": cls._validate_executives,
            "Historical Price": cls._validate_historical_price,
        }

        validator_fn = validator_map.get(category)
        if validator_fn:
            validator_fn(data, result)
        else:
            cls._validate_generic(category, data, result)

        return result

    @classmethod
    def _validate_valuation(cls, data: dict, result: ValidationResult):
        if not isinstance(data, dict):
            result.add_error("Valuation", "Valuation data must be a dictionary", data)
            return

        # Check numeric valuation metrics
        if "forward_pe" in data and data["forward_pe"] is not None:
            fpe = data["forward_pe"]
            if not isinstance(fpe, (int, float)):
                result.add_error("forward_pe", "forward_pe must be numeric", fpe)
            elif fpe < 0:
                result.add_warning("forward_pe", "Negative forward PE indicates negative projected earnings", fpe)
            elif fpe > 300:
                result.add_warning("forward_pe", "Extremely high forward PE (>300)", fpe)

        if "intrinsic_value" in data and data["intrinsic_value"] is not None:
            iv = data["intrinsic_value"]
            if not isinstance(iv, (int, float)):
                result.add_error("intrinsic_value", "intrinsic_value must be numeric", iv)
            elif iv < 0:
                result.add_warning("intrinsic_value", "Negative intrinsic value", iv)

        if "sample_historical_valuation" in data:
            hist_val = data["sample_historical_valuation"]
            if isinstance(hist_val, dict):
                if "pe" in hist_val and hist_val["pe"] is not None and not isinstance(hist_val["pe"], (int, float)):
                    result.add_error("sample_historical_valuation.pe", "PE must be numeric", hist_val["pe"])
                if "pb" in hist_val and hist_val["pb"] is not None and not isinstance(hist_val["pb"], (int, float)):
                    result.add_error("sample_historical_valuation.pb", "PB must be numeric", hist_val["pb"])

    @classmethod
    def _validate_peer(cls, data: dict, result: ValidationResult):
        if not isinstance(data, dict):
            result.add_error("Peer", "Peer data must be a dictionary", data)
            return

        # Required fields
        if "symbol" not in data or not data["symbol"]:
            result.add_error("symbol", "Missing required field: symbol in Peer", data)
        if "company_name" not in data or not data["company_name"]:
            result.add_warning("company_name", "Missing company_name in Peer", data)

        # Numeric validations
        for num_field in ["market_cap", "net_income", "total_assets", "total_revenue"]:
            if num_field in data and data[num_field] is not None:
                val = data[num_field]
                if not isinstance(val, (int, float)):
                    result.add_error(num_field, f"{num_field} must be numeric", val)
                elif num_field in ["market_cap", "total_assets"] and val < 0:
                    result.add_error(num_field, f"{num_field} cannot be negative", val)

        # Cross-field check: total_assets vs total_liabilities + total_equity
        if "total_assets" in data and "total_liabilities" in data and "total_equity" in data:
            ta = data.get("total_assets")
            tl = data.get("total_liabilities")
            te = data.get("total_equity")
            if all(isinstance(v, (int, float)) for v in [ta, tl, te]):
                if abs(ta - (tl + te)) > (ta * 0.05 + 1e-6):  # allowing 5% discrepancy margin for approximations
                    result.add_warning("balance_sheet_consistency", f"Assets ({ta}) differs from Liab+Equity ({tl+te})")

    @classmethod
    def _validate_future_forecast(cls, data: dict, result: ValidationResult):
        if not isinstance(data, dict):
            result.add_error("Future Forecast", "Forecast data must be a dictionary", data)
            return

        if "estimate_year" in data and data["estimate_year"] is not None:
            yr = data["estimate_year"]
            if not isinstance(yr, int) or yr < 2000 or yr > 2100:
                result.add_warning("estimate_year", f"Unusual forecast estimate year: {yr}", yr)

        for num_field in ["eps_estimate", "revenue_estimate"]:
            if num_field in data and data[num_field] is not None:
                val = data[num_field]
                if not isinstance(val, (int, float)):
                    result.add_error(num_field, f"{num_field} must be numeric", val)

    @classmethod
    def _validate_institutional_transactions(cls, data: dict, result: ValidationResult):
        if not isinstance(data, dict):
            result.add_error("Institutional Transactions", "Transaction data must be a dictionary", data)
            return

        if "date" in data and data["date"]:
            if not cls.is_valid_date(str(data["date"])):
                result.add_error("date", "Invalid date format in Institutional Transactions", data["date"])

        for party in ["sample_buyer", "sample_seller"]:
            if party in data and data[party] is not None:
                p_data = data[party]
                if isinstance(p_data, dict):
                    if "name" not in p_data or not p_data["name"]:
                        result.add_warning(f"{party}.name", "Missing institution name", p_data)
                    if "changeAmount" in p_data and p_data["changeAmount"] is not None:
                        if not isinstance(p_data["changeAmount"], (int, float)):
                            result.add_error(f"{party}.changeAmount", "changeAmount must be numeric", p_data["changeAmount"])

    @classmethod
    def _validate_executive_shareholdings(cls, data: dict, result: ValidationResult):
        if not isinstance(data, dict):
            result.add_error("Executive Shareholdings", "Shareholding data must be a dictionary", data)
            return

        if "name" not in data or not data["name"]:
            result.add_error("name", "Missing required executive name", data)

        if "share_amount" in data and data["share_amount"] is not None:
            val = data["share_amount"]
            if not isinstance(val, (int, float)) or val < 0:
                result.add_error("share_amount", "share_amount must be a non-negative number", val)

        if "share_percentage" in data and data["share_percentage"] is not None:
            pct = data["share_percentage"]
            try:
                pct_val = float(pct)
                if pct_val < 0 or pct_val > 100:
                    result.add_error("share_percentage", "share_percentage must be between 0 and 100 (or 0 and 1.0)", pct)
            except (ValueError, TypeError):
                result.add_error("share_percentage", "Invalid percentage format", pct)

    @classmethod
    def _validate_major_shareholders(cls, data: dict, result: ValidationResult):
        if not isinstance(data, dict):
            result.add_error("Major Shareholders", "Shareholder data must be a dictionary", data)
            return

        if "name" not in data or not data["name"]:
            result.add_error("name", "Missing major shareholder name", data)

        if "share_percentage" in data and data["share_percentage"] is not None:
            pct = data["share_percentage"]
            try:
                pct_val = float(pct)
                if pct_val < 0 or pct_val > 100:
                    result.add_error("share_percentage", "share_percentage out of range [0, 100]", pct)
            except (ValueError, TypeError):
                result.add_error("share_percentage", "Invalid percentage format", pct)

    @classmethod
    def _validate_shareholder_composition(cls, data: dict, result: ValidationResult):
        if not isinstance(data, dict):
            result.add_error("Shareholder Composition", "Composition data must be a dictionary", data)
            return
        if not data:
            result.add_warning("Shareholder Composition", "Composition data is empty", data)

    @classmethod
    def _validate_dividend(cls, data: dict, result: ValidationResult):
        if not isinstance(data, dict):
            result.add_error("Dividend", "Dividend data must be a dictionary", data)
            return

        if "year" in data and data["year"] is not None:
            try:
                yr = int(data["year"])
                if yr < 1990 or yr > 2100:
                    result.add_warning("year", f"Unusual dividend year: {yr}", yr)
            except ValueError:
                result.add_error("year", "Invalid dividend year format", data["year"])

        div_data = data.get("data", {})
        if isinstance(div_data, dict):
            if "total_dividend" in div_data and div_data["total_dividend"] is not None:
                if not isinstance(div_data["total_dividend"], (int, float)) or div_data["total_dividend"] < 0:
                    result.add_error("total_dividend", "total_dividend must be non-negative numeric", div_data["total_dividend"])

            # Cross-field validation: sum of breakdown totals
            breakdown = div_data.get("breakdown", [])
            if isinstance(breakdown, list) and breakdown and "total_dividend" in div_data:
                calc_total = 0.0
                for item in breakdown:
                    if isinstance(item, dict) and "total" in item and isinstance(item["total"], (int, float)):
                        calc_total += item["total"]
                    if isinstance(item, dict) and "date" in item and item["date"]:
                        if not cls.is_valid_date(str(item["date"])):
                            result.add_error("breakdown.date", "Invalid breakdown date", item["date"])
                
                expected_total = float(div_data["total_dividend"])
                if abs(calc_total - expected_total) > 0.01:
                    result.add_warning("dividend_breakdown_sum", f"Sum of breakdown ({calc_total}) != total_dividend ({expected_total})")

    @classmethod
    def _validate_executives(cls, data: dict, result: ValidationResult):
        if not isinstance(data, dict):
            result.add_error("Executives", "Executives data must be a dictionary", data)
            return

        if "name" not in data or not data["name"]:
            result.add_error("name", "Missing required executive name", data)
        if "position" not in data or not data["position"]:
            result.add_warning("position", "Missing executive position", data)

    @classmethod
    def _validate_historical_price(cls, data: dict, result: ValidationResult):
        if not isinstance(data, dict):
            result.add_error("Historical Price", "Price record must be a dictionary", data)
            return

        # Required fields
        for req in ["symbol", "date", "close"]:
            if req not in data or data[req] is None:
                result.add_error(req, f"Missing required price field: {req}", data)

        # Date validation
        if "date" in data and data["date"]:
            if not cls.is_valid_date(str(data["date"])):
                result.add_error("date", "Invalid date format in historical price", data["date"])

        # OHLC numeric and range checks
        for p in ["open", "high", "low", "close"]:
            if p in data and data[p] is not None:
                val = data[p]
                if not isinstance(val, (int, float)):
                    result.add_error(p, f"{p} must be numeric", val)
                elif val <= 0:
                    result.add_error(p, f"{p} price must be greater than 0", val)

        if "volume" in data and data["volume"] is not None:
            vol = data["volume"]
            if not isinstance(vol, (int, float)) or vol < 0:
                result.add_error("volume", "Volume must be a non-negative number", vol)

        # Cross-field consistency: High >= Low, High >= Open/Close, Low <= Open/Close
        ohlc = {k: data[k] for k in ["open", "high", "low", "close"] if k in data and isinstance(data[k], (int, float))}
        if len(ohlc) == 4:
            if ohlc["high"] < ohlc["low"]:
                result.add_error("ohlc_consistency", f"High ({ohlc['high']}) is less than Low ({ohlc['low']})")
            if ohlc["high"] < max(ohlc["open"], ohlc["close"]):
                result.add_error("ohlc_consistency", f"High ({ohlc['high']}) is lower than Open/Close")
            if ohlc["low"] > min(ohlc["open"], ohlc["close"]):
                result.add_error("ohlc_consistency", f"Low ({ohlc['low']}) is higher than Open/Close")

    @classmethod
    def _validate_generic(cls, category: str, data: Any, result: ValidationResult):
        if not data:
            result.add_warning(category, "Category data is empty or null", data)

    @classmethod
    def validate_mined_dataset(cls, dataset: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates full mined dataset containing multiple categories.
        Returns a comprehensive report.
        """
        category_reports = {}
        total_errors = 0
        total_warnings = 0

        for category, content in dataset.items():
            cat_result = cls.validate_category(category, content)
            category_reports[category] = cat_result.to_dict()
            total_errors += len(cat_result.errors)
            total_warnings += len(cat_result.warnings)

        if total_errors > 0:
            overall_status = ValidationStatus.INVALID
        elif total_warnings > 0:
            overall_status = ValidationStatus.WARNING
        else:
            overall_status = ValidationStatus.VALID

        return {
            "overall_status": overall_status,
            "is_valid": total_errors == 0,
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "categories": category_reports
        }


# =====================================================================
# DATA MINER MODULE
# =====================================================================

class SectorsDataMiner:
    """
    Mines financial data from Sectors API v2 with automatic error handling,
    data extraction, and built-in schema/data validation.
    """
    BASE_URL = "https://api.sectors.app/v2"

    def __init__(self, api_key: Optional[str] = None):
        if not api_key:
            env = load_env()
            api_key = env.get("SECTORS_API_KEY")
        if not api_key:
            raise ValueError("SECTORS_API_KEY not found in environment or .env file.")
        
        self.api_key = api_key
        self.headers = {
            "Authorization": self.api_key,
            "User-Agent": "MarketIntelligenceMiner/1.0"
        }
        self.validator = SectorsDataValidator()

    def _get(self, endpoint: str) -> Optional[Union[dict, list]]:
        """Helper to send HTTP GET request to Sectors API v2."""
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        req = urllib.request.Request(url, headers=self.headers)
        try:
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            # Return None to skip missing/404 endpoints gracefully
            return None
        except Exception:
            return None

    def mine_company_report(self, symbol: str) -> Optional[dict]:
        """Fetches complete company report from Sectors API."""
        clean_symbol = symbol.replace(".JK", "").upper()
        return self._get(f"/company/report/{clean_symbol}/")

    def mine_daily_prices(self, symbol: str) -> Optional[List[dict]]:
        """Fetches daily historical price array for the ticker."""
        clean_symbol = symbol.replace(".JK", "").upper()
        return self._get(f"/daily/{clean_symbol}/")

    def mine_sample_data(self, symbol: str = "BBCA", validate: bool = True) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
        """
        Mines the 10 data categories specified in dataminer.md:
        1. Valuation
        2. Peer
        3. Future Forecast
        4. Institutional Transactions
        5. Executive Shareholdings
        6. Major Shareholders
        7. Shareholder Composition
        8. Dividend
        9. Executives
        10. Historical Price

        Returns:
            Tuple of (mined_data_dict, validation_report_dict)
        """
        clean_symbol = symbol.replace(".JK", "").upper()
        report = self.mine_company_report(clean_symbol) or {}
        daily_prices = self.mine_daily_prices(clean_symbol)

        extracted_data: Dict[str, Any] = {}

        # 1. Valuation
        valuation_raw = report.get("valuation")
        if valuation_raw:
            sample_val = {}
            if "forward_pe" in valuation_raw:
                sample_val["forward_pe"] = valuation_raw.get("forward_pe")
            if "intrinsic_value" in valuation_raw:
                sample_val["intrinsic_value"] = valuation_raw.get("intrinsic_value")
            if "historical_valuation" in valuation_raw and valuation_raw["historical_valuation"]:
                sample_val["sample_historical_valuation"] = valuation_raw["historical_valuation"][0]
            if sample_val:
                extracted_data["Valuation"] = sample_val

        # 2. Peer
        peers_raw = report.get("peers")
        if peers_raw and isinstance(peers_raw, list) and len(peers_raw) > 0:
            peer_item = peers_raw[0]
            if isinstance(peer_item, dict) and "peers_data" in peer_item:
                companies = peer_item.get("peers_data", {}).get("companies", [])
                if companies:
                    extracted_data["Peer"] = companies[0]
            else:
                extracted_data["Peer"] = peer_item

        # 3. Future Forecast
        future_raw = report.get("future")
        if future_raw and isinstance(future_raw, dict):
            forecasts = future_raw.get("company_value_forecasts", [])
            if forecasts:
                extracted_data["Future Forecast"] = forecasts[0]

        # 4. Institutional Transactions
        ownership_raw = report.get("ownership", {})
        inst_flow = ownership_raw.get("institutional_transaction_flow", [])
        top_tx = ownership_raw.get("top_transactions", {})
        
        if top_tx and (top_tx.get("top_buyers") or top_tx.get("top_sellers")):
            sample_inst = {
                "date": top_tx.get("date"),
                "sample_buyer": top_tx.get("top_buyers", [None])[0],
                "sample_seller": top_tx.get("top_sellers", [None])[0]
            }
            extracted_data["Institutional Transactions"] = sample_inst
        elif inst_flow:
            extracted_data["Institutional Transactions"] = inst_flow[0]

        # 5. Executive Shareholdings
        management_raw = report.get("management", {})
        exec_shareholdings = management_raw.get("executives_shareholdings", [])
        if exec_shareholdings:
            extracted_data["Executive Shareholdings"] = exec_shareholdings[0]

        # 6. Major Shareholders
        major_holders = ownership_raw.get("major_shareholders", [])
        if major_holders:
            extracted_data["Major Shareholders"] = major_holders[0]

        # 7. Shareholder Composition
        whale_investors = ownership_raw.get("whale_investors", [])
        conglomerates = ownership_raw.get("conglomerates_group", [])
        composition = {}
        if whale_investors:
            composition["sample_whale_investor"] = whale_investors[0]
        if conglomerates:
            composition["sample_conglomerate_group"] = conglomerates[0]
        if composition:
            extracted_data["Shareholder Composition"] = composition

        # 8. Dividend
        dividend_raw = report.get("dividend", {})
        hist_div = dividend_raw.get("historical_dividends", {})
        if hist_div:
            sample_year = next(iter(hist_div))
            extracted_data["Dividend"] = {
                "year": sample_year,
                "data": hist_div[sample_year]
            }

        # 9. Executives
        executives = management_raw.get("key_executives", [])
        if executives:
            extracted_data["Executives"] = executives[0]

        # 10. Historical Price
        if daily_prices and isinstance(daily_prices, list) and len(daily_prices) > 0:
            extracted_data["Historical Price"] = daily_prices[0]

        # Perform data validation if requested
        validation_report = None
        if validate:
            validation_report = self.validator.validate_mined_dataset(extracted_data)

        return extracted_data, validation_report


def display_mining_and_validation(symbol: str, data: dict, val_report: Optional[dict]):
    """Prints mined data alongside its validation report."""
    print("=" * 75)
    print(f"📊 DATA MINING & VALIDATION RESULT for Symbol: {symbol.upper()}")
    print("=" * 75)
    
    for category, content in data.items():
        cat_val = val_report.get("categories", {}).get(category, {}) if val_report else {}
        status_icon = "✅" if cat_val.get("status") == "VALID" else ("⚠️" if cat_val.get("status") == "WARNING" else "❌")
        
        print(f"\n🔹 [{category.upper()}]  -- Validation: {status_icon} {cat_val.get('status', 'UNVALIDATED')}")
        print(json.dumps(content, indent=2, ensure_ascii=False))
        
        # Print issues if any
        if cat_val.get("issues"):
            for issue in cat_val["issues"]:
                print(f"   ↳ [{issue['level']}] Field '{issue['field']}': {issue['message']}")

    print("\n" + "=" * 75)
    print(f"📈 Summary: {len(data)} / 10 categories mined.")
    if val_report:
        print(f"🛡️  Validation Status : {val_report['overall_status']}")
        print(f"    - Total Errors   : {val_report['total_errors']}")
        print(f"    - Total Warnings : {val_report['total_warnings']}")
    print("=" * 75)


if __name__ == "__main__":
    target_symbol = sys.argv[1] if len(sys.argv) > 1 else "BBCA"
    miner = SectorsDataMiner()
    mined_data, validation_report = miner.mine_sample_data(target_symbol, validate=True)
    display_mining_and_validation(target_symbol, mined_data, validation_report)
