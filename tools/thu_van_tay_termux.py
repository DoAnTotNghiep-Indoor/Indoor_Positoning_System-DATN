#!/data/data/com.termux/files/usr/bin/python
"""Thu vân tay WiFi bằng Termux, chạy thẳng trên điện thoại — không cần cáp.

    python thu_van_tay_termux.py RP46 --nguoi-thu <MSSV> --so-lan 20 --giay 45

CHƯA DÙNG ĐƯỢC trên máy thử nghiệm, giữ lại làm tài liệu. Termux:API bản
F-Droid là 0.53.0 (2022) trong khi gói `termux-api` là 0.59.1, nên
`termux-wifi-scaninfo` treo vô hạn không trả gì. Bản Play Store thì lệch chữ
ký với Termux:API của F-Droid. Dùng `tools/thu_van_tay.py` qua cáp.

Bản song sinh của `thu_van_tay.py`: cùng ghi 20 cột của `combined_data.csv`,
chỉ khác nguồn đọc — bản kia đọc qua `adb` dưới UID `shell`, bản này gọi
`termux-wifi-scaninfo` vì Termux chạy dưới UID ứng dụng nên không có quyền
dùng `cmd wifi list-scan-results`.

Cài: Termux và Termux:API từ F-Droid, `pkg install python termux-api`,
`termux-setup-storage`, rồi cấp quyền Vị trí cho Termux:API — thiếu quyền thì
Android 10+ trả danh sách rỗng mà không báo lỗi. CSV ghi ra
`~/storage/shared/ips_thu/`. Kiểm trước bằng `termux-wifi-scaninfo | head`.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

RA = Path.home() / "storage" / "shared" / "ips_thu"

COT = [
    "Time", "WiFi fingerprint serial number", "WiFi AP serial number",
    "Total number of AP scanned", "WiFi SSID", "WiFi BSSID",
    "WiFi Frequency (MHz)", "WiFi RSSI (dBm)",
    "Magnetic x (µT)", "Magnetic y (µT)", "Magnetic z (µT)",
    "GPS Longitude (°)", "GPS Latitude (°)", "GPS Altitude (m)",
    "Orientation Azimuth (°)", "Orientation Pitch (°)", "Orientation Roll (°)",
    "Phone Model", "Student ID", "Reference Point ID",
]


def _chay(*lenh: str) -> str:
    kq = subprocess.run(lenh, capture_output=True, text=True)
    if kq.returncode:
        raise SystemExit(f"{lenh[0]}: {kq.stderr.strip()[:150]}")
    return kq.stdout


def ten_may() -> str:
    try:
        return _chay("getprop", "ro.product.model").strip() or "khong-ro"
    except SystemExit:
        return "khong-ro"


def quet() -> list[dict]:
    """Một lần đọc bảng kết quả quét. Danh sách rỗng là chưa có quyền vị trí."""
    tho = _chay("termux-wifi-scaninfo")
    try:
        ds = json.loads(tho)
    except json.JSONDecodeError:
        raise SystemExit(f"termux-wifi-scaninfo trả về thứ không phải JSON:\n{tho[:200]}")
    return [
        {"bssid": str(a["bssid"]).lower(), "ssid": a.get("ssid", ""),
         "tan_so": int(a.get("frequency", 0)), "rssi": int(a["rssi"])}
        for a in ds if a.get("bssid") and a.get("rssi") is not None
    ]


def thu(rp_id: str, so_lan: int, giay: float, nguoi_thu: str) -> Path:
    may = ten_may()
    RA.mkdir(parents=True, exist_ok=True)
    ra = RA / f"{rp_id}.csv"
    if ra.exists():
        raise SystemExit(f"{ra} đã có — đổi tên hoặc xoá trước khi thu lại {rp_id}.")

    print(f"Thu {rp_id} · {so_lan} lần × {giay:.0f} giây ≈ "
          f"{so_lan * giay / 60:.0f} phút · máy {may}")
    print("Đứng yên tại điểm, giữ máy ngang tầm ngực. Ctrl+C để dừng sớm.\n")

    dong: list[dict] = []
    lan = 0
    truoc: set[tuple[str, int]] = set()
    try:
        while lan < so_lan:
            ds = quet()
            if not ds:
                raise SystemExit(
                    "Danh sách rỗng. Nhiều khả năng Termux:API chưa được cấp quyền\n"
                    "Vị trí, hoặc ROM đang chặn quét nền. Kiểm bằng:\n"
                    "    termux-wifi-scaninfo | head")

            # Android chặn 4 lần startScan mỗi 2 phút; quá tay thì API trả lại
            # đúng bảng cũ. Không lọc thì tệp đầy bản sao và mô hình tưởng điểm
            # đó rất ổn định.
            dau = {(a["bssid"], a["rssi"]) for a in ds}
            if dau == truoc:
                print("   (kết quả trùng lần trước, chờ thêm)")
                time.sleep(giay)
                continue
            truoc = dau

            lan += 1
            luc = datetime.now().strftime("%Y:%m:%d:%H:%M:%S")
            for i, ap in enumerate(ds, start=1):
                dong.append({
                    "Time": luc,
                    "WiFi fingerprint serial number": lan,
                    "WiFi AP serial number": i,
                    "Total number of AP scanned": len(ds),
                    "WiFi SSID": ap["ssid"],
                    "WiFi BSSID": ap["bssid"],
                    "WiFi Frequency (MHz)": ap["tan_so"],
                    "WiFi RSSI (dBm)": ap["rssi"],
                    "Phone Model": may,
                    "Student ID": nguoi_thu,
                    "Reference Point ID": rp_id,
                })
            manh = sum(1 for a in ds if a["rssi"] > -70)
            print(f"  {lan:>2}/{so_lan}  {len(ds)} AP  ({manh} mạnh hơn −70 dBm)")
            if lan < so_lan:
                time.sleep(giay)
    except KeyboardInterrupt:
        print(f"\nDừng sớm sau {lan} lần.")

    if not dong:
        raise SystemExit("Không thu được lần quét nào, không ghi tệp.")

    with ra.open("w", encoding="utf-8", newline="") as f:
        ghi = csv.DictWriter(f, fieldnames=COT, restval="")
        ghi.writeheader()
        ghi.writerows(dong)

    print(f"\n→ {ra}  ({lan} lần quét, {len(dong)} dòng)")
    return ra


def main() -> None:
    bo = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    bo.add_argument("rp_id", help="mã điểm, ví dụ RP46")
    bo.add_argument("--so-lan", type=int, default=20)
    bo.add_argument("--giay", type=float, default=45.0)
    bo.add_argument("--nguoi-thu", required=True,
                    help="MSSV người đi thu (bắt buộc — xem tools/thu_van_tay.py)")
    tham = bo.parse_args()

    if not re.fullmatch(r"RP\d{2}", tham.rp_id):
        raise SystemExit(f"Mã điểm phải dạng RP46, nhận được '{tham.rp_id}'.")
    thu(tham.rp_id, tham.so_lan, tham.giay, tham.nguoi_thu)


if __name__ == "__main__":
    main()
