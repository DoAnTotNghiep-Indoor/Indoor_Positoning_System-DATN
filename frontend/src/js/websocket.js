// Kết nối WebSocket realtime, tự động nối lại.
//
// Dashboard chỉ XEM: mở kênh rồi ngồi nghe, không gửi lần quét nào. Máy chủ
// phát toạ độ của mọi thiết bị cho mọi kênh đang mở, kể cả toạ độ đến từ
// POST /predict.

const CHO_LAI_DAU_MS = 1000;
const CHO_LAI_TOI_DA_MS = 15000;

export class KenhViTri extends EventTarget {
  constructor() {
    super();
    this._ws = null;
    this._choLai = CHO_LAI_DAU_MS;
    this._hen = null;
  }

  moKenh() {
    // Phải theo đúng giao thức của trang, không thì trình duyệt chặn vì nội
    // dung hỗn hợp.
    const giaoThuc = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${giaoThuc}//${location.host}/ws/location`);
    this._ws = ws;

    ws.onopen = () => {
      this._choLai = CHO_LAI_DAU_MS;
      this._bao('trang-thai', { noi: true });
    };

    ws.onmessage = (e) => {
      let goi;
      try {
        goi = JSON.parse(e.data);
      } catch {
        return; // gói hỏng thì bỏ, không được làm đứt kênh
      }
      if (goi.loi) return;
      this._bao('vi-tri', goi);
    };

    // Chỉ nối lại ở onclose: mỗi lần hỏng trình duyệt bắn onerror RỒI onclose,
    // xử lý cả hai là hẹn hai lần và thời gian chờ tăng gấp đôi mỗi vòng.
    ws.onclose = () => {
      this._bao('trang-thai', { noi: false });
      this._hen = setTimeout(() => this.moKenh(), this._choLai);
      // Giãn dần rồi chặn trần.
      this._choLai = Math.min(this._choLai * 2, CHO_LAI_TOI_DA_MS);
    };
  }

  _bao(loai, chiTiet) {
    this.dispatchEvent(new CustomEvent(loai, { detail: chiTiet }));
  }
}
