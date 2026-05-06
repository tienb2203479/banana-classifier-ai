# Banana Classifier (v3)

Một repository cho dự án phân loại chuối đa nhiệm (multitask) — mã nguồn, cấu hình và scripts để huấn luyện, đánh giá và triển khai mô hình. Thư mục này là phiên bản "v3"; các dữ liệu lớn, mô hình đã train và outputs thực tế bị loại trừ khỏi repo (xem phần `Excluded` bên dưới).

## Nội dung chính
- `train_b4_v3.py`, `evaluate_b4_v3.py`, `ensemble_inference.py` — scripts chính để huấn luyện, đánh giá và inference.
- `configs/` — cấu hình huấn luyện (`train_config.yaml`).
- `src/banana_multitask/` — mã nguồn model, dataset, loss, metrics và helper.
- `data/`, `dataset_demo/`, `dataset_train/` — (bị loại trừ khỏi repo) chứa ảnh và label; xem phần `Dataset` để biết cách thêm.
- `models/`, `outputs/`, `logs/` — (bị loại trừ) nơi lưu checkpoints, báo cáo và logs.
- `web/` — mã cho web frontend/backend (tùy chọn deploy).

## Yêu cầu
- Python 3.8+ (khuyến nghị 3.9/3.10)
- Tạo virtualenv và cài dependencies:

```bash
python -m venv .venv
\.venv\Scripts\activate    # Windows
pip install -r requirements-web.txt
pip install -r requirements.txt  # nếu có (project phụ thuộc khác)
```

## Cách dùng nhanh

- Chuẩn bị dữ liệu theo cấu trúc trong `dataset_train/` (ví dụ đã có cấu trúc phân loại theo thư mục). File label và split mẫu có trong `data/splits`.
- Huấn luyện (ví dụ dùng EfficientNet-B4 config):

```bash
python train_b4_v3.py --config configs/train_config.yaml
```

- Đánh giá:

```bash
python evaluate_b4_v3.py --checkpoint outputs/efficientnet_b4_v3/last.pt
```

- Ensemble / Inference:

```bash
python ensemble_inference.py --models models/...
```

## Dataset & Files excluded from repo
Để giữ repo gọn nhẹ, các thư mục lớn sau được thêm vào `.gitignore` và **không** đẩy lên GitHub:

- `data/`
- `dataset_demo/`
- `dataset_train/`
- `models/`
- `outputs/`

Nếu bạn muốn chia sẻ dữ liệu hoặc model checkpoint, nén và upload riêng (ví dụ lên Google Drive hoặc Git LFS) rồi cập nhật đường dẫn trong cấu hình.

## Cấu trúc mẫu (tóm tắt)

- `configs/` — file cấu hình YAML cho huấn luyện
- `src/banana_multitask/`
  - `data.py` — loader và augmentation
  - `model.py` — kiến trúc mô hình
  - `training.py` — vòng huấn luyện
  - `metrics.py`, `losses.py` — hàm đánh giá và loss

## Gợi ý phát triển
- Kiểm tra `configs/train_config.yaml` để điều chỉnh learning rate, batch size, augmentation.
- Sử dụng GPU và virtualenv để chạy huấn luyện nhanh hơn.

## Liên hệ
Nếu cần thêm README chi tiết (hướng dẫn cài đặt môi trường, chạy demo web, hoặc template config), cho tôi biết phần bạn muốn mở rộng.

---
Generated for v3 workspace on local machine.
