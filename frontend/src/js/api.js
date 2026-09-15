// Gọi REST API. Đường dẫn tương đối vì Dashboard do chính máy chủ API phục vụ.

const HET_HAN_MS = 8000;

export class LoiApi extends Error {
  constructor(thongDiep, maHttp, chiTiet = null) {
    super(thongDiep);
    this.name = 'LoiApi';
    this.maHttp = maHttp;
    this.chiTiet = chiTiet;
  }
}

// `detail` có ba dạng: chuỗi (404, 409), object lỗi nghiệp vụ, mảng lỗi schema.
export function moTaLoi(detail, maHttp) {
  if (typeof detail === 'string') return detail;

  if (Array.isArray(detail)) {
    const muc = detail
      .slice(0, 3)
      .map((d) => `${(d.loc || []).slice(1).join('.') || '?'}: ${d.msg}`);
    return `Yêu cầu sai định dạng — ${muc.join('; ')}`;
  }

  if (detail && typeof detail === 'object') {
    if (detail.loi === 'khong_du_ap') {
      return `Không đủ dữ liệu để định vị — chỉ khớp ${detail.so_ap} access point, `
        + `cần ít nhất ${detail.toi_thieu}`;
    }
    if (detail.loi === 'ngoai_pham_vi') {
      const p = detail.pham_vi || {};
      return `Điểm xuất phát (${detail.tu_x}, ${detail.tu_y}) nằm ngoài bản đồ `
        + `(x ${p.x_min}…${p.x_max}, y ${p.y_min}…${p.y_max})`;
    }
    if (detail.loi) return `Máy chủ báo lỗi '${detail.loi}'`;
  }

  return `HTTP ${maHttp}`;
}

async function goi(duongDan, tuyChon = {}) {
  // fetch không tự bỏ cuộc khi máy chủ treo.
  const bo = new AbortController();
  const hen = setTimeout(() => bo.abort(), HET_HAN_MS);
  let tra;
  try {
    tra = await fetch(duongDan, { ...tuyChon, signal: bo.signal });
    if (!tra.ok) {
      let detail = null;
      try {
        detail = (await tra.json()).detail ?? null;
      } catch {
        /* thân không phải JSON, giữ nguyên mã số */
      }
      throw new LoiApi(moTaLoi(detail, tra.status), tra.status, detail);
    }
    // `await` trong try để hẹn giờ phủ cả lúc đọc thân.
    return await tra.json();
  } catch (e) {
    if (e.name === 'AbortError') throw new LoiApi('Máy chủ không trả lời', 0);
    if (e instanceof LoiApi) throw e;
    if (tra) throw new LoiApi('Máy chủ trả dữ liệu không đọc được', tra.status);
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
