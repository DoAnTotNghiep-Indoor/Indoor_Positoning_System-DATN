// Biểu đồ nhỏ vẽ bằng canvas.
//
// Không nạp thư viện: cả dashboard chỉ cần một đường, mà thêm gói CDN là thêm
// một thứ phải có mạng mới chạy — máy chấm có thể không nối Internet.

export function veDuong(canvas, gt, { mau = '#2563eb' } = {}) {
  const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1;
  const rong = canvas.parentElement.clientWidth;
  const cao = 64;
  canvas.width = Math.round(rong * dpr);
  canvas.height = Math.round(cao * dpr);
  canvas.style.width = `${rong}px`;
  canvas.style.height = `${cao}px`;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, rong, cao);

  if (gt.length < 2) return;

  const nho = Math.min(...gt);
  const lon = Math.max(...gt);
  // Khoảng giá trị bằng 0 thì chia cho 0 ra NaN và canvas trống trơn, không lỗi.
  const bien = lon - nho || 1;
  const buoc = rong / (gt.length - 1);

  ctx.beginPath();
  gt.forEach((v, i) => {
    const x = i * buoc;
    const y = cao - 6 - ((v - nho) / bien) * (cao - 12);
    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
  });
  ctx.strokeStyle = mau;
  ctx.lineWidth = 1.8;
  ctx.lineJoin = 'round';
  ctx.stroke();
}
