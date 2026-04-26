# PROMPT 3 - TICH HOP MODEL + MO RONG DATASET TU UPLOAD

Ban la MLOps + Backend Engineer senior.
Hay tich hop model phan loai chuoi vao web hien co va trien khai co che thu thap du lieu moi tu anh nguoi dung de retrain ve sau.

Muc tieu:
- Du doan online tu anh upload/chup.
- Luu anh va metadata de mo rong dataset.
- Co quy trinh gan nhan thu cong va retrain dinh ky.

Yeu cau tich hop inference:
1. API predict nhan anh, preprocess dung chuan model.
2. Tra ket qua 3 dau ra + confidence + thoi gian suy luan.
3. Neu confidence thap hon nguong, gan co can review.
4. Luu log inference de theo doi chat luong.

Yeu cau mo rong dataset tu nguoi dung:
1. Khi user upload anh, luu vao kho du lieu raw cung metadata:
- timestamp
- device/source
- prediction ban dau
- confidence
- trang thai da gan nhan hay chua
2. Tao luong gan nhan thu cong:
- hang cho anh can nhan
- giao dien/endpoint cap nhat nhan chuan
- luu lich su ai gan, khi nao
3. Sau khi co nhan:
- chuyen anh vao kho du lieu labeled
- cap nhat manifest du lieu
- chuan bi cho retrain

Yeu cau retrain:
1. Thiet ke pipeline retrain dinh ky hoac theo nguong du lieu moi.
2. So sanh model moi va model cu bang cung bo test.
3. Chi promote model moi khi vuot tieu chi da dinh.
4. Co version model va kha nang rollback.

Yeu cau quan tri du lieu:
1. Chong anh trung lap.
2. Kiem tra chat luong anh (qua mo, qua toi).
3. Tuan thu quyen rieng tu, co co che xoa anh theo yeu cau.
4. Tach ro du lieu train va du lieu danh gia.

Dau ra mong muon:
1. Thiet ke CSDL/bang cho raw upload, manual labels, model registry.
2. API spec cho predict, enqueue review, submit label, trigger retrain.
3. Quy trinh end-to-end tu upload den model moi.
4. Checklist trien khai production.
5. Cac metric giam sat online:
- latency
- error rate
- confidence distribution
- drift theo thoi gian
- ti le anh can gan nhan

Format tra loi:
1. Kien truc de xuat
2. File/Module can tao
3. API chi tiet
4. Luong du lieu
5. Ke hoach rollout an toan
