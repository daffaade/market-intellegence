import logging
from typing import Dict, Any, List

from ai_engine.core.data_loader import UnifiedDataLoader
from ai_engine.providers.gemini_provider import GeminiProvider
from ai_engine.models.ai_summary.context_builder import build_context_and_evidence
from ai_engine.models.ai_summary.summary_prompt import SUMMARY_PROMPT, SUMMARY_SCHEMA, generate_rule_based_fallback
from ai_engine.models.ai_summary.output_validator import validate_ai_output, MANDATORY_DISCLAIMER

logger = logging.getLogger(__name__)

class SummaryService:
    def __init__(self, data_loader: UnifiedDataLoader):
        self.data_loader = data_loader
        self.provider = GeminiProvider()

    def generate_summary(self, ticker: str, include_models: List[str] = None) -> Dict[str, Any]:
        """
        Orchestrates the entire AI Summary generation flow.
        1. Validates input
        2. Builds context & extracts evidence from sub-models
        3. Calls Gemini API (or falls back to Rule-Based)
        4. Validates output and enforces OJK constraints
        5. Returns structured JSON
        """
        ticker = ticker.upper()
        if include_models is None:
            include_models = []

        try:
            # Step 1: Build context and evidence
            context, evidence_list = build_context_and_evidence(ticker, include_models, self.data_loader)
            
            # Step 2: Generate AI explanation
            ai_output = None
            used_fallback = False
            try:
                ai_output = self.provider.generate_summary(
                    context=context,
                    instruction=SUMMARY_PROMPT,
                    output_schema=SUMMARY_SCHEMA
                )
            except Exception as e:
                logger.error(f"GeminiProvider failed: {e}. Falling back to Rule-Based Synthesizer.")
                ai_output = generate_rule_based_fallback(context)
                used_fallback = True

            # Step 3: Validate AI output (Anti-Hallucination & OJK Compliance)
            is_valid, error_msg, validated_output = validate_ai_output(ai_output, context)
            
            if not is_valid:
                logger.warning(f"AI Output validation failed: {error_msg}. Using fallback.")
                validated_output = generate_rule_based_fallback(context)
                used_fallback = True
                
            # Step 4: Build standard JSON response
            response = {
                "feature": "ai_summary",
                "status": "SUCCESS",
                "ticker": ticker,
                "summary": {
                    "overview": validated_output.get("overview", ""),
                    "positive_findings": validated_output.get("positive_findings", []),
                    "negative_findings": validated_output.get("negative_findings", []),
                    "key_risks": validated_output.get("key_risks", []),
                    "key_opportunities": validated_output.get("key_opportunities", []),
                    "conflicting_signals": validated_output.get("conflicting_signals", []),
                    "data_limitations": validated_output.get("data_limitations", [])
                },
                "evidence": evidence_list,
                "disclaimer": MANDATORY_DISCLAIMER,
                "metadata": {
                    "provider": "rule_based_fallback" if used_fallback else "gemini",
                    "models_requested": include_models
                }
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to generate summary for {ticker}: {str(e)}")
            return {
                "feature": "ai_summary",
                "status": "ERROR",
                "message": str(e)
            }
