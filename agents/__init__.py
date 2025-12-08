"""Agents package for AI Virtual Photographer."""
from agents.garment_understanding_agent import analyze_garment, analyze_garment_with_retry
from agents.prompt_builder_agent import build_image_prompt, build_simple_prompt
from agents.tryon_generation_agent import (
    generate_tryon_image,
    generate_tryon_response,
    batch_generate,
)
from agents.quality_checker_agent import check_consistency, should_regenerate

__all__ = [
    # Understanding
    "analyze_garment",
    "analyze_garment_with_retry",
    # Prompt Building
    "build_image_prompt",
    "build_simple_prompt",
    # Generation
    "generate_tryon_image",
    "generate_tryon_response",
    "batch_generate",
    # Quality
    "check_consistency",
    "should_regenerate",
]
