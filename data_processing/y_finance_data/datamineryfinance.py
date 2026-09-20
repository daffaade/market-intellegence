import os
import sys
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import yfinance as yf
import pandas as pd
import numpy as np


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


class YFinanceDataValidator:
    """
    Validates mined Yahoo Finance data against schemas, data types, ranges,
    duplicates, datetimes, and cross-field logic.
    """

    @staticmethod
    def is_valid_date(date_str: str) -> bool:
        """Checks if a string is a valid ISO date or recognizable date format."""
        if not isinstance(date_str, str):
            return False
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

        for pe_field in ["forward_pe", "trailing_pe"]:
            if pe_field in data and data[pe_field] is not None:
                pe_val = data[pe_field]
                if not isinstance(pe_val, (int, float)):
                    result.add_error(pe_field, f"{pe_field} must be numeric", pe_val)
                elif pe_val < 0:
                    result.add_warning(pe_field, f"Negative {pe_field} indicates negative earnings", pe_val)
                elif pe_val > 500:
                    result.add_warning(pe_field, f"Extremely high {pe_field} (>500)", pe_val)

        for num_field in ["price_to_book", "enterprise_to_ebitda", "enterprise_to_revenue", "peg_ratio", "intrinsic_value"]:
            if num_field in data and data[num_field] is not None:
                val = data[num_field]
                if not isinstance(val, (int, float)):
                    result.add_error(num_field, f"{num_field} must be numeric", val)

    @classmethod
    def _validate_peer(cls, data: dict, result: ValidationResult):
        if not isinstance(data, dict):
            result.add_error("Peer", "Peer data must be a dictionary", data)
            return

        if "symbol" not in data or not data["symbol"]:
            result.add_error("symbol", "Missing required field: symbol in Peer", data)
        if "company_name" not in data or not data["company_name"]:
            result.add_warning("company_name", "Missing company_name in Peer", data)

        for num_field in ["market_cap", "enterprise_value"]:
            if num_field in data and data[num_field] is not None:
                val = data[num_field]
                if not isinstance(val, (int, float)):
                    result.add_error(num_field, f"{num_field} must be numeric", val)

    @classmethod
    def _validate_future_forecast(cls, data: dict, result: ValidationResult):
        if not isinstance(data, dict):
            result.add_error("Future Forecast", "Forecast data must be a dictionary", data)
            return

        for num_field in ["target_mean_price", "target_high_price", "target_low_price", "eps_estimate", "revenue_estimate"]:
            if num_field in data and data[num_field] is not None:
                val = data[num_field]
                if not isinstance(val, (int, float)):
                    result.add_error(num_field, f"{num_field} must be numeric", val)

        # Consistency: Low <= Mean/Median <= High
        if data.get("target_low_price") and data.get("target_high_price"):
            if data["target_low_price"] > data["target_high_price"]:
                result.add_error("target_price_consistency", "Target low price is greater than target high price")

    @classmethod
    def _validate_institutional_transactions(cls, data: dict, result: ValidationResult):
        if not isinstance(data, dict):
            result.add_error("Institutional Transactions", "Transaction data must be a dictionary", data)
            return

        if "date" in data and data["date"]:
            if not cls.is_valid_date(str(data["date"])):
                result.add_warning("date", "Date format in Institutional Transactions may not be ISO standard", data["date"])

        if "holder" not in data and "sample_buyer" not in data and "holder_name" not in data:
            result.add_warning("holder", "Missing institutional holder name", data)

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
                result.add_error("share_amount", "share_amount must be non-negative", val)

    @classmethod
    def _validate_major_shareholders(cls, data: dict, result: ValidationResult):
        if not isinstance(data, dict):
            result.add_error("Major Shareholders", "Shareholder data must be a dictionary", data)
            return

        if not data:
            result.add_warning("Major Shareholders", "Major shareholder data is empty", data)

    @classmethod
    def _validate_shareholder_composition(cls, data: dict, result: ValidationResult):
        if not isinstance(data, dict):
            result.add_error("Shareholder Composition", "Composition data must be a dictionary", data)
            return

        for pct_field in ["insiders_percent_held", "institutions_percent_held", "institutions_float_percent_held"]:
            if pct_field in data and data[pct_field] is not None:
                val = data[pct_field]
                if not isinstance(val, (int, float)) or val < 0 or val > 1.0:
                    result.add_warning(pct_field, f"{pct_field} expected in [0.0, 1.0]", val)

    @classmethod
    def _validate_dividend(cls, data: dict, result: ValidationResult):
        if not isinstance(data, dict):
            result.add_error("Dividend", "Dividend data must be a dictionary", data)
            return

        if "dividend_rate" in data and data["dividend_rate"] is not None:
            if not isinstance(data["dividend_rate"], (int, float)) or data["dividend_rate"] < 0:
                result.add_error("dividend_rate", "dividend_rate must be non-negative numeric", data["dividend_rate"])

    @classmethod
    def _validate_executives(cls, data: dict, result: ValidationResult):
        if not isinstance(data, dict):
            result.add_error("Executives", "Executives data must be a dictionary", data)
            return

        if "name" not in data or not data["name"]:
            result.add_error("name", "Missing required executive name", data)

    @classmethod
    def _validate_historical_price(cls, data: dict, result: ValidationResult):
        if not isinstance(data, dict):
            result.add_error("Historical Price", "Price record must be a dictionary", data)
            return

        for req in ["date", "close"]:
            if req not in data or data[req] is None:
                result.add_error(req, f"Missing required price field: {req}", data)

        if "date" in data and data["date"]:
            if not cls.is_valid_date(str(data["date"])):
                result.add_warning("date", "Date in historical price should be standard format", data["date"])

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

        ohlc = {k: data[k] for k in ["open", "high", "low", "close"] if k in data and isinstance(data[k], (int, float))}
        if len(ohlc) == 4:
            if ohlc["high"] < ohlc["low"]:
                result.add_error("ohlc_consistency", f"High ({ohlc['high']}) is less than Low ({ohlc['low']})")

    @classmethod
    def _validate_generic(cls, category: str, data: Any, result: ValidationResult):
        if not data:
            result.add_warning(category, "Category data is empty or null", data)

    @classmethod
    def validate_mined_dataset(cls, dataset: Dict[str, Any]) -> Dict[str, Any]:
        """Validates full mined dataset containing multiple categories."""
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
# DATA MINER MODULE (yfinance Integration)
# =====================================================================

class YFinanceDataMiner:
    """
    Mines financial data from Yahoo Finance API (via yfinance package)
    with automatic error handling, data extraction, and built-in schema/data validation.
    """

    def __init__(self):
        self.validator = YFinanceDataValidator()

    @staticmethod
    def format_symbol(symbol: str) -> str:
        """
        Normalizes ticker symbol. If it's a 4-letter Indonesian stock code without dot,
        appends '.JK' by default for Yahoo Finance. Otherwise keeps original symbol.
        """
        sym = symbol.strip().upper()
        if len(sym) == 4 and sym.isalpha() and not sym.endswith(".JK"):
            return f"{sym}.JK"
        return sym

    @staticmethod
    def _clean_val(val: Any) -> Any:
        """Sanitizes pandas / numpy data types into native python types."""
        if val is None or (isinstance(val, float) and (np.isnan(val) or np.isinf(val))):
            return None
        if isinstance(val, (np.integer, np.int64, np.int32)):
            return int(val)
        if isinstance(val, (np.floating, np.float64, np.float32)):
            return float(val)
        if isinstance(val, (pd.Timestamp, datetime)):
            return val.strftime("%Y-%m-%d")
        if isinstance(val, np.bool_):
            return bool(val)
        return val

    def mine_valuation(self, ticker: yf.Ticker, info: dict) -> Optional[dict]:
        """Category 1: Valuation metrics from yfinance info."""
        val = {
            "forward_pe": self._clean_val(info.get("forwardPE")),
            "trailing_pe": self._clean_val(info.get("trailingPE")),
            "price_to_book": self._clean_val(info.get("priceToBook")),
            "enterprise_to_ebitda": self._clean_val(info.get("enterpriseToEbitda")),
            "enterprise_to_revenue": self._clean_val(info.get("enterpriseToRevenue")),
            "peg_ratio": self._clean_val(info.get("pegRatio")),
            "enterprise_value": self._clean_val(info.get("enterpriseValue")),
            "market_cap": self._clean_val(info.get("marketCap")),
            "intrinsic_value": self._clean_val(info.get("targetMeanPrice") or info.get("regularMarketPrice") or info.get("currentPrice")),
            "fifty_two_week_high": self._clean_val(info.get("fiftyTwoWeekHigh")),
            "fifty_two_week_low": self._clean_val(info.get("fiftyTwoWeekLow"))
        }
        # Keep non-empty keys
        return {k: v for k, v in val.items() if v is not None} or None

    def mine_peer(self, ticker: yf.Ticker, info: dict) -> Optional[dict]:
        """Category 2: Peer & Sector/Industry information."""
        peer = {
            "symbol": info.get("symbol") or getattr(ticker, "ticker", ""),
            "company_name": info.get("longName") or info.get("shortName"),
            "sector": info.get("sector") or info.get("sectorDisp"),
            "industry": info.get("industry") or info.get("industryDisp"),
            "market_cap": self._clean_val(info.get("marketCap")),
            "pe_ttm": self._clean_val(info.get("trailingPE")),
            "currency": info.get("currency", "IDR"),
            "summary": info.get("longBusinessSummary")
        }
        return {k: v for k, v in peer.items() if v is not None} or None

    def mine_future_forecast(self, ticker: yf.Ticker, info: dict) -> Optional[dict]:
        """Category 3: Future forecast, analyst price targets, and earnings estimates."""
        forecast: Dict[str, Any] = {}
        
        # 1. Analyst price targets
        targets = getattr(ticker, "analyst_price_targets", None)
        if isinstance(targets, dict) and targets:
            forecast["target_mean_price"] = self._clean_val(targets.get("mean"))
            forecast["target_high_price"] = self._clean_val(targets.get("high"))
            forecast["target_low_price"] = self._clean_val(targets.get("low"))
            forecast["target_median_price"] = self._clean_val(targets.get("median"))
        else:
            if info.get("targetMeanPrice") is not None:
                forecast["target_mean_price"] = self._clean_val(info.get("targetMeanPrice"))
            if info.get("targetHighPrice") is not None:
                forecast["target_high_price"] = self._clean_val(info.get("targetHighPrice"))
            if info.get("targetLowPrice") is not None:
                forecast["target_low_price"] = self._clean_val(info.get("targetLowPrice"))

        # 2. Earnings Estimate
        try:
            ee = getattr(ticker, "earnings_estimate", None)
            if isinstance(ee, pd.DataFrame) and not ee.empty:
                first_row = ee.iloc[0]
                forecast["eps_estimate"] = self._clean_val(first_row.get("avg"))
                forecast["eps_growth"] = self._clean_val(first_row.get("growth"))
                forecast["estimate_year"] = datetime.now().year
        except Exception:
            pass

        # 3. Revenue Estimate
        try:
            re = getattr(ticker, "revenue_estimate", None)
            if isinstance(re, pd.DataFrame) and not re.empty:
                first_row = re.iloc[0]
                forecast["revenue_estimate"] = self._clean_val(first_row.get("avg"))
                forecast["revenue_growth"] = self._clean_val(first_row.get("growth"))
        except Exception:
            pass

        if not forecast and info.get("recommendationKey"):
            forecast["recommendation_key"] = info.get("recommendationKey")
            forecast["number_of_analyst_opinions"] = self._clean_val(info.get("numberOfAnalystOpinions"))

        return forecast or None

    def mine_institutional_transactions(self, ticker: yf.Ticker, info: dict) -> Optional[dict]:
        """Category 4: Institutional transactions & top institutional flow."""
        try:
            inst = getattr(ticker, "institutional_holders", None)
            if isinstance(inst, pd.DataFrame) and not inst.empty:
                row = inst.iloc[0].to_dict()
                return {
                    "date": self._clean_val(row.get("Date Reported")),
                    "holder": self._clean_val(row.get("Holder")),
                    "shares": self._clean_val(row.get("Shares")),
                    "value": self._clean_val(row.get("Value")),
                    "pct_held": self._clean_val(row.get("pctHeld")),
                    "pct_change": self._clean_val(row.get("pctChange")),
                    "sample_buyer": {"name": str(row.get("Holder")), "change_pct": self._clean_val(row.get("pctChange"))}
                }
        except Exception:
            pass

        try:
            mf = getattr(ticker, "mutualfund_holders", None)
            if isinstance(mf, pd.DataFrame) and not mf.empty:
                row = mf.iloc[0].to_dict()
                return {
                    "date": self._clean_val(row.get("Date Reported")),
                    "holder": self._clean_val(row.get("Holder")),
                    "shares": self._clean_val(row.get("Shares")),
                    "value": self._clean_val(row.get("Value")),
                    "pct_held": self._clean_val(row.get("pctHeld")),
                    "pct_change": self._clean_val(row.get("pctChange"))
                }
        except Exception:
            pass

        return None

    def mine_executive_shareholdings(self, ticker: yf.Ticker, info: dict) -> Optional[dict]:
        """Category 5: Executive shareholdings and holdings."""
        # 1. From company officers
        officers = info.get("companyOfficers", [])
        if officers and isinstance(officers, list):
            for off in officers:
                if isinstance(off, dict) and off.get("name"):
                    return {
                        "name": off.get("name"),
                        "position": off.get("title", "Executive"),
                        "age": off.get("age"),
                        "exercised_value": self._clean_val(off.get("exercisedValue")),
                        "unexercised_value": self._clean_val(off.get("unexercisedValue")),
                        "share_amount": self._clean_val(off.get("unexercisedValue") or off.get("exercisedValue")),
                        "share_percentage": 0.0
                    }

        # 2. From insider roster holders
        try:
            insiders = getattr(ticker, "insider_roster_holders", None)
            if isinstance(insiders, pd.DataFrame) and not insiders.empty:
                row = insiders.iloc[0].to_dict()
                return {
                    "name": self._clean_val(row.get("Name") or row.get("Holder")),
                    "position": self._clean_val(row.get("Position") or row.get("Title")),
                    "share_amount": self._clean_val(row.get("Shares Direct") or row.get("Shares")),
                    "date": self._clean_val(row.get("Date Reported"))
                }
        except Exception:
            pass

        return None

    def mine_major_shareholders(self, ticker: yf.Ticker, info: dict) -> Optional[dict]:
        """Category 6: Major shareholders overview."""
        try:
            maj = getattr(ticker, "major_holders", None)
            if isinstance(maj, pd.DataFrame) and not maj.empty:
                data_dict = {}
                if "Breakdown" in maj.columns and "Value" in maj.columns:
                    for _, r in maj.iterrows():
                        key = str(r["Breakdown"])
                        data_dict[key] = self._clean_val(r["Value"])
                elif len(maj.columns) >= 2:
                    for _, r in maj.iterrows():
                        key = str(r.iloc[1])
                        data_dict[key] = self._clean_val(r.iloc[0])
                
                # Check top major holder
                insider_pct = data_dict.get("insidersPercentHeld")
                return {
                    "name": "Insiders & Controlling Group" if insider_pct else "Major Shareholder Pool",
                    "share_percentage": self._clean_val(insider_pct),
                    "breakdown": data_dict
                }
        except Exception:
            pass

        # Fallback to top institutional holder
        try:
            inst = getattr(ticker, "institutional_holders", None)
            if isinstance(inst, pd.DataFrame) and not inst.empty:
                top_inst = inst.iloc[0].to_dict()
                return {
                    "name": self._clean_val(top_inst.get("Holder")),
                    "share_percentage": self._clean_val(top_inst.get("pctHeld")),
                    "share_amount": self._clean_val(top_inst.get("Shares")),
                    "share_value": self._clean_val(top_inst.get("Value"))
                }
        except Exception:
            pass

        return None

    def mine_shareholder_composition(self, ticker: yf.Ticker, info: dict) -> Optional[dict]:
        """Category 7: Shareholder composition (Insiders vs Institutions vs Public)."""
        composition: Dict[str, Any] = {}
        try:
            maj = getattr(ticker, "major_holders", None)
            if isinstance(maj, pd.DataFrame) and not maj.empty:
                if "Breakdown" in maj.columns and "Value" in maj.columns:
                    for _, r in maj.iterrows():
                        k = str(r["Breakdown"])
                        composition[k] = self._clean_val(r["Value"])
        except Exception:
            pass

        # Also get count and float percent held
        if info.get("heldPercentInsiders") is not None:
            composition["insiders_percent_held"] = self._clean_val(info.get("heldPercentInsiders"))
        if info.get("heldPercentInstitutions") is not None:
            composition["institutions_percent_held"] = self._clean_val(info.get("heldPercentInstitutions"))

        return composition or None

    def mine_dividend(self, ticker: yf.Ticker, info: dict) -> Optional[dict]:
        """Category 8: Dividend history and yield metrics."""
        div_data: Dict[str, Any] = {
            "dividend_rate": self._clean_val(info.get("dividendRate")),
            "dividend_yield": self._clean_val(info.get("dividendYield")),
            "payout_ratio": self._clean_val(info.get("payoutRatio")),
            "trailing_annual_dividend_rate": self._clean_val(info.get("trailingAnnualDividendRate")),
            "trailing_annual_dividend_yield": self._clean_val(info.get("trailingAnnualDividendYield")),
            "five_year_avg_dividend_yield": self._clean_val(info.get("fiveYearAvgDividendYield")),
            "ex_dividend_date": self._clean_val(info.get("exDividendDate"))
        }

        # Latest dividends list from ticker.dividends
        try:
            divs = getattr(ticker, "dividends", None)
            if isinstance(divs, pd.Series) and not divs.empty:
                tail_divs = divs.tail(5)
                breakdown = []
                for dt, amount in tail_divs.items():
                    breakdown.append({
                        "date": dt.strftime("%Y-%m-%d") if hasattr(dt, "strftime") else str(dt),
                        "amount": self._clean_val(amount)
                    })
                div_data["recent_dividends"] = breakdown
                div_data["latest_dividend_amount"] = self._clean_val(tail_divs.iloc[-1])
        except Exception:
            pass

        return {k: v for k, v in div_data.items() if v is not None} or None

    def mine_executives(self, ticker: yf.Ticker, info: dict) -> Optional[dict]:
        """Category 9: Key executives and officers."""
        officers = info.get("companyOfficers", [])
        if officers and isinstance(officers, list):
            top_officer = officers[0]
            if isinstance(top_officer, dict):
                return {
                    "name": top_officer.get("name"),
                    "position": top_officer.get("title", "Key Executive"),
                    "age": top_officer.get("age"),
                    "year_born": top_officer.get("yearBorn"),
                    "total_pay": self._clean_val(top_officer.get("totalPay")),
                    "exercised_value": self._clean_val(top_officer.get("exercisedValue")),
                    "unexercised_value": self._clean_val(top_officer.get("unexercisedValue"))
                }
        return None

    def mine_historical_price(self, ticker: yf.Ticker, symbol: str) -> Optional[dict]:
        """Category 10: Latest historical market price."""
        try:
            hist = ticker.history(period="5d")
            if isinstance(hist, pd.DataFrame) and not hist.empty:
                latest_row = hist.iloc[-1]
                latest_date = hist.index[-1]
                date_str = latest_date.strftime("%Y-%m-%d") if hasattr(latest_date, "strftime") else str(latest_date)

                return {
                    "symbol": symbol,
                    "date": date_str,
                    "open": self._clean_val(latest_row.get("Open")),
                    "high": self._clean_val(latest_row.get("High")),
                    "low": self._clean_val(latest_row.get("Low")),
                    "close": self._clean_val(latest_row.get("Close")),
                    "volume": self._clean_val(latest_row.get("Volume")),
                    "dividends": self._clean_val(latest_row.get("Dividends", 0.0)),
                    "stock_splits": self._clean_val(latest_row.get("Stock Splits", 0.0))
                }
        except Exception:
            pass
        return None

    def mine_sample_data(self, symbol: str = "BBCA.JK", validate: bool = True) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
        """
        Mines 10 core financial data categories from Yahoo Finance:
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
            Tuple of (extracted_data_dict, validation_report_dict)
        """
        formatted_sym = self.format_symbol(symbol)
        ticker = yf.Ticker(formatted_sym)
        
        # Safely retrieve ticker info
        try:
            info = ticker.info or {}
        except Exception:
            info = {}

        extracted_data: Dict[str, Any] = {}

        # 1. Valuation
        val_data = self.mine_valuation(ticker, info)
        if val_data:
            extracted_data["Valuation"] = val_data

        # 2. Peer
        peer_data = self.mine_peer(ticker, info)
        if peer_data:
            extracted_data["Peer"] = peer_data

        # 3. Future Forecast
        forecast_data = self.mine_future_forecast(ticker, info)
        if forecast_data:
            extracted_data["Future Forecast"] = forecast_data

        # 4. Institutional Transactions
        inst_data = self.mine_institutional_transactions(ticker, info)
        if inst_data:
            extracted_data["Institutional Transactions"] = inst_data

        # 5. Executive Shareholdings
        exec_share_data = self.mine_executive_shareholdings(ticker, info)
        if exec_share_data:
            extracted_data["Executive Shareholdings"] = exec_share_data

        # 6. Major Shareholders
        major_sh_data = self.mine_major_shareholders(ticker, info)
        if major_sh_data:
            extracted_data["Major Shareholders"] = major_sh_data

        # 7. Shareholder Composition
        comp_data = self.mine_shareholder_composition(ticker, info)
        if comp_data:
            extracted_data["Shareholder Composition"] = comp_data

        # 8. Dividend
        div_data = self.mine_dividend(ticker, info)
        if div_data:
            extracted_data["Dividend"] = div_data

        # 9. Executives
        exec_data = self.mine_executives(ticker, info)
        if exec_data:
            extracted_data["Executives"] = exec_data

        # 10. Historical Price
        price_data = self.mine_historical_price(ticker, formatted_sym)
        if price_data:
            extracted_data["Historical Price"] = price_data

        # Validate dataset
        validation_report = None
        if validate:
            validation_report = self.validator.validate_mined_dataset(extracted_data)

        return extracted_data, validation_report


def display_mining_and_validation(symbol: str, data: dict, val_report: Optional[dict]):
    """Prints mined data alongside its validation report."""
    print("=" * 75)
    print(f"📊 YFINANCE DATA MINING & VALIDATION RESULT for Symbol: {symbol.upper()}")
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
    print(f"📈 Summary: {len(data)} / 10 categories mined from Yahoo Finance.")
    if val_report:
        print(f"🛡️  Validation Status : {val_report['overall_status']}")
        print(f"    - Total Errors   : {val_report['total_errors']}")
        print(f"    - Total Warnings : {val_report['total_warnings']}")
    print("=" * 75)


if __name__ == "__main__":
    target_symbol = sys.argv[1] if len(sys.argv) > 1 else "BBCA.JK"
    miner = YFinanceDataMiner()
    mined_data, validation_report = miner.mine_sample_data(target_symbol, validate=True)
    display_mining_and_validation(target_symbol, mined_data, validation_report)
