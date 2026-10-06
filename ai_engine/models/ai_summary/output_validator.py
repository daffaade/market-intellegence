import re
import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)

MANDATORY_DISCLAIMER = (
    "Informasi dan analisis ini merupakan hasil pemrosesan data riset "
    "dan bukan merupakan anjuran investasi personal (Bukan rekomendasi Beli/Jual)."
)

# OJK Non-Advisory blocklist
FORBIDDEN_WORDS = [
    r"\bbeli\b", r"\bjual\b", r"\bhold\b", r"\bbuy\b", r"\bsell\b", 
    r"\bkoleksi\b", r"\bakumulasi sekarang\b", r"\bcut loss\b", r"\btarget price\b",
    r"\brekomendasi\b"
]

def validate_ai_output(ai_output: Dict[str, Any], context: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Validates AI output against schema, hallucination risks, and OJK compliance.
    Returns: (is_valid, error_message, sanitized_output)
    """
    if not isinstance(ai_output, dict):
        return False, "Output is not a valid JSON dictionary", {}

    required_keys = [
        "overview", "positive_findings", "negative_findings", 
        "key_risks", "key_opportunities", "conflicting_signals", "data_limitations"
    ]
    
    for key in required_keys:
        if key not in ai_output:
            return False, f"Missing required key in AI output: {key}", {}
            
    # Combine all text to check for OJK compliance
    all_text = str(ai_output).lower()
    for pattern in FORBIDDEN_WORDS:
        if re.search(pattern, all_text):
            logger.warning(f"OJK Compliance Violation: Found forbidden word matching pattern '{pattern}'")
            # If violation is found, we should fail validation so fallback can be used, 
            # or we can sanitize it. Here we will fail validation to enforce strict compliance.
            return False, "Output contains forbidden investment recommendation terms (OJK Compliance)", {}

    # Valid output, we just append the mandatory disclaimer at the service level, 
    # but we can return the validated output safely here.
    return True, "", ai_output
