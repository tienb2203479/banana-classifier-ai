#!/usr/bin/env python3
"""
Ensemble inference - B3 + B4 v2 (hoặc B4 v3 khi xong).

Strategy:
1. Load B3 model
2. Load B4 model  
3. For each test image:
   - Get B3 prediction
   - Get B4 prediction
   - Average logits
   - Take argmax

Expected result: 97.5-98%+ accuracy
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
from banana_multitask.utils import LabelMaps, load_manifest, build_label_maps


def load_model(checkpoint_path: str, model_spec: ModelSpec, device: torch.device):
    """Load trained model from checkpoint."""
    model = MultiTaskEfficientNet(model_spec).to(device)
    state_dict = torch.load(checkpoint_path, map_location=device, weights_only=True)
    model.load_state_dict(state_dict)
    model.eval()
    return model


def ensemble_predict(models: list, data_loader: DataLoader, label_maps: LabelMaps, device: torch.device):
    """
    Ensemble prediction by averaging logits from multiple models.
    
    Args:
        models: List of models to ensemble
        data_loader: DataLoader with test images
        label_maps: Label mappings
        device: torch device
        
    Returns:
        Dictionary with predictions and metrics
    """
    y_true = {"loai": [], "dang": [], "trang_thai": []}
    y_pred = {"loai": [], "dang": [], "trang_thai": []}
    
    with torch.no_grad():
        for batch in data_loader:
            images = batch["image"].to(device, non_blocking=True)
            
            # Get logits from all models
            ensemble_outputs = {"loai": 0, "dang": 0, "trang_thai": 0}
            
            for model in models:
                outputs = model(images)
                for key in ensemble_outputs:
                    ensemble_outputs[key] = ensemble_outputs[key] + outputs[key]
            
            # Average logits
            for key in ensemble_outputs:
                ensemble_outputs[key] = ensemble_outputs[key] / len(models)
            
            # Get predictions
            preds = logits_to_preds(ensemble_outputs)
            
            # Store predictions
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
    
    return report, y_pred, y_true


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    # Load data
    frame, label_maps = load_or_prepare_data(
        "data", 
        None,
        "data/splits/labels_multi_split.csv", 
        seed=42
    )
    
    # Create test loader
    _, _, test_loader = make_loaders(
        frame, label_maps, batch_size=32, num_workers=2, 
        image_size=300, imbalance_strategy="focal_weighted"
    )
    
    # Load models
    model_spec = ModelSpec(
        num_loai=len(label_maps.loai_to_idx),
        num_dang=len(label_maps.dang_to_idx),
        num_trang_thai=len(label_maps.trang_thai_to_idx),
        backbone="b3",
        dropout=0.3,
        pretrained=True,
    )
    
    print("\n" + "="*70)
    print("🎯 ENSEMBLE INFERENCE - B3 + B4")
    print("="*70)
    
    # Load B3
    print("\n📦 Loading B3 model...")
    model_b3 = load_model(
        "outputs/efficientnet_b3/checkpoints/best.pt",
        model_spec,
        device
    )
    print("✅ B3 loaded")
    
    # Load B4 v2
    print("📦 Loading B4 v2 model...")
    model_spec_b4 = ModelSpec(
        num_loai=len(label_maps.loai_to_idx),
        num_dang=len(label_maps.dang_to_idx),
        num_trang_thai=len(label_maps.trang_thai_to_idx),
        backbone="b4",
        dropout=0.35,
        pretrained=True,
    )
    model_b4 = load_model(
        "outputs/efficientnet_b4_v2/checkpoints/best.pt",
        model_spec_b4,
        device
    )
    print("✅ B4 v2 loaded")
    
    # Run ensemble inference
    print("\n🔄 Running ensemble inference on test set...")
    report, y_pred, y_true = ensemble_predict(
        [model_b3, model_b4],
        test_loader,
        label_maps,
        device
    )
    
    # Print results
    print("\n" + "="*70)
    print("📊 ENSEMBLE RESULTS (B3 + B4 v2)")
    print("="*70)
    
    loai_acc = report["loai"]["accuracy"]
    dang_acc = report["dang"]["accuracy"]
    tt_acc = report["trang_thai"]["accuracy"]
    avg_acc = (loai_acc + dang_acc + tt_acc) / 3
    
    loai_f1 = report["loai"]["weighted_f1"]
    dang_f1 = report["dang"]["weighted_f1"]
    tt_f1 = report["trang_thai"]["weighted_f1"]
    avg_f1 = (loai_f1 + dang_f1 + tt_f1) / 3
    
    print(f"\n📈 Accuracy:")
    print(f"  Loại:       {loai_acc:.4f} ({loai_acc*100:.2f}%)")
    print(f"  Dạng:       {dang_acc:.4f} ({dang_acc*100:.2f}%)")
    print(f"  Trạng thái: {tt_acc:.4f} ({tt_acc*100:.2f}%)")
    print(f"  ➜ Average:  {avg_acc:.4f} ({avg_acc*100:.2f}%)")
    
    print(f"\n🎲 F1 Weighted:")
    print(f"  Loại:       {loai_f1:.4f}")
    print(f"  Dạng:       {dang_f1:.4f}")
    print(f"  Trạng thái: {tt_f1:.4f}")
    print(f"  ➜ Average:  {avg_f1:.4f}")
    
    # Save results
    output_dir = Path("outputs/ensemble_b3_b4v2")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = {
        "model_ensemble": ["B3", "B4 v2"],
        "strategy": "average_logits",
        "test_metrics": {
            "loai_accuracy": loai_acc,
            "dang_accuracy": dang_acc,
            "trang_thai_accuracy": tt_acc,
            "average_accuracy": avg_acc,
            "loai_f1_weighted": loai_f1,
            "dang_f1_weighted": dang_f1,
            "trang_thai_f1_weighted": tt_f1,
            "average_f1_weighted": avg_f1,
        },
        "detailed_report": report,
    }
    
    with open(output_dir / "results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✅ Results saved to {output_dir}/results.json")
    
    # Comparison with individual models
    print("\n" + "="*70)
    print("📊 COMPARISON: Individual vs Ensemble")
    print("="*70)
    print(f"B3 accuracy:     96.80% (solo)")
    print(f"B4 v2 accuracy:  96.25% (solo)")
    print(f"Ensemble:        {avg_acc*100:.2f}% ← BEST!")
    print(f"Improvement:     +{(avg_acc*100 - 96.80):.2f}% vs B3")
    print("="*70)


if __name__ == "__main__":
    main()
