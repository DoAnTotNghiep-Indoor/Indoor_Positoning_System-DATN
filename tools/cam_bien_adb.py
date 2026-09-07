"""Đọc từ kế, góc nghiêng và GPS của máy Android qua `adb`.

`dumpsys` là công cụ gỡ lỗi chứ không phải API, định dạng đổi theo hãng — nên
mọi hàm trả None khi không đọc được, KHÔNG bao giờ bịa số.

Hai điều kiện quyết định giá trị có dùng được không:

1. Chỉ nhận dòng tiêu đề đúng dạng `<tên>: last N events`. Dò theo tên trên cả
   bản dump sẽ khớp phải mục `Sensor List` rồi lấy sự kiện của cảm biến khác.
2. Vùng đệm không tự làm mới — không app nào nghe thì số cũ nằm nguyên đó, nên
   mọi giá trị bị đối chiếu `ts` với `/proc/uptime`, quá `TUOI_TOI_DA_GIAY`
   thì loại.

Ba cột `Orientation *` ghi nhãn độ nhưng `combined_data.csv` lưu RADIAN, và
`ml.config.AZIMUTH_IS_RADIAN = True` dựa vào đúng điều đó; ghi ra độ thì
pipeline vẫn chạy êm mà azimuth lệch 57 lần. Thử cảm biến `Orientation` trước
(đổi độ sang radian), không có thì dùng Rotation Vector; loại `Game` vì nó
không tham chiếu bắc từ.

Lấy được `Orientation *` khi mở khoá máy và để la bàn `com.miui.compass` ở màn
hình trước; `GPS *` từ vị trí biết cuối cùng. `Magnetic *` thì KHÔNG — không
app nào trên máy đăng ký từ kế thô, muốn có phải thêm listener
TYPE_MAGNETIC_FIELD vào app Flutter.

Chạy `python -m tools.cam_bien_adb` để dò trước khi ra thực địa.
"""

from __future__ import annotations

import math
import re
import subprocess

COT_TU_KE = ["Magnetic x (µT)", "Magnetic y (µT)", "Magnetic z (µT)"]
COT_GOC = ["Orientation Azimuth (°)", "Orientation Pitch (°)",
           "Orientation Roll (°)"]
COT_GPS = ["GPS Longitude (°)", "GPS Latitude (°)", "GPS Altitude (m)"]
COT_CAM_BIEN = COT_TU_KE + COT_GOC + COT_GPS

# Sáu cột đã chứng minh lấy được qua adb. Ba cột từ kế không nằm ở đây vì trên
# máy này không có đường nào đọc được, nên chặn buổi đo vì chúng là chặn vô ích.
# `Orientation Azimuth (°)` nằm trong `ml.config.REQUIRED_RAW_COLS` — thiếu nó
# thì `ml.pipeline` từ chối chạy, nên nó phải là điều kiện chặn thật sự.
COT_CHAN = COT_GOC + COT_GPS

# Cảm biến đang được nghe cập nhật hàng chục lần mỗi giây; quá ngưỡng này nghĩa
# là không ai nghe và ta đang nhìn vào giá trị đọng lại từ lần trước.
TUOI_TOI_DA_GIAY = 15.0

_SO = r"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?"

# Chỉ dòng đúng dạng "<tên>: last N events" mới được coi là mở đầu một vùng đệm.
# Đây là thứ chặn cái bẫy số 1: `Sensor List` nhắc lại tên cảm biến nhưng không
# dòng nào ở đó khớp mẫu này, nên không thể nhận nhầm sự kiện của cảm biến khác.
TIEU_DE = re.compile(r"^(?P<ten>\S.*?):\s*last\s+\d+\s+events\s*$")
SU_KIEN = re.compile(rf"^\s+\d+\s+\(ts=({_SO}),[^)]*\)\s*(.+)$")


def _adb(*lenh: str) -> str:
    kq = subprocess.run(("adb", *lenh), capture_output=True, text=True,
                        encoding="utf-8", errors="replace")
    return "" if kq.returncode else kq.stdout


def uptime() -> float | None:
    """Giây kể từ lúc máy khởi động — cùng gốc thời gian với `ts` của cảm biến."""
    try:
        return float(_adb("shell", "cat", "/proc/uptime").split()[0])
    except (IndexError, ValueError):
        return None


def vung_su_kien(tho: str) -> dict[str, tuple[float, list[float]]]:
    """{tên cảm biến (thường): (ts mới nhất, các giá trị)} trong Recent Sensor events."""
    kq: dict[str, tuple[float, list[float]]] = {}
    ten = None
    for dong in tho.splitlines():
        td = TIEU_DE.match(dong)
        if td:
            ten = td.group("ten").strip().lower()
            continue
        sk = ten and SU_KIEN.match(dong)
        if not sk:
            continue
        gt = [float(x) for x in re.findall(_SO, sk.group(2))]
        ts = float(sk.group(1))
        # Vùng đệm xếp theo thứ tự tăng dần; giữ bản ghi mới nhất.
        if gt and (ten not in kq or ts >= kq[ten][0]):
            kq[ten] = (ts, gt)
    return kq


def _lay(vung: dict[str, tuple[float, list[float]]], co: str,
         khong: tuple[str, ...] = (), bay_gio: float | None = None,
         can: int = 3) -> list[float] | None:
    for ten, (ts, gt) in vung.items():
        if co not in ten or any(k in ten for k in khong) or len(gt) < can:
            continue
        if bay_gio is not None and bay_gio - ts > TUOI_TOI_DA_GIAY:
            continue
        return gt
    return None


def _goc_tu_rotation_vector(gt: list[float]) -> tuple[float, float, float]:
    """Quaternion -> (azimuth, pitch, roll) radian.

    Chép đúng `getRotationMatrixFromVector` + `getOrientation` của Android để so
    được với bộ CTK45, vốn do chính hai hàm này sinh ra. Máy nào trả sẵn thành
    phần vô hướng thì dùng luôn, không thì suy từ chuẩn hoá quaternion.
    """
    q1, q2, q3 = gt[:3]
    q0 = gt[3] if len(gt) >= 4 else math.sqrt(
        max(0.0, 1.0 - q1 * q1 - q2 * q2 - q3 * q3))

    sq1, sq2, sq3 = 2 * q1 * q1, 2 * q2 * q2, 2 * q3 * q3
    q1q2, q3q0 = 2 * q1 * q2, 2 * q3 * q0
    q1q3, q2q0 = 2 * q1 * q3, 2 * q2 * q0
    q2q3, q1q0 = 2 * q2 * q3, 2 * q1 * q0

    m1, m4 = q1q2 - q3q0, 1 - sq1 - sq3
    m6, m7, m8 = q1q3 - q2q0, q2q3 + q1q0, 1 - sq1 - sq2
    return math.atan2(m1, m4), math.asin(-max(-1.0, min(1.0, m7))), math.atan2(-m6, m8)


def _chuan_hoa_pi(rad: float) -> float:
    """Đưa về [-pi, pi) — cảm biến Orientation cũ trả azimuth 0..360."""
    return (rad + math.pi) % (2 * math.pi) - math.pi


def phan_tich_cam_bien(tho: str, bay_gio: float | None = None) -> dict[str, float | None]:
    """Sáu cột cảm biến từ `dumpsys sensorservice`.

    `bay_gio` là `/proc/uptime`; để None thì BỎ kiểm tra tuổi — chỉ dùng khi
    test, vì khi đo thật giá trị cũ cũng sai như giá trị bịa.
    """
    vung = vung_su_kien(tho)
    kq: dict[str, float | None] = dict.fromkeys(COT_TU_KE + COT_GOC)

    # "uncalibrated" trả thêm ba thành phần độ lệch; chỉ dùng khi không còn gì khác.
    tu = (_lay(vung, "magnetometer", ("uncalibrated",), bay_gio)
          or _lay(vung, "magnetic", ("uncalibrated",), bay_gio)
          or _lay(vung, "magnetometer", (), bay_gio)
          or _lay(vung, "magnetic", (), bay_gio))
    if tu:
        kq.update(dict(zip(COT_TU_KE, tu[:3])))

    # Loại "Device Orientation" — cảm biến báo chiều cầm máy, không phải góc nghiêng.
    goc = _lay(vung, "orientation", ("device orientation",), bay_gio)
    if goc:
        # Cảm biến Orientation trả ĐỘ; bộ cũ lưu radian.
        rad = [math.radians(x) for x in goc[:3]]
        goc3 = (_chuan_hoa_pi(rad[0]), rad[1], rad[2])
    else:
        rv = _lay(vung, "rotation vector", ("game",), bay_gio)
        goc3 = _goc_tu_rotation_vector(rv) if rv else None
    if goc3:
        kq.update(dict(zip(COT_GOC, goc3)))
    return kq


def phan_tich_gps(tho: str) -> dict[str, float | None]:
    """Ba cột GPS từ `dumpsys location`. Định dạng:
    `Location[fused 11.957233,108.444842 hAcc=13 et=+5m alt=1523.8 ...]`
    """
    kq: dict[str, float | None] = dict.fromkeys(COT_GPS)
    for dong in tho.splitlines():
        m = re.search(rf"({_SO})\s*,\s*({_SO})\s+(?:hAcc|acc|\+/-)", dong)
        if not m:
            continue
        cao = re.search(rf"\balt=({_SO})", dong)
        kq["GPS Latitude (°)"] = float(m.group(1))
        kq["GPS Longitude (°)"] = float(m.group(2))
        kq["GPS Altitude (m)"] = float(cao.group(1)) if cao else None
        return kq
    return kq


def doc_het() -> dict[str, float | None]:
    """Chín cột, một lần đọc — mỗi lần quét gọi một lần, giống hệt bộ cũ."""
    return {
        **phan_tich_cam_bien(_adb("shell", "dumpsys", "sensorservice"), uptime()),
        **phan_tich_gps(_adb("shell", "dumpsys", "location")),
    }


def thieu(gt: dict[str, float | None]) -> list[str]:
    return [c for c in COT_CAM_BIEN if gt.get(c) is None]


def thieu_chan(gt: dict[str, float | None]) -> list[str]:
    """Chỉ những cột vừa cần vừa lấy được — cơ sở để chặn hay cho đo tiếp."""
    return [c for c in COT_CHAN if gt.get(c) is None]


def main() -> None:
    import sys

    for luong in (sys.stdout, sys.stderr):
        if hasattr(luong, "reconfigure"):
            try:
                luong.reconfigure(encoding="utf-8", errors="replace")
            except (ValueError, OSError):
                pass

    tho = _adb("shell", "dumpsys", "sensorservice")
    bay_gio = uptime()
    gt = {**phan_tich_cam_bien(tho, bay_gio),
          **phan_tich_gps(_adb("shell", "dumpsys", "location"))}

    print("Dò 9 cột cảm biến qua adb:\n")
    for c in COT_CAM_BIEN:
        v = gt[c]
        them = ""
        if v is not None and c == "Orientation Azimuth (°)":
            them = f"   ({math.degrees(v):+.1f}° — cột lưu radian, đúng như bộ cũ)"
        print(f"  {c:<26} {'—— không đọc được' if v is None else f'{v:>12.4f}'}{them}")

    t = thieu(gt)
    if not t:
        print("\nĐủ cả 9 cột. Đo được rồi.")
        return

    print(f"\n{len(t)}/9 cột chưa đọc được:")
    for c in t:
        print(f"  · {c}")

    # Phân biệt "máy không có cảm biến" với "có mà đang không ai nghe" — hai
    # tình huống này cách khắc phục khác hẳn nhau.
    if bay_gio is not None:
        for ten, (ts, _) in sorted(vung_su_kien(tho).items()):
            if any(k in ten for k in ("magnet", "rotation vector", "orientation")):
                cu = bay_gio - ts
                print(f"    {ten}: bản ghi mới nhất cũ {cu:,.0f} giây"
                      f"{' — QUÁ CŨ, đã loại' if cu > TUOI_TOI_DA_GIAY else ''}")

    if any(c in t for c in COT_GOC):
        print("\nGóc nghiêng: vùng đệm chỉ mới khi có app đang nghe cảm biến.\n"
              "  → Mở la bàn và ĐỂ NGUYÊN Ở MÀN HÌNH TRƯỚC:\n"
              "    adb shell monkey -p com.miui.compass -c "
              "android.intent.category.LAUNCHER 1")
    if any(c in t for c in COT_GPS):
        print("\nGPS lấy vị trí biết cuối cùng.\n"
              "  → Bật định vị, mở bản đồ một lần gần cửa sổ rồi chạy lại.")
    if any(c in t for c in COT_TU_KE):
        print("\nTừ kế: chưa có đường đọc trên máy này — không app nào đăng ký\n"
              "  `TYPE_MAGNETIC_FIELD`, và `cmd sensorservice` không có lệnh đăng ký.\n"
              "  Ba cột này sẽ rỗng cho tới khi app Flutter có listener từ kế.")


if __name__ == "__main__":
    main()
