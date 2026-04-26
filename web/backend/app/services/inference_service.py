from __future__ import annotations

from pathlib import Path
import sys

import torch
from PIL import Image, ImageEnhance, ImageOps
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.banana_multitask.data import build_transforms
from src.banana_multitask.model import load_checkpoint
from src.banana_multitask.utils import CLASS_SPECS, HEADS, get_device


class InferenceService:
    def __init__(self, checkpoint_path: Path, image_size: int = 300) -> None:
        self.checkpoint_path = checkpoint_path
        self.image_size = image_size
        self.device = get_device(prefer_cuda=True)
        _, eval_transform = build_transforms(image_size=image_size)
        self.transform = eval_transform
        self.model = None
        self.class_specs = CLASS_SPECS.copy()

    @property
    def is_ready(self) -> bool:
        return self.checkpoint_path.exists()

    def load(self) -> None:
        if not self.is_ready:
            return
        model, checkpoint = load_checkpoint(self.checkpoint_path, device=self.device, pretrained=True)
        label_maps = checkpoint.get("label_maps", {}) if isinstance(checkpoint, dict) else {}
        self.class_specs = {
            "loai": list(label_maps.get("loai_to_idx", label_maps.get("loai", {})).keys()) or CLASS_SPECS["loai"],
            "dang": list(label_maps.get("dang_to_idx", label_maps.get("dang", {})).keys()) or CLASS_SPECS["dang"],
            "trang_thai": list(label_maps.get("trang_thai_to_idx", label_maps.get("trang_thai", {})).keys()) or CLASS_SPECS["trang_thai"],
        }
        model.eval()
        self.model = model

    def predict(self, image_path: Path) -> dict:
        if self.model is None:
            self.load()
        if self.model is None:
            raise RuntimeError(f"Checkpoint not found: {self.checkpoint_path}")

        with Image.open(image_path) as image:
            rgb_image = ImageOps.exif_transpose(image).convert("RGB")

        quality = self._analyze_quality(rgb_image)
        preprocessed_image = self._preprocess_for_inference(rgb_image, quality)
        post_quality = self._analyze_quality(preprocessed_image)
        warnings: list[str] = []
        if quality["is_dark"]:
            warnings.append("Anh toi, nen tang anh sang hoac chup noi co du anh sang.")
        if quality["is_blurry"]:
            warnings.append("Anh mo, nen giu may on dinh hoac chup lai ro hon.")

        tensor = self.transform(preprocessed_image).unsqueeze(0).to(self.device)
        with torch.no_grad():
            outputs = self.model(tensor)

        predictions: dict[str, dict[str, float | str]] = {}
        for head in HEADS:
            probabilities = torch.softmax(outputs[head], dim=1)[0]
            confidence, index = torch.max(probabilities, dim=0)
            predictions[head] = {
                "label": self.class_specs[head][int(index.item())],
                "confidence": float(confidence.item()),
            }

        can_review = any(item["confidence"] < 0.60 for item in predictions.values()) or bool(warnings)
        return {
            "predictions": predictions,
            "can_review": can_review,
            "image_quality": quality,
            "image_quality_after_preprocess": post_quality,
            "warnings": warnings,
            "preprocess_applied": True,
        }

    def _preprocess_for_inference(self, rgb_image: Image.Image, quality: dict[str, float | bool]) -> Image.Image:
        # Keep preprocessing conservative to avoid drifting too far from training distribution.
        image = ImageOps.autocontrast(rgb_image, cutoff=1)
        if bool(quality.get("is_dark", False)):
            image = ImageEnhance.Brightness(image).enhance(1.18)
            image = ImageEnhance.Contrast(image).enhance(1.08)
        if bool(quality.get("is_blurry", False)):
            image = ImageEnhance.Sharpness(image).enhance(1.35)
        return image

    def _analyze_quality(self, rgb_image: Image.Image) -> dict[str, float | bool]:
        gray = np.asarray(rgb_image.convert("L"), dtype=np.float32)
        brightness_mean = float(gray.mean())

        gx = np.diff(gray, axis=1)
        gy = np.diff(gray, axis=0)
        min_h = min(gx.shape[0], gy.shape[0])
        min_w = min(gx.shape[1], gy.shape[1])
        if min_h == 0 or min_w == 0:
            sharpness_score = 0.0
        else:
            grad_mag = np.sqrt(gx[:min_h, :min_w] ** 2 + gy[:min_h, :min_w] ** 2)
            sharpness_score = float(np.var(grad_mag))

        # Empirical thresholds for smartphone-like uploads.
        dark_threshold = 65.0
        blurry_threshold = 120.0
        return {
            "brightness_mean": brightness_mean,
            "sharpness_score": sharpness_score,
            "is_dark": brightness_mean < dark_threshold,
            "is_blurry": sharpness_score < blurry_threshold,
        }
