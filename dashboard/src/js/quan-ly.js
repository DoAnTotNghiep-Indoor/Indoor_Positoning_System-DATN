// Trang Quản lý: sơ đồ và số thiết bị đang sử dụng ứng dụng, lấy từ `/predictions` như
// trang giám sát; bảng AP lạ lấy từ `/ap-la`.

import { api } from './api.js';
import { SoDoCanvas } from './map-renderer.js';
import { theSoLieu } from '../components/metric-card.js';
import { veHuyHieu } from '../components/status-badge.js';
import { veBang } from '../components/data-table.js';

// Cùng nhịp và ngưỡng với trang giám sát.
const CHU_KY_MS = 2000;
const HET_HAN_MS = 20000;
// AP lạ đổi chậm, hỏi thưa hơn.
const CHU_KY_AP_LA_MS = 10000;

const $ = (chon) => document.querySelector(chon);
const soDo = new SoDoCanvas($('#so-do'));
/** device_id -> lúc nhận lần định vị gần nhất. */
const lanCuoi = new Map();

function veDem() {
  $('#the-dem').replaceChildren(
    theSoLieu({ nhan: 'Đang sử dụng', giaTri: String(lanCuoi.size), phu: 'thiết bị' }),
  );
}

async function khoiDong() {
  try {
    soDo.datDiem((await api.banDo()).diem_tham_chieu);
  } catch {
    /* thiếu điểm tham chiếu vẫn vẽ được sơ đồ và chấm */
  }
  veDem();

  // Lượt hỏi đầu chỉ lấy mốc: bản ghi cũ không phải thiết bị đang dùng.
  let moc = null;
  setInterval(async () => {
    try {
      const ds = (await api.lichSu(50)).map((d) => ({ ...d, t: Date.parse(d.luc) }));
      veHuyHieu($('#trang-thai-ket-noi'), { noi: true, chu: `Cập nhật ${CHU_KY_MS / 1000} s` });
      if (moc !== null) {
        for (const d of ds.filter((d) => d.t > moc).sort((a, b) => a.t - b.t)) {
          soDo.capNhatThietBi({ device_id: d.device_id, x_smooth: d.x_gop, y_smooth: d.y_gop });
          lanCuoi.set(d.device_id, Date.now());
        }
      }
      moc = Math.max(moc ?? 0, ...ds.map((d) => d.t));
    } catch {
      veHuyHieu($('#trang-thai-ket-noi'), { noi: false, chu: 'Mất kết nối' });
    }
    for (const [id, luc] of lanCuoi) {
      if (Date.now() - luc > HET_HAN_MS) {
        lanCuoi.delete(id);
        soDo.quenThietBi(id);
      }
    }
    veDem();
  }, CHU_KY_MS);
}

const so = new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 1 });
const gio = new Intl.DateTimeFormat('vi-VN', { dateStyle: 'short', timeStyle: 'medium' });
let apLa = null;

function veApLa() {
  if (!apLa) return;
  const { so_lan_quet: tong, nguong_thuong_xuyen: nguong, ap } = apLa;
  const moi = ap.filter((a) => !a.trong_du_lieu);
  const moiThuongXuyen = moi.filter((a) => a.ti_le >= nguong && !a.mac_ngau_nhien);
  $('#the-ap-la').replaceChildren(
    theSoLieu({ nhan: 'Lần quét đã nhận', giaTri: so.format(tong), phu: 'từ mọi thiết bị' }),
    theSoLieu({ nhan: 'AP lạ', giaTri: String(ap.length), phu: `${moi.length} AP mới` }),
    theSoLieu({
      nhan: 'AP mới thường xuyên',
      giaTri: String(moiThuongXuyen.length),
      phu: `≥ ${so.format(nguong)}% lần quét, MAC cố định`,
    }),
  );
  const chiMoi = $('#chi-ap-moi').checked;
  veBang(
    $('#bang-ap-la'),
    [
      { ten: 'BSSID', lay: (a) => a.bssid, lop: () => 'ma' },
      {
        ten: 'Loại',
        lay: (a) => (a.trong_du_lieu ? 'Đã có, bị loại' : 'Mới'),
        lop: (a) => (a.trong_du_lieu ? 'nhan-cu' : 'nhan-moi'),
      },
      { ten: 'MAC', lay: (a) => (a.mac_ngau_nhien ? 'Ngẫu nhiên' : 'Cố định') },
      {
        ten: 'Tỉ lệ lần quét',
        so: true,
        lay: (a) => `${so.format(a.ti_le)}%`,
        lop: (a) => (a.ti_le >= nguong ? 'thuong-xuyen' : ''),
      },
      { ten: 'Lần quét', so: true, lay: (a) => so.format(a.so_lan) },
      { ten: 'RSSI TB (dBm)', so: true, lay: (a) => so.format(a.rssi_tb) },
      { ten: 'Mạnh nhất (dBm)', so: true, lay: (a) => so.format(a.rssi_manh_nhat) },
      { ten: 'Lần đầu', lay: (a) => gio.format(new Date(a.lan_dau)) },
      { ten: 'Lần cuối', lay: (a) => gio.format(new Date(a.lan_cuoi)) },
    ],
    chiMoi ? moi : ap,
    chiMoi ? 'Chưa gặp AP mới nào.' : 'Chưa gặp AP lạ nào.',
  );
}

async function capNhatApLa() {
  try {
    apLa = await api.apLa();
    veApLa();
  } catch {
    /* lần sau hỏi lại; huy hiệu kết nối đã do vòng định vị báo */
  }
}

$('#chi-ap-moi').addEventListener('change', veApLa);
capNhatApLa();
setInterval(capNhatApLa, CHU_KY_AP_LA_MS);
khoiDong();
