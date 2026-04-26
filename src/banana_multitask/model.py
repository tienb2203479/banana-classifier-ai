from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import torch
from torch import nn
from torchvision.models import EfficientNet_B3_Weights, EfficientNet_B4_Weights, efficientnet_b3, efficientnet_b4


@dataclass(frozen=True)
class ModelSpec:
    num_loai: int
    num_dang: int
    num_trang_thai: int
    backbone: str = "b3"
    dropout: float = 0.3
    pretrained: bool = True


class MultiTaskEfficientNet(nn.Module):
    def __init__(self, spec: ModelSpec):
        super().__init__()
        backbone_name = str(spec.backbone).lower().strip()
        if backbone_name == "b4":
            weights = EfficientNet_B4_Weights.IMAGENET1K_V1 if spec.pretrained else None
            backbone = efficientnet_b4(weights=weights)
            hidden = 1792
        else:
            weights = EfficientNet_B3_Weights.IMAGENET1K_V1 if spec.pretrained else None
            backbone = efficientnet_b3(weights=weights)
            hidden = 1536
        self.features = backbone.features
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.dropout = nn.Dropout(spec.dropout)
        self.head_loai = nn.Linear(hidden, spec.num_loai)
        self.head_dang = nn.Linear(hidden, spec.num_dang)
        self.head_trang_thai = nn.Linear(hidden, spec.num_trang_thai)

    def freeze_backbone(self) -> None:
        for p in self.features.parameters():
            p.requires_grad = False

    def unfreeze_backbone(self) -> None:
        for p in self.features.parameters():
            p.requires_grad = True

    def forward(self, image: torch.Tensor) -> dict[str, torch.Tensor]:
        x = self.features(image)
        x = self.pool(x).flatten(1)
        x = self.dropout(x)
        return {
            "loai": self.head_loai(x),
            "dang": self.head_dang(x),
            "trang_thai": self.head_trang_thai(x),
        }


class MultiTaskEfficientNetB3(MultiTaskEfficientNet):
    def __init__(self, spec: ModelSpec):
        adjusted = ModelSpec(
            num_loai=spec.num_loai,
            num_dang=spec.num_dang,
            num_trang_thai=spec.num_trang_thai,
            backbone="b3",
            dropout=spec.dropout,
            pretrained=spec.pretrained,
        )
        super().__init__(adjusted)


def _infer_model_spec(checkpoint: dict[str, Any], pretrained: bool = True) -> ModelSpec:
    label_maps = checkpoint.get("label_maps", {}) if isinstance(checkpoint, dict) else {}
    config = checkpoint.get("config", {}) if isinstance(checkpoint, dict) else {}

    loai_map = label_maps.get("loai_to_idx", {}) or label_maps.get("loai", {})
    dang_map = label_maps.get("dang_to_idx", {}) or label_maps.get("dang", {})
    tt_map = label_maps.get("trang_thai_to_idx", {}) or label_maps.get("trang_thai", {})

    backbone = str(config.get("backbone", "b4")).lower().strip()
    dropout = float(config.get("dropout", 0.5 if backbone == "b4" else 0.3))

    return ModelSpec(
        num_loai=max(len(loai_map), 1),
        num_dang=max(len(dang_map), 1),
        num_trang_thai=max(len(tt_map), 1),
        backbone=backbone,
        dropout=dropout,
        pretrained=pretrained,
    )


def load_checkpoint(checkpoint_path: str | Path, device: torch.device | str | None = None, pretrained: bool = True) -> tuple[MultiTaskEfficientNet, dict[str, Any]]:
    device_obj = torch.device(device) if device is not None else torch.device("cpu")
    checkpoint = torch.load(checkpoint_path, map_location=device_obj, weights_only=False)
    if isinstance(checkpoint, dict) and "model_state" in checkpoint:
        model_state = checkpoint["model_state"]
    elif isinstance(checkpoint, dict) and "state_dict" in checkpoint:
        model_state = checkpoint["state_dict"]
    else:
        model_state = checkpoint

    spec = _infer_model_spec(checkpoint if isinstance(checkpoint, dict) else {}, pretrained=pretrained)
    model = MultiTaskEfficientNet(spec).to(device_obj)
    model.load_state_dict(model_state)
    return model, checkpoint if isinstance(checkpoint, dict) else {"model_state": model_state}
