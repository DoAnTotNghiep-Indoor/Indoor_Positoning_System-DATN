"""Đưa ảnh khu vực và ảnh toàn cảnh vào app, dạng AVIF.

    python -m tools.anh_app tmp/pics

AVIF vì cùng dung lượng thì giữ chi tiết hơn WebP (ảnh toàn cảnh thu về 8192 px: AVIF
chất lượng 80 và WebP chất lượng 90 đều khoảng 2 MB). Flutter trên Android giải
mã AVIF qua bộ giải mã của hệ điều hành, cần Android 12 trở lên; đề tài dùng
máy đời mới nên chấp nhận.

Ảnh nhóm 15 chụp ([MOI]) mã hoá lại từ bản gốc trong thư mục nguồn, cạnh dài
2048 px. Ảnh CTK45 không còn bản gốc nên đổi thẳng từ WebP đang có, giữ kích
thước. Ảnh toàn cảnh giữ nguyên độ phân giải gốc (9216–10240 px ngang) và tỉ lệ:
ảnh toàn cảnh của Google Camera cắt mất đỉnh trần và sàn, trình xem khai vùng cắt
nên không cần độn. Riêng ảnh toàn cảnh ghi WebP chất lượng 90: bộ giải mã AV1 của
vivo X300 (cả MediaTek lẫn dav1d) từ chối ảnh rộng quá 8192 px, còn WebP do
Flutter tự giải mã, nhận tới 16383 px.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageOps

ANH = Path("mobile/assets/images")
TOAN_CANH = Path("mobile/assets/panorama")
CHAT_LUONG = 80

# (thư mục, số thứ tự) -> tên ảnh gốc của nhóm 15.
MOI = {
    ("tv3_4", 1): "tv3", ("tv3_4", 2): "tv4",
    ("hoc_nhom", 1): "hocnhom",
    ("nghiep_vu_1", 1): "truocnghiepvu1",
    ("thang_may", 1): "thangmay",
    ("xuong_tv1_2", 1): "duongxuongtv12", ("xuong_tv1_2", 2): "tv12",
    ("nha_sach", 1): "khonggianphongsach", ("nha_sach", 2): "khonggianphongsach1",
    ("nha_sach", 3): "truocphongsach", ("nha_sach", 4): "notebanquaybentrongphongsach",
    ("wc_trai", 2): "truocwcphiatv34", ("wc_phai", 2): "truocwcphiahoitruong",
    ("can_tin", 3): "duongxuongcanten",
    ("ban_thu_thu", 4): "manhinhtruocquay",
    ("cua_chinh", 3): "chusanhchinh",
}

PANO = {
    "sanh_cua_chinh": "pano-sanhduoilentvorhoitruong",
    "tu_hoc_tap_chi": "panocauthangphiatapchi",
    "tu_hoc_loi_ra": "panophiaduoicauthangphialoirasau",
    "quay_thu_thu": "panothuthu",
    "hoc_nhom": "panotruocphongdoc",
}


def _ghi(im: Image.Image, canh: int | None, ra: Path) -> None:
    im = ImageOps.exif_transpose(im).convert("RGB")
    if canh:
        im.thumbnail((canh, canh), Image.LANCZOS)
    # convert("RGB") và không truyền exif: ảnh gốc có toạ độ GPS, không được lọt ra.
    if ra.suffix == ".webp":
        im.save(ra, "WEBP", quality=90, method=6)
    else:
        im.save(ra, "AVIF", quality=CHAT_LUONG)


def main() -> None:
    goc = Path(sys.argv[1])
    for thu_muc in sorted(p for p in ANH.iterdir() if p.is_dir()):
        for cu in sorted(thu_muc.glob("*.webp")):
            ten = MOI.get((thu_muc.name, int(cu.stem)))
            _ghi(Image.open(goc / f"{ten}.jpg" if ten else cu), 2048, cu.with_suffix(".avif"))
            cu.unlink()
        print(f"{thu_muc.name}: {len(list(thu_muc.glob('*.avif')))} ảnh")

    TOAN_CANH.mkdir(parents=True, exist_ok=True)
    for cu in TOAN_CANH.glob("*.avif"):
        cu.unlink()
    for ma, ten in PANO.items():
        ra = TOAN_CANH / f"{ma}.webp"
        _ghi(Image.open(goc / f"{ten}.jpg"), None, ra)
        w, h = Image.open(ra).size
        print(f"{ma}: {w}x{h}, {ra.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
