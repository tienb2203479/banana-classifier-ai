# Banana AI Web Deployment

Web app du doan chuoi voi giao dien hien dai, ho tro:
- Upload anh hoac chup anh bang camera
- Predict theo model tot nhat efficientnet_b4_v3
- Hien thong tin chuoi sau du doan
- Luu lich su + thong tin du doan vao MySQL
- Luu file anh upload vao web/backend/storage/uploads

## 1) Cai dat nhanh

```bash
cd d:\NLN\dataset\v3
pip install -r requirements-web.txt
copy web\backend\.env.example web\backend\.env
```

Cap nhat thong tin MySQL trong web/backend/.env.

## 2) Tao database

```sql
CREATE DATABASE IF NOT EXISTS banana_ai CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Import CSDL mau:

```bash
mysql -u root -p banana_ai < web/backend/db_init.sql
```

Hoac de app tu import khi startup (neu da cau hinh .env dung).

## 3) Chay local

```bash
cd d:\NLN\dataset\v3
uvicorn app.main:app --app-dir web/backend --host 0.0.0.0 --port 8001 --reload
```

Mo:
- Trang du doan: http://localhost:8001
- Trang lich su: http://localhost:8001/history
- Health check: http://localhost:8001/health

## 4) API chinh

- POST /api/predict
  - Input: file image
  - Output: nhan (loai, dang, trang_thai), confidence, banana_info, image_url
- GET /api/history?limit=40
  - Output: lich su du doan moi nhat

## 5) Ghi chu

- Neu confidence < 70% o bat ky head nao, UI se canh bao low confidence.
- CSDL co bang banana_info seed san thong tin chuoi co ban theo loai.
- Anh upload duoc luu theo timestamp + uuid de tranh trung ten.

## 6) CSDL

- File schema: `web/backend/db_init.sql`
- File cau hinh mau: `web/backend/.env.example`
- Cac bang chinh: `banana_type`, `nutrition`, `image`, `prediction`

## 7) Deploy len Render

Repo da co file `render.yaml` o thu muc goc de Render doc Blueprint va tu tao Web Service.

### Cach 1: Blueprint (khuyen nghi)

1. Push code len GitHub (bao gom `render.yaml`).
2. Vao Render -> New -> Blueprint.
3. Chon repo va nhanh can deploy.
4. Render se doc `render.yaml` va tao service `banana-ai-web`.

### Cach 2: Tao service thu cong

- Runtime: Python
- Build Command:

```bash
pip install --upgrade pip
pip install -r requirements-web.txt
```

- Start Command:

```bash
python -m uvicorn app.main:app --app-dir web/backend --host 0.0.0.0 --port $PORT
```

### Bien moi truong can set tren Render

- `BANANA_CHECKPOINT=outputs/efficientnet_b4_v3/best.pt`
- `MAX_UPLOAD_MB=8`
- `MYSQL_HOST`
- `MYSQL_PORT=3306`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_DATABASE=banana_ai`

Neu chua co MySQL cloud, app van chay voi session memory (khong luu lich su vao DB).
