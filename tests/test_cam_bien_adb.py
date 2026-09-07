"""Kiểm phần tách chuỗi của `tools.cam_bien_adb`.

Không cắm máy vẫn chạy được: mọi thứ phụ thuộc `adb` nằm trong `_adb`, còn
`phan_tich_*` chỉ nhận chuỗi. Bản mẫu chép nguyên bố cục thật của
`dumpsys sensorservice` trên Redmi K40 Pro, giữ đủ hai cái bẫy đã làm bản đầu
trả về số rác: `Sensor List` nhắc lại tên cảm biến TRƯỚC mục sự kiện và ngay
dưới là sự kiện `Touch Sensor` toàn số 0; và từ kế máy này tên là
`ak0991x Magnetometer Non-wakeup`, không phải `Magnetic Field Sensor`.
"""

from __future__ import annotations

import math

import pytest

from tools import cam_bien_adb as cb

# Rút gọn từ bản dump thật, giữ nguyên thứ tự mục, cách thụt đầu dòng và tên.
SENSOR_DUMP = """\
Sensor List:
0x00000015) ak0991x Magnetometer Non-wakeup | akm | ver: 146970 | type: android.sensor.magnetic_field(2) | flags: 0x00000880
0x5f726f76) Rotation Vector Sensor    | AOSP | ver: 3 | type: android.sensor.rotation_vector(11) | flags: 0x00000000
0x5f797072) Orientation Sensor        | AOSP | ver: 1 | type: android.sensor.orientation(3) | flags: 0x00000000
Fusion States:
9-axis fusion disabled (0 clients), gyro-rate= 200.00Hz, q=< 0, 0, 0, 0 > (0), b=< 0, 0, 0 >
Recent Sensor events:
Touch Sensor: last 4 events
\t 1 (ts=24.640209364, wall=05:52:52.559) 0.00, 0.00, 0.00, 0.00, 0.00, 0.00,
\t 2 (ts=130220.189715506, wall=18:10:05.802) 1.00, 0.00, 0.00, 0.00, 0.00, 0.00,
device_orient  Wakeup: last 1000 events
\t 1 (ts=130221.000000000, wall=18:02:47.000) 3.00, 0.00, 0.00,
Rotation Vector  Non-wakeup: last 10 events
\t 1 (ts=130220.504041582, wall=18:02:46.157) -0.01, -0.01, 0.25, 0.97, -1.00,
\t 2 (ts=130221.534041582, wall=18:02:47.180) -0.01, -0.01, 0.25, 0.97, -1.00,
ak0991x Magnetometer-Uncalibrated Non-wakeup: last 10 events
\t 1 (ts=130221.400000000, wall=18:02:47.000) 99.00, 99.00, 99.00, 0.10, 0.10, 0.10,
ak0991x Magnetometer Non-wakeup: last 10 events
\t 1 (ts=130221.413656847, wall=18:02:47.032) 23.61, 8.04, 21.08,
\t 2 (ts=130221.513656847, wall=18:02:47.132) 23.72, 7.86, 21.71,
"""

# Máy đọc lúc 130.226 s uptime: mọi bản ghi trên đều mới dưới 15 giây.
BAY_GIO = 130226.0

LOCATION_DUMP = """\
Location Manager State:
  Last Known Locations:
    gps: Location[gps 11.957233,108.444842 hAcc=8 et=+3m12s alt=1523.79 vel=0.0]
    fused: Location[fused 11.957100,108.444700 hAcc=13 et=+1m alt=1520.10]
"""


def test_doc_du_ba_truc_tu_ke():
    kq = cb.phan_tich_cam_bien(SENSOR_DUMP, BAY_GIO)
    assert (kq["Magnetic x (µT)"], kq["Magnetic y (µT)"], kq["Magnetic z (µT)"]) \
        == (23.72, 7.86, 21.71)


def test_khong_vo_phai_su_kien_cua_cam_bien_khac():
    """Bẫy đã gặp thật: khớp tên ở `Sensor List` rồi lấy nhầm `Touch Sensor` toàn 0."""
    kq = cb.phan_tich_cam_bien(SENSOR_DUMP, BAY_GIO)
    assert kq["Magnetic x (µT)"] != 0.0
    assert kq["Orientation Azimuth (°)"] != 0.0


def test_rotation_vector_dung_thanh_phan_vo_huong_san_co():
    """Máy trả 5 giá trị (x, y, z, w, độ tin cậy); phải dùng w có sẵn, không tự suy.
    Số đối chiếu ghi cứng chứ không gọi lại chính hàm đang kiểm — suy w từ điều
    kiện chuẩn hoá cho 0,9681 thay vì 0,97, lệch azimuth 0,047 độ.
    """
    kq = cb.phan_tich_cam_bien(SENSOR_DUMP, BAY_GIO)
    assert kq["Orientation Azimuth (°)"] == pytest.approx(-0.506049676, abs=1e-9)
    assert kq["Orientation Pitch (°)"] == pytest.approx(0.024402422, abs=1e-9)
    assert kq["Orientation Roll (°)"] == pytest.approx(-0.014404766, abs=1e-9)


def test_loai_gia_tri_qua_cu():
    """Không app nào nghe thì vùng đệm đứng yên; số cũ 43 phút cũng sai như số bịa."""
    kq = cb.phan_tich_cam_bien(SENSOR_DUMP, BAY_GIO + 3600)
    assert all(kq[c] is None for c in cb.COT_TU_KE + cb.COT_GOC)


def test_uu_tien_tu_ke_da_hieu_chinh():
    """Bản `-Uncalibrated` đứng ngay trước và cũng đủ mới, nhưng phải bị bỏ qua."""
    assert cb.phan_tich_cam_bien(SENSOR_DUMP, BAY_GIO)["Magnetic x (µT)"] == 23.72


def test_bo_qua_device_orientation():
    """`Device Orientation` báo chiều cầm máy (0..3), tên lại chứa cả "orientation".
    Máy thử nghiệm gọi nó là `device_orient` nên không đụng bộ lọc, nhưng bản AOSP
    đặt tên đầy đủ thì khớp — và giá trị 3,0 sẽ thành azimuth 3 độ.
    """
    tho = SENSOR_DUMP + ("Device Orientation Sensor: last 10 events\n"
                         "\t 1 (ts=130225.900000000, wall=18:02:51.900) 3.00, 0.00, 0.00,\n")
    kq = cb.phan_tich_cam_bien(tho, BAY_GIO)
    assert kq["Orientation Azimuth (°)"] != pytest.approx(math.radians(3.0), abs=1e-9)
    assert kq["Orientation Azimuth (°)"] == pytest.approx(-0.506049676, abs=1e-9)


def test_orientation_uu_tien_hon_rotation_vector_va_doi_sang_radian():
    tho = SENSOR_DUMP + (
        "Orientation Sensor: last 10 events\n"
        "\t 1 (ts=130221.900000000, wall=18:02:47.900) 344.0, -4.75, -0.62, \n")
    kq = cb.phan_tich_cam_bien(tho, BAY_GIO)
    assert kq["Orientation Azimuth (°)"] == pytest.approx(math.radians(344 - 360), abs=1e-9)
    assert kq["Orientation Pitch (°)"] == pytest.approx(math.radians(-4.75), abs=1e-9)


def test_bo_qua_game_rotation_vector():
    """Game RV không tham chiếu bắc từ, azimuth của nó không so được với bộ cũ."""
    tho = ("Recent Sensor events:\n"
           "Game Rotation Vector  Non-wakeup: last 10 events\n"
           "\t 1 (ts=130221.0, wall=18:02:47.0) 0.0, 0.0, 0.70710678, 0.70710678, \n")
    assert cb.phan_tich_cam_bien(tho, BAY_GIO)["Orientation Azimuth (°)"] is None


def test_quy_uoc_dau_cua_android():
    """Quay 90 độ quanh trục z; quy ước Android cho azimuth = -pi/2."""
    az, pitch, roll = cb._goc_tu_rotation_vector([0.0, 0.0, 0.70710678])
    assert az == pytest.approx(-math.pi / 2, abs=1e-6)
    assert (pitch, roll) == (pytest.approx(0.0, abs=1e-6), pytest.approx(0.0, abs=1e-6))


def test_khong_doc_duoc_thi_tra_none_chu_khong_bia_so():
    kq = cb.phan_tich_cam_bien("Sensor List:\n 0x15) ak0991x Magnetometer\n", BAY_GIO)
    assert all(kq[c] is None for c in cb.COT_TU_KE + cb.COT_GOC)


def test_gps_lay_ban_ghi_dau_va_dung_thu_tu_lat_lon():
    kq = cb.phan_tich_gps(LOCATION_DUMP)
    assert kq["GPS Latitude (°)"] == 11.957233
    assert kq["GPS Longitude (°)"] == 108.444842
    assert kq["GPS Altitude (m)"] == 1523.79


def test_gps_thieu_alt_van_lay_duoc_toa_do():
    kq = cb.phan_tich_gps("gps: Location[gps 11.95,108.44 hAcc=8 et=+3m]")
    assert (kq["GPS Latitude (°)"], kq["GPS Altitude (m)"]) == (11.95, None)


def test_thieu_liet_ke_dung_cot_con_rong():
    """Cột vắng mặt trong dict cũng tính là thiếu, không chỉ cột mang giá trị None."""
    gt = {**cb.phan_tich_cam_bien(SENSOR_DUMP, BAY_GIO), **cb.phan_tich_gps("")}
    assert cb.thieu(gt) == cb.COT_GPS
    assert cb.thieu(cb.phan_tich_gps(LOCATION_DUMP)) == cb.COT_TU_KE + cb.COT_GOC


def test_gia_tri_doc_duoc_nam_trong_khoang_cua_bo_ctk45():
    """Chốt đơn vị bằng chính biên độ bộ cũ: azimuth [-3.140, 3.135], alt ~1523 m."""
    gt = {**cb.phan_tich_cam_bien(SENSOR_DUMP, BAY_GIO),
          **cb.phan_tich_gps(LOCATION_DUMP)}
    assert cb.thieu(gt) == []
    assert -3.141 <= gt["Orientation Azimuth (°)"] <= 3.141
    assert abs(gt["Orientation Pitch (°)"]) <= math.pi / 2
    assert 1500 <= gt["GPS Altitude (m)"] <= 1550
    assert 108.0 <= gt["GPS Longitude (°)"] <= 109.0
