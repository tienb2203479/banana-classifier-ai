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

NUM_WORKERS = min(4, CPU_COUNT)
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

Train transforms (Data Augmentation - 8 kỹ thuật):
- RandomResizedCrop(INPUT_SIZE, scale=(0.75, 1.0)) - thu phóng ngẫu nhiên
- RandomHorizontalFlip - lật ngang
- RandomRotation(20°) - xoay ±20 độ
- RandomPerspective (distortion_scale=0.22) - biến dạng phối cảnh
- RandomAffine (15°, translate 10%) - affine transform
- ColorJitter (brightness 0.35, contrast 0.35, saturation 0.3, hue 0.08) - thay đổi màu sắc
- GaussianBlur (kernel 3x3) - làm mờ Gaussian
- RandomGrayscale (p=0.08) - chuyển xám
- RandomErasing (p=0.25, scale 0.02-0.12) - xóa ngẫu nhiên
- Normalize ImageNet (mean/std)

Val/Test:
- Resize → CenterCrop(INPUT_SIZE)
- Normalize ImageNet

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
⚙️ VI) TRAINING STRATEGY
==================================================

Optimizer:
- AdamW(lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY)

Scheduler:
- CosineAnnealingLR (điều chỉnh theo weighted_f1)

Training Flow:
1. Freeze backbone trong FREEZE_BACKBONE_EPOCHS
2. Sau đó unfreeze toàn bộ model

Loss Function:
- CrossEntropyLoss cho mỗi head
- Nếu USE_WEIGHTED_LOSS → áp dụng class weights để cân bằng lớp

Total loss mỗi batch:
loss = 
    LOSS_WEIGHTS["loai"] * loss_loai +
    LOSS_WEIGHTS["dang"] * loss_dang +
    LOSS_WEIGHTS["trang_thai"] * loss_trang_thai

Early Stopping Strategy:
- Sau mỗi epoch validation, tính weighted_f1_combined
- Nếu weighted_f1_combined không cải thiện trong EARLY_STOPPING_PATIENCE epoch → dừng
- Lưu best checkpoint dựa trên weighted_f1_combined
- Theo dõi macro_f1 của từng head để log metrics

==================================================
📊 VII) METRICS & EARLY STOPPING
==================================================

Metrics được tính toán từ Confusion Matrix:
- Accuracy: Tỷ lệ dự đoán đúng tổng thể
- Precision: Độ chính xác của dự đoán lớp dương
- Recall: Khả năng phát hiện đầy đủ các mẫu lớp
- Per-class F1: Trung bình điều hòa Precision & Recall từng lớp

F1-Score Variants (được áp dụng cho mỗi head):
- F1-Macro: Trung bình cộng F1 tất cả lớp (cân bằng cho lớp ít mẫu)
  F1_macro = (1/N) × Σ F1_i
- F1-Weighted: Trung bình có trọng số dựa trên số mẫu thực tế (phản ánh phân phối dữ liệu)
  F1_weighted = Σ (F1_i × support_i) / total_samples
- Balanced Accuracy: Trung bình Recall tất cả lớp

⭐ METRIC CHÍNH CHO EARLY STOPPING:
- Tính weighted F1 từng head: loai, dang, trang_thai
- Tính trung bình: weighted_f1_combined = (wf1_loai + wf1_dang + wf1_trang_thai) / 3
- Early stopping dựa trên weighted_f1_combined (mục tiêu chính)
- Theo dõi thêm macro_f1 để đảm bảo mô hình học tốt các lớp ít mẫu

Score tổng (cho thông tin):
score = 
    0.40 * macro_f1_loai +
    0.35 * macro_f1_dang +
    0.25 * macro_f1_trang_thai

Confusion matrix + per-class metrics được lưu cho mỗi head

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