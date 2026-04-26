from __future__ import annotations

from pathlib import Path
from typing import Any

import json

import numpy as np
import pandas as pd
import torch


def confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray, num_classes: int) -> np.ndarray:
    cm = np.zeros((num_classes, num_classes), dtype=np.int64)
    for t, p in zip(y_true, y_pred):
        cm[int(t), int(p)] += 1
    return cm


def classification_metrics(y_true: np.ndarray, y_pred: np.ndarray, class_names: list[str]) -> dict[str, Any]:
    cm = confusion_matrix(y_true, y_pred, len(class_names))
    per_class = []
    support = cm.sum(axis=1)
    total = support.sum()
    recalls = []
    for i, cls in enumerate(class_names):
        tp = float(cm[i, i])
        fp = float(cm[:, i].sum() - tp)
        fn = float(cm[i, :].sum() - tp)
        precision = tp / (tp + fp) if tp + fp > 0 else 0.0
        recall = tp / (tp + fn) if tp + fn > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall > 0 else 0.0
        per_class.append({"class": cls, "precision": precision, "recall": recall, "f1": f1, "support": int(support[i])})
        recalls.append(recall)

    accuracy = float((y_true == y_pred).mean()) if len(y_true) else 0.0
    macro_precision = float(np.mean([x["precision"] for x in per_class])) if per_class else 0.0
    macro_recall = float(np.mean([x["recall"] for x in per_class])) if per_class else 0.0
    macro_f1 = float(np.mean([x["f1"] for x in per_class])) if per_class else 0.0
    weighted_precision = float(np.sum([x["precision"] * x["support"] for x in per_class]) / total) if total else 0.0
    weighted_recall = float(np.sum([x["recall"] * x["support"] for x in per_class]) / total) if total else 0.0
    weighted_f1 = float(np.sum([x["f1"] * x["support"] for x in per_class]) / total) if total else 0.0
    balanced_accuracy = float(np.mean(recalls)) if recalls else 0.0
    return {
        "accuracy": accuracy,
        "macro_precision": macro_precision,
        "macro_recall": macro_recall,
        "macro_f1": macro_f1,
        "weighted_precision": weighted_precision,
        "weighted_recall": weighted_recall,
        "weighted_f1": weighted_f1,
        "balanced_accuracy": balanced_accuracy,
        "confusion_matrix": cm.tolist(),
        "per_class": per_class,
    }


def logits_to_preds(outputs: dict[str, torch.Tensor]) -> dict[str, np.ndarray]:
    return {
        "loai": outputs["loai"].argmax(dim=1).cpu().numpy(),
        "dang": outputs["dang"].argmax(dim=1).cpu().numpy(),
        "trang_thai": outputs["trang_thai"].argmax(dim=1).cpu().numpy(),
    }


def save_report(report: dict[str, Any], output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)


def save_confusion_csv(cm: np.ndarray, class_names: list[str], output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(cm, index=class_names, columns=class_names).to_csv(path)
