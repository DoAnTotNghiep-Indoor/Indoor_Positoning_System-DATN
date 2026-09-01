// Vẽ sơ đồ mặt bằng, điểm tham chiếu, thiết bị đang định vị và tuyến chỉ đường.

import { SO_DO, metSangKhung } from './coordinate.js';

const MAU = {
  diem: '#94a3b8',
  diemTuyen: '#e08a1e',
  tuyen: '#e08a1e',
  thietBi: '#2563eb',
  vet: 'rgba(37, 99, 235, 0.28)',
  chu: '#475569',
};

// Số vị trí cũ giữ lại mỗi thiết bị để vẽ vệt đã đi.
const DAI_VET = 25;

export class SoDoCanvas {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.diem = [];
    this.thietBi = new Map(); // device_id -> { x, y, vet: [] }
    this.tuyen = null;

    this.anh = new Image();
    this.anh.src = SO_DO.anh;
    this.anh.onload = () => this.ve();

    // ResizeObserver chứ không nghe resize của cửa sổ: canvas còn co giãn khi
    // cột bên cạnh đổi bề rộng, lúc đó cửa sổ không đổi kích thước nào cả.
    new ResizeObserver(() => this.ve()).observe(canvas.parentElement);
  }

  datDiem(ds) {
    this.diem = ds;
    this.ve();
  }

  datTuyen(duongDi) {
    this.tuyen = duongDi;
    this.ve();
  }

  capNhatThietBi(goi) {
    const cu = this.thietBi.get(goi.device_id);
    const vet = cu ? cu.vet : [];
    vet.push({ x: goi.x_smooth, y: goi.y_smooth });
    if (vet.length > DAI_VET) vet.shift();
    this.thietBi.set(goi.device_id, {
      x: goi.x_smooth,
      y: goi.y_smooth,
      luc: Date.now(),
      vet,
    });
    this.ve();
  }

  quenThietBi(deviceId) {
    this.thietBi.delete(deviceId);
    this.ve();
  }

  ve() {
    const { canvas, ctx } = this;
    const rongCss = canvas.parentElement.clientWidth;
    if (rongCss <= 0) return;
    const caoCss = (rongCss * SO_DO.caoPx) / SO_DO.rongPx;

    // Nhân devicePixelRatio rồi thu lại bằng CSS, không thì nét vẽ răng cưa
    // trên màn HiDPI.
    const dpr = window.devicePixelRatio || 1;
    canvas.width = Math.round(rongCss * dpr);
    canvas.height = Math.round(caoCss * dpr);
    canvas.style.width = `${rongCss}px`;
    canvas.style.height = `${caoCss}px`;

    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, rongCss, caoCss);

    if (this.anh.complete && this.anh.naturalWidth) {
      ctx.globalAlpha = 0.6;
      ctx.drawImage(this.anh, 0, 0, rongCss, caoCss);
      ctx.globalAlpha = 1;
    }

    const q = (d) => metSangKhung(d.x, d.y, rongCss);
    const tren = new Set(this.tuyen?.map((d) => d.rp_id) ?? []);

    for (const d of this.diem) {
      const p = q(d);
      ctx.beginPath();
      ctx.arc(p.x, p.y, tren.has(d.rp_id) ? 5 : 3.5, 0, Math.PI * 2);
      ctx.fillStyle = tren.has(d.rp_id) ? MAU.diemTuyen : MAU.diem;
      ctx.fill();
    }

    if (this.tuyen?.length > 1) {
      ctx.beginPath();
      this.tuyen.forEach((d, i) => {
        const p = q(d);
        i === 0 ? ctx.moveTo(p.x, p.y) : ctx.lineTo(p.x, p.y);
      });
      ctx.strokeStyle = MAU.tuyen;
      ctx.lineWidth = 2.5;
      ctx.lineJoin = 'round';
      ctx.stroke();
    }

    for (const [id, tb] of this.thietBi) {
      if (tb.vet.length > 1) {
        ctx.beginPath();
        tb.vet.forEach((v, i) => {
          const p = q(v);
          i === 0 ? ctx.moveTo(p.x, p.y) : ctx.lineTo(p.x, p.y);
        });
        ctx.strokeStyle = MAU.vet;
        ctx.lineWidth = 2;
        ctx.stroke();
      }

      const p = q(tb);
      ctx.beginPath();
      ctx.arc(p.x, p.y, 7, 0, Math.PI * 2);
      ctx.fillStyle = MAU.thietBi;
      ctx.fill();
      ctx.strokeStyle = '#fff';
      ctx.lineWidth = 2.5;
      ctx.stroke();

      ctx.fillStyle = MAU.chu;
      ctx.font = '11px system-ui, sans-serif';
      ctx.textAlign = 'center';
      // Mã thiết bị dài 24 ký tự, để nguyên là nhãn chồng lên nhau.
      ctx.fillText(id.slice(-6), p.x, p.y - 11);
    }
  }
}
