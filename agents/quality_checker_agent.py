"""
Quality Checker Agent for AI Virtual Photographer.

This agent compares the original garment image with the generated
try-on image to verify that key details have been preserved:
- Colors (primary and secondary)
- Embroidery style and placement
- Pattern integrity
- Silhouette/shape

This helps identify when regeneration might be needed.
"""

import json
import re
from typing import Optional

from schemas.garment_schema import GarmentDescription
from schemas.generation_request import QualityReport
from services.gemini_client import get_gemini_client, GeminiClientError
from utils.logging_utils import get_agent_logger

logger = get_agent_logger("QualityChecker")


# Prompt for quality comparison
COMPARISON_PROMPT = """You are a quality assurance expert for fashion photography.

Your task is to compare two images:
1. ORIGINAL: A product image of an Indian ethnic garment
2. GENERATED: An AI-generated image of a model wearing what should be the same garment

Analyze whether the generated image accurately preserves the original garment's:
1. PRIMARY COLOR - Does the main color match?
2. EMBROIDERY - Are the embroidery style, patterns, and placement preserved?
3. PATTERNS - Are printed/woven patterns accurately reproduced?
4. SILHOUETTE - Does the garment shape (length, fit, neckline) match?
5. DETAILS - Are decorative elements (buttons, borders, etc.) preserved?

Return ONLY a JSON object in this exact format:
{
    "color_match": true/false,
    "embroidery_match": true/false,
    "pattern_match": true/false,
    "silhouette_match": true/false,
    "overall_score": 0.0-1.0,
    "issues": ["list of specific issues found"],
    "recommendations": ["suggestions for improvement"]
}

Be strict in your evaluation. The generated garment should look like the SAME garment, not just a similar one.
If you cannot see certain details clearly in either image, assume they don't match.
"""


def check_consistency(
    original_image_bytes: bytes,
    generated_image_bytes: bytes,
    garment: Optional[GarmentDescription] = None
) -> QualityReport:
    """
    Check consistency between original garment and generated try-on image.
    
    This is the main function of the Quality Checker Agent. It uses
    Gemini's vision capabilities to compare the two images and
    identify any discrepancies.
    
    Args:
        original_image_bytes: Original garment image
        generated_image_bytes: Generated try-on image
        garment: Optional garment description for context
    
    Returns:
        QualityReport with match assessments and recommendations
    
    Example:
        >>> report = check_consistency(original_bytes, generated_bytes)
        >>> if report.overall_score < 0.7:
        ...     print("Quality issues detected:", report.issues)
    """
    logger.info("Starting quality consistency check...")
    
    try:
        client = get_gemini_client()
        
        # Add garment context to the prompt if available
        prompt = COMPARISON_PROMPT
        if garment:
            context = f"""

Known garment details for reference:
- Type: {garment.garment_type or 'Unknown'}
- Primary color: {garment.colors.primary if garment.colors else 'Unknown'}
- Embroidery styles: {', '.join(e.style for e in garment.embroidery if e.style) or 'None specified'}
- Patterns: {', '.join(p.name for p in garment.patterns if p.name) or 'None specified'}

Use these details to verify the accuracy of the generated image.
"""
            prompt += context
        
        # Compare images
        response_text = client.compare_images(
            original_image_bytes,
            generated_image_bytes,
            prompt
        )
        
        logger.debug(f"Raw comparison response: {response_text[:500]}...")
        
        # Parse response
        report = _parse_quality_response(response_text)
        
        logger.info(f"Quality check complete. Score: {report.overall_score:.2f}")
        if report.issues:
            logger.warning(f"Issues found: {report.issues}")
        
        return report
        
    except GeminiClientError as e:
        logger.error(f"Quality check failed: {e}")
        # Return a conservative report on failure
        return QualityReport(
            color_match=False,
            embroidery_match=False,
            pattern_match=False,
            silhouette_match=False,
            overall_score=0.0,
            issues=["Quality check failed - unable to compare images"],
            recommendations=["Manual review recommended"]
        )


def _parse_quality_response(response_text: str) -> QualityReport:
    """
    Parse the quality check response into a QualityReport.
    
    Args:
        response_text: Raw response from the model
    
    Returns:
        Parsed QualityReport
    """
    try:
        # Try to extract JSON from response
        json_patterns = [
            r'```json\s*([\s\S]*?)\s*```',
            r'```\s*([\s\S]*?)\s*```',
            r'\{[\s\S]*\}',
        ]
        
        for pattern in json_patterns:
            match = re.search(pattern, response_text)
            if match:
                json_str = match.group(1) if '```' in pattern else match.group(0)
                try:
                    data = json.loads(json_str)
                    return QualityReport.model_validate(data)
                except (json.JSONDecodeError, Exception):
                    continue
        
        # If JSON parsing fails, try to infer from text
        logger.warning("Could not parse JSON, inferring from text response")
        return _infer_report_from_text(response_text)
        
    except Exception as e:
        logger.error(f"Failed to parse quality response: {e}")
        return QualityReport(
            color_match=False,
            embroidery_match=False,
            pattern_match=False,
            silhouette_match=False,
            overall_score=0.5,
            issues=["Unable to parse quality check response"],
            recommendations=["Manual review recommended"]
        )


def _infer_report_from_text(text: str) -> QualityReport:
    """
    Infer quality report from unstructured text response.
    
    Args:
        text: Unstructured response text
    
    Returns:
        Inferred QualityReport
    """
    text_lower = text.lower()
    
    # Check for matches (look for positive indicators)
    color_match = "color" in text_lower and ("match" in text_lower or "same" in text_lower or "accurate" in text_lower)
    embroidery_match = "embroidery" in text_lower and ("preserved" in text_lower or "match" in text_lower)
    pattern_match = "pattern" in text_lower and ("preserved" in text_lower or "match" in text_lower)
    silhouette_match = "silhouette" in text_lower and ("match" in text_lower or "same" in text_lower)
    
    # Calculate overall score
    matches = [color_match, embroidery_match, pattern_match, silhouette_match]
    overall_score = sum(1 for m in matches if m) / 4
    
    # Extract issues (sentences with negative words)
    issues = []
    negative_words = ["different", "missing", "lost", "changed", "incorrect", "wrong", "not"]
    for sentence in text.split('.'):
        if any(word in sentence.lower() for word in negative_words):
            clean_sentence = sentence.strip()
            if clean_sentence:
                issues.append(clean_sentence)
    
    return QualityReport(
        color_match=color_match,
        embroidery_match=embroidery_match,
        pattern_match=pattern_match,
        silhouette_match=silhouette_match,
        overall_score=overall_score,
        issues=issues[:5],  # Limit to 5 issues
        recommendations=["Consider regenerating if quality is unsatisfactory"]
    )


def should_regenerate(report: QualityReport, threshold: float = 0.6) -> bool:
    """
    Determine if regeneration is recommended based on quality report.
    
    Args:
        report: Quality check report
        threshold: Minimum acceptable score (default 0.6)
    
    Returns:
        True if regeneration is recommended
    """
    # Always regenerate if color doesn't match (most noticeable)
    if not report.color_match:
        logger.info("Regeneration recommended: Color mismatch")
        return True
    
    # Regenerate if overall score is too low
    if report.overall_score < threshold:
        logger.info(f"Regeneration recommended: Score {report.overall_score:.2f} < {threshold}")
        return True
    
    # Regenerate if multiple aspects don't match
    matches = [report.color_match, report.embroidery_match, report.pattern_match, report.silhouette_match]
    if sum(1 for m in matches if not m) >= 2:
        logger.info("Regeneration recommended: Multiple mismatches")
        return True
    
    return False
