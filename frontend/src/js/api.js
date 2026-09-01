// Gọi REST API.
//
// Mọi đường dẫn đều tương đối vì Dashboard do chính máy chủ API phục vụ (xem
// app.mount ở backend/main.py): đổi cổng hay đưa lên máy khác vẫn chạy.

const HET_HAN_MS = 8000;

export class LoiApi extends Error {
  constructor(thongDiep, maHttp) {
    super(thongDiep);
    this.name = 'LoiApi';
    this.maHttp = maHttp;
  }
}

async function goi(duongDan, tuyChon = {}) {
  // Máy chủ tắt giữa chừng thì fetch không tự bỏ cuộc, giao diện đứng im.
  const bo = new AbortController();
  const hen = setTimeout(() => bo.abort(), HET_HAN_MS);
  try {
    const tra = await fetch(duongDan, { ...tuyChon, signal: bo.signal });
    if (!tra.ok) {
      // Câu lỗi của FastAPI nói rõ hơn hẳn mã số.
      let chiTiet = `HTTP ${tra.status}`;
      try {
        const than = await tra.json();
        if (than.detail) chiTiet = than.detail;
      } catch {
        /* thân không phải JSON, giữ nguyên mã số */
      }
      throw new LoiApi(chiTiet, tra.status);
    }
    return tra.json();
  } catch (e) {
    if (e.name === 'AbortError') throw new LoiApi('Máy chủ không trả lời', 0);
    if (e instanceof LoiApi) throw e;
    throw new LoiApi('Không kết nối được máy chủ', 0);
  } finally {
    clearTimeout(hen);
  }
}

export const api = {
  trangThai: () => goi('health'),
  banDo: () => goi('map'),
  doThi: () => goi('graph'),

  lichSu: (gioiHan = 50, deviceId = null) => {
    const t = new URLSearchParams({ gioi_han: String(gioiHan) });
    if (deviceId) t.set('device_id', deviceId);
    return goi(`predictions?${t}`);
  },

  chiDuong: (tuRp, denRp) =>
    goi('route', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tu_rp: tuRp, den_rp: denRp }),
    }),
};
