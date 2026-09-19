"""
forecast_model.py — Multi-Horizon Dual-Task Model (Model-P0)
7 RandomForestClassifier + 7 RandomForestRegressor (H+1 … H+7)
StandardScaler fit on train set only. Temporal split 60/40.
Implements §5-§8 of implementation-plan-forecast-signal-module.md
"""

import sys
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List

from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, mean_absolute_error,
    mean_squared_error, r2_score,
)

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
for _p in [str(_HERE), str(_ROOT)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from feature_engineering import FEATURE_COLS, HORIZONS, temporal_split

RF_CLF = dict(n_estimators=200, max_depth=8, random_state=42, n_jobs=-1)
RF_REG = dict(n_estimators=200, max_depth=8, random_state=42, n_jobs=-1)


def _mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    mask = y_true != 0
    if mask.sum() == 0:
        return float("nan")
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)


def _dir_acc(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    match = np.sign(y_pred) == np.sign(y_true)
    return float(match.mean()) if len(match) > 0 else float("nan")


def train_all_horizons(df_all: pd.DataFrame) -> Dict[int, Dict[str, Any]]:
    """
    Trains clf + reg for each horizon on combined ticker data.
    Returns forecast_results dict keyed by horizon int.
    """
    results: Dict[int, Dict[str, Any]] = {}
    df_clean = df_all.dropna(subset=FEATURE_COLS).copy()

    for h in HORIZONS:
        dir_col = f"label_dir_{h}"
        ret_col = f"label_ret_{h}"
        df_h = df_clean.dropna(subset=[dir_col, ret_col]).copy()

        if len(df_h) < 200:
            print(f"  [WARN] H+{h}: only {len(df_h)} rows, skipping")
            continue

        train_df, test_df = temporal_split(df_h)

        X_tr = train_df[FEATURE_COLS].values
        X_te = test_df[FEATURE_COLS].values
        y_dir_tr = train_df[dir_col].values
        y_dir_te = test_df[dir_col].values
        y_ret_tr = train_df[ret_col].values
        y_ret_te = test_df[ret_col].values

        scaler = StandardScaler()
        X_tr   = scaler.fit_transform(X_tr)
        X_te   = scaler.transform(X_te)

        # Classification
        clf      = RandomForestClassifier(**RF_CLF)
        clf.fit(X_tr, y_dir_tr)
        clf_pred = clf.predict(X_te)
        clf_acc  = float(accuracy_score(y_dir_te, clf_pred))

        # Regression
        reg      = RandomForestRegressor(**RF_REG)
        reg.fit(X_tr, y_ret_tr)
        reg_pred = reg.predict(X_te)

        mae    = float(mean_absolute_error(y_ret_te, reg_pred))
        rmse   = float(np.sqrt(mean_squared_error(y_ret_te, reg_pred)))
        mape_v = _mape(y_ret_te, reg_pred)
        r2     = float(r2_score(y_ret_te, reg_pred))
        da     = _dir_acc(y_ret_te, reg_pred)

        results[h] = {
            "clf":        clf,
            "reg":        reg,
            "scaler":     scaler,
            "clf_acc":    clf_acc,
            "reg_metrics": {"mae": mae, "rmse": rmse, "mape": mape_v, "r2": r2, "dir_acc": da},
            "train_rows": len(train_df),
            "test_rows":  len(test_df),
        }
        print(
            f"  H+{h}  clf_acc={clf_acc:.3f}  "
            f"reg_MAE={mae:.4f}  reg_dir_acc={da:.3f}"
        )

    return results


def generate_forecast_curve(
    forecast_results: Dict[int, Dict[str, Any]],
    latest_features: np.ndarray,
) -> Dict[str, Any]:
    """H+1..H+7 forecast from latest snapshot row."""
    x = np.array(latest_features).reshape(1, -1)
    horizon_curve: Dict[str, Any] = {}
    disagreements: List[int] = []

    for h in HORIZONS:
        if h not in forecast_results:
            horizon_curve[f"H+{h}"] = {"predicted_return": None, "direction": None}
            continue

        bundle   = forecast_results[h]
        x_scaled = bundle["scaler"].transform(x)

        pred_dir = int(bundle["clf"].predict(x_scaled)[0])
        pred_ret = float(bundle["reg"].predict(x_scaled)[0])

        reg_dir = 1 if pred_ret >= 0 else 0
        if pred_dir != reg_dir:
            disagreements.append(h)

        horizon_curve[f"H+{h}"] = {
            "predicted_return": round(pred_ret, 6),
            "direction":        pred_dir,
        }

    return {
        "horizon_curve":         horizon_curve,
        "model_agreement_flag":  len(disagreements) == 0,
        "disagreement_horizons": disagreements,
    }


def build_accuracy_table(forecast_results: Dict[int, Dict[str, Any]]) -> str:
    hdr  = f"{'Horizon':<8} {'CLF Acc':>9} {'MAE':>9} {'RMSE':>9} {'MAPE%':>9} {'R²':>8} {'Dir Acc':>9}"
    sep  = "-" * len(hdr)
    rows = [hdr, sep]
    for h in HORIZONS:
        if h not in forecast_results:
            rows.append(f"  H+{h}    — skipped")
            continue
        r = forecast_results[h]
        m = r["reg_metrics"]
        rows.append(
            f"  H+{h}    "
            f"{r['clf_acc']:>8.3f}  "
            f"{m['mae']:>8.5f}  "
            f"{m['rmse']:>8.5f}  "
            f"{m['mape']:>8.2f}  "
            f"{m['r2']:>7.4f}  "
            f"{m['dir_acc']:>8.3f}"
        )
    return "\n".join(rows)
