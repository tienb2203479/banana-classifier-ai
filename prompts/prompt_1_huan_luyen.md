Bạn là ML Engineer senior.

Hãy xây dựng project huấn luyện Multi-task Learning (MTL) cho phân loại chuối từ ảnh với 3 đầu ra:
- loai: 5 class
- dang: 3 class
- trang_thai: 2 class

==================================================
🔥 I) HYPERPARAMETERS (CHO PHÉP CHỈNH NHANH - ĐẶT TRÊN CÙNG)
==================================================

MODEL_NAME = "efficientnet_b4"

INPUT_SIZE = 300
BATCH_SIZE = 32
EPOCHS = 60
FREEZE_BACKBONE_EPOCHS = 5

LEARNING_RATE = 1e-4
WEIGHT_DECAY = 1e-4

LOSS_WEIGHTS = {
    "loai": 0.4,
    "dang": 0.4,
    "trang_thai": 0.2
}

EARLY_STOPPING_PATIENCE = 7
SEED = 42

USE_WEIGHTED_LOSS = True
USE_SAMPLER = False

NUM_WORKERS = min(8, CPU_COUNT)
PIN_MEMORY = True

DEVICE = "cuda" if available else "cpu"

==================================================
📁 II) DATA (GIỮ NGUYÊN LOGIC)
==================================================

- Chỉ đọc dataset_train (KHÔNG sửa)
- Copy sang data/images
- Rename: img001.jpg → ...
- Tạo:
  - image_map.csv
  - labels_multi.csv
  - labels_multi_split.csv (80/10/10, stratified theo tổ hợp label)

==================================================
🧪 III) PREPROCESSING (DÙNG CHUNG)
==================================================

Train transforms:
- RandomResizedCrop(INPUT_SIZE)
- HorizontalFlip
- ColorJitter
- RandomRotation(15)
- RandomGrayscale
- RandomAutocontrast
- RandomAdjustSharpness
- GaussianBlur (optional)
- Normalize ImageNet

Val/Test:
- Resize → CenterCrop(INPUT_SIZE)
- Normalize

==================================================
📦 IV) DATASET + DATALOADER
==================================================

- MultiTaskDataset
- Output:
    image, loai, dang, trang_thai
- batch_size = BATCH_SIZE
- shuffle train only

==================================================
🧠 V) MODEL (CHỈ EfficientNet-B4)
==================================================

- Load pretrained EfficientNet-B4 (timm hoặc torchvision)
- Replace classifier bằng 3 head:

shared backbone →
    ├── fc_loai (5)
    ├── fc_dang (3)
    └── fc_trang_thai (2)

==================================================
⚙️ VI) TRAINING
==================================================

Optimizer:
- AdamW(lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY)

Scheduler:
- CosineAnnealingLR

Training strategy:
1. Freeze backbone trong FREEZE_BACKBONE_EPOCHS
2. Sau đó unfreeze toàn bộ

Loss:
- CrossEntropyLoss
- Nếu USE_WEIGHTED_LOSS → dùng class weights

Total loss:
loss = 
    LOSS_WEIGHTS["loai"] * loss_loai +
    LOSS_WEIGHTS["dang"] * loss_dang +
    LOSS_WEIGHTS["trang_thai"] * loss_trang_thai

Early stopping:
- Stop nếu F1 không cải thiện trong EARLY_STOPPING_PATIENCE

==================================================
📊 VII) METRICS
==================================================

- Accuracy từng head
- F1 macro + weighted
- Balanced accuracy
- Per-class F1
- Confusion matrix từng head

Score tổng:
score = 
    0.40 * macro_f1_loai +
    0.35 * macro_f1_dang +
    0.25 * macro_f1_trang_thai

==================================================
💾 VIII) OUTPUT
==================================================

outputs/efficientnet_b4/
  checkpoints/
    best.pt
  metrics/
  confusion_matrices/
  plots/
  reports/

==================================================
🖥 IX) CLI (CHỈ 1 MODEL)
==================================================

python train.py \
  --model efficientnet_b4 \
  --dataset-root data/images \
  --labels-csv data/labels_multi.csv \
  --split-csv data/splits/labels_multi_split.csv

==================================================
❗ X) RÀNG BUỘC
==================================================

- KHÔNG train nhiều model cùng lúc
- KHÔNG thay đổi dataset_train
- Pipeline reusable
- Output tách riêng

==================================================
🎯 XI) OUTPUT FORMAT
==================================================

1. Việc đã làm
2. Cấu trúc project
3. File đã tạo
4. Lệnh chạy
5. Metrics + score
6. Vấn đề
7. Next step