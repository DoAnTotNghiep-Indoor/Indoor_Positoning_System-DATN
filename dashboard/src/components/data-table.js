// Bảng dữ liệu dựng từ mảng đối tượng.

export function veBang(el, cot, hang, khiRong = 'Chưa có dữ liệu') {
  el.replaceChildren();

  if (!hang.length) {
    const p = document.createElement('p');
    p.className = 'trong';
    p.textContent = khiRong;
    el.append(p);
    return;
  }

  const bang = document.createElement('table');
  const dau = bang.createTHead().insertRow();
  for (const c of cot) {
    const th = document.createElement('th');
    th.textContent = c.ten;
    if (c.so) th.className = 'so';
    dau.append(th);
  }

  const than = bang.createTBody();
  for (const h of hang) {
    const tr = than.insertRow();
    for (const c of cot) {
      const td = tr.insertCell();
      td.textContent = c.lay(h);
      // `lop(h)`: lớp CSS theo giá trị của dòng, ví dụ tô nhãn.
      td.className = [c.so ? 'so' : '', c.lop?.(h) ?? ''].join(' ').trim();
    }
  }
  el.append(bang);
}
