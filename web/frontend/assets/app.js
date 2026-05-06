const fileInput = document.getElementById('fileInput');
const previewImage = document.getElementById('previewImage');
const uploadPrompt = document.getElementById('uploadPrompt');
const uploadArea = document.getElementById('uploadArea');
const predictBtn = document.getElementById('predictBtn');
const statusEl = document.getElementById('status');
const resultEl = document.getElementById('result');
const historyEl = document.getElementById('history');
const tabHome = document.getElementById('tabHome');
const tabHistory = document.getElementById('tabHistory');
const homeSection = document.getElementById('homeSection');
const historySection = document.getElementById('historySection');
const filePickerModal = document.getElementById('filePickerModal');
const cameraBtnOption = document.getElementById('cameraBtnOption');
const galleryBtnOption = document.getElementById('galleryBtnOption');
const closeFilePickerBtn = document.getElementById('closeFilePickerBtn');
const alertContainer = document.getElementById('alertContainer');
let currentFile = null;
let historyItems = [];

// Toast/Alert notification system
function showAlert(message, type = 'error', duration = 5000) {
  const alertEl = document.createElement('div');
  
  // Determine styling based on type
  let bgColor, borderColor, textColor, icon;
  if (type === 'error') {
    bgColor = 'bg-red-100';
    borderColor = 'border-red-400';
    textColor = 'text-red-800';
    icon = '❌';
  } else if (type === 'success') {
    bgColor = 'bg-green-100';
    borderColor = 'border-green-400';
    textColor = 'text-green-800';
    icon = '✅';
  } else if (type === 'warning') {
    bgColor = 'bg-yellow-100';
    borderColor = 'border-yellow-400';
    textColor = 'text-yellow-800';
    icon = '⚠️';
  } else {
    bgColor = 'bg-blue-100';
    borderColor = 'border-blue-400';
    textColor = 'text-blue-800';
    icon = 'ℹ️';
  }
  
  alertEl.className = `${bgColor} ${borderColor} ${textColor} border-l-4 p-4 mb-3 rounded-lg shadow-lg flex items-start gap-3 alert-enter`;
  alertEl.innerHTML = `
    <span class="text-xl flex-shrink-0 mt-0.5">${icon}</span>
    <div class="flex-1">
      <p class="font-semibold text-sm md:text-base">${message}</p>
    </div>
    <button class="flex-shrink-0 text-xl hover:opacity-70 transition" onclick="this.parentElement.parentElement.remove()">×</button>
  `;
  
  alertContainer.appendChild(alertEl);
  
  // Auto-remove after duration (only for non-error messages)
  if (type !== 'error') {
    setTimeout(() => {
      alertEl.classList.remove('alert-enter');
      alertEl.classList.add('alert-exit');
      setTimeout(() => alertEl.remove(), 300);
    }, duration);
  }
}

function validateImageFile(file) {
  if (!file) return null;
  
  const validTypes = ['image/jpeg', 'image/png'];
  const validExtensions = ['.jpg', '.jpeg', '.png'];
  
  // Check extension
  const fileName = file.name.toLowerCase();
  const hasValidExt = validExtensions.some(ext => fileName.endsWith(ext));
  if (!hasValidExt) {
    return `Loai file khong hop le: ${file.name}. Chi chap nhan PNG, JPEG`;
  }
  
  // Check MIME type
  if (!validTypes.includes(file.type)) {
    return `File khong phai hinh anh. Chi chap nhan PNG, JPEG`;
  }
  
  return null;
}

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

const NUTRITION_FALLBACK = {
  'Chuối cau': {
    calories: 89,
    carbs: 22.8,
    sugar: 12.2,
    fiber: 2.6,
    protein: 1.1,
    fat: 0.3,
    vitaminC: 8.7,
    vitaminB6: 0.4,
    potassium: 358,
    magnesium: 27,
  },
  'Chuối già': {
    calories: 90,
    carbs: 23.0,
    sugar: 12.2,
    fiber: 2.6,
    protein: 1.1,
    fat: 0.3,
    vitaminC: 8.7,
    vitaminB6: 0.4,
    potassium: 358,
    magnesium: 27,
  },
  'Chuối sáp': {
    calories: 105,
    carbs: 27.0,
    sugar: 14.0,
    fiber: 2.7,
    protein: 1.3,
    fat: 0.4,
    vitaminC: 8.0,
    vitaminB6: 0.4,
    potassium: 360,
    magnesium: 32,
  },
  'Chuối táo quạ': {
    calories: 92,
    carbs: 23.5,
    sugar: 12.5,
    fiber: 2.5,
    protein: 1.1,
    fat: 0.3,
    vitaminC: 9.0,
    vitaminB6: 0.4,
    potassium: 355,
    magnesium: 28,
  },
  'Chuối xiêm': {
    calories: 88,
    carbs: 22.5,
    sugar: 11.8,
    fiber: 2.4,
    protein: 1.0,
    fat: 0.2,
    vitaminC: 8.5,
    vitaminB6: 0.4,
    potassium: 350,
    magnesium: 27,
  },
};

function extractCalories(text) {
  const match = String(text || '').match(/(\d+(?:\.\d+)?)/);
  return match ? Number(match[1]) : null;
}

function toDisplayNumber(value, unit, digits = 1) {
  if (!Number.isFinite(value)) return '--';
  return `${value.toFixed(digits)} ${unit}`;
}

function nutritionProfile(info, bananaLabel) {
  const fallback = NUTRITION_FALLBACK[bananaLabel] || {};
  return {
    calories: Number(info.calories_per_100g ?? fallback.calories ?? extractCalories(info.calo_uoc_luong)),
    carbs: Number(info.carbs_g ?? fallback.carbs),
    sugar: Number(info.sugar_g ?? fallback.sugar),
    fiber: Number(info.fiber_g ?? fallback.fiber),
    protein: Number(info.protein_g ?? fallback.protein),
    fat: Number(info.fat_g ?? fallback.fat),
    vitaminC: Number(info.vitamin_c_mg ?? fallback.vitaminC),
    vitaminB6: Number(info.vitamin_b6_mg ?? fallback.vitaminB6),
    potassium: Number(info.potassium_mg ?? fallback.potassium),
    magnesium: Number(info.magnesium_mg ?? fallback.magnesium),
  };
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
  
  if (!file) {
    currentFile = null;
    previewImage.classList.add('hidden');
    previewImage.src = '';
    uploadPrompt.classList.remove('hidden');
    statusEl.textContent = '';
    return;
  }
  
  // Validate file
  const error = validateImageFile(file);
  if (error) {
    showAlert(error, 'error');
    currentFile = null;
    previewImage.classList.add('hidden');
    previewImage.src = '';
    uploadPrompt.classList.remove('hidden');
    fileInput.value = '';
    return;
  }
  
  // Show preview
  currentFile = file;
  previewImage.src = URL.createObjectURL(file);
  previewImage.classList.remove('hidden');
  uploadPrompt.classList.add('hidden');
  statusEl.textContent = `Da chon: ${file.name}`;
});

predictBtn.addEventListener('click', async () => {
  if (!currentFile) {
    showAlert('Hãy chọn ảnh trước khi nhận dạng.', 'warning');
    return;
  }

  showAlert('Đang phân tích ảnh và nhận dạng...', 'info', 3000);
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
    showAlert('✨ Nhận dạng thành công! Ảnh đã được lưu an toàn.', 'success');
  } catch (error) {
    showAlert(`Lỗi: ${error.message}`, 'error');
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
  const bananaLabel = toDisplayLabel(p.loai.label);
  const nutrition = nutritionProfile(info, bananaLabel);
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
  const trangThaiLabel = toDisplayLabel(p.trang_thai.label);
  const dangLabel = toDisplayLabel(p.dang.label);
  const nenAn = ['Chín', 'Chin'].includes(p.trang_thai.label) ? 'Nên dùng ngay để cảm nhận vị ngon trọn vẹn.' : 'Nên để thêm 1-2 ngày để hương vị đạt độ chín lý tưởng.';
  const phuHop = info.goi_y_su_dung || 'Phù hợp ăn trực tiếp hoặc làm sinh tố.';
  const anhThamChieu = item.reference_image_url || item.image_url;

  resultEl.className = 'glass p-5 sm:p-7 md:p-8 rounded-[2.5rem] space-y-4 sm:space-y-6 min-h-[430px]';
  resultEl.innerHTML = `
    <div class="text-xs font-bold uppercase tracking-wider text-yellow-600">Kết quả nhận diện</div>
    <div class="glass p-4 sm:p-6 rounded-[2.5rem] flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 sm:gap-4 shadow-sm">
      <div class="flex items-start gap-3 flex-1">
        <div class="w-20 h-20 sm:w-24 sm:h-24 rounded-[1.5rem] overflow-hidden shadow-lg border-3 border-white flex-shrink-0">
          <img src="${item.image_url}" alt="banana" class="w-full h-full object-cover" />
        </div>
        <div class="flex-1">
          <span class="inline-block px-2.5 py-1 ${item.can_review ? 'bg-red-100 text-red-600' : 'bg-green-100 text-green-600'} rounded-full text-xs font-bold mb-2">
            ${item.can_review ? 'CẦN KIỂM TRA' : 'NHẬN DIỆN TỐT'}
          </span>
          <h3 class="text-2xl sm:text-4xl font-bold text-gray-800 leading-tight">${bananaLabel}</h3>
          <p class="text-sm sm:text-base text-gray-700 font-bold mt-1">Độ tin cậy: <span class="text-emerald-600 text-lg">${asPercent(p.loai.confidence)}</span></p>
        </div>
      </div>
      <div class="w-full sm:w-auto text-center sm:text-right">
        <p class="text-xs text-gray-400 font-semibold uppercase tracking-widest">Độ ngọt</p>
        <p class="text-2xl sm:text-3xl font-extrabold text-orange-500">${doNgotNhanh}</p>
      </div>
    </div>

    <div class="text-xs font-bold uppercase tracking-wider text-yellow-600">Thông tin nhanh</div>
    <div class="grid grid-cols-3 gap-2 sm:gap-4">
      <div class="bg-white/40 p-3 sm:p-5 rounded-2xl sm:rounded-3xl text-center border border-white/50">
        <i class="fas fa-circle-check text-yellow-500 mb-2 text-base sm:text-xl"></i>
        <p class="text-xs text-gray-400 font-bold uppercase">Dạng</p>
        <p class="font-bold text-gray-800 text-sm">${dangLabel}</p>
        <p class="text-xs sm:text-sm font-bold text-emerald-600 mt-1">${asPercent(p.dang.confidence)}</p>
      </div>
      <div class="bg-white/40 p-3 sm:p-5 rounded-2xl sm:rounded-3xl text-center border border-white/50">
        <i class="fas fa-sun text-orange-500 mb-2 text-base sm:text-xl"></i>
        <p class="text-xs text-gray-400 font-bold uppercase">Độ chín</p>
        <p class="font-bold text-gray-800 text-sm">${trangThaiLabel}</p>
        <p class="text-xs sm:text-sm font-bold text-emerald-600 mt-1">${asPercent(p.trang_thai.confidence)}</p>
      </div>
      <div class="bg-white/40 p-3 sm:p-5 rounded-2xl sm:rounded-3xl text-center border border-white/50">
        <i class="fas fa-fire text-red-500 mb-2 text-base sm:text-xl"></i>
        <p class="text-xs text-gray-400 font-bold uppercase">Calo</p>
        <p class="font-bold text-gray-800 text-sm">${info.calo_uoc_luong || '89 kcal'}</p>
      </div>
    </div>

    <div class="grid lg:grid-cols-2 gap-4 sm:gap-6">
      <div class="bg-yellow-400/10 border border-yellow-200 p-4 sm:p-6 rounded-2xl sm:rounded-[2.5rem]">
        <h4 class="font-bold text-yellow-700 text-xs sm:text-sm mb-3 uppercase tracking-widest"><i class="fas fa-lightbulb mr-2"></i>Gợi ý thông minh</h4>
        <ul class="space-y-2 sm:space-y-3">
          <li class="text-xs sm:text-sm font-semibold flex items-start gap-2">
            <i class="fas fa-utensils text-yellow-500 mt-0.5 flex-shrink-0"></i> <span>${nenAn}</span>
          </li>
          <li class="text-xs sm:text-sm font-semibold flex items-start gap-2">
            <i class="fas fa-blender text-yellow-500 mt-0.5 flex-shrink-0"></i> <span>${info.goi_y_su_dung || 'Phù hợp ăn trực tiếp hoặc làm sinh tố.'}</span>
          </li>
        </ul>
      </div>

      <div class="bg-green-500/10 border border-green-200 p-4 sm:p-6 rounded-2xl sm:rounded-[2.5rem]">
        <h4 class="font-bold text-green-700 text-xs sm:text-sm mb-3 uppercase tracking-widest"><i class="fas fa-heart-pulse mr-2"></i>Dinh dưỡng</h4>
        <div class="grid grid-cols-2 gap-1.5 sm:gap-2 mb-3">
          <div class="bg-white px-2 py-1.5 sm:px-3 sm:py-2 rounded-lg text-xs font-bold text-green-800">Calo: ${toDisplayNumber(nutrition.calories, 'kcal', 0)}</div>
          <div class="bg-white px-2 py-1.5 sm:px-3 sm:py-2 rounded-lg text-xs font-bold text-green-800">Carbs: ${toDisplayNumber(nutrition.carbs, 'g')}</div>
          <div class="bg-white px-2 py-1.5 sm:px-3 sm:py-2 rounded-lg text-xs font-bold text-green-800">Đường: ${toDisplayNumber(nutrition.sugar, 'g')}</div>
          <div class="bg-white px-2 py-1.5 sm:px-3 sm:py-2 rounded-lg text-xs font-bold text-green-800">Chất xơ: ${toDisplayNumber(nutrition.fiber, 'g')}</div>
          <div class="bg-white px-2 py-1.5 sm:px-3 sm:py-2 rounded-lg text-xs font-bold text-green-800">Protein: ${toDisplayNumber(nutrition.protein, 'g')}</div>
          <div class="bg-white px-2 py-1.5 sm:px-3 sm:py-2 rounded-lg text-xs font-bold text-green-800">Fat: ${toDisplayNumber(nutrition.fat, 'g')}</div>
        </div>
        <div class="text-xs font-bold uppercase tracking-wider text-green-700 mb-2">Vitamin & khoáng</div>
        <div class="grid grid-cols-2 gap-1.5 sm:gap-2">
          <div class="bg-white px-2 py-1.5 sm:px-3 sm:py-2 rounded-lg text-xs font-bold text-emerald-700">Vitamin C: ${toDisplayNumber(nutrition.vitaminC, 'mg')}</div>
          <div class="bg-white px-2 py-1.5 sm:px-3 sm:py-2 rounded-lg text-xs font-bold text-emerald-700">B6: ${toDisplayNumber(nutrition.vitaminB6, 'mg')}</div>
          <div class="bg-white px-2 py-1.5 sm:px-3 sm:py-2 rounded-lg text-xs font-bold text-emerald-700">Kali: ${toDisplayNumber(nutrition.potassium, 'mg', 0)}</div>
          <div class="bg-white px-2 py-1.5 sm:px-3 sm:py-2 rounded-lg text-xs font-bold text-emerald-700">Magie: ${toDisplayNumber(nutrition.magnesium, 'mg', 0)}</div>
        </div>
      </div>
    </div>

    <div class="rounded-2xl sm:rounded-[2rem] overflow-hidden bg-white/45 border border-white/60 p-4 sm:p-6 text-xs sm:text-sm text-gray-700 leading-relaxed space-y-2">
      <h4 class="font-bold text-gray-700 text-xs uppercase tracking-widest mb-2">Mô tả chi tiết</h4>
      <p><span class="font-bold">Tên gọi:</span> ${thongTinCoBan}</p>
      <p><span class="font-bold">Đặc điểm:</span> ${dacDiem}</p>
      <p><span class="font-bold">Vị:</span> ${huongVi}</p>
      <p><span class="font-bold">Dinh dưỡng:</span> ${dinhDuongText}</p>
      <p><span class="font-bold">Cách dùng:</span> ${goiYSuDung}</p>
      <p><span class="font-bold">Bảo quản:</span> ${baoQuan}</p>
    </div>

    <div class="text-xs font-bold uppercase tracking-wider text-yellow-600">Ảnh tham chiếu</div>
    <div class="rounded-2xl sm:rounded-3xl border border-white/50 bg-white/40 p-2 sm:p-3">
      <a href="${anhThamChieu}" target="_blank" rel="noopener noreferrer" class="block group">
        <img src="${anhThamChieu}" alt="Ảnh tham chiếu" class="w-full h-40 sm:h-52 object-cover rounded-xl sm:rounded-2xl group-hover:opacity-95 transition" />
        <p class="text-xs text-gray-500 font-semibold mt-1.5 sm:mt-2 text-right">Bấm để xem toàn bộ</p>
      </a>
    </div>

    ${warningHtml}

  `;
}

async function fetchHistory() {
  const response = await fetch('/api/history');
  const payload = await response.json();
  const items = payload.items || [];
  historyItems = items;

  if (!items.length) {
    historyEl.className = 'text-gray-500 font-semibold';
    historyEl.textContent = 'Chưa có lịch sử';
    return;
  }

  historyEl.className = 'grid md:grid-cols-2 gap-3';
  historyEl.innerHTML = items.map((item, index) => `
    <article class="history-item rounded-2xl border-2 border-yellow-100 bg-white/60 p-3 flex gap-3 cursor-pointer transition-all hover:border-yellow-400 hover:bg-yellow-50/70 hover:shadow-md" data-index="${index}">
      <img src="${item.image_url}" alt="uploaded" class="w-24 h-24 object-cover rounded-xl" />
      <div class="min-w-0 flex-1">
        <div class="text-lg font-bold text-gray-800">${toDisplayLabel(item.predictions.loai.label)}</div>
        <div class="text-sm text-gray-500">Dạng: ${toDisplayLabel(item.predictions.dang.label)} · Trạng thái: ${toDisplayLabel(item.predictions.trang_thai.label)}</div>
        <div class="text-sm text-gray-500 mt-1">${new Date(item.created_at).toLocaleString()} · ${asPercent(item.predictions.loai.confidence)} độ tin cậy</div>
      </div>
    </article>
  `).join('');

  document.querySelectorAll('.history-item').forEach((el) => {
    el.addEventListener('click', () => {
      const index = parseInt(el.getAttribute('data-index'));
      const item = historyItems[index];
      if (item) {
        renderResult(item);
        homeSection.classList.remove('hidden');
        historySection.classList.add('hidden');
        tabHome.className = 'glass px-5 py-2 rounded-full text-sm font-bold transition text-gray-800 bg-white/90';
        tabHistory.className = 'glass px-5 py-2 rounded-full text-sm font-bold transition text-gray-500';
      }
    });
  });
}

// File Picker Modal Logic
// File Picker Modal Logic
function isMobileView() {
  return window.innerWidth < 768; // md breakpoint
}

function createTempFileInput(capture = null) {
  const tempInput = document.createElement('input');
  tempInput.type = 'file';
  tempInput.accept = 'image/png,image/jpeg';
  if (capture) {
    tempInput.capture = capture;
  }
  tempInput.addEventListener('change', function() {
    if (this.files && this.files[0]) {
      const file = this.files[0];
      
      // Validate file
      const error = validateImageFile(file);
      if (error) {
        showAlert(error, 'error');
        currentFile = null;
        previewImage.classList.add('hidden');
        previewImage.src = '';
        uploadPrompt.classList.remove('hidden');
        return;
      }
      
      // Show preview
      currentFile = file;
      previewImage.src = URL.createObjectURL(file);
      previewImage.classList.remove('hidden');
      uploadPrompt.classList.add('hidden');
      statusEl.textContent = `Da chon: ${file.name}`;
    }
  });
  return tempInput;
}

function showFilePicker() {
  filePickerModal.classList.remove('hidden');
}

function hideFilePicker() {
  filePickerModal.classList.add('hidden');
}

// Upload area click - show modal on mobile, file input on desktop
uploadArea.addEventListener('click', (e) => {
  if (e.target !== previewImage) {
    e.preventDefault();
    if (isMobileView()) {
      showFilePicker();
    } else {
      // On desktop, trigger standard file input
      const tempInput = createTempFileInput(null);
      tempInput.click();
    }
  }
});

// Camera option - trigger camera capture (mobile only)
cameraBtnOption.addEventListener('click', () => {
  hideFilePicker();
  const tempInput = createTempFileInput('environment');
  tempInput.click();
});

// Gallery option - trigger file picker
galleryBtnOption.addEventListener('click', () => {
  hideFilePicker();
  const tempInput = createTempFileInput(null);
  tempInput.click();
});

// Close button
closeFilePickerBtn.addEventListener('click', hideFilePicker);

// Modal overlay click - close modal
filePickerModal.addEventListener('click', (e) => {
  if (e.target === filePickerModal) {
    hideFilePicker();
  }
});

// Handle window resize for responsive behavior
window.addEventListener('resize', () => {
  if (!isMobileView() && !filePickerModal.classList.contains('hidden')) {
    hideFilePicker();
  }
});

fetchHistory();
renderEmptyResult();
setActiveTab('home');
