#!/usr/bin/env python3
"""
Generate evaluation reports for B4 v3 - similar to B3 format.

Outputs:
- reports/eval.json (detailed test metrics)
- reports/summary.json (best score summary)
- reports/summary.md (markdown summary)
"""

from pathlib import Path
import sys
import json
import numpy as np
import torch
import pandas as pd
from torch.utils.data import DataLoader

sys.path.insert(0, str(Path(__file__).parent / "src"))

from banana_multitask.model import MultiTaskEfficientNet, ModelSpec
from banana_multitask.data import load_or_prepare_data, make_loaders
from banana_multitask.metrics import logits_to_preds, classification_metrics
from banana_multitask.utils import LabelMaps


def load_model(checkpoint_path: str, model_spec: ModelSpec, device: torch.device):
    """Load trained model from checkpoint."""
    model = MultiTaskEfficientNet(model_spec).to(device)
    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)
    
    # Extract model_state if it's a full checkpoint
    if isinstance(checkpoint, dict) and "model_state" in checkpoint:
        state_dict = checkpoint["model_state"]
    elif isinstance(checkpoint, dict) and "state_dict" in checkpoint:
        state_dict = checkpoint["state_dict"]
    else:
        state_dict = checkpoint
    
    model.load_state_dict(state_dict)
    model.eval()
    return model


def evaluate_model(model: MultiTaskEfficientNet, test_loader: DataLoader, label_maps: LabelMaps, device: torch.device):
    """Evaluate model on test set."""
    y_true = {"loai": [], "dang": [], "trang_thai": []}
    y_pred = {"loai": [], "dang": [], "trang_thai": []}
    
    with torch.no_grad():
        for batch in test_loader:
            images = batch["image"].to(device, non_blocking=True)
            outputs = model(images)
            preds = logits_to_preds(outputs)
            
            y_true["loai"].extend(batch["loai"].cpu().numpy().tolist())
            y_true["dang"].extend(batch["dang"].cpu().numpy().tolist())
            y_true["trang_thai"].extend(batch["trang_thai"].cpu().numpy().tolist())
            y_pred["loai"].extend(preds["loai"].tolist())
            y_pred["dang"].extend(preds["dang"].tolist())
            y_pred["trang_thai"].extend(preds["trang_thai"].tolist())
    
    # Compute metrics
    report = {}
    for head, names in [
        ("loai", list(label_maps.loai_to_idx.keys())),
        ("dang", list(label_maps.dang_to_idx.keys())),
        ("trang_thai", list(label_maps.trang_thai_to_idx.keys())),
    ]:
        report[head] = classification_metrics(
            np.asarray(y_true[head]), 
            np.asarray(y_pred[head]), 
            names
        )
    
    return report


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}\n")
    
    # Load data
    print("📦 Loading data...")
    frame, label_maps = load_or_prepare_data(
        "data", 
        None,
        "data/splits/labels_multi_split.csv", 
        seed=42
    )
    
    # Create test loader
    _, _, test_loader = make_loaders(
        frame, label_maps, batch_size=32, num_workers=2, image_size=300, strategy="none"
    )
    print("✅ Data loaded\n")
    
    # Load B4 v3 model
    print("📦 Loading B4 v3 checkpoint...")
    model_spec = ModelSpec(
        num_loai=len(label_maps.loai_to_idx),
        num_dang=len(label_maps.dang_to_idx),
        num_trang_thai=len(label_maps.trang_thai_to_idx),
        backbone="b4",
        dropout=0.5,
        pretrained=True,
    )
    
    model = load_model(
        "outputs/efficientnet_b4_v3/best.pt",
        model_spec,
        device
    )
    print("✅ Model loaded\n")
    
    # Evaluate
    print("🔄 Evaluating on test set...")
    report = evaluate_model(model, test_loader, label_maps, device)
    print("✅ Evaluation completed\n")
    
    # Create reports directory
    reports_dir = Path("outputs/efficientnet_b4_v3/reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    # Save eval.json (detailed metrics)
    eval_data = {
        "loai": report["loai"],
        "dang": report["dang"],
        "trangthai": report["trang_thai"],
        "score": (
            float(report["loai"]["accuracy"]) +
            float(report["dang"]["accuracy"]) +
            float(report["trang_thai"]["accuracy"])
        ) / 3
    }
    
    with open(reports_dir / "eval.json", "w") as f:
        json.dump(eval_data, f, indent=2)
    
    # Save summary.json
    summary_data = {
        "best_val_score": 0.9788851515565016,  # From metrics.json
    }
    
    with open(reports_dir / "summary.json", "w") as f:
        json.dump(summary_data, f, indent=2)
    
    # Save summary.md
    loai_acc = report["loai"]["accuracy"]
    dang_acc = report["dang"]["accuracy"]
    tt_acc = report["trang_thai"]["accuracy"]
    score = eval_data["score"]
    
    summary_md = f"""# Summary - efficientnet_b4_v3

- Trained epochs: 32 (best epoch)
- Best val_score: 0.978885
- Model: EfficientNet-B4 (Optimized)

## Test Metrics
- score: {score:.6f}
- loai_accuracy: {loai_acc:.6f}
- dang_accuracy: {dang_acc:.6f}
- trangthai_accuracy: {tt_acc:.6f}

## Optimizations Applied
- Batch size: 32 → 16
- Dropout: 0.35 → 0.5
- Weight decay: 1e-4 → 5e-3
- Patience: 7 → 15
- Label smoothing: Increased
- Augmentation: Enhanced
"""
    
    with open(reports_dir / "summary.md", "w", encoding="utf-8") as f:
        f.write(summary_md)
    
    # Print results
    print("=" * 70)
    print("📊 B4 V3 - TEST RESULTS")
    print("=" * 70)
    print(f"\nAccuracy:")
    print(f"  Loại:       {loai_acc:.4f} ({loai_acc*100:.2f}%)")
    print(f"  Dạng:       {dang_acc:.4f} ({dang_acc*100:.2f}%)")
    print(f"  Trạng thái: {tt_acc:.4f} ({tt_acc*100:.2f}%)")
    print(f"  ➜ Average:  {score:.4f} ({score*100:.2f}%)")
    
    print(f"\n📈 Comparison:")
    print(f"  B3 (baseline):  96.80%")
    print(f"  B4 v2 (old):    96.25%")
    print(f"  B4 v3 (new):    {score*100:.2f}% ✅")
    print(f"\n  Improvement vs B3:   +{(score - 0.968)*100:.2f}%")
    print(f"  Improvement vs B4v2: +{(score - 0.9625)*100:.2f}%")
    
    print(f"\n✅ Reports saved to: outputs/efficientnet_b4_v3/reports/")
    print(f"   - eval.json")
    print(f"   - summary.json")
    print(f"   - summary.md")
    print("=" * 70)


if __name__ == "__main__":
    main()
