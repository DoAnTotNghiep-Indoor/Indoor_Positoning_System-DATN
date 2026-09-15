// Biểu đồ đường bằng canvas, không thư viện CDN để chạy được khi không có mạng.

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
  // Tránh chia cho 0 khi mọi giá trị bằng nhau.
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
