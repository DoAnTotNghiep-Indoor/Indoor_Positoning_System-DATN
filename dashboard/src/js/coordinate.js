// Quy đổi toạ độ lưới sang pixel — cùng phép với `SoDoThat` (Dart) và
// `tools/ve_so_do_tang1.py`. Sơ đồ SVG đặt trong khung pixel của Map.png cũ;
// `khung*` là viewBox của nó.

export const SO_DO = {
  anh: 'so_do_tang1.svg',
  khungX: -580.2,
  khungY: -282.0,
  khungRong: 2209.3,
  khungCao: 1547.4,
  gocXPx: 24.5,
  gocYPx: 625.5,
  pxMoiDonViX: 11.6279,
  pxMoiDonViY: 11.6346,

  // Toạ độ lưới của gốc pixel x.
  gocX: -43,
};

// Trục y hướng lên: y = 0 ở cửa chính.
function sangPixel(x, y) {
  return {
    x: SO_DO.gocXPx + (x - SO_DO.gocX) * SO_DO.pxMoiDonViX,
    y: SO_DO.gocYPx - y * SO_DO.pxMoiDonViY,
  };
}

/** Toạ độ lưới sang toạ độ trong khung vẽ rộng `rong` pixel, giữ nguyên tỉ lệ sơ đồ. */
export function metSangKhung(x, y, rong) {
  const s = rong / SO_DO.khungRong;
  const p = sangPixel(x, y);
  return { x: (p.x - SO_DO.khungX) * s, y: (p.y - SO_DO.khungY) * s };
}

export function khoangCach(a, b) {
  return Math.hypot(a.x - b.x, a.y - b.y);
}
