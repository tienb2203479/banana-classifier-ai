from __future__ import annotations

import json
import os
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

import mysql.connector
from mysql.connector.pooling import MySQLConnectionPool

from app.core.banana_info import BANANA_TYPE_INFO
from src.banana_multitask.utils import normalize_text

PROJECT_ROOT = Path(__file__).resolve().parents[4]


def _load_env_files() -> None:
    try:
        from dotenv import load_dotenv
    except Exception:
        return

    for env_path in [
        PROJECT_ROOT / "web" / "backend" / ".env",
        PROJECT_ROOT / "web" / ".env",
        PROJECT_ROOT / ".env",
    ]:
        if env_path.exists():
            load_dotenv(env_path, override=False)


_load_env_files()


def _normalize_label(value: str) -> str:
    return normalize_text(value)


class DatabaseManager:
    def __init__(self) -> None:
        self.host = os.getenv("MYSQL_HOST", "localhost")
        self.port = int(os.getenv("MYSQL_PORT", "3306"))
        self.user = os.getenv("MYSQL_USER", "root")
        self.password = os.getenv("MYSQL_PASSWORD", "")
        self.database = os.getenv("MYSQL_DATABASE", "banana_ai")
        self.pool_name = os.getenv("MYSQL_POOL_NAME", "banana_pool")
        self.pool_size = int(os.getenv("MYSQL_POOL_SIZE", "5"))
        self._pool: MySQLConnectionPool | None = None
        self._ready = False

    @property
    def enabled(self) -> bool:
        return self._pool is not None

    def initialize(self) -> None:
        if self._pool is not None:
            return

        try:
            self._ensure_database_exists()
            self._pool = MySQLConnectionPool(
                pool_name=self.pool_name,
                pool_size=self.pool_size,
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                autocommit=False,
            )
            self._create_schema_and_seed()
            self._ready = True
        except Exception:
            self._pool = None
            self._ready = False

    def _ensure_database_exists(self) -> None:
        conn = mysql.connector.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
        )
        try:
            cur = conn.cursor()
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{self.database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            conn.commit()
        finally:
            conn.close()

    def _create_schema_and_seed(self) -> None:
        schema_path = PROJECT_ROOT / "web" / "backend" / "db_init.sql"
        statements = [stmt.strip() for stmt in schema_path.read_text(encoding="utf-8").split(";") if stmt.strip()]
        with self.connection() as conn:
            cur = conn.cursor()
            for statement in statements:
                if statement.upper().startswith("CREATE DATABASE") or statement.upper().startswith("USE "):
                    continue
                cur.execute(statement)
            conn.commit()

        self._seed_reference_data()

    def _seed_reference_data(self) -> None:
        banana_rows = [
            (
                "Chuối cau",
                "Lady Finger",
                "Quả thon, vỏ vàng đẹp khi chín, mùi thơm nhẹ.",
                "Việt Nam và khu vực Đông Nam Á.",
                "Ngọt cao, thơm nhẹ.",
                "Ăn tươi, sinh tố, tráng miệng.",
                "Phù hợp ăn tươi hoặc làm món tráng miệng.",
                "Ăn khi chín vàng.",
            ),
            (
                "Chuối già",
                "Cavendish nội địa",
                "Kích thước vừa đến lớn, vỏ dày hơn, dễ vận chuyển.",
                "Phổ biến trong canh tác thương mại.",
                "Ngọt vừa, đều vị.",
                "Ăn tươi, làm bánh, ép.",
                "Phù hợp ăn tươi, làm bánh, xay sinh tố.",
                "Để nơi khô thoáng, tránh để gần trái cây sinh ethylene cao.",
            ),
            (
                "Chuối sáp",
                "Chuối sáp dẻo",
                "Thịt dẻo, đậm, thường dùng hấp/luộc.",
                "Phổ biến ở miền Tây và nhiều tỉnh thành.",
                "Ngọt đậm, béo nhẹ.",
                "Hấp, nướng, ăn kèm dừa.",
                "Thích hợp hấp, nướng, chế biến đồ ăn.",
                "Để nơi khô, tránh ẩm cao.",
            ),
            (
                "Chuối táo quạ",
                "Chuối táo quạ",
                "Mùi thơm đặc trưng, thịt quả chắc.",
                "Một số vùng trồng chiến lược.",
                "Ngọt vừa đến cao.",
                "Ăn tươi, salad trái cây, sinh tố.",
                "Phù hợp ăn tươi, làm món tráng miệng.",
                "Không nên để quá lâu khi đã chín.",
            ),
            (
                "Chuối xiêm",
                "Chuối xiêm/chuối sứ",
                "Quả nhỏ hơn, hương vị đậm, phổ biến để ăn tươi.",
                "Rộng rãi tại Việt Nam.",
                "Ngọt vừa.",
                "Ăn tươi, chiên, nấu chè.",
                "Phù hợp ăn tươi hoặc chế biến.",
                "Bảo quản nơi thoáng, tránh ánh nắng trực tiếp.",
            ),
        ]
        nutrition_rows = {
            "Chuối cau": (89.0, 22.8, 12.2, 2.6, 1.1, 0.3, 8.7, 358.0),
            "Chuối già": (90.0, 23.0, 12.2, 2.6, 1.1, 0.3, 8.7, 358.0),
            "Chuối sáp": (105.0, 27.0, 14.0, 2.7, 1.3, 0.4, 8.0, 360.0),
            "Chuối táo quạ": (92.0, 23.5, 12.5, 2.5, 1.1, 0.3, 9.0, 355.0),
            "Chuối xiêm": (88.0, 22.5, 11.8, 2.4, 1.0, 0.2, 8.5, 350.0),
        }

        with self.connection() as conn:
            cur = conn.cursor()
            for row in banana_rows:
                cur.execute(
                    """
                    INSERT INTO banana_type
                        (b_name, b_scientific_name, description, origin, taste, recommended_usage, best_for, storage_tip)
                    VALUES
                        (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        b_scientific_name = VALUES(b_scientific_name),
                        description = VALUES(description),
                        origin = VALUES(origin),
                        taste = VALUES(taste),
                        recommended_usage = VALUES(recommended_usage),
                        best_for = VALUES(best_for),
                        storage_tip = VALUES(storage_tip)
                    """,
                    row,
                )

            cur.execute("SELECT b_id, b_name FROM banana_type")
            banana_ids = {str(name): int(b_id) for b_id, name in cur.fetchall()}
            for b_name, nutrition in nutrition_rows.items():
                cur.execute(
                    """
                    INSERT INTO nutrition
                        (b_id, calories_per_100g, carbs_g, sugar_g, fiber_g, protein_g, fat_g, vitamin_c_mg, potassium_mg)
                    VALUES
                        (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        calories_per_100g = VALUES(calories_per_100g),
                        carbs_g = VALUES(carbs_g),
                        sugar_g = VALUES(sugar_g),
                        fiber_g = VALUES(fiber_g),
                        protein_g = VALUES(protein_g),
                        fat_g = VALUES(fat_g),
                        vitamin_c_mg = VALUES(vitamin_c_mg),
                        potassium_mg = VALUES(potassium_mg)
                    """,
                    (banana_ids[b_name], *nutrition),
                )
            conn.commit()

    @contextmanager
    def connection(self) -> Iterator[mysql.connector.connection.MySQLConnection]:
        if self._pool is None:
            raise RuntimeError("MySQL is not configured")
        conn = self._pool.get_connection()
        try:
            yield conn
        finally:
            conn.close()

    def get_banana_type_id(self, name: str) -> int | None:
        if not self.enabled:
            return None
        with self.connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT b_id FROM banana_type WHERE LOWER(b_name) = %s LIMIT 1", (_normalize_label(name),))
            row = cur.fetchone()
            return int(row[0]) if row else None

    def save_prediction(self, session_id: str, image_path: Path, result: dict[str, Any]) -> None:
        if not self.enabled:
            return

        predictions = result["predictions"]
        loai_label = str(predictions["loai"]["label"])
        dang_label = str(predictions["dang"]["label"])
        trang_thai_label = str(predictions["trang_thai"]["label"])
        can_review = bool(result.get("can_review", False))
        image_quality = json.dumps(result.get("image_quality", {}), ensure_ascii=False)
        warnings = json.dumps(result.get("warnings", []), ensure_ascii=False)

        with self.connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO image (img_path, img_upload_time, session_id)
                VALUES (%s, %s, %s)
                """,
                (str(image_path), datetime.utcnow(), session_id),
            )
            img_id = cur.lastrowid

            b_id = self.get_banana_type_id(loai_label)
            cur.execute(
                """
                INSERT INTO prediction (
                    img_id, b_id, structure_type, ripeness_level,
                    type_confidence, structure_confidence, ripeness_confidence,
                    can_review, image_quality_json, warnings_json
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    img_id,
                    b_id,
                    dang_label,
                    trang_thai_label,
                    float(predictions["loai"]["confidence"]),
                    float(predictions["dang"]["confidence"]),
                    float(predictions["trang_thai"]["confidence"]),
                    int(can_review),
                    image_quality,
                    warnings,
                ),
            )
            conn.commit()

    def fetch_history(self, session_id: str, limit: int = 40) -> list[dict[str, Any]]:
        if not self.enabled:
            return []

        with self.connection() as conn:
            cur = conn.cursor(dictionary=True)
            cur.execute(
                """
                SELECT
                    i.img_id,
                    i.img_path,
                    i.img_upload_time,
                    p.p_id,
                    p.structure_type,
                    p.ripeness_level,
                    p.type_confidence,
                    p.structure_confidence,
                    p.ripeness_confidence,
                    p.can_review,
                    p.image_quality_json,
                    p.warnings_json,
                    b.b_name,
                    b.b_scientific_name,
                    b.description,
                    b.origin,
                    b.taste,
                    b.recommended_usage,
                    b.best_for,
                    b.storage_tip,
                    n.calories_per_100g,
                    n.carbs_g,
                    n.sugar_g,
                    n.fiber_g,
                    n.protein_g,
                    n.fat_g,
                    n.vitamin_c_mg,
                    n.potassium_mg
                FROM image i
                INNER JOIN prediction p ON p.img_id = i.img_id
                LEFT JOIN banana_type b ON b.b_id = p.b_id
                LEFT JOIN nutrition n ON n.b_id = b.b_id
                WHERE i.session_id = %s
                ORDER BY p.p_id DESC
                LIMIT %s
                """,
                (session_id, limit),
            )
            rows = cur.fetchall()

        history: list[dict[str, Any]] = []
        for row in rows:
            loai_label = row["b_name"] or "Đang cập nhật"
            banana_info = {
                "ten_goi_khac": row["b_scientific_name"] or "Đang cập nhật",
                "dac_diem": row["description"] or "Chưa có mô tả chi tiết cho loại này.",
                "dinh_duong": f"Calo: {row['calories_per_100g']:.0f} kcal / 100g" if row["calories_per_100g"] is not None else "Đang cập nhật",
                "dinh_duong_highlights": [
                    f"Giàu kali - {row['potassium_mg']:.0f} mg/100g" if row["potassium_mg"] is not None else "Giàu kali",
                    f"Carbs: {row['carbs_g']:.1f} g/100g" if row["carbs_g"] is not None else "Cung cấp năng lượng nhanh",
                    f"Chất xơ: {row['fiber_g']:.1f} g/100g" if row["fiber_g"] is not None else "Tốt cho tiêu hóa",
                ],
                "do_ngot": row["taste"] or "Đang cập nhật",
                "goi_y_su_dung": row["recommended_usage"] or "Đang cập nhật",
                "bao_quan": row["storage_tip"] or "Đang cập nhật",
                "calo_uoc_luong": f"{row['calories_per_100g']:.0f} kcal / 100g" if row["calories_per_100g"] is not None else "89 kcal / 100g",
            }
            image_url = ""
            try:
                image_path = Path(str(row["img_path"]))
                image_url = f"/uploads/{image_path.parent.name}/{image_path.name}"
            except Exception:
                image_url = ""

            history.append(
                {
                    "id": str(row["p_id"]),
                    "created_at": row["img_upload_time"].isoformat() + "Z" if row["img_upload_time"] else datetime.utcnow().isoformat() + "Z",
                    "image_url": image_url,
                    "predictions": {
                        "loai": {"label": loai_label, "confidence": float(row["type_confidence"] or 0.0)},
                        "dang": {"label": row["structure_type"] or "", "confidence": float(row["structure_confidence"] or 0.0)},
                        "trang_thai": {"label": row["ripeness_level"] or "", "confidence": float(row["ripeness_confidence"] or 0.0)},
                    },
                    "can_review": bool(row["can_review"]),
                    "image_quality": json.loads(row["image_quality_json"] or "{}"),
                    "warnings": json.loads(row["warnings_json"] or "[]"),
                    "banana_info": banana_info,
                    "reference_image_url": None,
                }
            )
        return history

    def clear_history(self, session_id: str) -> None:
        if not self.enabled:
            return

        with self.connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                DELETE p
                FROM prediction p
                INNER JOIN image i ON i.img_id = p.img_id
                WHERE i.session_id = %s
                """,
                (session_id,),
            )
            cur.execute("DELETE FROM image WHERE session_id = %s", (session_id,))
            conn.commit()
