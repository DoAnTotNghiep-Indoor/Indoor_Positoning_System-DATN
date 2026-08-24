"""Bước 9 — Chia train / validation / test.

Chia TRƯỚC khi chuẩn hoá. Đảo lại là rò rỉ dữ liệu: scaler học được cả phân bố
của tập kiểm thử, kết quả đẹp giả tạo và sụp khi chạy thật.

Ba cách chia, khai báo ở `config.SPLIT_STRATEGY`:

- "random"         phân tầng theo rp_id, mỗi điểm đều có mặt ở cả ba tập.
- "device_holdout" để riêng một thiết bị làm test. Đây là phép thử quan trọng
                   nhất theo tài liệu thiết kế — đồ án cũ đạt 88-97% trong phòng
                   thí nghiệm nhưng rớt xuống 5-12 m ngoài thực tế vì chỉ dùng
                   random split. Cần dữ liệu từ >= 2 máy mới chạy được.
- "time_holdout"   để riêng khoảng thời gian cuối làm test, kiểm tra mô hình có
                   chịu được việc hạ tầng WiFi thay đổi theo thời gian không.
"""

from __future__ import annotations

import pandas as pd
from sklearn.model_selection import train_test_split

from ml import config


def _gan_nhan(train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame) -> pd.DataFrame:
    return pd.concat(
        [
            train.assign(split="train"),
            val.assign(split="validation"),
            test.assign(split="test"),
        ],
        ignore_index=True,
    )


def split_random(fingerprint: pd.DataFrame) -> pd.DataFrame:
    """Chia ngẫu nhiên, phân tầng theo rp_id."""
    # Phân tầng cần mỗi lớp có ít nhất 2 mẫu ở mỗi lần cắt.
    dem = fingerprint["rp_id"].value_counts()
    phan_tang = fingerprint["rp_id"] if dem.min() >= 3 else None

    ty_le_tam = config.TEST_SIZE + config.VALIDATION_SIZE
    train, tam = train_test_split(
        fingerprint,
        test_size=ty_le_tam,
        stratify=phan_tang,
        random_state=config.RANDOM_STATE,
    )

    # Phải kiểm tra lại trên tập tạm: nó nhỏ hơn nhiều nên một điểm có thể rơi
    # xuống còn 1 mẫu, lúc đó sklearn ném lỗi thay vì phân tầng.
    dem_tam = tam["rp_id"].value_counts()
    phan_tang_tam = tam["rp_id"] if (phan_tang is not None and dem_tam.min() >= 2) else None

    val, test = train_test_split(
        tam,
        test_size=config.TEST_SIZE / ty_le_tam,
        stratify=phan_tang_tam,
        random_state=config.RANDOM_STATE,
    )

    return _gan_nhan(train, val, test)


def split_device_holdout(fingerprint: pd.DataFrame, holdout_device: str | None = None) -> pd.DataFrame:
    """Để riêng toàn bộ dữ liệu của một thiết bị làm tập test."""
    thiet_bi = sorted(fingerprint["device_id"].unique())
    if len(thiet_bi) < 2:
        raise ValueError(
            f"Chỉ có {len(thiet_bi)} thiết bị ({thiet_bi}) — không tách device holdout được.\n"
            f"Cần thu thêm dữ liệu bằng ít nhất một máy thứ hai."
        )

    giu = holdout_device or config.HOLDOUT_DEVICE or thiet_bi[-1]
    if giu not in thiet_bi:
        raise ValueError(f"Thiết bị '{giu}' không có trong dữ liệu. Đang có: {thiet_bi}")

    test = fingerprint[fingerprint["device_id"] == giu]
    con_lai = fingerprint[fingerprint["device_id"] != giu]

    dem = con_lai["rp_id"].value_counts()
    phan_tang = con_lai["rp_id"] if dem.min() >= 2 else None
    ty_le_val = config.VALIDATION_SIZE / (1 - config.TEST_SIZE)
    train, val = train_test_split(
        con_lai,
        test_size=ty_le_val,
        stratify=phan_tang,
        random_state=config.RANDOM_STATE,
    )

    return _gan_nhan(train, val, test)


def split_time_holdout(fingerprint: pd.DataFrame) -> pd.DataFrame:
    """Để riêng khoảng thời gian cuối làm tập test.

    `scan_id` bắt nguồn từ cột Time định dạng YYYY:MM:DD:HH:MM:SS nên sắp xếp
    chuỗi cũng chính là sắp xếp theo thời gian.
    """
    theo_thoi_gian = fingerprint.sort_values("scan_id", kind="stable").reset_index(drop=True)
    n = len(theo_thoi_gian)

    cat_test = int(n * (1 - config.TEST_SIZE))
    cat_val = int(n * (1 - config.TEST_SIZE - config.VALIDATION_SIZE))

    return _gan_nhan(
        theo_thoi_gian.iloc[:cat_val],
        theo_thoi_gian.iloc[cat_val:cat_test],
        theo_thoi_gian.iloc[cat_test:],
    )


def split_dataset(fingerprint: pd.DataFrame, strategy: str | None = None) -> tuple[pd.DataFrame, dict]:
    """Chia tập theo chiến lược đã chọn và kiểm tra kết quả hợp lệ."""
    cach = strategy or config.SPLIT_STRATEGY

    if cach == "random":
        ket_qua = split_random(fingerprint)
    elif cach == "device_holdout":
        ket_qua = split_device_holdout(fingerprint)
    elif cach == "time_holdout":
        ket_qua = split_time_holdout(fingerprint)
    else:
        raise ValueError(
            f"Chiến lược chia tập không hợp lệ: '{cach}'. "
            f"Chọn một trong: random, device_holdout, time_holdout"
        )

    thong_ke = {
        "chien_luoc": cach,
        "so_mau": ket_qua["split"].value_counts().to_dict(),
        "so_rp_moi_tap": ket_qua.groupby("split")["rp_id"].nunique().to_dict(),
    }

    # Điểm tham chiếu chỉ có trong test mà không có trong train là không học được.
    rp_train = set(ket_qua.loc[ket_qua["split"] == "train", "rp_id"])
    rp_test = set(ket_qua.loc[ket_qua["split"] == "test", "rp_id"])
    thieu = sorted(rp_test - rp_train)
    if thieu:
        thong_ke["canh_bao"] = f"{len(thieu)} điểm chỉ có trong test, không có trong train: {thieu}"

    return ket_qua, thong_ke
