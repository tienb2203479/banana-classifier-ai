Bạn là một ML engineer senior.

Hãy viết code PyTorch để huấn luyện một mô hình phân loại ảnh (multi-class) với dataset nhỏ (~500 ảnh), mục tiêu là benchmark nhanh nhiều backbone khác nhau.

Yêu cầu hệ thống:

## 1. INPUT PARAMETER HÓA
- Model backbone có thể chọn 1 trong:
  - densenet121
  - resnet50
  - efficientnet_b3
  - efficientnet_b4
  - mobilenetv3
- Input image size:
  - mobilenetv3 / resnet50 / densenet121: 224x224
  - efficientnet_b3: 300x300
  - efficientnet_b4: 300x300 (không dùng 224)

## 2. DATASET
- Dataset nhỏ (~500 images)
- Dùng ImageFolder format
- Split:
  - train: 70%
  - val: 15%
  - test: 15%
- Ensure no data leakage
- Stratified split theo class

## 3. AUGMENTATION (BẮT BUỘC)
Train transforms:
- RandomHorizontalFlip
- RandomRotation(±15 degrees)
- ColorJitter (brightness, contrast, saturation)
- RandomResizedCrop

Val/Test:
- Resize + CenterCrop

## 4. MODEL
- Use pretrained ImageNet weights
- Replace classifier head phù hợp số class
- Freeze backbone 10 epochs đầu
- Unfreeze last block sau đó

## 5. TRAINING STRATEGY
- Optimizer: AdamW
- LR: 1e-3 (head), 1e-4 (fine-tune)
- Scheduler: ReduceLROnPlateau
- Loss: CrossEntropyLoss
- Epochs:
  - max 35 epochs
  - Early stopping patience = 6

## 6. METRICS
- Accuracy
- F1-score (macro)
- Confusion matrix
- Save best model theo F1-score

## 7. PERFORMANCE LOGGING
- Print per epoch:
  - train loss
  - val loss
  - val accuracy
  - val F1

- Save training log into CSV file

## 8. OUTPUT STRUCTURE
Code phải có dạng:

train_model(model_name="resnet50", data_path="...", epochs=...)

=> chỉ cần đổi model_name để train model khác

## 9. GPU SUPPORT
- Use CUDA if available
- fallback CPU nếu không có GPU

## 10. CLEAN CODE REQUIREMENTS
- Modular functions:
  - get_model()
  - get_dataloader()
  - train_one_epoch()
  - validate()
- Clean, readable, production-level PyTorch code

Chỉ viết code, không giải thích.