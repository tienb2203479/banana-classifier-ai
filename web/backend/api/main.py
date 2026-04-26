from __future__ import annotations

import os
import uuid
import csv
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.core.banana_info import BANANA_TYPE_INFO, DEFAULT_BANANA_INFO
from app.core.database import DatabaseManager
from app.services.inference_service import InferenceService

PROJECT_ROOT = Path(__file__).resolve().parents[3]
FRONTEND_ROOT = PROJECT_ROOT / "web" / "frontend"
UPLOAD_ROOT = PROJECT_ROOT / "web" / "backend" / "storage" / "uploads"
DATA_IMAGES_ROOT = PROJECT_ROOT / "data" / "images"
if not DATA_IMAGES_ROOT.exists():
    DATA_IMAGES_ROOT = PROJECT_ROOT / "data" / "image"
LABELS_CSV = PROJECT_ROOT / "data" / "label.csv"
UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)

MAX_UPLOAD_MB = float(os.getenv("MAX_UPLOAD_MB", "8"))
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def _resolve_checkpoint_path() -> Path:
    default_path = PROJECT_ROOT / "outputs" / "efficientnet_b4_v3" / "best.pt"
    env_value = os.getenv("BANANA_CHECKPOINT", "").strip()
    if env_value:
        candidate = Path(env_value)
        if candidate.exists():
            return candidate
    return default_path


CHECKPOINT_PATH = _resolve_checkpoint_path()

app = FastAPI(title="Banana Recognition Web API", version="1.0.0")
service = InferenceService(checkpoint_path=CHECKPOINT_PATH)
database = DatabaseManager()
SESSION_HISTORY: dict[str, list[dict[str, Any]]] = {}


def _build_reference_image_map() -> dict[str, str]:
    mapping: dict[str, str] = {}
    if not LABELS_CSV.exists() or not DATA_IMAGES_ROOT.exists():
        return mapping

    def _norm(text: str) -> str:
        value = unicodedata.normalize("NFD", str(text).strip().lower())
        value = value.replace("đ", "d")
        return "".join(ch for ch in value if unicodedata.category(ch) != "Mn")

    def _combo_key(loai: str, dang: str, trang_thai: str) -> str:
        return f"{_norm(loai)}|{_norm(dang)}|{_norm(trang_thai)}"

    try:
        with LABELS_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                loai = str(row.get("loai", "")).strip()
                dang = str(row.get("dang", "")).strip()
                trang_thai = str(row.get("trang_thai", row.get("trangthai", ""))).strip()
                image_name = str(row.get("image", "")).strip()
                if not loai or not dang or not trang_thai or not image_name:
                    continue
                image_path = DATA_IMAGES_ROOT / image_name
                if image_path.exists():
                    combo = _combo_key(loai, dang, trang_thai)
                    if combo not in mapping:
                        mapping[combo] = f"/data-images/{image_name}"

                    loai_only = _norm(loai)
                    if loai_only not in mapping:
                        mapping[loai_only] = f"/data-images/{image_name}"
    except Exception:
        return {}
    return mapping


REFERENCE_IMAGE_MAP = _build_reference_image_map()


@app.middleware("http")
async def attach_session_id(request: Request, call_next):
    sid = request.cookies.get("sid")
    if not sid:
        sid = uuid.uuid4().hex
    request.state.sid = sid
    response = await call_next(request)
    if "sid" not in request.cookies:
        response.set_cookie("sid", sid, httponly=True, samesite="lax")
    return response


def _ensure_session_history(sid: str) -> list[dict[str, Any]]:
    if sid not in SESSION_HISTORY:
        SESSION_HISTORY[sid] = []
    return SESSION_HISTORY[sid]


@app.on_event("startup")
def startup_event() -> None:
    database.initialize()


def _validate_upload(file: UploadFile) -> None:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only jpg/jpeg/png files are supported")


def _save_upload(file: UploadFile) -> Path:
    suffix = Path(file.filename or "").suffix.lower()
    safe_suffix = suffix if suffix in ALLOWED_EXTENSIONS else ".jpg"
    today = datetime.utcnow().strftime("%Y%m%d")
    target_dir = UPLOAD_ROOT / today
    target_dir.mkdir(parents=True, exist_ok=True)
    target_name = f"{datetime.utcnow().strftime('%H%M%S')}_{uuid.uuid4().hex[:8]}{safe_suffix}"
    target_path = target_dir / target_name

    content = file.file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > MAX_UPLOAD_MB:
        raise HTTPException(status_code=413, detail=f"File is too large. Limit is {MAX_UPLOAD_MB} MB")

    target_path.write_bytes(content)
    return target_path


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "model_ready": service.is_ready,
        "checkpoint": str(CHECKPOINT_PATH),
    }


@app.post("/api/predict")
def predict(request: Request, file: UploadFile = File(...)) -> dict[str, Any]:
    _validate_upload(file)
    image_path = _save_upload(file)

    try:
        result = service.predict(image_path)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    loai_label = result["predictions"]["loai"]["label"]
    dang_label = result["predictions"]["dang"]["label"]
    trang_thai_label = result["predictions"]["trang_thai"]["label"]
    banana_info = BANANA_TYPE_INFO.get(loai_label, DEFAULT_BANANA_INFO)

    def _norm(text: str) -> str:
        value = unicodedata.normalize("NFD", str(text).strip().lower())
        value = value.replace("đ", "d")
        return "".join(ch for ch in value if unicodedata.category(ch) != "Mn")

    combo_key = f"{_norm(loai_label)}|{_norm(dang_label)}|{_norm(trang_thai_label)}"
    reference_image_url = REFERENCE_IMAGE_MAP.get(combo_key) or REFERENCE_IMAGE_MAP.get(_norm(loai_label))

    item = {
        "id": uuid.uuid4().hex,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "image_url": f"/uploads/{image_path.relative_to(UPLOAD_ROOT).as_posix()}",
        "predictions": result["predictions"],
        "can_review": result["can_review"],
        "image_quality": result.get("image_quality", {}),
        "warnings": result.get("warnings", []),
        "banana_info": banana_info,
        "reference_image_url": reference_image_url,
    }

    history = _ensure_session_history(request.state.sid)
    history.insert(0, item)
    try:
        database.save_prediction(request.state.sid, image_path, result)
    except Exception:
        pass

    return {
        "item": item,
        "history_count": len(history),
        "session_only": not database.enabled,
    }


@app.get("/api/history")
def get_history(request: Request) -> dict[str, Any]:
    if database.enabled:
        try:
            history = database.fetch_history(request.state.sid)
            if history:
                def _norm(text: str) -> str:
                    value = unicodedata.normalize("NFD", str(text).strip().lower())
                    value = value.replace("đ", "d")
                    return "".join(ch for ch in value if unicodedata.category(ch) != "Mn")

                for item in history:
                    loai_label = item.get("predictions", {}).get("loai", {}).get("label", "")
                    dang_label = item.get("predictions", {}).get("dang", {}).get("label", "")
                    trang_thai_label = item.get("predictions", {}).get("trang_thai", {}).get("label", "")
                    combo_key = f"{_norm(loai_label)}|{_norm(dang_label)}|{_norm(trang_thai_label)}"
                    item["reference_image_url"] = REFERENCE_IMAGE_MAP.get(combo_key) or REFERENCE_IMAGE_MAP.get(_norm(loai_label))
                return {"items": history, "session_only": False}
        except Exception:
            pass
    history = _ensure_session_history(request.state.sid)
    return {"items": history, "session_only": True}


@app.delete("/api/history")
def clear_history(request: Request) -> dict[str, Any]:
    try:
        database.clear_history(request.state.sid)
    except Exception:
        pass
    SESSION_HISTORY[request.state.sid] = []
    return {"ok": True}


@app.get("/")
def index() -> FileResponse:
    return FileResponse(FRONTEND_ROOT / "index.html")


app.mount("/uploads", StaticFiles(directory=UPLOAD_ROOT), name="uploads")
app.mount("/assets", StaticFiles(directory=FRONTEND_ROOT / "assets"), name="assets")
app.mount("/data-images", StaticFiles(directory=DATA_IMAGES_ROOT), name="data-images")
