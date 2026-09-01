// Quy đổi toạ độ mét <-> pixel.
//
// Cùng phép biến đổi với `SoDoThat` bên Dart và `tools/trich_ban_do.py`; số gốc
// ở data/reference/ban_do_tang1.json và tests/test_dashboard.py đối chiếu cả ba
// nơi. Lệch nhau thì cùng một toạ độ hiện ở hai chỗ khác nhau trên hai màn
// hình, triệu chứng nhìn y hệt "mô hình đoán sai".

export const SO_DO = {
  anh: 'map/so-do.png',
  rongPx: 1053,
  caoPx: 651,
  gocXPx: 24.5,
  gocYPx: 625.5,
  pxMoiMetX: 11.6279,
  pxMoiMetY: 11.6346,

  // Toạ độ mét của cạnh trái sơ đồ. Có tên riêng chứ không viết thẳng vào công
  // thức: đây là số hạng duy nhất từng nằm trần ở cả ba ngôn ngữ mà không tệp
  // nào khai nó, nên không bài test nào so được.
  gocMetX: -43,
};

// Trục y hướng LÊN: y = 0 ở cạnh dưới ảnh, chỗ cửa ra vào. Kết luận từ hình
// dạng toà nhà chứ không phải quy ước tuỳ chọn — xem tools/trich_ban_do.py.
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
