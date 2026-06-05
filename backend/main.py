import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
import sys
import io
import logging

sys.path.append(str(Path(__file__).resolve().parent.parent))
from context_aware_organizer import organize_directory, load_config

app = FastAPI(title="File Organizer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "tauri://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class OrganizeRequest(BaseModel):
    target_dir: str
    dry_run: bool = True
    recursive: bool = False

@app.post("/organize")
def organize(req: OrganizeRequest):
    try:
        config = load_config()
        org_config = {
            "target_dirs": [req.target_dir],
            "categories": config["categories"],
            "important_patterns": config["important_patterns"],
            "hidden_exceptions": config["hidden_exceptions"],
            "recursive": req.recursive,
            "dry_run": req.dry_run,
            "run_interval_hours": config.get("run_interval_hours", 3),
        }
        log_stream = io.StringIO()
        handler = logging.StreamHandler(log_stream)
        handler.setLevel(logging.INFO)
        logger = logging.getLogger("file_organizer")
        logger.handlers = [handler]
        logger.setLevel(logging.INFO)
        organize_directory(req.target_dir, org_config)
        log_output = log_stream.getvalue()
        return {"status": "ok", "log": log_output}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/categories")
def get_categories():
    config = load_config()
    return {"categories": list(config["categories"].keys())}

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)