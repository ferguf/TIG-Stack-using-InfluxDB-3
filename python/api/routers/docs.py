import os
import time
import markdown2
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse
from pathlib import Path

router = APIRouter(prefix="/docs", tags=["documentation"])

# Standardize the Directory Name
DOCS_DIR = Path(__file__).resolve().parent.parent / "markdown_docs"

@router.get("/index")
def get_docs_index():
    """Recursively crawls the folder to return a list for the Streamlit sidebar."""
    if not DOCS_DIR.exists():
        raise HTTPException(status_code=404, detail=f"Directory {DOCS_DIR} not found.")

    file_list = []
    for root, _, files in os.walk(DOCS_DIR):
        for file in files:
            if file.endswith(".md"):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, DOCS_DIR).replace("\\", "/")
                file_list.append({
                    "path": rel_path,
                    "name": file.replace(".md", ""),
                    "timestamp": os.path.getmtime(full_path)
                })
    return file_list

@router.get("/raw/{file_path:path}")
async def get_raw_markdown(file_path: str):
    """Returns RAW text for Streamlit to render natively."""
    if not file_path.endswith(".md"):
        file_path += ".md"
    
    absolute_path = DOCS_DIR / file_path
    if not absolute_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    with open(absolute_path, "r", encoding="utf-8") as f:
        return PlainTextResponse(f.read())

@router.get("/view/{file_path:path}", response_class=HTMLResponse)
async def get_html_view(file_path: str):
    """Returns RENDERED HTML (what you currently have)."""
    if not file_path.endswith(".md"):
        file_path += ".md"
    
    absolute_path = DOCS_DIR / file_path
    if not absolute_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    with open(absolute_path, "r", encoding="utf-8") as f:
        md_content = f.read()
        html_body = markdown2.markdown(md_content, extras=["fenced-code-blocks", "tables"])
        return f"<html><body style='padding:40px; font-family: sans-serif;'>{html_body}</body></html>"