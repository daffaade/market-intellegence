// ============================================
// 1. DATA PREPARATION — 5 Emiten Besar
// ============================================
FUNCTION prepare_multi_emiten_data(tickers=["BBCA", "BBRI", "BMRI", "BBNI", "TLKM"]):
    all_raw_data = {}

    FOR EACH ticker IN tickers:
        raw_prices = fetch_historical_price(ticker, start="2015-01-01", end="current")
        all_raw_data[ticker] = raw_prices

    RETURN all_raw_data


// ============================================
// 2. FEATURE ENGINEERING PER HARI
// ============================================
FUNCTION compute_daily_features(price_series):
    features = []

    FOR i IN range(60, length(price_series)):
        window = price_series[i-60 : i]
        current = price_series[i]

        daily_return = safe_divide(current.close - price_series[i-1].close, price_series[i-1].close) * 100
        volatility_20d = std_dev(daily_returns(window[-20:])) * sqrt(252)
        volume_zscore = safe_divide(current.volume - mean(window.volume), std_dev(window.volume))
        price_vs_ma20 = safe_divide(current.close - mean(window[-20:].close), mean(window[-20:].close)) * 100
        price_vs_ma60 = safe_divide(current.close - mean(window.close), mean(window.close)) * 100
        range_pct = safe_divide(current.high - current.low, current.close) * 100

        features.append({
            "date": current.date,
            "close": current.close,
            "daily_return": daily_return,
            "volatility_20d": volatility_20d,
            "volume_zscore": volume_zscore,
            "price_vs_ma20": price_vs_ma20,
            "price_vs_ma60": price_vs_ma60,
            "range_pct": range_pct
        })

    RETURN features


// ============================================
// 3. SPLIT BERDASARKAN TANGGAL (bukan rasio)
// ============================================
FUNCTION split_by_date(features_df, train_end="2024-12-31", test_start="2025-01-01"):
    train_data = [row FOR row IN features_df IF row.date <= train_end]
    test_data  = [row FOR row IN features_df IF row.date >= test_start]

    RETURN train_data, test_data


// ============================================
// 4. TRAINING — hanya pakai data 2015-2024
// ============================================
FUNCTION train_model(train_data, feature_columns):
    X_train = extract_columns(train_data, feature_columns)
    X_train_clean = impute_missing(X_train, method="median")

    feature_stats = compute_feature_stats(X_train_clean, feature_columns)  
        // simpan mean & std dari TRAIN saja, dipakai konsisten saat testing

    model = IsolationForest(
        n_estimators=200,
        contamination=0.03,
        random_state=42
    )
    model.fit(X_train_clean)

    RETURN model, feature_stats


// ============================================
// 5. TESTING — apply ke data 2025-sekarang
// ============================================
FUNCTION apply_to_test(model, test_data, feature_columns, feature_stats):
    X_test = extract_columns(test_data, feature_columns)
    X_test_clean = impute_missing(X_test, method="median", reference_stats=feature_stats)
        // PENTING: imputasi test pakai statistik dari TRAIN, bukan hitung ulang dari test
        // supaya tidak ada "kebocoran" informasi dari data 2025 ke proses training

    scores = model.decision_function(X_test_clean)
    labels = model.predict(X_test_clean)

    FOR i, row IN enumerate(test_data):
        row["anomaly_score"] = normalize_score(scores[i])
        row["is_anomaly"] = (labels[i] == -1)
        row["contributing_factors"] = find_contributing_factors(
            X_test_clean[i], feature_columns, feature_stats, top_n=3
        )

    RETURN test_data


// ============================================
// 6. JALANKAN UNTUK SEMUA 5 EMITEN
// ============================================
FUNCTION run_full_pipeline(tickers=["BBCA", "BBRI", "BMRI", "BBNI", "TLKM"]):
    feature_columns = ["daily_return", "volatility_20d", "volume_zscore",
                         "price_vs_ma20", "price_vs_ma60", "range_pct"]

    all_raw_data = prepare_multi_emiten_data(tickers)
    results = {}

    FOR EACH ticker, raw_prices IN all_raw_data:
        features_df = compute_daily_features(raw_prices)
        train_data, test_data = split_by_date(features_df, "2024-12-31", "2025-01-01")

        model, feature_stats = train_model(train_data, feature_columns)
        test_with_anomalies = apply_to_test(model, test_data, feature_columns, feature_stats)

        results[ticker] = {
            "model": model,
            "feature_stats": feature_stats,
            "train_data": train_data,
            "test_data": test_with_anomalies
        }

    RETURN results


// ============================================
// 7. OUTPUT GRAFIK GARIS 2D + TITIK OUTLIER
// ============================================
FUNCTION format_for_line_chart(results):
    chart_data = {}

    FOR EACH ticker, r IN results:
        full_series = r.train_data + r.test_data   // gabung biar garis kontinu dari 2015

        line_points = [{"date": row.date, "value": row.close} FOR row IN full_series]

        mean_line = [
            {"date": row.date, "value": rolling_mean(full_series, row.date, window=60)}
            FOR row IN full_series
        ]

        // outlier HANYA ditandai di periode test (2025-sekarang), sesuai skenario evaluasi
        outlier_points = [
            {"date": row.date, "value": row.close, "score": row.anomaly_score, 
             "factors": row.contributing_factors}
            FOR row IN r.test_data IF row.is_anomaly == TRUE
        ]

        chart_data[ticker] = {
            "line": line_points,
            "mean_line": mean_line,
            "outliers": outlier_points,
            "train_test_boundary": "2025-01-01"   // dipakai untuk garis vertikal pemisah di chart
        }

    RETURN chart_data

// ============================================
// AKURASI VIA INJECTED GROUND TRUTH
// ============================================
FUNCTION measure_accuracy(model, test_data, feature_columns, feature_stats, n_injections=30):
    X_test = extract_columns(test_data, feature_columns)
    X_injected = copy(X_test)
    injected_indices = []

    FOR i IN range(n_injections):
        idx = random_index(X_injected)
        combo = random_sample(feature_columns, k=2)
        FOR field IN combo:
            std = feature_stats[field]["std"]
            mean = feature_stats[field]["mean"]
            X_injected[idx][field] = mean + 4 * std
        injected_indices.append(idx)

    labels = model.predict(X_injected)
    predicted_anomaly_indices = [i FOR i, l IN enumerate(labels) IF l == -1]

    // ============================================
    // CONFUSION MATRIX
    // ============================================
    true_positive  = count(idx IN injected_indices IF idx IN predicted_anomaly_indices)
    false_negative = length(injected_indices) - true_positive
    false_positive = count(idx IN predicted_anomaly_indices IF idx NOT IN injected_indices)
    true_negative  = length(X_injected) - length(injected_indices) - false_positive

    // ============================================
    // METRIK STANDAR
    // ============================================
    precision = safe_divide(true_positive, true_positive + false_positive)
    recall = safe_divide(true_positive, true_positive + false_negative)
    f1_score = safe_divide(2 * precision * recall, precision + recall)
    accuracy = safe_divide(true_positive + true_negative, length(X_injected))

    // ============================================
    // ERROR RATE
    // ============================================
    error_rate = 1 - accuracy
    false_positive_rate = safe_divide(false_positive, false_positive + true_negative)
    false_negative_rate = safe_divide(false_negative, false_negative + true_positive)

    RETURN {
        "confusion_matrix": {
            "true_positive": true_positive,
            "false_positive": false_positive,
            "true_negative": true_negative,
            "false_negative": false_negative
        },
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score,
        "accuracy": accuracy,
        "error_rate": error_rate,
        "false_positive_rate": false_positive_rate,
        "false_negative_rate": false_negative_rate
    }


// ============================================
// VALIDASI TAMBAHAN — Cross-check Event Nyata
// ============================================
FUNCTION validate_against_known_events(test_data, known_events, tolerance_days=3):
    matches = []

    FOR EACH event IN known_events:
        window = get_dates_within(event.date, days=tolerance_days)
        detected = ANY(test_data WHERE date IN window AND is_anomaly == TRUE)

        matches.append({
            "event": event.description,
            "date": event.date,
            "detected": detected
        })

    match_rate = safe_divide(count(m.detected FOR m IN matches), length(known_events))

    RETURN {"event_match_rate": match_rate, "details": matches}


// ============================================
// GABUNGKAN SEMUA JADI SATU LAPORAN AKURASI PER EMITEN
// ============================================
FUNCTION generate_full_accuracy_report(results, known_events_per_ticker):
    report = {}

    FOR EACH ticker, r IN results:
        injection_metrics = measure_accuracy(
            r.model, r.test_data, feature_columns, r.feature_stats, n_injections=30
        )
        event_metrics = validate_against_known_events(
            r.test_data, known_events_per_ticker[ticker]
        )

        report[ticker] = {
            "train_period": "2015-01-01 to 2024-12-31",
            "test_period": "2025-01-01 to current",
            "n_anomalies_detected": count(r.test_data WHERE is_anomaly == TRUE),
            "pct_of_test_period": safe_divide(
                count(r.test_data WHERE is_anomaly == TRUE), length(r.test_data)
            ) * 100,
            "injection_test": injection_metrics,
            "event_validation": event_metrics
        }

    RETURN report
    
## REVISION

// ============================================
// 1.4 VERIFIKASI DEBUG — CEK GAP FULL VS RECENT VOL
// ============================================
FUNCTION debug_volatility_shift(train_sets, recent_window_days=500):
    debug_report = []

    FOR EACH ticker, train_data IN train_sets:
        full_returns = [row.daily_return FOR row IN train_data IF row.daily_return IS NOT NULL]
        recent_returns = [row.daily_return FOR row IN train_data[-recent_window_days:] IF row.daily_return IS NOT NULL]

        full_vol = std_dev(full_returns)
        recent_vol = std_dev(recent_returns)
        shift_ratio = safe_divide(recent_vol, full_vol)

        debug_report.append({
            "ticker": ticker,
            "full_10yr_vol": full_vol,
            "recent_2yr_vol": recent_vol,
            "shift_ratio": shift_ratio,
            "regime_changed": shift_ratio > 1.3 OR shift_ratio < 0.7   // flag kalau beda signifikan
        })

    RETURN debug_report

    // ============================================
// 2.1 MEASURE ACCURACY — DIPERBAIKI, PAKAI HASIL GABUNGAN
// ============================================
FUNCTION measure_accuracy_fixed(combined_results, injected_indices, n_injections):
    // combined_results = hasil dari combine_time_series_and_cross_sectional()
    // KUNCI PERBAIKAN: pakai row.final_is_anomaly, BUKAN row.time_series_anomaly

    predicted_anomaly_indices = [
        i FOR i, row IN enumerate(combined_results) IF row.final_is_anomaly == TRUE
    ]

    true_positive  = count(idx IN injected_indices IF idx IN predicted_anomaly_indices)
    false_negative = length(injected_indices) - true_positive
    false_positive = count(idx IN predicted_anomaly_indices IF idx NOT IN injected_indices)
    true_negative  = length(combined_results) - length(injected_indices) - false_positive

    precision = safe_divide(true_positive, true_positive + false_positive)
    recall = safe_divide(true_positive, true_positive + false_negative)
    f1_score = safe_divide(2 * precision * recall, precision + recall)
    accuracy = safe_divide(true_positive + true_negative, length(combined_results))
    error_rate = 1 - accuracy

    RETURN {
        "confusion_matrix": {
            "true_positive": true_positive, "false_positive": false_positive,
            "true_negative": true_negative, "false_negative": false_negative
        },
        "precision": precision, "recall": recall, "f1_score": f1_score,
        "accuracy": accuracy, "error_rate": error_rate,
        "source_used": "final_is_anomaly (combined)"   // penanda eksplisit, hindari bug terulang
    }


// ============================================
// 2.2 VALIDASI EVENT — DIPERBAIKI, PAKAI HASIL GABUNGAN + LIFT CORRECTION
// ============================================
FUNCTION validate_against_events_with_lift(combined_results, known_events, tolerance_days=3):
    total_days = length(combined_results)
    n_flagged = count(row.final_is_anomaly FOR row IN combined_results)
    anomaly_rate = safe_divide(n_flagged, total_days)

    matches = []
    FOR EACH event IN known_events:
        window = get_dates_within(event.date, days=tolerance_days)
        detected = ANY(combined_results WHERE date IN window AND final_is_anomaly == TRUE)
        matches.append({"event": event.description, "detected": detected})

    observed_match_rate = safe_divide(count(m.detected FOR m IN matches), length(known_events))

    // koreksi base-rate: peluang match secara kebetulan murni
    window_span_days = tolerance_days * 2 + 1
    expected_by_chance = 1 - (1 - anomaly_rate) ^ window_span_days

    lift = safe_divide(observed_match_rate, expected_by_chance)

    RETURN {
        "anomaly_rate": anomaly_rate,
        "observed_match_rate": observed_match_rate,
        "expected_by_chance": expected_by_chance,
        "lift": lift,   // lift > 1.5-2x baru dianggap meyakinkan, bukan cuma kebetulan
        "details": matches
    }


// ============================================
// 2.3 GRID SEARCH THRESHOLD CROSS-SECTIONAL — CARI TITIK SEIMBANG
// ============================================
FUNCTION grid_search_market_wide_threshold(cross_df, tickers,
                                              threshold_range=[0.4, 0.45, 0.5, 0.55, 0.6],
                                              z_range=[1.0, 1.25, 1.5, 1.75, 2.0],
                                              target_pct_range=[0.03, 0.10]):   // target 3-10% hari
    results = []

    FOR EACH threshold IN threshold_range:
        FOR EACH z IN z_range:
            detection = detect_market_wide_anomaly(cross_df, tickers, threshold, z)
            n_flagged = count(d.is_market_wide_anomaly FOR d IN detection)
            pct_flagged = safe_divide(n_flagged, length(detection))

            in_target_range = target_pct_range[0] <= pct_flagged <= target_pct_range[1]

            results.append({
                "threshold_pct": threshold,
                "z_threshold": z,
                "pct_days_flagged": pct_flagged,
                "in_target_range": in_target_range
            })

    // pilih kombinasi yang masuk target range, prioritaskan yang paling mendekati tengah (misal ~5%)
    valid_options = [r FOR r IN results IF r.in_target_range]
    best = min(valid_options, by=abs(r.pct_days_flagged - 0.05)) IF length(valid_options) > 0 ELSE NULL

    RETURN {"all_results": results, "recommended": best}