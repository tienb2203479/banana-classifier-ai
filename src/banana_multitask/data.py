from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd
import torch
from PIL import Image
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler
from torchvision import transforms

from .utils import (
    LabelMaps,
    build_label_maps,
    class_counts,
    load_manifest,
    normalize_manifest_columns,
    resolve_image_paths,
    save_manifest,
    split_manifest,
)


class BananaDataset(Dataset):
    def __init__(self, frame: pd.DataFrame, label_maps: LabelMaps, transform: Any | None = None):
        self.frame = frame.reset_index(drop=True).copy()
        self.label_maps = label_maps
        self.transform = transform

    def __len__(self) -> int:
        return len(self.frame)

    def __getitem__(self, index: int) -> dict[str, Any]:
        row = self.frame.iloc[index]
        image = Image.open(row["image"]).convert("RGB")
        if self.transform is not None:
            image = self.transform(image)
        return {
            "image": image,
            "loai": torch.tensor(self.label_maps.loai_to_idx[str(row["loai"])], dtype=torch.long),
            "dang": torch.tensor(self.label_maps.dang_to_idx[str(row["dang"])], dtype=torch.long),
            "trang_thai": torch.tensor(self.label_maps.trang_thai_to_idx[str(row["trang_thai"])], dtype=torch.long),
            "image_path": row["image"],
        }


def build_transforms(image_size: int = 300) -> tuple[Any, Any]:
    mean = [0.485, 0.456, 0.406]
    std = [0.229, 0.224, 0.225]
    train_tf = transforms.Compose(
        [
            transforms.RandomResizedCrop(image_size, scale=(0.75, 1.0)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomApply([transforms.RandomRotation(20)], p=0.6),
            transforms.RandomApply([transforms.RandomPerspective(distortion_scale=0.22, p=1.0)], p=0.35),
            transforms.RandomApply([transforms.RandomAffine(degrees=15, translate=(0.1, 0.1))], p=0.5),
            transforms.RandomApply(
                [
                    transforms.ColorJitter(
                        brightness=0.35,
                        contrast=0.35,
                        saturation=0.3,
                        hue=0.08,
                    )
                ],
                p=0.8,
            ),
            transforms.RandomApply([transforms.GaussianBlur(kernel_size=(3, 3), sigma=(0.1, 2.0))], p=0.4),
            transforms.RandomGrayscale(p=0.08),
            transforms.ToTensor(),
            transforms.RandomErasing(p=0.25, scale=(0.02, 0.12), ratio=(0.3, 3.3), value="random"),
            transforms.Normalize(mean=mean, std=std),
        ]
    )
    eval_tf = transforms.Compose(
        [
            transforms.Resize((image_size, image_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=mean, std=std),
        ]
    )
    return train_tf, eval_tf


def oversample_train_frame(frame: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    counts = class_counts(frame, "loai")
    target = max(counts.values())
    chunks = [frame]
    for label, cnt in counts.items():
        if cnt >= target:
            continue
        rows = frame[frame["loai"] == label]
        extra = rows.sample(n=target - cnt, replace=True, random_state=seed)
        chunks.append(extra)
    return pd.concat(chunks, ignore_index=True).sample(frac=1.0, random_state=seed).reset_index(drop=True)


def build_weighted_sampler(frame: pd.DataFrame) -> WeightedRandomSampler:
    counts = Counter(frame["loai"].astype(str).tolist())
    weights = [1.0 / counts[str(lbl)] for lbl in frame["loai"].astype(str).tolist()]
    return WeightedRandomSampler(weights=torch.DoubleTensor(weights), num_samples=len(weights), replacement=True)


def load_or_prepare_data(dataset_root: str | Path, labels_csv: str | Path | None, split_csv: str | Path, seed: int = 42) -> tuple[pd.DataFrame, LabelMaps]:
    split_path = Path(split_csv)
    if split_path.exists():
        frame = pd.read_csv(split_path)
        frame = normalize_manifest_columns(frame)
        frame = resolve_image_paths(frame, dataset_root)
        return frame, build_label_maps(frame)
    frame = load_manifest(dataset_root, labels_csv)
    split_df = split_manifest(frame, seed=seed)
    save_manifest(split_df, split_csv)
    return split_df, build_label_maps(split_df)


def make_loaders(
    frame: pd.DataFrame,
    label_maps: LabelMaps,
    batch_size: int,
    num_workers: int,
    image_size: int,
    strategy: str,
) -> tuple[DataLoader, DataLoader, DataLoader]:
    train_tf, eval_tf = build_transforms(image_size)
    split_series = frame["split"].astype(str).str.lower().str.strip()
    train_df = frame[split_series == "train"].copy().reset_index(drop=True)
    if strategy == "oversample":
        train_df = oversample_train_frame(train_df)
    valid_df = frame[split_series.isin({"valid", "val", "validation"})].copy().reset_index(drop=True)
    test_df = frame[split_series == "test"].copy().reset_index(drop=True)

    train_ds = BananaDataset(train_df, label_maps, transform=train_tf)
    valid_ds = BananaDataset(valid_df, label_maps, transform=eval_tf)
    test_ds = BananaDataset(test_df, label_maps, transform=eval_tf)

    sampler = build_weighted_sampler(train_df) if strategy == "sampler" else None
    use_cuda = torch.cuda.is_available()
    kwargs: dict[str, Any] = {"num_workers": num_workers, "pin_memory": use_cuda}
    if num_workers > 0:
        kwargs["persistent_workers"] = True

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=sampler is None, sampler=sampler, **kwargs)
    valid_loader = DataLoader(valid_ds, batch_size=batch_size, shuffle=False, **kwargs)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False, **kwargs)
    return train_loader, valid_loader, test_loader
