from __future__ import annotations

BANANA_TYPE_INFO: dict[str, dict[str, str]] = {
    "Chuối cau": {
        "ten_goi_khac": "Lady Finger",
        "dac_diem": "Quả thon, vỏ mỏng và vàng sáng khi chín, mùi thơm nhẹ dễ nhận biết.",
        "dinh_duong": "Giàu kali, vitamin B6 và chất xơ; hỗ trợ tim mạch, tiêu hóa và cung cấp năng lượng nhanh.",
        "calo_uoc_luong": "89 kcal / 100g",
        "dinh_duong_highlights": [
            "Giàu kali - hỗ trợ tim mạch",
            "Cung cấp năng lượng nhanh",
            "Chất xơ hỗ trợ tiêu hóa",
        ],
        "do_ngot": "Ngọt cao, thơm dịu",
        "goi_y_su_dung": "Ăn tươi, làm sinh tố, tráng miệng hoặc kết hợp salad trái cây.",
        "bao_quan": "Để nơi khô thoáng khi còn xanh; khi chín có thể giữ mát ngắn ngày để ổn định độ ngọt.",
    },
    "Chuối già": {
        "ten_goi_khac": "Cavendish nhóm nội địa",
        "dac_diem": "Kích thước vừa đến lớn, vỏ dày hơn nên chịu va chạm tốt, phù hợp vận chuyển.",
        "dinh_duong": "Cân bằng carbohydrate, kali và magiê; phù hợp bổ sung năng lượng hằng ngày.",
        "calo_uoc_luong": "90 kcal / 100g",
        "dinh_duong_highlights": [
            "Bổ sung kali cho cơ bắp",
            "Nguồn năng lượng bền vững",
            "Chất xơ giúp no lâu",
        ],
        "do_ngot": "Ngọt vừa, vị cân bằng",
        "goi_y_su_dung": "Ăn tươi, ép nước, làm bánh chuối hoặc topping ngũ cốc.",
        "bao_quan": "Tránh đặt gần trái cây phát thải ethylene cao nếu muốn làm chậm tốc độ chín.",
    },
    "Chuối sáp": {
        "ten_goi_khac": "Chuối sáp dẻo",
        "dac_diem": "Thịt dẻo, đặc và chắc; cấu trúc phù hợp chế biến nhiệt như hấp, luộc, nướng.",
        "dinh_duong": "Năng lượng cao hơn nhờ hàm lượng tinh bột và chất xơ khá dồi dào.",
        "calo_uoc_luong": "105 kcal / 100g",
        "dinh_duong_highlights": [
            "Giàu tinh bột tạo năng lượng",
            "Hàm lượng chất xơ khá",
            "Phù hợp bữa phụ trước vận động",
        ],
        "do_ngot": "Ngọt đậm, hậu vị béo nhẹ",
        "goi_y_su_dung": "Hấp, nướng, dùng kèm dừa nạo hoặc chế biến món tráng miệng.",
        "bao_quan": "Nên để khô ráo, tránh độ ẩm cao để hạn chế thâm vỏ và mềm nhanh.",
    },
    "Chuối táo quạ": {
        "ten_goi_khac": "Chuối táo quạ",
        "dac_diem": "Mùi thơm đặc trưng, thịt quả chắc, độ đồng đều tốt ở nhiều điều kiện trồng.",
        "dinh_duong": "Bổ sung kali và nhóm chất chống oxy hóa tự nhiên, hỗ trợ cân bằng điện giải.",
        "calo_uoc_luong": "92 kcal / 100g",
        "dinh_duong_highlights": [
            "Kali hỗ trợ cân bằng điện giải",
            "Có chất chống oxy hóa tự nhiên",
            "Phù hợp bổ sung năng lượng nhanh",
        ],
        "do_ngot": "Ngọt vừa đến cao, thơm rõ",
        "goi_y_su_dung": "Ăn tươi, làm salad trái cây hoặc xay sinh tố.",
        "bao_quan": "Không nên để tủ lạnh khi còn xanh để tránh xỉn màu và giảm hương vị.",
    },
    "Chuối xiêm": {
        "ten_goi_khac": "Chuối xiêm / chuối sứ",
        "dac_diem": "Kích thước nhỏ hơn, hương vị đậm, thịt chắc; phổ biến trong tiêu dùng hằng ngày.",
        "dinh_duong": "Giá trị năng lượng vừa phải, bổ sung kali và vitamin C, hỗ trợ chuyển hóa.",
        "calo_uoc_luong": "88 kcal / 100g",
        "dinh_duong_highlights": [
            "Giá trị năng lượng vừa phải",
            "Bổ sung kali và vitamin C",
            "Hỗ trợ tiêu hóa nhờ chất xơ",
        ],
        "do_ngot": "Ngọt vừa, vị đậm",
        "goi_y_su_dung": "Ăn tươi, chiên, nấu chè hoặc làm món ăn nhẹ.",
        "bao_quan": "Bảo quản nơi thoáng mát, tránh ánh nắng trực tiếp và tránh xếp chồng nặng.",
    },
}

DEFAULT_BANANA_INFO: dict[str, str] = {
    "ten_goi_khac": "Đang cập nhật",
    "dac_diem": "Chưa có mô tả chi tiết cho loại này.",
    "dinh_duong": "Đang cập nhật",
    "calo_uoc_luong": "89 kcal / 100g",
    "dinh_duong_highlights": [
        "Giàu kali",
        "Cung cấp năng lượng nhanh",
        "Tốt cho tiêu hóa",
    ],
    "do_ngot": "Đang cập nhật",
    "goi_y_su_dung": "Đang cập nhật",
    "bao_quan": "Đang cập nhật",
}
