import json
import time
import logging
from typing import Dict, Any, List, Optional
from uuid import uuid4
from datetime import datetime

from backend.services.r2_client import upload_file_to_r2

logger = logging.getLogger(__name__)

class PreviewTracer:
    """
    Captures flow decisions, midpoint generations, AI logs, and quality checks
    during a preview generation pipeline, rendering them into a visual HTML
    report for easy debugging.
    """
    
    def __init__(self, url: str):
        self.trace_id = str(uuid4())
        self.url = url
        self.start_time = time.time()
        self.steps: List[Dict[str, Any]] = []
        self.logger = logging.getLogger(f"PreviewTracer[{self.trace_id[:8]}]")
        self.logger.info(f"Started trace for {url}")
        
    def add_step(self, name: str, details: Any = None, image_url: Optional[str] = None, 
                 image_base64: Optional[str] = None, json_data: Optional[Dict[str, Any]] = None,
                 error: Optional[str] = None):
        """Append a pipeline step to the trace."""
        step = {
            "name": name,
            "timestamp": datetime.now().isoformat(),
            "elapsed_ms": int((time.time() - self.start_time) * 1000),
            "details": details,
            "image_url": image_url,
            "image_base64": image_base64,
            "json_data": json_data,
            "error": error
        }
        self.steps.append(step)
        
        # Also log it standardly
        log_msg = f"Step: {name} ({step['elapsed_ms']}ms)"
        if error:
            self.logger.error(f"{log_msg} - ERROR: {error}")
        else:
            self.logger.info(log_msg)
            
    def _generate_html(self) -> str:
        """Render the collected steps into a styled HTML report."""
        
        steps_html = ""
        for i, step in enumerate(self.steps):
            
            # Formatting details
            details_html = ""
            if step["details"]:
                details_html = f"<div class='details'>{str(step['details'])}</div>"
                
            # Formatting JSON
            json_html = ""
            if step["json_data"]:
                try:
                    formatted_json = json.dumps(step["json_data"], indent=2, default=str)
                    json_html = f"<pre class='json-data'><code>{formatted_json}</code></pre>"
                except Exception as e:
                    json_html = f"<div class='error'>Could not format JSON: {e}</div>"
                    
            # Formatting images
            image_html = ""
            if step["image_url"]:
                image_html = f"<div class='image-container'><img src='{step['image_url']}' alt='Step image' loading='lazy'/></div>"
            elif step["image_base64"]:
                # Default to PNG if missing prefix
                prefix = "" if step["image_base64"].startswith("data:image") else "data:image/png;base64,"
                image_html = f"<div class='image-container'><img src='{prefix}{step['image_base64']}' alt='Step image base64' loading='lazy'/></div>"

            # Formatting Errors
            error_html = ""
            if step["error"]:
                error_html = f"<div class='error-box'><strong>Error:</strong> {step['error']}</div>"
            
            status_class = "error" if step["error"] else "success"
            
            steps_html += f"""
            <div class="step-card {status_class}">
                <div class="step-header">
                    <span class="step-number">{i+1}</span>
                    <h3 class="step-name">{step['name']}</h3>
                    <span class="step-time">+{step['elapsed_ms']}ms</span>
                </div>
                <div class="step-body">
                    {error_html}
                    {details_html}
                    
                    <div class="step-content { 'split-view' if (image_html and json_html) else '' }">
                        { f"<div class='media-col'>{image_html}</div>" if image_html else "" }
                        { f"<div class='data-col'>{json_html}</div>" if json_html else "" }
                    </div>
                </div>
            </div>
            """

        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Preview Trace: {self.url}</title>
            <style>
                :root {{
                    --bg-color: #0f172a;
                    --card-bg: #1e293b;
                    --text-color: #f8fafc;
                    --text-muted: #94a3b8;
                    --border-color: #334155;
                    --accent-color: #3b82f6;
                    --error-color: #ef4444;
                    --success-color: #10b981;
                }}
                
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                    background-color: var(--bg-color);
                    color: var(--text-color);
                    margin: 0;
                    padding: 2rem;
                    line-height: 1.5;
                }}
                
                .header {{
                    margin-bottom: 2rem;
                    padding-bottom: 1rem;
                    border-bottom: 1px solid var(--border-color);
                }}
                
                .header h1 {{ margin: 0 0 0.5rem 0; font-size: 1.5rem; }}
                .meta-info {{ color: var(--text-muted); font-size: 0.9rem; display: flex; gap: 1rem; }}
                
                .timeline {{
                    display: flex;
                    flex-direction: column;
                    gap: 1.5rem;
                    max-width: 1200px;
                    margin: 0 auto;
                }}
                
                .step-card {{
                    background-color: var(--card-bg);
                    border: 1px solid var(--border-color);
                    border-radius: 8px;
                    overflow: hidden;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                }}
                
                .step-card.error {{ border-left: 4px solid var(--error-color); }}
                .step-card.success {{ border-left: 4px solid var(--accent-color); }}
                
                .step-header {{
                    display: flex;
                    align-items: center;
                    padding: 1rem 1.5rem;
                    background-color: rgba(0,0,0,0.2);
                    border-bottom: 1px solid var(--border-color);
                }}
                
                .step-number {{
                    background-color: var(--accent-color);
                    color: white;
                    width: 24px;
                    height: 24px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 0.8rem;
                    font-weight: bold;
                    margin-right: 1rem;
                }}
                
                .step-name {{ margin: 0; flex-grow: 1; font-size: 1.1rem; }}
                .step-time {{ color: var(--text-muted); font-family: monospace; font-size: 0.9rem; }}
                
                .step-body {{ padding: 1.5rem; }}
                
                .details {{ margin-bottom: 1rem; color: #cbd5e1; }}
                
                .error-box {{
                    background-color: rgba(239, 68, 68, 0.1);
                    color: #fca5a5;
                    padding: 0.75rem 1rem;
                    border-radius: 4px;
                    border-left: 2px solid var(--error-color);
                    margin-bottom: 1rem;
                }}
                
                .step-content {{
                    display: flex;
                    flex-direction: column;
                    gap: 1.5rem;
                }}
                
                @media (min-width: 768px) {{
                    .step-content.split-view {{
                        flex-direction: row;
                    }}
                    .step-content.split-view > div {{
                        flex: 1;
                        min-width: 0; /* Prevent flex overflow */
                    }}
                }}
                
                .image-container img {{
                    max-width: 100%;
                    height: auto;
                    border-radius: 4px;
                    border: 1px solid var(--border-color);
                    background-color: #000;
                }}
                
                .json-data {{
                    background-color: #0f172a;
                    padding: 1rem;
                    border-radius: 4px;
                    overflow-x: auto;
                    margin: 0;
                    border: 1px solid var(--border-color);
                    font-size: 0.85rem;
                }}
                
                .json-data code {{
                    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
                    color: #a5b4fc;
                }}
            </style>
        </head>
        <body>
            <div class="timeline">
                <div class="header">
                    <h1>🔍 Preview Trace Report</h1>
                    <div class="meta-info">
                        <span><strong>URL:</strong> <a href="{self.url}" target="_blank" style="color:var(--accent-color)">{self.url}</a></span>
                        <span><strong>ID:</strong> {self.trace_id}</span>
                        <span><strong>Total Time:</strong> {int((time.time() - self.start_time) * 1000)}ms</span>
                    </div>
                </div>
                
                {steps_html}
            </div>
        </body>
        </html>
        """
        return html

    def upload_trace(self) -> Optional[str]:
        """Generate the HTML report and upload it to R2."""
        try:
            self.logger.info("Generating and uploading trace report...")
            html_content = self._generate_html()
            
            # Save to R2
            filename = f"traces/{datetime.now().strftime('%Y-%m-%d')}/{self.trace_id}.html"
            
            public_url = upload_file_to_r2(
                html_content.encode('utf-8'),
                filename,
                "text/html; charset=utf-8"
            )
            
            self.logger.info(f"📊 Trace report generated: {public_url}")
            return public_url
            
        except Exception as e:
            self.logger.error(f"Failed to upload trace report: {e}")
            return None
