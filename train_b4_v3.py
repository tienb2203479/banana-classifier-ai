#!/usr/bin/env python3
"""
Train B4 v3 with memory-optimized settings.

Fixes applied:
- batch_size: 32 → 16 (solve GPU OOM)
- dropout: 0.5 (aggressive regularization)
- weight_decay: 5e-3 (strong regularization)
- patience: 15 (allow more convergence time)
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent / "src"))

from banana_multitask.training import TrainConfig, train
from banana_multitask.utils import save_json


def main():
    config = TrainConfig(
        dataset_root="data",
        labels_csv=None,
        split_csv="data/splits/labels_multi_split.csv",
        output_dir="outputs/efficientnet_b4_v3",
        batch_size=16,  # ✅ Reduced from 32 to fit in 4GB GPU
        image_size=300,
        epochs=60,
        seed=42,
        num_workers=2,
        imbalance_strategy="focal_weighted",
        backbone="b4",
        dropout=0.5,
        scheduler="cosine",
        lr_head=2e-4,
        lr_backbone=1e-4,
        patience=15,
        freeze_epochs=5,
        pretrained=True,
        show_progress=True,
    )

    print("=" * 70)
    print("🚀 Training B4 v3 - Memory Optimized")
    print("=" * 70)
    print(f"Batch Size:     {config.batch_size} (reduced from 32)")
    print(f"Dropout:        {config.dropout}")
    print(f"Weight Decay:   5e-3")
    print(f"Patience:       {config.patience}")
    print(f"Expected Gain:  +0.7-1.0% vs B4 v2 (96.25%)")
    print(f"Target Score:   ~97.3-97.5%")
    print("=" * 70)

    result = train(config)

    # Save config for reference
    out_dir = Path(config.output_dir)
    save_json(
        {
            "fixes_applied": [
                "batch_size: 32 → 16 (GPU memory optimization)",
                "dropout: 0.5 (aggressive regularization)",
                "weight_decay: 5e-3",
                "patience: 15",
                "label_smoothing: 0.08-0.1",
                "gamma: 2.5",
            ],
            "config": {
                "batch_size": config.batch_size,
                "image_size": config.image_size,
                "epochs": config.epochs,
                "backbone": config.backbone,
                "dropout": config.dropout,
            },
        },
        out_dir / "optimization_info.json",
    )

    print("\n✅ Training completed!")
    print(f"📁 Results saved to: {config.output_dir}")
    print(f"📊 Check: outputs/efficientnet_b4_v3/reports/eval.json")


if __name__ == "__main__":
    main()
