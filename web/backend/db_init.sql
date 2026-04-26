CREATE DATABASE IF NOT EXISTS banana_ai CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE banana_ai;

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS prediction;
DROP TABLE IF EXISTS image;
DROP TABLE IF EXISTS nutrition;
DROP TABLE IF EXISTS banana_type;
SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE IF NOT EXISTS banana_type (
    b_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    b_name VARCHAR(100) NOT NULL UNIQUE,
    b_scientific_name VARCHAR(180) NULL,
    description TEXT NULL,
    origin VARCHAR(180) NULL,
    taste VARCHAR(120) NULL,
    recommended_usage TEXT NULL,
    best_for TEXT NULL,
    storage_tip TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS nutrition (
    n_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    b_id BIGINT NOT NULL UNIQUE,
    calories_per_100g DECIMAL(6,2) NULL,
    carbs_g DECIMAL(6,2) NULL,
    sugar_g DECIMAL(6,2) NULL,
    fiber_g DECIMAL(6,2) NULL,
    protein_g DECIMAL(6,2) NULL,
    fat_g DECIMAL(6,2) NULL,
    vitamin_c_mg DECIMAL(6,2) NULL,
    potassium_mg DECIMAL(7,2) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_nutrition_banana_type FOREIGN KEY (b_id) REFERENCES banana_type (b_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS image (
    img_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    img_path VARCHAR(500) NOT NULL,
    img_upload_time DATETIME NOT NULL,
    session_id VARCHAR(64) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_image_session_id (session_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS prediction (
    p_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    img_id BIGINT NOT NULL UNIQUE,
    b_id BIGINT NULL,
    structure_type VARCHAR(100) NOT NULL,
    ripeness_level VARCHAR(100) NOT NULL,
    type_confidence DECIMAL(6,5) NOT NULL,
    structure_confidence DECIMAL(6,5) NOT NULL,
    ripeness_confidence DECIMAL(6,5) NOT NULL,
    can_review TINYINT(1) NOT NULL DEFAULT 0,
    image_quality_json JSON NULL,
    warnings_json JSON NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_prediction_image FOREIGN KEY (img_id) REFERENCES image (img_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_prediction_banana_type FOREIGN KEY (b_id) REFERENCES banana_type (b_id)
        ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO banana_type
    (b_name, b_scientific_name, description, origin, taste, recommended_usage, best_for, storage_tip)
VALUES
    ('Chuối cau', 'Lady Finger', 'Quả thon, vỏ vàng đẹp khi chín, mùi thơm nhẹ.', 'Việt Nam và khu vực Đông Nam Á.', 'Ngọt cao, thơm nhẹ.', 'Ăn tươi, sinh tố, tráng miệng.', 'Phù hợp ăn tươi hoặc làm món tráng miệng.', 'Ăn khi chín vàng.'),
    ('Chuối già', 'Cavendish nội địa', 'Kích thước vừa đến lớn, vỏ dày hơn, dễ vận chuyển.', 'Phổ biến trong canh tác thương mại.', 'Ngọt vừa, đều vị.', 'Ăn tươi, làm bánh, ép.', 'Phù hợp ăn tươi, làm bánh, xay sinh tố.', 'Để nơi khô thoáng, tránh để gần trái cây sinh ethylene cao.'),
    ('Chuối sáp', 'Chuối sáp dẻo', 'Thịt dẻo, đậm, thường dùng hấp/luộc.', 'Phổ biến ở miền Tây và nhiều tỉnh thành.', 'Ngọt đậm, béo nhẹ.', 'Hấp, nướng, ăn kèm dừa.', 'Thích hợp hấp, nướng, chế biến đồ ăn.', 'Để nơi khô, tránh ẩm cao.'),
    ('Chuối táo quạ', 'Chuối táo quạ', 'Mùi thơm đặc trưng, thịt quả chắc.', 'Một số vùng trồng chiến lược.', 'Ngọt vừa đến cao.', 'Ăn tươi, salad trái cây, sinh tố.', 'Phù hợp ăn tươi, làm món tráng miệng.', 'Không nên để quá lâu khi đã chín.'),
    ('Chuối xiêm', 'Chuối xiêm/chuối sứ', 'Quả nhỏ hơn, hương vị đậm, phổ biến để ăn tươi.', 'Rộng rãi tại Việt Nam.', 'Ngọt vừa.', 'Ăn tươi, chiên, nấu chè.', 'Phù hợp ăn tươi hoặc chế biến.', 'Bảo quản nơi thoáng, tránh ánh nắng trực tiếp.');

INSERT INTO nutrition
    (b_id, calories_per_100g, carbs_g, sugar_g, fiber_g, protein_g, fat_g, vitamin_c_mg, potassium_mg)
SELECT b_id, 89.00, 22.80, 12.20, 2.60, 1.10, 0.30, 8.70, 358.00 FROM banana_type WHERE b_name = 'Chuối cau'
UNION ALL SELECT b_id, 90.00, 23.00, 12.20, 2.60, 1.10, 0.30, 8.70, 358.00 FROM banana_type WHERE b_name = 'Chuối già'
UNION ALL SELECT b_id, 105.00, 27.00, 14.00, 2.70, 1.30, 0.40, 8.00, 360.00 FROM banana_type WHERE b_name = 'Chuối sáp'
UNION ALL SELECT b_id, 92.00, 23.50, 12.50, 2.50, 1.10, 0.30, 9.00, 355.00 FROM banana_type WHERE b_name = 'Chuối táo quạ'
UNION ALL SELECT b_id, 88.00, 22.50, 11.80, 2.40, 1.00, 0.20, 8.50, 350.00 FROM banana_type WHERE b_name = 'Chuối xiêm';
