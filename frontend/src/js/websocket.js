// Kênh WebSocket chỉ xem, tự nối lại. Máy chủ phát toạ độ mọi thiết bị lên đây.

const CHO_LAI_DAU_MS = 1000;
const CHO_LAI_TOI_DA_MS = 15000;

export class KenhViTri extends EventTarget {
  constructor() {
    super();
    this._ws = null;
    this._choLai = CHO_LAI_DAU_MS;
    this._hen = null;
    this._dong = false;
  }

  moKenh() {
    // Huỷ hẹn đang chờ, không thì thành hai chuỗi nối lại song song.
    clearTimeout(this._hen);
    this._hen = null;
    this._dong = false;

    // Theo giao thức của trang, không thì bị chặn vì nội dung hỗn hợp.
    const giaoThuc = location.protocol === 'https:' ? 'wss:' : 'ws:';
    this._ws?.close();
    const ws = new WebSocket(`${giaoThuc}//${location.host}/ws/location`);
    this._ws = ws;

    // Socket cũ còn bắn sự kiện sau khi đã có socket mới — bỏ qua.
    const cu = () => this._ws !== ws;

    ws.onopen = () => {
      if (cu()) return;
      this._choLai = CHO_LAI_DAU_MS;
      this._bao('trang-thai', { noi: true });
    };

    ws.onmessage = (e) => {
      if (cu()) return;
      let goi;
      try {
        goi = JSON.parse(e.data);
      } catch {
        return; // gói hỏng thì bỏ, không được làm đứt kênh
      }
      if (goi.loi) return;
      this._bao('vi-tri', goi);
    };

    // Chỉ nối lại ở onclose: trình duyệt bắn cả onerror lẫn onclose.
    ws.onclose = () => {
      if (cu()) return;
      this._bao('trang-thai', { noi: false });
      if (this._dong) return; // đóng có chủ đích thì thôi nối lại
      this._hen = setTimeout(() => this.moKenh(), this._choLai);
      // Giãn dần rồi chặn trần.
      this._choLai = Math.min(this._choLai * 2, CHO_LAI_TOI_DA_MS);
    };
  }

  /** Đóng hẳn: huỷ hẹn đang chờ và không nối lại nữa. */
  dong() {
    this._dong = true;
    clearTimeout(this._hen);
    this._hen = null;
    this._ws?.close();
  }

  _bao(loai, chiTiet) {
    this.dispatchEvent(new CustomEvent(loai, { detail: chiTiet }));
  }
}
