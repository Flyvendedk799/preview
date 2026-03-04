import sys
import logging
from backend.core.config import settings
from backend.services.preview_engine import PreviewEngine

logging.basicConfig(level=logging.INFO)

settings.ENABLE_MULTI_AGENT = True
settings.ENABLE_AI_REASONING = True
settings.ENABLE_COMPOSITED_IMAGE = True

engine = PreviewEngine(config=settings)
res = engine.generate('https://dinredaktion.dk/', is_demo=True)
print("SUCCESS!")
print("TITLE:", res.title)
print("BLUEPRINT:", dict(res.blueprint))
