from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import json
import random
import unicodedata

import numpy as np
import pandas as pd
import torch


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


@dataclass(frozen=True)
class LabelMaps:
    loai_to_idx: dict[str, int]
    dang_to_idx: dict[str, int]
    trang_thai_to_idx: dict[str, int]


HEADS = ["loai", "dang", "trang_thai"]


CLASS_SPECS = {
    "loai": ["Chuối cau", "Chuối già", "Chuối sáp", "Chuối táo quạ", "Chuối xiêm"],
    "dang": ["Buồng", "Nải", "Trái"],
    "trang_thai": ["Chín", "Xanh"],
}


def get_device(prefer_cuda: bool = True) -> torch.device:
    return torch.device("cuda" if prefer_cuda and torch.cuda.is_available() else "cpu")


def normalize_text(value: str) -> str:
    text = str(value).strip().lower().replace("đ", "d")
    normalized = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def normalize_manifest_columns(frame: pd.DataFrame) -> pd.DataFrame:
    work = frame.copy()
    rename_map: dict[str, str] = {}
    if "trangthai" in work.columns and "trang_thai" not in work.columns:
        rename_map["trangthai"] = "trang_thai"
    if "trangThai" in work.columns and "trang_thai" not in work.columns:
        rename_map["trangThai"] = "trang_thai"
    if rename_map:
        work = work.rename(columns=rename_map)
    return work


def resolve_image_paths(frame: pd.DataFrame, dataset_root: str | Path) -> pd.DataFrame:
    work = frame.copy()
    root = Path(dataset_root)

    def _resolve(p: Any) -> str:
        raw = Path(str(p))
        if raw.is_absolute():
            return str(raw)
        direct = root / raw
        if direct.exists():
            return str(direct.resolve())
        candidate = root / "image" / raw
        if candidate.exists():
            return str(candidate.resolve())
        return str(direct.resolve())

    work["image"] = work["image"].apply(_resolve)
    return work


def ensure_columns(frame: pd.DataFrame, required: list[str]) -> None:
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"Missing columns: {', '.join(missing)}")


def discover_manifest_from_tree(dataset_root: str | Path) -> pd.DataFrame:
    root = Path(dataset_root)
    records: list[dict[str, Any]] = []
    for image_path in root.rglob("*"):
        if image_path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        parts = image_path.relative_to(root).parts
        if len(parts) < 4:
            continue
        loai, dang, trang_thai = parts[0], parts[1], parts[2]
        records.append(
            {
                "image": str(image_path.resolve()),
                "loai": str(loai).strip(),
                "dang": str(dang).strip(),
                "trang_thai": str(trang_thai).strip(),
            }
        )
    if not records:
        raise FileNotFoundError(f"No images found under {root}")
    frame = pd.DataFrame(records)
    frame["split"] = ""
    return frame


def load_manifest(dataset_root: str | Path, labels_csv: str | Path | None = None) -> pd.DataFrame:
    if labels_csv and Path(labels_csv).exists():
        frame = pd.read_csv(labels_csv)
        frame = normalize_manifest_columns(frame)
        frame = resolve_image_paths(frame, dataset_root)
        ensure_columns(frame, ["image", "loai", "dang", "trang_thai"])
        if "split" not in frame.columns:
            frame["split"] = ""
        return frame
    return discover_manifest_from_tree(dataset_root)


def _alloc_counts(group_size: int, ratios: tuple[float, float, float]) -> tuple[int, int, int]:
    if group_size == 1:
        return 1, 0, 0
    if group_size == 2:
        return 1, 1, 0
    raw = np.array(ratios) * group_size
    counts = np.floor(raw).astype(int)
    counts[counts == 0] = 1
    while counts.sum() > group_size:
        idx = int(np.argmax(counts))
        if counts[idx] > 1:
            counts[idx] -= 1
        else:
            break
    remain = group_size - int(counts.sum())
    order = np.argsort(raw - np.floor(raw))[::-1].tolist()
    for idx in order:
        if remain <= 0:
            break
        counts[idx] += 1
        remain -= 1
    return int(counts[0]), int(counts[1]), int(counts[2])


def _ensure_loai_presence(frame: pd.DataFrame, seed: int) -> pd.DataFrame:
    rng = random.Random(seed)
    work = frame.copy()
    for loai in sorted(work["loai"].astype(str).unique()):
        present = set(work.loc[work["loai"] == loai, "split"].tolist())
        missing = [x for x in ["train", "valid", "test"] if x not in present]
        for target in missing:
            moved = False
            for donor in ["train", "valid", "test"]:
                if donor == target:
                    continue
                rows = work[(work["loai"] == loai) & (work["split"] == donor)]
                if rows.empty:
                    continue
                idx = rng.choice(rows.index.tolist())
                work.loc[idx, "split"] = target
                moved = True
                break
            if not moved:
                continue
    return work


def split_manifest(
    frame: pd.DataFrame,
    seed: int = 42,
    min_key_count: int = 10,
    ratios: tuple[float, float, float] = (0.8, 0.1, 0.1),
) -> pd.DataFrame:
    work = frame.copy().reset_index(drop=True)
    work["stratify_key"] = work["loai"].astype(str) + "_" + work["trang_thai"].astype(str)
    strat_col = "stratify_key"
    if (work[strat_col].value_counts() < min_key_count).any():
        strat_col = "loai"

    rng = random.Random(seed)
    buckets: dict[str, list[int]] = {"train": [], "valid": [], "test": []}
    for _, group in work.groupby(strat_col, sort=False):
        idxs = group.index.tolist()
        rng.shuffle(idxs)
        n_train, n_valid, n_test = _alloc_counts(len(idxs), ratios)
        buckets["train"].extend(idxs[:n_train])
        buckets["valid"].extend(idxs[n_train:n_train + n_valid])
        buckets["test"].extend(idxs[n_train + n_valid:n_train + n_valid + n_test])

    split_names = pd.Series(index=work.index, dtype="object")
    for split_name, idxs in buckets.items():
        split_names.loc[idxs] = split_name
    work["split"] = split_names.fillna("train")
    return _ensure_loai_presence(work, seed)


def save_manifest(frame: pd.DataFrame, output_csv: str | Path) -> None:
    out = Path(output_csv)
    out.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(out, index=False)


def build_label_maps(frame: pd.DataFrame) -> LabelMaps:
    return LabelMaps(
        loai_to_idx={x: i for i, x in enumerate(sorted(frame["loai"].astype(str).unique()))},
        dang_to_idx={x: i for i, x in enumerate(sorted(frame["dang"].astype(str).unique()))},
        trang_thai_to_idx={x: i for i, x in enumerate(sorted(frame["trang_thai"].astype(str).unique()))},
    )


def class_counts(frame: pd.DataFrame, column: str) -> dict[str, int]:
    return frame[column].astype(str).value_counts().sort_index().to_dict()


def compute_class_weights(frame: pd.DataFrame, column: str) -> dict[str, float]:
    counts = class_counts(frame, column)
    total = float(sum(counts.values()))
    num_classes = max(len(counts), 1)
    return {key: total / (num_classes * val) for key, val in counts.items() if val > 0}


def save_json(data: dict[str, Any], output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
