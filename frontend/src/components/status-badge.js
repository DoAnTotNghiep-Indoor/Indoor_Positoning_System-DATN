// Chấm trạng thái kết nối.

export function veHuyHieu(el, { noi, chu }) {
  el.className = `huy-hieu ${noi ? 'noi' : 'mat'}`;
  el.textContent = chu;
}
