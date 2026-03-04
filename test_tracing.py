import asyncio
import os
import sys

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.preview_engine import PreviewEngine, PreviewEngineConfig

async def test_tracing():
    print("Testing Preview Engine with Tracing...")
    
    config = PreviewEngineConfig(
        is_demo=True,
        enable_brand_extraction=True,
        enable_ai_reasoning=True,
        enable_composited_image=True,
        enable_cache=False, # Disable cache to force generation
        timeout_seconds=600
    )
    
    engine = PreviewEngine(config)
    url = "https://example.com"
    
    try:
        result = engine.generate(url)
        print(f"\n✅ Success!")
        print(f"URL: {result.url}")
        print(f"Trace URL: {result.trace_url}")
        if result.trace_url:
            print("TRACING WORKS! Report uploaded to R2.")
        else:
            print("❌ Trace URL is missing from result.")
            
    except Exception as e:
        print(f"\n❌ Generation failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_tracing())
