from typing import Dict, Any, List

SUMMARY_PROMPT = """
You are an AI financial analysis explanation assistant for Indonesian Equities (IDX).
Your task is to explain the analysis results and numerical evidence provided in the CONTEXT.

CRITICAL RULES (NON-NEGOTIABLE):
1. **Facts First**: Use ONLY the provided analysis results and evidence. Do NOT invent, hallucinate, or recalculate financial data.
2. **Non-Advisory (OJK Compliance)**: You are STRICTLY FORBIDDEN from giving investment recommendations. Do NOT use words like "Beli", "Jual", "Hold", "Buy", "Sell", "Koleksi", "Akumulasi sekarang", "Cut loss", or "Target price". Provide objective market signatures.
3. **Structured Explanation**: Explain the opportunity signals, risks, anomalies, and divergences clearly in Bahasa Indonesia.
4. **Conflicting Signals**: Identify if different models contradict each other (e.g., strong fundamental divergence but negative smart money flow).
5. **Output**: Return valid JSON exactly matching the requested schema. Use professional Bahasa Indonesia.

Provide the analysis under the following keys:
- overview: 1-2 paragraphs summarizing the current intelligence state of the ticker.
- positive_findings: list of positive points backed by evidence.
- negative_findings: list of negative points/risks backed by evidence.
- key_risks: list of major risks to monitor.
- key_opportunities: list of potential opportunities.
- conflicting_signals: list of any contradictory evidence.
- data_limitations: list of missing data or limitations in the analysis.
"""

SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {
        "overview": {"type": "string"},
        "positive_findings": {"type": "array", "items": {"type": "string"}},
        "negative_findings": {"type": "array", "items": {"type": "string"}},
        "key_risks": {"type": "array", "items": {"type": "string"}},
        "key_opportunities": {"type": "array", "items": {"type": "string"}},
        "conflicting_signals": {"type": "array", "items": {"type": "string"}},
        "data_limitations": {"type": "array", "items": {"type": "string"}}
    },
    "required": [
        "overview", "positive_findings", "negative_findings", 
        "key_risks", "key_opportunities", "conflicting_signals", "data_limitations"
    ]
}

def generate_rule_based_fallback(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fallback synthesizer if AI generation fails. Returns a structured JSON matching the schema.
    """
    ticker = context.get("ticker", "Emiten")
    evidence = context.get("evidence", [])
    
    positives = []
    negatives = []
    risks = []
    
    # Simple rule engine to extract basic points from evidence
    for ev in evidence:
        metric = ev.get("metric", "")
        value = ev.get("value")
        
        if metric == "opportunity_score" and isinstance(value, (int, float)) and value > 60:
            positives.append(f"Skor Peluang menunjukkan sinyal kuat di level {value}/100.")
        elif metric == "risk_score" and isinstance(value, (int, float)) and value > 60:
            negatives.append(f"Tingkat Risiko terdeteksi tinggi di level {value}/100.")
            risks.append("Volatilitas atau risiko fundamental meningkat.")
        elif metric == "is_anomaly" and value is True:
            risks.append("Anomali pergerakan harga/volume terdeteksi oleh Isolation Forest.")
        elif metric == "divergence_score" and isinstance(value, (int, float)) and value > 0.7:
            positives.append("Terdeteksi divergensi fundamental positif dibandingkan peer industri.")
    
    if not positives:
        positives.append("Tidak ada sinyal positif dominan yang terdeteksi secara otomatis.")
    if not negatives:
        negatives.append("Tidak ada indikator risiko ekstrem dari data saat ini.")
        
    overview = (
        f"Berdasarkan pemrosesan data otomatis untuk {ticker}, sistem mendeteksi sejumlah "
        f"sinyal teknikal dan fundamental. Analisis AI dinamis saat ini sedang menggunakan fallback statis."
    )
    
    return {
        "overview": overview,
        "positive_findings": positives,
        "negative_findings": negatives,
        "key_risks": risks if risks else ["Pantau pergerakan harga secara berkala"],
        "key_opportunities": positives if positives else ["Perhatikan jika ada perubahan tren"],
        "conflicting_signals": ["Sinyal AI dinamis tidak tersedia (Fallback Mode)"],
        "data_limitations": ["Menggunakan rule-based engine karena AI provider sedang tidak dapat diakses."]
    }
