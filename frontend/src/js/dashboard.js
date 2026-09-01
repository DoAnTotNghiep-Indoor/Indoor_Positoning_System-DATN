// Dashboard theo dõi thời gian thực: /health cho trạng thái mô hình, /map cho
// 40 điểm tham chiếu, WS /ws/location cho toạ độ đang chảy về, /predictions
// cho lịch sử.

import { api, LoiApi } from './api.js';
import { KenhViTri } from './websocket.js';
import { SoDoCanvas } from './map-renderer.js';
import { khoangCach } from './coordinate.js';
import { veDuong } from './charts.js';
import { veHuyHieu } from '../components/status-badge.js';
import { theSoLieu } from '../components/metric-card.js';
import { veBang } from '../components/data-table.js';

// Dài hơn hẳn chu kỳ quét 5 giây của app, để một lần quét lỗi không làm biến
// mất marker.
const HET_HAN_THIET_BI_MS = 20000;

const $ = (chon) => document.querySelector(chon);

const so = new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 2 });
const gio = new Intl.DateTimeFormat('vi-VN', {
  hour: '2-digit', minute: '2-digit', second: '2-digit',
});

const trangThai = {
  diem: [],           // 40 điểm tham chiếu từ /map
  thietBi: new Map(), // device_id -> gói mới nhất
  saiLech: [],        // độ dịch giữa toạ độ thô và toạ độ đã gộp, để vẽ đường
};

let soDo;

/** Tên khu vực gần một toạ độ nhất — cùng cách app di động đặt tên vị trí. */
function tenKhuVuc(x, y) {
  if (!trangThai.diem.length) return '';
  let gan = trangThai.diem[0];
  let min = Infinity;
  for (const d of trangThai.diem) {
    const l = khoangCach(d, { x, y });
    if (l < min) { min = l; gan = d; }
  }
  return gan.ten || gan.rp_id;
}

function baoLoi(thongDiep) {
  const el = $('#loi');
  el.textContent = thongDiep ?? '';
  el.hidden = !thongDiep;
}

// --- Trạng thái hệ thống ---

async function napTrangThai() {
  try {
    const t = await api.trangThai();
    $('#the-he-thong').replaceChildren(
      theSoLieu({ nhan: 'Mô hình', giaTri: t.mo_hinh }),
      theSoLieu({ nhan: 'Số đặc trưng', giaTri: t.so_dac_trung, phu: 'BSSID' }),
      theSoLieu({
        nhan: 'Điền khi thiếu', giaTri: `${t.gia_tri_dien_thieu} dBm`,
        phu: 'AP không bắt được',
      }),
      theSoLieu({
        nhan: 'Cửa sổ gộp', giaTri: t.cua_so_gop, phu: 'lần quét',
      }),
    );
  } catch (e) {
    baoLoi(`Không đọc được trạng thái máy chủ: ${e.message}`);
  }
}

// --- Bản đồ và danh sách điểm ---

async function napBanDo() {
  const bd = await api.banDo();
  trangThai.diem = bd.diem_tham_chieu;
  soDo.datDiem(bd.diem_tham_chieu);

  $('#pham-vi').textContent =
    `${so.format(bd.pham_vi.x_max - bd.pham_vi.x_min)} × ` +
    `${so.format(bd.pham_vi.y_max - bd.pham_vi.y_min)} m · ` +
    `${bd.do_thi.so_diem} điểm · ${bd.do_thi.so_canh} cạnh · ` +
    `cạnh dài nhất ${so.format(bd.do_thi.canh_dai_nhat_m)} m`;

  for (const el of [$('#tu-rp'), $('#den-rp')]) {
    el.replaceChildren();
    for (const d of bd.diem_tham_chieu) {
      const o = document.createElement('option');
      o.value = d.rp_id;
      o.textContent = d.ten ? `${d.rp_id} — ${d.ten}` : d.rp_id;
      el.append(o);
    }
  }
  $('#tu-rp').value = 'RP01';
  $('#den-rp').value = 'RP39';
}

// --- Thiết bị đang định vị ---

function nhanViTri(goi) {
  trangThai.thietBi.set(goi.device_id, { ...goi, nhanLuc: Date.now() });
  soDo.capNhatThietBi(goi);

  // Gộp càng ăn thì khoảng cách này càng lớn — thứ trực quan nhất cho thấy hậu
  // xử lý đang làm việc.
  trangThai.saiLech.push(
    khoangCach({ x: goi.x, y: goi.y }, { x: goi.x_smooth, y: goi.y_smooth }),
  );
  if (trangThai.saiLech.length > 60) trangThai.saiLech.shift();

  veThietBi();
  veDuong($('#bieu-do-gop'), trangThai.saiLech);
}

function veThietBi() {
  const nay = Date.now();
  for (const [id, tb] of trangThai.thietBi) {
    if (nay - tb.nhanLuc > HET_HAN_THIET_BI_MS) {
      trangThai.thietBi.delete(id);
      soDo.quenThietBi(id);
    }
  }

  const ds = [...trangThai.thietBi.values()].sort((a, b) => b.nhanLuc - a.nhanLuc);
  $('#so-thiet-bi').textContent = ds.length;

  veBang(
    $('#bang-thiet-bi'),
    [
      { ten: 'Thiết bị', lay: (d) => d.device_id.slice(-8) },
      { ten: 'Khu vực', lay: (d) => tenKhuVuc(d.x_smooth, d.y_smooth) },
      { ten: 'x (m)', so: true, lay: (d) => so.format(d.x_smooth) },
      { ten: 'y (m)', so: true, lay: (d) => so.format(d.y_smooth) },
      { ten: 'AP khớp', so: true, lay: (d) => d.matched_ap },
      { ten: 'Đã gộp', so: true, lay: (d) => d.scan_count },
      { ten: 'Trễ (ms)', so: true, lay: (d) => so.format(d.latency_ms) },
    ],
    ds,
    'Chưa có thiết bị nào gửi dữ liệu lên.',
  );
}

// --- Chỉ đường ---

const CAU_HUONG = {
  bat_dau: 'Đi',
  di_thang: 'Đi thẳng',
  chech_trai: 'Chếch trái',
  chech_phai: 'Chếch phải',
  re_trai: 'Rẽ trái',
  re_phai: 'Rẽ phải',
  quay_dau: 'Quay đầu',
};

async function timDuong() {
  const tu = $('#tu-rp').value;
  const den = $('#den-rp').value;
  const ra = $('#ket-qua-duong');

  try {
    const kq = await api.chiDuong(tu, den);
    soDo.datTuyen(kq.duong_di);

    $('#tom-tat-duong').textContent =
      `${so.format(kq.quang_duong_m)} m · ${kq.so_chang} chặng · ` +
      `${kq.chi_dan.length} bước`;

    ra.replaceChildren();
    // Ghép câu ở client vì API trả `huong` dạng mã, để app di động còn dịch được.
    for (const b of kq.chi_dan) {
      const li = document.createElement('li');
      const dong = document.createElement('span');
      dong.className = 'buoc-chinh';
      dong.textContent = `${CAU_HUONG[b.huong] ?? b.huong} ${so.format(b.khoang_cach_m)} m`;
      const noi = document.createElement('span');
      noi.className = 'buoc-den';
      noi.textContent = b.den_ten ? `tới ${b.den_ten}` : `tới ${b.den_rp}`;
      li.append(dong, noi);
      ra.append(li);
    }
    baoLoi(null);
  } catch (e) {
    soDo.datTuyen(null);
    ra.replaceChildren();
    $('#tom-tat-duong').textContent = '';
    baoLoi(
      e instanceof LoiApi && e.maHttp === 409
        ? `Không có đường từ ${tu} tới ${den}`
        : `Lỗi chỉ đường: ${e.message}`,
    );
  }
}

// --- Lịch sử ---

async function napLichSu() {
  try {
    const ds = await api.lichSu(30);
    veBang(
      $('#bang-lich-su'),
      [
        { ten: 'Lúc', lay: (d) => gio.format(new Date(d.luc)) },
        { ten: 'Khu vực', lay: (d) => tenKhuVuc(d.x_gop, d.y_gop) },
        { ten: 'x (m)', so: true, lay: (d) => so.format(d.x_gop) },
        { ten: 'y (m)', so: true, lay: (d) => so.format(d.y_gop) },
        { ten: 'AP', so: true, lay: (d) => d.so_ap_bat_duoc },
        { ten: 'Mô hình', lay: (d) => d.mo_hinh },
      ],
      ds,
      'Chưa có lần định vị nào được ghi lại.',
    );
  } catch (e) {
    baoLoi(`Không đọc được lịch sử: ${e.message}`);
  }
}

// --- Khởi động ---

async function chay() {
  soDo = new SoDoCanvas($('#so-do'));

  try {
    await napBanDo();
  } catch (e) {
    baoLoi(`Không tải được bản đồ: ${e.message}`);
    return;
  }

  await napTrangThai();
  await napLichSu();
  veThietBi();

  const kenh = new KenhViTri();
  kenh.addEventListener('trang-thai', (e) =>
    veHuyHieu($('#trang-thai-ws'), {
      noi: e.detail.noi,
      chu: e.detail.noi ? 'Đang kết nối' : 'Mất kết nối',
    }),
  );
  kenh.addEventListener('vi-tri', (e) => nhanViTri(e.detail));
  kenh.moKenh();

  // Quét dọn thiết bị đã im lặng, kể cả khi không có gói nào chảy về.
  setInterval(veThietBi, 5000);
  $('#nut-tim-duong').addEventListener('click', timDuong);
  $('#nut-lam-moi').addEventListener('click', napLichSu);
}

chay();
