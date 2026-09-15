// Quy đổi mét sang pixel — cùng phép với `SoDoThat` (Dart) và
// `tools/trich_ban_do.py`.

export const SO_DO = {
  anh: 'map/so-do.png',
  rongPx: 1053,
  caoPx: 651,
  gocXPx: 24.5,
  gocYPx: 625.5,
  pxMoiMetX: 11.6279,
  pxMoiMetY: 11.6346,

  // Toạ độ mét của cạnh trái sơ đồ.
  gocMetX: -43,
};

// Trục y hướng lên: y = 0 ở cạnh dưới ảnh, chỗ cửa ra vào.
function metSangPixel(x, y) {
  return {
    x: SO_DO.gocXPx + (x - SO_DO.gocMetX) * SO_DO.pxMoiMetX,
    y: SO_DO.gocYPx - y * SO_DO.pxMoiMetY,
  };
}

/** Mét sang toạ độ trong khung vẽ rộng `rong` pixel, giữ nguyên tỉ lệ ảnh. */
export function metSangKhung(x, y, rong) {
  const s = rong / SO_DO.rongPx;
  const p = metSangPixel(x, y);
  return { x: p.x * s, y: p.y * s };
}

export function khoangCach(a, b) {
  return Math.hypot(a.x - b.x, a.y - b.y);
}
