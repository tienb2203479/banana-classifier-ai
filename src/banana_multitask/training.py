from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import nn
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR, ReduceLROnPlateau
from tqdm import tqdm

from .data import load_or_prepare_data, make_loaders
from .losses import build_losses, compute_total_loss
from .metrics import classification_metrics, logits_to_preds, save_confusion_csv
from .model import ModelSpec, MultiTaskEfficientNet
from .utils import LabelMaps, compute_class_weights, save_json, seed_everything


@dataclass
class TrainConfig:
    dataset_root: str
    labels_csv: str | None
    split_csv: str
    output_dir: str
    batch_size: int = 32
    image_size: int = 300
    epochs: int = 50
    seed: int = 42
    num_workers: int = 2
    imbalance_strategy: str = "focal_weighted"
    backbone: str = "b4"
    dropout: float = 0.5
    scheduler: str = "cosine"
    lr_head: float = 2e-4
    lr_backbone: float = 1e-4
    patience: int = 15
    freeze_epochs: int = 5
    pretrained: bool = True
    show_progress: bool = True


def _move_batch(batch: dict[str, Any], device: torch.device) -> dict[str, Any]:
    return {
        "image": batch["image"].to(device, non_blocking=True),
        "loai": batch["loai"].to(device, non_blocking=True),
        "dang": batch["dang"].to(device, non_blocking=True),
        "trang_thai": batch["trang_thai"].to(device, non_blocking=True),
        "image_path": batch["image_path"],
    }


def evaluate(model: nn.Module, loader: torch.utils.data.DataLoader, label_maps: LabelMaps, device: torch.device) -> dict[str, Any]:
    model.eval()
    y_true = {"loai": [], "dang": [], "trang_thai": []}
    y_pred = {"loai": [], "dang": [], "trang_thai": []}
    with torch.no_grad():
        for batch in loader:
            batch = _move_batch(batch, device)
            outputs = model(batch["image"])
            preds = logits_to_preds(outputs)
            y_true["loai"].extend(batch["loai"].cpu().numpy().tolist())
            y_true["dang"].extend(batch["dang"].cpu().numpy().tolist())
            y_true["trang_thai"].extend(batch["trang_thai"].cpu().numpy().tolist())
            y_pred["loai"].extend(preds["loai"].tolist())
            y_pred["dang"].extend(preds["dang"].tolist())
            y_pred["trang_thai"].extend(preds["trang_thai"].tolist())

    report: dict[str, Any] = {}
    for head, names in [
        ("loai", list(label_maps.loai_to_idx.keys())),
        ("dang", list(label_maps.dang_to_idx.keys())),
        ("trang_thai", list(label_maps.trang_thai_to_idx.keys())),
    ]:
        report[head] = classification_metrics(np.asarray(y_true[head]), np.asarray(y_pred[head]), names)
    return report


def train(config: TrainConfig) -> dict[str, Any]:
    seed_everything(config.seed)
    out_dir = Path(config.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    frame, label_maps = load_or_prepare_data(config.dataset_root, config.labels_csv, config.split_csv, seed=config.seed)
    train_loader, valid_loader, test_loader = make_loaders(
        frame, label_maps, config.batch_size, config.num_workers, config.image_size, config.imbalance_strategy
    )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    use_amp = device.type == "cuda"
    torch.set_float32_matmul_precision("high")

    model = MultiTaskEfficientNet(
        ModelSpec(
            num_loai=len(label_maps.loai_to_idx),
            num_dang=len(label_maps.dang_to_idx),
            num_trang_thai=len(label_maps.trang_thai_to_idx),
            backbone=config.backbone,
            dropout=config.dropout,
            pretrained=config.pretrained,
        )
    ).to(device)

    train_frame = frame[frame["split"] == "train"]
    class_weights = {
        "loai": compute_class_weights(train_frame, "loai"),
        "dang": compute_class_weights(train_frame, "dang"),
        "trang_thai": compute_class_weights(train_frame, "trang_thai"),
    }
    losses = build_losses(config.imbalance_strategy, class_weights, label_maps, device)

    model.freeze_backbone()
    optimizer = AdamW(
        [
            {"params": model.features.parameters(), "lr": config.lr_backbone},
            {
                "params": list(model.pool.parameters())
                + list(model.dropout.parameters())
                + list(model.head_loai.parameters())
                + list(model.head_dang.parameters())
                + list(model.head_trang_thai.parameters()),
                "lr": config.lr_head,
            },
        ],
        weight_decay=5e-3,
    )

    scheduler: Any
    if config.scheduler == "cosine":
        scheduler = CosineAnnealingLR(optimizer, T_max=max(config.epochs, 1))
    else:
        scheduler = ReduceLROnPlateau(optimizer, mode="max", patience=2, factor=0.5)

    scaler = torch.amp.GradScaler("cuda", enabled=use_amp)
    best_f1 = -1.0
    best_epoch = 0
    stale = 0
    history: list[dict[str, Any]] = []

    for epoch in range(1, config.epochs + 1):
        if epoch == config.freeze_epochs + 1:
            model.unfreeze_backbone()

        model.train()
        running_loss = 0.0
        train_iter = tqdm(train_loader, desc=f"epoch {epoch}/{config.epochs}", leave=False) if config.show_progress else train_loader
        for batch in train_iter:
            batch = _move_batch(batch, device)
            optimizer.zero_grad(set_to_none=True)
            with torch.amp.autocast("cuda", enabled=use_amp):
                outputs = model(batch["image"])
                bundle = compute_total_loss(outputs, batch, losses)
            scaler.scale(bundle.total).backward()
            scaler.step(optimizer)
            scaler.update()
            running_loss += float(bundle.total.detach().cpu()) * len(batch["image"])
            if config.show_progress:
                train_iter.set_postfix(loss=float(bundle.total.detach().cpu()))

        train_loss = running_loss / max(len(train_loader.dataset), 1)
        valid_report = evaluate(model, valid_loader, label_maps, device)
        head_scores = [
            float(valid_report["loai"]["weighted_f1"]),
            float(valid_report["dang"]["weighted_f1"]),
            float(valid_report["trang_thai"]["weighted_f1"]),
        ]
        weighted_f1 = float(sum(head_scores) / len(head_scores))
        if config.scheduler == "cosine":
            scheduler.step()
        else:
            scheduler.step(weighted_f1)

        history.append(
            {
                "epoch": epoch,
                "train_loss": train_loss,
                "valid_weighted_f1_loai": weighted_f1,
                "valid_macro_f1_loai": float(valid_report["loai"]["macro_f1"]),
            }
        )
        loai_macro = float(valid_report["loai"]["macro_f1"])
        dang_macro = float(valid_report["dang"]["macro_f1"])
        tt_macro = float(valid_report["trang_thai"]["macro_f1"])
        macro_f1_combined = (loai_macro + dang_macro + tt_macro) / 3.0
        loai_acc = float(valid_report["loai"]["accuracy"])
        dang_acc = float(valid_report["dang"]["accuracy"])
        tt_acc = float(valid_report["trang_thai"]["accuracy"])
        acc_combined = (loai_acc + dang_acc + tt_acc) / 3.0
        print(
            (
                f"[epoch {epoch}/{config.epochs}] "
                f"train_loss={train_loss:.4f} "
                f"macro_f1_loai={loai_macro:.4f} "
                f"macro_f1_dang={dang_macro:.4f} "
                f"macro_f1_trang_thai={tt_macro:.4f} "
                f"macro_f1_combined={macro_f1_combined:.4f} "
                f"acc_loai={loai_acc:.4f} "
                f"acc_dang={dang_acc:.4f} "
                f"acc_trang_thai={tt_acc:.4f} "
                f"acc_combined={acc_combined:.4f} "
                f"wf1_combined={weighted_f1:.4f}"
            ),
            flush=True,
        )

        checkpoint = {
            "epoch": epoch,
            "model_state": model.state_dict(),
            "optimizer_state": optimizer.state_dict(),
            "label_maps": {
                "loai_to_idx": label_maps.loai_to_idx,
                "dang_to_idx": label_maps.dang_to_idx,
                "trang_thai_to_idx": label_maps.trang_thai_to_idx,
            },
            "config": asdict(config),
            "valid_report": valid_report,
            "history": history,
        }
        torch.save(checkpoint, out_dir / "last.pt")
        if weighted_f1 > best_f1:
            best_f1 = weighted_f1
            best_epoch = epoch
            stale = 0
            torch.save(checkpoint, out_dir / "best.pt")
        else:
            stale += 1

        if stale >= config.patience:
            print(f"[early_stop] epoch={epoch} patience={config.patience}", flush=True)
            break

    best_ckpt = torch.load(out_dir / "best.pt", map_location=device, weights_only=False)
    model.load_state_dict(best_ckpt["model_state"])
    test_report = evaluate(model, test_loader, label_maps, device)

    save_json(
        {
            "best_epoch": best_epoch,
            "best_weighted_f1_loai": best_f1,
            "history": history,
            "test_report": test_report,
            "class_weights": class_weights,
            "label_maps": {
                "loai": label_maps.loai_to_idx,
                "dang": label_maps.dang_to_idx,
                "trang_thai": label_maps.trang_thai_to_idx,
            },
            "device": str(device),
        },
        out_dir / "metrics.json",
    )

    for head in ["loai", "dang", "trang_thai"]:
        save_confusion_csv(
            np.asarray(test_report[head]["confusion_matrix"]),
            list(getattr(label_maps, f"{head}_to_idx").keys()),
            out_dir / f"confusion_{head}.csv",
        )

    return {
        "best_epoch": best_epoch,
        "best_weighted_f1_loai": best_f1,
        "metrics_path": str(out_dir / "metrics.json"),
        "best_checkpoint": str(out_dir / "best.pt"),
        "device": str(device),
    }


def build_config_from_args(args: Any) -> TrainConfig:
    return TrainConfig(
        dataset_root=args.dataset_root,
        labels_csv=args.labels_csv,
        split_csv=args.split_csv,
        output_dir=args.output_dir,
        batch_size=args.batch_size,
        image_size=args.image_size,
        epochs=args.epochs,
        seed=args.seed,
        num_workers=args.num_workers,
        imbalance_strategy=args.imbalance_strategy,
        backbone=args.backbone,
        dropout=args.dropout,
        scheduler=args.scheduler,
        lr_head=args.lr_head,
        lr_backbone=args.lr_backbone,
        patience=args.patience,
        freeze_epochs=args.freeze_epochs,
        pretrained=not args.no_pretrained,
    )
