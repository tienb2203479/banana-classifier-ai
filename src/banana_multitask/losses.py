from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import torch
from torch import nn
from torch.nn import functional as F


def _weights_to_tensor(weights: dict[str, float] | None, mapping: dict[str, int], device: torch.device) -> torch.Tensor | None:
    if not weights:
        return None
    values = [float(weights.get(lbl, 1.0)) for lbl, _ in sorted(mapping.items(), key=lambda x: x[1])]
    return torch.tensor(values, dtype=torch.float32, device=device)


class FocalLoss(nn.Module):
    def __init__(self, alpha: torch.Tensor | None = None, gamma: float = 2.0, label_smoothing: float = 0.0):
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.label_smoothing = max(float(label_smoothing), 0.0)

    def forward(self, logits: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        logp = F.log_softmax(logits, dim=1)
        p = logp.exp()
        target = target.long().view(-1, 1)
        log_pt = logp.gather(1, target).squeeze(1)
        pt = p.gather(1, target).squeeze(1)
        loss = -(1 - pt).pow(self.gamma) * log_pt
        if self.label_smoothing > 0:
            smooth = -logp.mean(dim=1)
            loss = (1.0 - self.label_smoothing) * loss + self.label_smoothing * smooth
        if self.alpha is not None:
            alpha = self.alpha.gather(0, target.squeeze(1))
            loss = loss * alpha
        return loss.mean()


@dataclass
class LossBundle:
    loss_loai: torch.Tensor
    loss_dang: torch.Tensor
    loss_trang_thai: torch.Tensor
    total: torch.Tensor


def build_losses(strategy: str, class_weights: dict[str, dict[str, float]], label_maps: Any, device: torch.device) -> dict[str, Any]:
    w_loai = _weights_to_tensor(class_weights.get("loai"), label_maps.loai_to_idx, device)
    w_dang = _weights_to_tensor(class_weights.get("dang"), label_maps.dang_to_idx, device)
    w_tt = _weights_to_tensor(class_weights.get("trang_thai"), label_maps.trang_thai_to_idx, device)

    if strategy in {"focal", "focal_weighted"}:
        use_ce_weights = strategy == "focal_weighted"
        return {
            "loai": FocalLoss(alpha=w_loai, gamma=2.5, label_smoothing=0.1),
            "dang": nn.CrossEntropyLoss(weight=w_dang if use_ce_weights else None, label_smoothing=0.08),
            "trang_thai": nn.CrossEntropyLoss(weight=w_tt if use_ce_weights else None, label_smoothing=0.08),
        }
    use_weight = strategy == "weighted_loss"
    return {
        "loai": nn.CrossEntropyLoss(weight=w_loai if use_weight else None),
        "dang": nn.CrossEntropyLoss(weight=w_dang if use_weight else None),
        "trang_thai": nn.CrossEntropyLoss(weight=w_tt if use_weight else None),
    }


def compute_total_loss(outputs: dict[str, torch.Tensor], batch: dict[str, torch.Tensor], losses: dict[str, Any]) -> LossBundle:
    l_loai = losses["loai"](outputs["loai"], batch["loai"])
    l_dang = losses["dang"](outputs["dang"], batch["dang"])
    l_tt = losses["trang_thai"](outputs["trang_thai"], batch["trang_thai"])
    total = 0.5 * l_loai + 0.3 * l_dang + 0.2 * l_tt
    return LossBundle(l_loai, l_dang, l_tt, total)
