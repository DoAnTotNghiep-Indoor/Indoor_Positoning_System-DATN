"""Thu vân tay WiFi tại một điểm tham chiếu, qua cáp USB.

    python -m tools.thu_van_tay RP46 --nguoi-thu <MSSV>
    python -m tools.thu_van_tay RP46 --nguoi-thu <MSSV> --so-lan 20 --giay 45

`--nguoi-thu` bắt buộc: 7 tệp buổi 06/09/2026 đứng tên nhầm vì mặc định cũ là mã
người thu bộ CTK45. Xem `data/raw/nhom15_2026/README.md`.

Đọc bằng `adb shell cmd wifi list-scan-results` nên KHÔNG cần sửa ứng dụng
Flutter; máy chỉ cần cắm cáp và bật gỡ lỗi USB. Ghi ra
`data/raw/nhom15_2026/<ngày>/<rp_id>.csv` đúng 20 cột của
`combined_data.csv`, để RIÊNG vì hai máy đọc RSSI lệch nhau vài dBm — xem
`data/raw/nhom15_2026/README.md`.

45 giây một lần vì Android chặn 4 lần `startScan` mỗi 2 phút; quét dày hơn
chỉ nhận lại bộ đệm cũ, và công cụ phát hiện việc đó bằng cột `Age`.

Chuẩn bị máy trước khi đo — thiếu là cột rỗng:

1. Mở khoá máy, mở la bàn, để ở màn hình trước, đừng để màn hình tắt::

       adb shell monkey -p com.miui.compass -c android.intent.category.LAUNCHER 1

2. Bật định vị, mở bản đồ một lần gần cửa sổ để `dumpsys location` có vị trí.

Công cụ dò trước và dừng nếu thiếu, thay vì để người đo đứng yên 15 phút rồi
mới biết tệp hỏng. Ba cột từ kế chưa đọc được nên không tính là chặn.
"""

from __future__ import annotations

import argparse
import csv
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from ml import config
from tools import cam_bien_adb

for _luong in (sys.stdout, sys.stderr):
    if hasattr(_luong, "reconfigure"):
        try:
            _luong.reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            pass

# Mỗi buổi một thư mục con theo ngày: buổi khác ngày là điều kiện đo khác,
# và `ml.audit` so sánh giữa các buổi nên ranh giới ấy phải giữ được.
RA = config.RAW_DIR / "nhom15_2026" / datetime.now().strftime("%Y-%m-%d")

COT = [
    "Time", "WiFi fingerprint serial number", "WiFi AP serial number",
    "Total number of AP scanned", "WiFi SSID", "WiFi BSSID",
    "WiFi Frequency (MHz)", "WiFi RSSI (dBm)",
    "Magnetic x (µT)", "Magnetic y (µT)", "Magnetic z (µT)",
    "GPS Longitude (°)", "GPS Latitude (°)", "GPS Altitude (m)",
    "Orientation Azimuth (°)", "Orientation Pitch (°)", "Orientation Roll (°)",
    "Phone Model", "Student ID", "Reference Point ID",
]

# SSID chứa được dấu cách nên không tách theo khoảng trắng: neo vào BSSID ở đầu
# dòng và dấu `[` mở phần Flags ở cuối.
DONG = re.compile(
    r"^\s*([0-9a-fA-F:]{17})\s+(\d+)\s+(-?\d+)\S*\s+([\d,.]+)\s+(.*?)\s*\[")

# Quá tuổi này coi như bộ đệm cũ, không phải lần quét vừa yêu cầu.
TUOI_TOI_DA_GIAY = 12.0


def _adb(*lenh: str) -> str:
    kq = subprocess.run(("adb", *lenh), capture_output=True, text=True,
                        encoding="utf-8", errors="replace")
    if kq.returncode:
        raise RuntimeError(f"adb {' '.join(lenh)}: {kq.stderr.strip()[:120]}")
    return kq.stdout


def kiem_may() -> str:
    ds = [d for d in _adb("devices").splitlines()[1:] if d.strip().endswith("device")]
    if not ds:
        raise SystemExit("Không thấy máy nào. Cắm cáp, bật gỡ lỗi USB rồi thử lại.")
    return _adb("shell", "getprop", "ro.product.model").strip()


def doc_ket_qua() -> list[dict]:
    """Bảng kết quả quét hiện có trên máy, đã lọc theo độ tuổi."""
    ds = []
    for dong in _adb("shell", "cmd", "wifi", "list-scan-results").splitlines():
        m = DONG.match(dong)
        if not m:
            continue
        bssid, tan_so, rssi, tuoi, ssid = m.groups()
        if float(tuoi.replace(",", ".")) > TUOI_TOI_DA_GIAY:
            continue
        ds.append({"bssid": bssid.lower(), "tan_so": int(tan_so),
                   "rssi": int(rssi), "ssid": ssid.strip()})
    return ds


def mot_lan_quet(cho_giay: float = 6.0) -> list[dict]:
    _adb("shell", "cmd", "wifi", "start-scan")
    time.sleep(cho_giay)
    return doc_ket_qua()


def do_cam_bien(bat_buoc: bool) -> None:
    """Dò cảm biến TRƯỚC khi đứng đo, để không mất 15 phút vào tệp thiếu cột.

    Chỉ chặn vì `COT_CHAN` — sáu cột đã chứng minh lấy được. Ba cột từ kế chưa
    có đường đọc trên máy này nên chặn vì chúng là chặn vĩnh viễn.
    """
    gt = cam_bien_adb.doc_het()
    t, chan = cam_bien_adb.thieu(gt), cam_bien_adb.thieu_chan(gt)
    print(f"Cảm biến: {9 - len(t)}/9 cột đọc được"
          + (f" — thiếu {', '.join(t)}" if t else ""))
    if not chan:
        return

    if bat_buoc:
        raise SystemExit(
            "Dừng lại: đo bây giờ sẽ ra tệp thiếu cột như buổi 06/09.\n"
            "  → Mở khoá máy, mở la bàn, để nguyên ở màn hình trước và đừng để\n"
            "    màn hình tắt (cấp góc nghiêng):\n"
            "    adb shell monkey -p com.miui.compass -c "
            "android.intent.category.LAUNCHER 1\n"
            "  → Bật định vị, mở bản đồ một lần gần cửa sổ (cấp GPS).\n"
            "  → Kiểm lại bằng `python -m tools.cam_bien_adb`.\n"
            "  → Chấp nhận thiếu thì thêm --thieu-cam-bien-van-do.")
    print("  (vẫn đo theo --thieu-cam-bien-van-do; các cột trên sẽ rỗng)")


def thu(rp_id: str, so_lan: int, giay: float, nguoi_thu: str, may: str) -> Path:
    RA.mkdir(parents=True, exist_ok=True)
    ra = RA / f"{rp_id}.csv"
    if ra.exists():
        raise SystemExit(f"{ra} đã có — đổi tên hoặc xoá trước khi thu lại {rp_id}.")

    print(f"Thu {rp_id} · {so_lan} lần × {giay:.0f} giây ≈ "
          f"{so_lan * giay / 60:.0f} phút · máy {may}")
    print("Đứng yên tại điểm, giữ máy ngang tầm ngực. Ctrl+C để dừng sớm.\n")

    dong: list[dict] = []
    lan = 0
    # Bắt MỌI lỗi chứ không riêng Ctrl+C: cáp tuột giữa chừng thì `adb` ném
    # RuntimeError, và bản trước để nó bay lên làm mất trắng số lần đã quét.
    # Đứng đo 15 phút mà mất dữ liệu vì một cú chạm dây là quá đắt.
    try:
        while lan < so_lan:
            ds = mot_lan_quet()
            if not ds:
                print("   (không có kết quả mới, chờ thêm)")
                time.sleep(giay)
                continue

            lan += 1
            luc = datetime.now().strftime("%Y:%m:%d:%H:%M:%S")
            # Một lần đọc cho cả lần quét, lặp lại trên mọi dòng AP — đúng cấu
            # trúc bộ CTK45 (mỗi lần quét chỉ 1 giá trị cảm biến).
            cb = {k: v for k, v in cam_bien_adb.doc_het().items() if v is not None}
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
                    **cb,
                })
            manh = sum(1 for a in ds if a["rssi"] > -70)
            hut = 9 - len(cb)
            print(f"  {lan:>2}/{so_lan}  {len(ds)} AP  ({manh} mạnh hơn −70 dBm)"
                  + (f"  · hụt {hut}/9 cột cảm biến" if hut else ""))
            if lan < so_lan:
                time.sleep(giay)
    except KeyboardInterrupt:
        print(f"\nDừng sớm sau {lan} lần.")
    except Exception as e:
        print(f"\nHỎNG sau {lan} lần: {e}")
        print("Phần đã quét vẫn được ghi lại — đo bù cho đủ bằng --so-lan.")

    if not dong:
        raise SystemExit("Không thu được lần quét nào, không ghi tệp.")

    with ra.open("w", encoding="utf-8", newline="") as f:
        ghi = csv.DictWriter(f, fieldnames=COT, restval="")
        ghi.writeheader()
        ghi.writerows(dong)

    print(f"\n→ {ra}  ({lan} lần quét, {len(dong)} dòng)")
    _bao_cao_cot(dong)
    return ra


def _bao_cao_cot(dong: list[dict]) -> None:
    """Cột nào rỗng ở bao nhiêu phần trăm dòng — biết ngay, không đợi lúc gộp bộ."""
    hong = [(c, sum(1 for d in dong if d.get(c) in (None, "")) / len(dong))
            for c in COT]
    hong = [(c, t) for c, t in hong if t]
    if not hong:
        print("Đủ 20/20 cột, khớp combined_data.csv.")
        return
    print(f"{20 - len(hong)}/20 cột đầy đủ. Còn rỗng:")
    for c, t in hong:
        print(f"  · {c:<26} rỗng {t:.0%} số dòng")


def main() -> None:
    bo = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    bo.add_argument("rp_id", help="mã điểm, ví dụ RP46")
    bo.add_argument("--so-lan", type=int, default=20,
                    help="số lần quét, mặc định 20 như buổi thu 2025")
    bo.add_argument("--giay", type=float, default=45.0,
                    help="giãn cách giữa hai lần quét, mặc định 45")
    # BẮT BUỘC, không có mặc định. Trước đây mặc định là 2212343 — mã người thu
    # bộ CTK45 lấy từ `combined_data.csv` — nên cả 7 tệp buổi 06/09/2026 đều đứng
    # tên nhầm người. Bắt gõ tay để lỗi đó không lặp lại lặng lẽ.
    bo.add_argument("--nguoi-thu", required=True,
                    help="MSSV người đi thu (bắt buộc, không có mặc định)")
    bo.add_argument("--thieu-cam-bien-van-do", action="store_true",
                    help="vẫn đo dù không đọc được từ kế / góc nghiêng / GPS")
    tham = bo.parse_args()

    if not re.fullmatch(r"RP\d{2}", tham.rp_id):
        raise SystemExit(f"Mã điểm phải dạng RP46, nhận được '{tham.rp_id}'.")
    may = kiem_may()
    do_cam_bien(bat_buoc=not tham.thieu_cam_bien_van_do)
    thu(tham.rp_id, tham.so_lan, tham.giay, tham.nguoi_thu, may)


if __name__ == "__main__":
    main()
