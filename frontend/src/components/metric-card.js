// Thẻ số liệu: một nhãn, một giá trị lớn, một dòng chú thích.

export function theSoLieu({ nhan, giaTri, phu = '' }) {
  const el = document.createElement('div');
  el.className = 'the-so-lieu';
  el.innerHTML = `
    <span class="nhan"></span>
    <strong class="gia-tri"></strong>
    <span class="phu"></span>`;
  // textContent chứ không innerHTML: dữ liệu tới từ máy chủ.
  el.querySelector('.nhan').textContent = nhan;
  el.querySelector('.gia-tri').textContent = giaTri;
  el.querySelector('.phu').textContent = phu;
  return el;
}
