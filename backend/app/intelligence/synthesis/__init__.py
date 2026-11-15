"""Scientific Synthesis Layer for FLARE M10.5."""
from app.intelligence.synthesis.prompt_builder import SYSTEM_PROMPT, build_synthesis_prompt
from app.intelligence.synthesis.schemas import SynthesizedResponse
from app.intelligence.synthesis.synthesizer import ScientificSynthesisService

__all__ = [
    "ScientificSynthesisService",
    "SynthesizedResponse",
    "SYSTEM_PROMPT",
    "build_synthesis_prompt",
]
