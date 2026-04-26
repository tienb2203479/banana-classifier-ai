const fileInput = document.getElementById('fileInput');
const previewImage = document.getElementById('previewImage');
const uploadPrompt = document.getElementById('uploadPrompt');
const predictBtn = document.getElementById('predictBtn');
const statusEl = document.getElementById('status');
const resultEl = document.getElementById('result');
const historyEl = document.getElementById('history');
const tabHome = document.getElementById('tabHome');
const tabHistory = document.getElementById('tabHistory');
const homeSection = document.getElementById('homeSection');
const historySection = document.getElementById('historySection');
let currentFile = null;

function toDisplayLabel(label) {
  const map = {
    Chin: 'Chín',
    Xanh: 'Xanh',
    Nai: 'Nải',
    Nải: 'Nải',
    Trai: 'Trái',
    Trái: 'Trái',
    Buong: 'Buồng',
    Buồng: 'Buồng',
    'Chuối già': 'Chuối già',
    'Chuối cau': 'Chuối cau',
    'Chuối sáp': 'Chuối sáp',
    'Chuối táo quạ': 'Chuối táo quạ',
    'Chuối xiêm': 'Chuối xiêm',
  };
  return map[label] || label;
}


function deriveSweetnessLevel(text) {
  const value = String(text || '').toLowerCase();
  if (value.includes('cao') || value.includes('đậm') || value.includes('dam')) return 'Cao';
  if (value.includes('vừa') || value.includes('vua')) return 'Trung bình';
  return 'Thấp';
}


function renderLoadingResult() {
  resultEl.className = 'glass p-7 md:p-8 rounded-[2.5rem] space-y-6 min-h-[500px] h-full';
  resultEl.innerHTML = `
    <div class="h-full min-h-[430px] flex flex-col items-center justify-center text-center text-gray-500">
      <div class="relative mb-5">
        <div class="w-20 h-20 rounded-full border-4 border-yellow-200 border-t-yellow-500 animate-spin"></div>
        <div class="absolute inset-0 flex items-center justify-center text-2xl">🍌</div>
      </div>
      <p class="text-2xl font-bold text-gray-700">Đang nhận dạng...</p>
      <p class="mt-2 text-sm">AI đang phân tích ảnh ở card này, vui lòng chờ trong giây lát.</p>
    </div>
  `;
}


function renderEmptyResult() {
  resultEl.className = 'glass p-7 md:p-8 rounded-[2.5rem] space-y-6 min-h-[500px] h-full';
  resultEl.innerHTML = `
    <div class="h-full min-h-[430px] flex flex-col items-center justify-center text-center text-gray-500">
      <div class="w-24 h-24 rounded-[28px] bg-gradient-to-br from-yellow-200 to-orange-300 flex items-center justify-center shadow-xl mb-4 rotate-[-8deg] ring-4 ring-white/70 text-5xl">
        <span class="drop-shadow-[0_1px_1px_rgba(0,0,0,0.25)]">🍌</span>
      </div>
      <p class="text-2xl font-bold text-gray-700">Sẵn sàng nhận dạng</p>
      <p class="mt-2 text-sm">Tải ảnh ở card bên trái rồi bấm "NHẬN DẠNG" để xem kết quả chi tiết.</p>
    </div>
  `;
}

fileInput.addEventListener('change', () => {
  const file = fileInput.files?.[0];
  currentFile = file || null;
  if (!file) {
    previewImage.classList.add('hidden');
    previewImage.src = '';
    uploadPrompt.classList.remove('hidden');
    return;
  }
  previewImage.src = URL.createObjectURL(file);
  previewImage.classList.remove('hidden');
  uploadPrompt.classList.add('hidden');
});

predictBtn.addEventListener('click', async () => {
  if (!currentFile) {
    statusEl.textContent = 'Hãy chọn ảnh trước khi nhận dạng.';
    return;
  }

  statusEl.textContent = 'Đang phân tích ảnh và nhận dạng...';
  renderLoadingResult();
  const formData = new FormData();
  formData.append('file', currentFile);

  try {
    const response = await fetch('/api/predict', { method: 'POST', body: formData });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || 'Prediction failed');
    }
    renderResult(payload.item);
    await fetchHistory();
    statusEl.textContent = 'Nhận dạng thành công. Ảnh đã được lưu an toàn trên máy chủ.';
  } catch (error) {
    statusEl.textContent = `Lỗi: ${error.message}`;
  }
});

function setActiveTab(tab) {
  const isHome = tab === 'home';
  homeSection.classList.toggle('hidden', !isHome);
  historySection.classList.toggle('hidden', isHome);

  tabHome.className = `glass px-5 py-2 rounded-full text-sm font-bold transition ${isHome ? 'text-gray-800 bg-white/90' : 'text-gray-500'}`;
  tabHistory.className = `glass px-5 py-2 rounded-full text-sm font-bold transition ${!isHome ? 'text-gray-800 bg-white/90' : 'text-gray-500'}`;
}

tabHome.addEventListener('click', () => setActiveTab('home'));
tabHistory.addEventListener('click', async () => {
  await fetchHistory();
  setActiveTab('history');
});

function asPercent(v) {
  return `${(v * 100).toFixed(1)}%`;
}

function renderResult(item) {
  const p = item.predictions;
  const info = item.banana_info;
  const quality = item.image_quality || {};
  const warnings = item.warnings || [];
  const dacDiem = info.dac_diem || 'Hình dáng hài hòa, vỏ mịn và dễ nhận biết theo từng giống.';
  const huongVi = info.do_ngot || 'Ngọt thanh, thơm nhẹ và dễ ăn.';
  const doNgotNhanh = deriveSweetnessLevel(huongVi);
  const thongTinCoBan = info.ten_goi_khac || 'Tên gọi phổ biến theo vùng miền.';
  const goiYSuDung = info.goi_y_su_dung || 'Phù hợp ăn trực tiếp hoặc làm sinh tố.';
  const baoQuan = info.bao_quan || 'Bảo quản nơi thoáng mát, tránh ánh nắng trực tiếp.';
  const dinhDuongText = info.dinh_duong || 'Giàu kali và chất xơ, tốt cho tiêu hóa.';
  const warningHtml = warnings.length
    ? `<div class="mt-2 rounded-2xl border border-rose-200 bg-rose-50 text-rose-700 text-sm p-3">${warnings.map((w) => `<div>• ${w}</div>`).join('')}</div>`
    : '';
  const dinhDuongHighlights = Array.isArray(info.dinh_duong_highlights) ? info.dinh_duong_highlights : [
    'Giàu kali',
    'Cung cấp năng lượng nhanh',
    'Tốt cho tiêu hóa',
  ];
  const trangThaiLabel = toDisplayLabel(p.trang_thai.label);
  const dangLabel = toDisplayLabel(p.dang.label);
  const nenAn = ['Chín', 'Chin'].includes(p.trang_thai.label) ? 'Nên dùng ngay để cảm nhận vị ngon trọn vẹn.' : 'Nên để thêm 1-2 ngày để hương vị đạt độ chín lý tưởng.';
  const phuHop = info.goi_y_su_dung || 'Phù hợp ăn trực tiếp hoặc làm sinh tố.';
  const anhThamChieu = item.reference_image_url || item.image_url;

  resultEl.className = 'glass p-7 md:p-8 rounded-[2.5rem] space-y-6 min-h-[430px]';
  resultEl.innerHTML = `
    <div class="text-xs font-bold uppercase tracking-wider text-yellow-600">Kết quả nhận diện</div>
    <div class="glass p-6 rounded-[2.5rem] flex flex-col md:flex-row justify-between items-start md:items-center gap-4 shadow-sm">
      <div class="flex items-center gap-4">
        <div class="w-24 h-24 rounded-[2rem] overflow-hidden shadow-xl border-4 border-white relative">
          <img src="${item.image_url}" alt="banana" class="w-full h-full object-cover" />
        </div>
        <div>
          <span class="px-3 py-1 ${item.can_review ? 'bg-red-100 text-red-600' : 'bg-green-100 text-green-600'} rounded-full text-xs font-bold">
            ${item.can_review ? 'CẦN KIỂM TRA' : 'NHẬN DIỆN TỐT'}
          </span>
          <h3 class="text-4xl font-bold text-gray-800">${toDisplayLabel(p.loai.label)}</h3>
          <p class="text-base text-gray-700 font-extrabold mt-1">Độ tin cậy: <span class="text-emerald-600 text-xl">${asPercent(p.loai.confidence)}</span></p>
        </div>
      </div>
      <div class="w-full md:w-auto text-right">
        <p class="text-sm text-gray-400 font-semibold uppercase tracking-widest">Độ ngọt</p>
        <p class="text-3xl font-extrabold text-orange-500">${doNgotNhanh}</p>
      </div>
    </div>

    <div class="text-xs font-bold uppercase tracking-wider text-yellow-600">Thông tin nhanh</div>
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div class="bg-white/40 p-5 rounded-3xl text-center border border-white/50">
        <i class="fas fa-circle-check text-yellow-500 mb-2"></i>
        <p class="text-xs text-gray-400 font-bold uppercase">Dạng</p>
        <p class="font-bold text-gray-800">${dangLabel}</p>
        <p class="text-sm font-extrabold text-emerald-600 mt-1">${asPercent(p.dang.confidence)}</p>
      </div>
      <div class="bg-white/40 p-5 rounded-3xl text-center border border-white/50">
        <i class="fas fa-sun text-orange-500 mb-2"></i>
        <p class="text-xs text-gray-400 font-bold uppercase">Độ chín</p>
        <p class="font-bold text-gray-800">${trangThaiLabel}</p>
        <p class="text-sm font-extrabold text-emerald-600 mt-1">${asPercent(p.trang_thai.confidence)}</p>
      </div>
      <div class="bg-white/40 p-5 rounded-3xl text-center border border-white/50">
        <i class="fas fa-fire text-red-500 mb-2"></i>
        <p class="text-xs text-gray-400 font-bold uppercase">Calo (ước lượng)</p>
        <p class="font-bold text-gray-800">${info.calo_uoc_luong || '89 kcal / 100g'}</p>
      </div>
    </div>

    <div class="grid md:grid-cols-2 gap-6">
      <div class="bg-yellow-400/10 border border-yellow-200 p-6 rounded-[2.5rem]">
        <h4 class="font-extrabold text-yellow-700 text-sm mb-4 uppercase tracking-widest"><i class="fas fa-lightbulb mr-2"></i>Gợi ý thông minh</h4>
        <ul class="space-y-3">
          <li class="text-sm font-semibold flex items-start gap-2">
            <i class="fas fa-utensils text-yellow-500 mt-1"></i> ${nenAn}
          </li>
          <li class="text-sm font-semibold flex items-start gap-2">
            <i class="fas fa-blender text-yellow-500 mt-1"></i> Phù hợp dùng: ${phuHop}
          </li>
        </ul>
      </div>

      <div class="bg-green-500/10 border border-green-200 p-6 rounded-[2.5rem]">
        <h4 class="font-extrabold text-green-700 text-sm mb-4 uppercase tracking-widest"><i class="fas fa-heart-pulse mr-2"></i>Giá trị sức khỏe</h4>
        <div class="flex flex-wrap gap-2">
          <span class="bg-white px-3 py-1.5 rounded-xl text-[11px] font-bold text-green-700 shadow-sm">💪 ${dinhDuongHighlights[0] || 'Giàu kali, tốt cho tim mạch'}</span>
          <span class="bg-white px-3 py-1.5 rounded-xl text-[11px] font-bold text-green-700 shadow-sm">⚡ ${dinhDuongHighlights[1] || 'Cung cấp năng lượng nhanh'}</span>
          <span class="bg-white px-3 py-1.5 rounded-xl text-[11px] font-bold text-green-700 shadow-sm">🥗 ${dinhDuongHighlights[2] || 'Tốt cho tiêu hóa'}</span>
        </div>
      </div>
    </div>

    <div class="rounded-[2rem] overflow-hidden bg-white/45 border border-white/60 p-6 text-sm text-gray-700 leading-relaxed space-y-2">
      <h4 class="font-extrabold text-gray-700 text-sm uppercase tracking-widest mb-2">Mô tả chi tiết loại chuối</h4>
      <p><span class="font-bold">Tên gọi khác:</span> ${thongTinCoBan}</p>
      <p><span class="font-bold">Đặc điểm:</span> ${dacDiem}</p>
      <p><span class="font-bold">Độ ngọt / Hương vị:</span> ${huongVi}</p>
      <p><span class="font-bold">Dinh dưỡng:</span> ${dinhDuongText}</p>
      <p><span class="font-bold">Cách dùng:</span> ${goiYSuDung}</p>
      <p><span class="font-bold">Bảo quản:</span> ${baoQuan}</p>
    </div>

    <div class="text-xs font-bold uppercase tracking-wider text-yellow-600">Ảnh tham chiếu</div>
    <div class="rounded-3xl border border-white/50 bg-white/40 p-3">
      <a href="${anhThamChieu}" target="_blank" rel="noopener noreferrer" class="block group">
        <img src="${anhThamChieu}" alt="Ảnh tham chiếu" class="w-full h-52 object-cover rounded-2xl group-hover:opacity-95 transition" />
        <p class="text-xs text-gray-500 font-semibold mt-2 text-right">Bấm vào ảnh để xem kích thước lớn</p>
      </a>
    </div>

    ${warningHtml}

  `;
}

async function fetchHistory() {
  const response = await fetch('/api/history');
  const payload = await response.json();
  const items = payload.items || [];

  if (!items.length) {
    historyEl.className = 'text-gray-500 font-semibold';
    historyEl.textContent = 'Chưa có lịch sử';
    return;
  }

  historyEl.className = 'grid md:grid-cols-2 gap-3';
  historyEl.innerHTML = items.map((item) => `
    <article class="rounded-2xl border border-yellow-100 bg-white/60 p-3 flex gap-3">
      <img src="${item.image_url}" alt="uploaded" class="w-24 h-24 object-cover rounded-xl" />
      <div class="min-w-0">
        <div class="text-lg font-bold text-gray-800">${toDisplayLabel(item.predictions.loai.label)}</div>
        <div class="text-sm text-gray-500">Dạng: ${toDisplayLabel(item.predictions.dang.label)} · Trạng thái: ${toDisplayLabel(item.predictions.trang_thai.label)}</div>
        <div class="text-sm text-gray-500 mt-1">${new Date(item.created_at).toLocaleString()} · ${asPercent(item.predictions.loai.confidence)} độ tin cậy</div>
      </div>
    </article>
  `).join('');
}

fetchHistory();
renderEmptyResult();
setActiveTab('home');
