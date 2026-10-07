"""Đo độ trễ máy chủ từ phía client: /health, /predict (lần quét test thật), /route.

    python -m tools.do_tre_may_chu https://dlu-ips.etylix.com [--lan 200]

Một client giữ kết nối (keep-alive) như app. `/predict` gửi lần quét của tập test với device_id `do-tre-<giờ>`
nên ghi vào CSDL máy chủ; `latency_ms` trong trả lời là thời gian mô hình chạy trên máy chủ. In trung vị, P90,
P99 mili giây.
"""
import json
import sys
import time

import httpx
import numpy as np
import pandas as pd

from ml import config


def thong_ke(ms) -> str:
    a = np.asarray(ms)
    return f"trung vị {np.median(a):6.1f}  P90 {np.percentile(a, 90):6.1f}  P99 {np.percentile(a, 99):6.1f}  ms"


def main() -> None:
    goc = sys.argv[1].rstrip("/")
    lan = int(sys.argv[sys.argv.index("--lan") + 1]) if "--lan" in sys.argv else 200
    ap = json.loads((config.ARTIFACTS_DIR / config.FEATURE_LIST_JSON).read_text(encoding="utf-8"))["ap_columns"]
    # Tệp thô (dBm) mà chế độ DEMO phát lại; splits/ đã chuẩn hoá về 0-1.
    te = pd.read_csv(config.PROCESSED_DIR / "fingerprint_dataset_raw.csv").query("split == 'test'")
    te = te.sample(lan, random_state=0, replace=len(te) < lan)
    quet = [[{"bssid": b, "rssi": float(r)} for b, r in zip(ap, h) if r > -100] for h in te[ap].fillna(-100).to_numpy()]
    rp = te[["x", "y"]].to_numpy()
    thiet_bi = f"do-tre-{time.strftime('%H%M%S')}"

    with httpx.Client(base_url=goc, timeout=15) as c:
        c.get("/health")  # mở kết nối và TLS trước khi đo
        kq = {"health": [], "predict": [], "route": [], "mo_hinh": []}
        for i in range(lan):
            t = time.perf_counter()
            c.get("/health").raise_for_status()
            kq["health"].append((time.perf_counter() - t) * 1000)

            t = time.perf_counter()
            r = c.post("/predict", json={"device_id": thiet_bi, "scan": quet[i]})
            kq["predict"].append((time.perf_counter() - t) * 1000)
            if r.status_code == 200:
                kq["mo_hinh"].append(r.json()["latency_ms"])

            t = time.perf_counter()
            c.post("/route", json={"tu_x": rp[i, 0], "tu_y": rp[i, 1], "den_nhom": "Bàn thủ thư"}).raise_for_status()
            kq["route"].append((time.perf_counter() - t) * 1000)

    print(f"{goc}, {lan} lần mỗi loại, {len(kq['mo_hinh'])} lần /predict trả 200")
    for k, v in kq.items():
        print(f"  {k:8s} {thong_ke(v)}")


if __name__ == "__main__":
    main()
