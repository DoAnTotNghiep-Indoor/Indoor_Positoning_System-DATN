"""Ghi lần quét WiFi liên tục suốt buổi đo, qua adb (cáp hoặc Tailscale).

    python -m tools.ghi_lien_tuc --nguoi-thu <MSSV>

Không cần mã điểm: người tại chỗ ghi phiếu (mã điểm, mặt đứng, hướng, giờ bắt đầu,
giờ kết thúc), sau buổi cắt theo giờ. Mỗi lần quét ghi ngay xuống tệp nên adb rớt
giữa chừng không mất dữ liệu; rớt thì tự `adb connect` lại.

Bỏ đọc cảm biến: `dumpsys` qua 4G chậm, và lúc app IPS ở màn hình trước thì la bàn
không chạy nên cột hướng rỗng; hướng lấy theo phiếu.
"""

from __future__ import annotations

import argparse
import csv
import os
import time
from datetime import datetime

from tools.thu_van_tay import COT, RA, _adb, doc_ket_qua


def _dia_chi() -> str:
    # Nhiều máy cùng nối thì chọn bằng ANDROID_SERIAL; adb tự đọc biến này cho mọi lệnh.
    if os.environ.get("ANDROID_SERIAL"):
        return os.environ["ANDROID_SERIAL"]
    ds = [d.split()[0] for d in _adb("devices").splitlines()[1:] if d.strip().endswith("device")]
    if not ds:
        raise SystemExit("Không thấy máy nào.")
    return ds[0]


def main() -> None:
    bo = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    bo.add_argument("--nguoi-thu", required=True)
    bo.add_argument("--cho", type=float, default=2.5, help="giây chờ sau lệnh quét")
    tham = bo.parse_args()

    dia_chi = _dia_chi()
    may = _adb("shell", "getprop", "ro.product.model").strip()
    RA.mkdir(parents=True, exist_ok=True)
    ra = RA / f"lien_tuc_{may}_{datetime.now():%H%M}.csv"
    print(f"Ghi vào {ra} · máy {may} ({dia_chi}). Ctrl+C để dừng.", flush=True)

    truoc, lan = None, 0
    with ra.open("w", encoding="utf-8", newline="") as f:
        ghi = csv.DictWriter(f, fieldnames=COT, restval="")
        ghi.writeheader()
        while True:
            try:
                _adb("shell", "cmd", "wifi", "start-scan")
                time.sleep(tham.cho)
                ds = doc_ket_qua()
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"{datetime.now():%H:%M:%S} rớt adb ({e}), nối lại...", flush=True)
                try:
                    _adb("connect", dia_chi)
                except Exception:
                    pass
                time.sleep(3)
                continue
            # Máy chưa quét xong thì trả lại đúng bộ cũ: bỏ để không đếm một lần quét hai lần.
            dau = sorted((a["bssid"], a["rssi"]) for a in ds)
            if not ds or dau == truoc:
                continue
            truoc, lan = dau, lan + 1
            luc = datetime.now()
            for i, ap in enumerate(ds, start=1):
                ghi.writerow({
                    "Time": f"{luc:%Y:%m:%d:%H:%M:%S}",
                    "WiFi fingerprint serial number": lan,
                    "WiFi AP serial number": i,
                    "Total number of AP scanned": len(ds),
                    "WiFi SSID": ap["ssid"], "WiFi BSSID": ap["bssid"],
                    "WiFi Frequency (MHz)": ap["tan_so"], "WiFi RSSI (dBm)": ap["rssi"],
                    "Phone Model": may, "Student ID": tham.nguoi_thu,
                })
            f.flush()
            manh = sum(a["rssi"] > -70 for a in ds)
            print(f"{luc:%H:%M:%S}  #{lan:<4} {len(ds):>3} AP  ({manh} mạnh hơn −70 dBm)", flush=True)


if __name__ == "__main__":
    main()
