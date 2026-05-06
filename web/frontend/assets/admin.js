let allPredictions = [];
let allBananas = [];
let exportPredictions = [];
let currentBananaId = null;

const bananaList = document.getElementById('bananaList');
const bananaForm = document.getElementById('bananaForm');
const bananaFormTitle = document.getElementById('bananaFormTitle');
const bananaNutritionSummary = document.getElementById('bananaNutritionSummary');
const bananaNutritionCalories = document.getElementById('bananaNutritionCalories');
const bananaNutritionText = document.getElementById('bananaNutritionText');
const bananaNutritionTags = document.getElementById('bananaNutritionTags');
const deleteBananaBtn = document.getElementById('deleteBananaBtn');
const newBananaBtn = document.getElementById('newBananaBtn');
const detailModal = document.getElementById('detailModal');
const detailBackdrop = document.getElementById('detailBackdrop');
const detailModalContainer = document.getElementById('detailModalContainer');
const detailModalBody = document.getElementById('detailModalBody');
const bananaInfoGrid = document.getElementById('bananaInfoGrid');
const filterStructure = document.getElementById('filterStructure');
const filterRipeness = document.getElementById('filterRipeness');
const predictionsFrom = document.getElementById('predictionsFrom');
const predictionsTo = document.getElementById('predictionsTo');
const clearPredictionDateFilter = document.getElementById('clearPredictionDateFilter');

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
  };
  return map[label] || label || '';
}

function openDetailModal(html) {
  if (!detailModal || !detailModalBody) return;
  detailModalBody.innerHTML = html;
  detailModal.classList.remove('hidden');
}

function closeDetailModal() {
  if (!detailModal || !detailModalBody) return;
  detailModal.classList.add('hidden');
  detailModalBody.innerHTML = '';
}

function updateBananaInfoLayout() {
  if (!bananaInfoGrid || !bananaForm) return;
  const isWideScreen = window.matchMedia('(min-width: 1280px)').matches;
  const formVisible = !bananaForm.classList.contains('hidden');
  bananaInfoGrid.style.gridTemplateColumns = isWideScreen && formVisible
    ? 'minmax(0,2.2fr) minmax(340px,1fr)'
    : 'minmax(0,1fr)';
}

detailBackdrop?.addEventListener('click', closeDetailModal);
detailModalContainer?.addEventListener('click', (event) => {
  if (event.target === detailModalContainer) {
    closeDetailModal();
  }
});
detailModal?.addEventListener('click', (event) => {
  if (event.target === detailModal) {
    closeDetailModal();
  }
});
document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape') closeDetailModal();
});

function buildQuery(params) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value) query.append(key, value);
  });
  return query.toString();
}

function toNullableNumber(value) {
  if (value === null || value === undefined || value === '') return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function getDateRangeParams(prefix) {
  const fromValue = document.getElementById(`${prefix}From`)?.value || '';
  const toValue = document.getElementById(`${prefix}To`)?.value || '';
  return {
    start_time: fromValue ? `${fromValue}T00:00:00` : '',
    end_time: toValue ? `${toValue}T23:59:59` : '',
  };
}

function getDateRangeValues(prefix) {
  return {
    from: document.getElementById(`${prefix}From`)?.value || '',
    to: document.getElementById(`${prefix}To`)?.value || '',
  };
}

function matchesDateRange(createdAt, prefix) {
  const { from, to } = getDateRangeValues(prefix);
  if (!from && !to) return true;

  const createdDate = String(createdAt || '').slice(0, 10);
  if (!createdDate) return false;
  if (from && createdDate < from) return false;
  if (to && createdDate > to) return false;
  return true;
}

function setBananaFormMode(mode, label) {
  if (bananaFormTitle) {
    bananaFormTitle.textContent = label || (mode === 'create' ? 'Thêm chuối mới' : 'Chọn một loại chuối để sửa');
  }
  if (deleteBananaBtn) {
    deleteBananaBtn.classList.toggle('hidden', mode !== 'edit');
  }
  if (bananaForm) {
    bananaForm.classList.remove('hidden');
  }
}

function clearBananaForm() {
  currentBananaId = null;
  const fields = ['bName', 'scientificName', 'description', 'origin', 'taste', 'recommendedUsage', 'bestFor', 'storageTip', 'caloriesPer100g', 'carbsG', 'sugarG', 'fiberG', 'proteinG', 'fatG', 'vitaminCMg', 'potassiumMg'];
  fields.forEach((field) => {
    const input = document.getElementById(field);
    if (input) input.value = '';
  });
  if (bananaNutritionSummary) {
    bananaNutritionSummary.classList.add('hidden');
  }
  setBananaFormMode('create', 'Thêm chuối mới');
}

function fillBananaForm(item) {
  setBananaFormMode('edit', `Đang sửa: ${item.b_name || 'Loại chuối'}`);
  document.getElementById('bName').value = item.b_name || '';
  document.getElementById('scientificName').value = item.b_scientific_name || '';
  document.getElementById('description').value = item.description || '';
  document.getElementById('origin').value = item.origin || '';
  document.getElementById('taste').value = item.taste || '';
  document.getElementById('recommendedUsage').value = item.recommended_usage || '';
  document.getElementById('bestFor').value = item.best_for || '';
  document.getElementById('storageTip').value = item.storage_tip || '';
  document.getElementById('caloriesPer100g').value = item.calories_per_100g ?? '';
  document.getElementById('carbsG').value = item.carbs_g ?? '';
  document.getElementById('sugarG').value = item.sugar_g ?? '';
  document.getElementById('fiberG').value = item.fiber_g ?? '';
  document.getElementById('proteinG').value = item.protein_g ?? '';
  document.getElementById('fatG').value = item.fat_g ?? '';
  document.getElementById('vitaminCMg').value = item.vitamin_c_mg ?? '';
  document.getElementById('potassiumMg').value = item.potassium_mg ?? '';
  if (bananaNutritionSummary) {
    bananaNutritionSummary.classList.remove('hidden');
  }
  if (bananaNutritionCalories) {
    bananaNutritionCalories.textContent = item.calo_uoc_luong || '';
  }
  if (bananaNutritionText) {
    bananaNutritionText.textContent = item.dinh_duong || '';
  }
  if (bananaNutritionTags) {
    const highlights = Array.isArray(item.dinh_duong_highlights) ? item.dinh_duong_highlights : [];
    bananaNutritionTags.innerHTML = highlights.map((highlight) => `<span class="px-2 py-1 rounded-full bg-white border border-amber-200 text-amber-900 text-xs font-semibold">${highlight}</span>`).join('');
  }
}

function bananaPayloadFromForm() {
  return {
    b_name: document.getElementById('bName').value.trim(),
    b_scientific_name: document.getElementById('scientificName').value.trim(),
    description: document.getElementById('description').value.trim(),
    origin: document.getElementById('origin').value.trim(),
    taste: document.getElementById('taste').value.trim(),
    recommended_usage: document.getElementById('recommendedUsage').value.trim(),
    best_for: document.getElementById('bestFor').value.trim(),
    storage_tip: document.getElementById('storageTip').value.trim(),
    calories_per_100g: toNullableNumber(document.getElementById('caloriesPer100g').value),
    carbs_g: toNullableNumber(document.getElementById('carbsG').value),
    sugar_g: toNullableNumber(document.getElementById('sugarG').value),
    fiber_g: toNullableNumber(document.getElementById('fiberG').value),
    protein_g: toNullableNumber(document.getElementById('proteinG').value),
    fat_g: toNullableNumber(document.getElementById('fatG').value),
    vitamin_c_mg: toNullableNumber(document.getElementById('vitaminCMg').value),
    potassium_mg: toNullableNumber(document.getElementById('potassiumMg').value),
  };
}

function renderBananaSelect(items) {
  if (!bananaList) return;

  if (!items.length) {
    bananaList.innerHTML = '<p class="text-sm text-gray-400">Chưa có loại chuối nào.</p>';
    return;
  }

  bananaList.innerHTML = items.map((item) => {
    const calories = item.calo_uoc_luong || (item.calories_per_100g != null ? `${Number(item.calories_per_100g).toFixed(0)} kcal` : '-- kcal');
    const highlights = Array.isArray(item.dinh_duong_highlights) ? item.dinh_duong_highlights.slice(0, 2) : [];
    return `
      <button type="button" class="banana-row w-full text-left p-4 pr-2 rounded-2xl border border-gray-100 bg-white hover:bg-amber-50 hover:shadow-md transition" data-bid="${item.b_id}">
        <div class="flex items-start justify-between gap-3">
          <div class="min-w-0 flex-1">
            <div class="font-bold text-gray-900 truncate">${item.b_name}</div>
            <div class="text-xs text-gray-500 truncate">${item.b_scientific_name || 'Chưa có tên khoa học'}</div>
            <div class="mt-2 text-xs text-gray-600">Dinh dưỡng: ${calories}</div>
            <div class="mt-1 flex flex-wrap gap-2 text-[11px]">
              ${highlights.map((highlight) => `<span class="px-2 py-1 rounded-full bg-amber-100 text-amber-900 font-semibold">${highlight}</span>`).join('')}
            </div>
            <div class="mt-2 text-xs text-gray-500 truncate">${item.origin || 'Chưa có xuất xứ'}${item.taste ? ` · ${item.taste}` : ''}</div>
          </div>
          <div class="shrink-0 text-right text-xs text-gray-400">›</div>
        </div>
      </button>
    `;
  }).join('');

  bananaList.querySelectorAll('.banana-row').forEach((button) => {
    button.addEventListener('click', async () => {
      const bId = button.getAttribute('data-bid');
      const item = allBananas.find((banana) => String(banana.b_id) === String(bId));
      if (!item) return;

      openDetailModal(
        `
          <div class="flex items-start justify-between mb-4">
            <h2 class="text-2xl font-extrabold text-gray-800">🍌 ${item.b_name}</h2>
            <button type="button" id="closeModalBtn" class="w-8 h-8 rounded-full bg-gray-100 hover:bg-gray-200 text-gray-700 font-bold text-lg">✕</button>
          </div>

            <form id="bananaModalForm" class="space-y-4 max-h-[calc(85vh-150px)] overflow-y-auto pr-2">
            <!-- Tên & Thông tin cơ bản -->
            <div class="bg-gradient-to-r from-yellow-50 to-amber-50 p-4 rounded-2xl border border-yellow-200">
              <h3 class="text-sm font-bold text-yellow-700 mb-3 uppercase tracking-widest">Thông tin cơ bản</h3>
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="text-xs font-bold text-gray-700">Tên loại *</label>
                  <input type="text" id="modalBName" class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm" value="${item.b_name || ''}" required>
                </div>
                <div>
                  <label class="text-xs font-bold text-gray-700">Tên khoa học</label>
                  <input type="text" id="modalScientificName" class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm" value="${item.b_scientific_name || ''}">
                </div>
              </div>
              <div class="mt-3">
                <label class="text-xs font-bold text-gray-700">Mô tả</label>
                <textarea id="modalDescription" rows="2" class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm">${item.description || ''}</textarea>
              </div>
            </div>

            <!-- Địa lý & Hương vị -->
            <div class="bg-gradient-to-r from-green-50 to-emerald-50 p-4 rounded-2xl border border-green-200">
              <h3 class="text-sm font-bold text-green-700 mb-3 uppercase tracking-widest">Địa lý & Hương vị</h3>
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="text-xs font-bold text-gray-700">Xuất xứ</label>
                  <input type="text" id="modalOrigin" class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm" value="${item.origin || ''}">
                </div>
                <div>
                  <label class="text-xs font-bold text-gray-700">Độ ngọt / Hương vị</label>
                  <input type="text" id="modalTaste" class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm" value="${item.taste || ''}">
                </div>
              </div>
            </div>

            <!-- Cách sử dụng & Bảo quản -->
            <div class="bg-gradient-to-r from-blue-50 to-cyan-50 p-4 rounded-2xl border border-blue-200">
              <h3 class="text-sm font-bold text-blue-700 mb-3 uppercase tracking-widest">Sử dụng & Bảo quản</h3>
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="text-xs font-bold text-gray-700">Cách dùng</label>
                  <input type="text" id="modalRecommendedUsage" class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm" value="${item.recommended_usage || ''}">
                </div>
                <div>
                  <label class="text-xs font-bold text-gray-700">Hợp nhất với</label>
                  <input type="text" id="modalBestFor" class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm" value="${item.best_for || ''}">
                </div>
              </div>
              <div class="mt-3">
                <label class="text-xs font-bold text-gray-700">Lưu ý bảo quản</label>
                <textarea id="modalStorageTip" rows="2" class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm">${item.storage_tip || ''}</textarea>
              </div>
            </div>

            <!-- Dinh dưỡng - Chính yếu -->
            <div class="bg-gradient-to-r from-orange-50 to-yellow-50 p-4 rounded-2xl border border-orange-200">
              <h3 class="text-sm font-bold text-orange-700 mb-3 uppercase tracking-widest">💪 Dinh dưỡng chính yếu</h3>
              <div class="grid grid-cols-3 gap-3">
                <div>
                  <label class="text-xs font-bold text-gray-700">Calo / 100g</label>
                  <input type="number" id="modalCaloriesPer100g" step="0.01" class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm" value="${item.calories_per_100g ?? ''}">
                </div>
                <div>
                  <label class="text-xs font-bold text-gray-700">Carbs (g)</label>
                  <input type="number" id="modalCarbsG" step="0.01" class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm" value="${item.carbs_g ?? ''}">
                </div>
                <div>
                  <label class="text-xs font-bold text-gray-700">Đường (g)</label>
                  <input type="number" id="modalSugarG" step="0.01" class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm" value="${item.sugar_g ?? ''}">
                </div>
              </div>
              <div class="grid grid-cols-3 gap-3 mt-3">
                <div>
                  <label class="text-xs font-bold text-gray-700">Chất xơ (g)</label>
                  <input type="number" id="modalFiberG" step="0.01" class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm" value="${item.fiber_g ?? ''}">
                </div>
                <div>
                  <label class="text-xs font-bold text-gray-700">Protein (g)</label>
                  <input type="number" id="modalProteinG" step="0.01" class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm" value="${item.protein_g ?? ''}">
                </div>
                <div>
                  <label class="text-xs font-bold text-gray-700">Fat (g)</label>
                  <input type="number" id="modalFatG" step="0.01" class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm" value="${item.fat_g ?? ''}">
                </div>
              </div>
            </div>

            <!-- Dinh dưỡng - Micronutrient -->
            <div class="bg-gradient-to-r from-red-50 to-pink-50 p-4 rounded-2xl border border-red-200">
              <h3 class="text-sm font-bold text-red-700 mb-3 uppercase tracking-widest">⚡ Vitamin & Khoáng chất</h3>
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="text-xs font-bold text-gray-700">Vitamin C (mg)</label>
                  <input type="number" id="modalVitaminCMg" step="0.01" class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm" value="${item.vitamin_c_mg ?? ''}">
                </div>
                <div>
                  <label class="text-xs font-bold text-gray-700">Kali (mg)</label>
                  <input type="number" id="modalPotassiumMg" step="0.01" class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm" value="${item.potassium_mg ?? ''}">
                </div>
              </div>
            </div>

          </form>
          
          <div class="h-4"></div>
          
          <!-- Buttons - Fixed/Sticky -->
          <div class="flex gap-3 pt-6 justify-center sticky bottom-0 bg-gradient-to-t from-white via-white to-transparent p-4 -m-4 mt-0">
            <button type="submit" form="bananaModalForm" class="px-8 py-3 bg-green-500 text-white rounded-full font-bold hover:bg-green-600 shadow-lg hover:shadow-xl transition text-sm uppercase tracking-widest"><i class="fas fa-save mr-2"></i>Lưu</button>
            <button type="button" id="modalDeleteBtn" class="px-8 py-3 bg-red-500 text-white rounded-full font-bold hover:bg-red-600 shadow-lg hover:shadow-xl transition text-sm uppercase tracking-widest"><i class="fas fa-trash mr-2"></i>Xóa</button>
          </div>
        `
      );

      // Close button
      const closeBtn = document.getElementById('closeModalBtn');
      closeBtn?.addEventListener('click', closeDetailModal);

      // Form submission
      const modalForm = document.getElementById('bananaModalForm');
      modalForm?.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const payload = {
          b_name: document.getElementById('modalBName').value.trim(),
          b_scientific_name: document.getElementById('modalScientificName').value.trim(),
          description: document.getElementById('modalDescription').value.trim(),
          origin: document.getElementById('modalOrigin').value.trim(),
          taste: document.getElementById('modalTaste').value.trim(),
          recommended_usage: document.getElementById('modalRecommendedUsage').value.trim(),
          best_for: document.getElementById('modalBestFor').value.trim(),
          storage_tip: document.getElementById('modalStorageTip').value.trim(),
          calories_per_100g: toNullableNumber(document.getElementById('modalCaloriesPer100g').value),
          carbs_g: toNullableNumber(document.getElementById('modalCarbsG').value),
          sugar_g: toNullableNumber(document.getElementById('modalSugarG').value),
          fiber_g: toNullableNumber(document.getElementById('modalFiberG').value),
          protein_g: toNullableNumber(document.getElementById('modalProteinG').value),
          fat_g: toNullableNumber(document.getElementById('modalFatG').value),
          vitamin_c_mg: toNullableNumber(document.getElementById('modalVitaminCMg').value),
          potassium_mg: toNullableNumber(document.getElementById('modalPotassiumMg').value),
        };

        try {
          const res = await fetch(`/api/admin/banana/${bId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
          });
          if (!res.ok) throw new Error(await res.text());
          closeDetailModal();
          await loadBananas();
        } catch (err) {
          console.error(err);
          alert('Lỗi khi lưu: ' + err.message);
        }
      });

      // Delete button
      const deleteBtn = document.getElementById('modalDeleteBtn');
      deleteBtn?.addEventListener('click', async () => {
        if (!confirm('Bạn chắc chắn muốn xóa loại chuối này?')) return;
        try {
          const res = await fetch(`/api/admin/banana/${bId}`, { method: 'DELETE' });
          if (!res.ok) throw new Error(await res.text());
          closeDetailModal();
          await loadBananas();
        } catch (err) {
          console.error(err);
          alert('Lỗi khi xóa: ' + err.message);
        }
      });
    });
  });
}

// Navigation
document.querySelectorAll('.nav-btn').forEach((btn) => {
  btn.addEventListener('click', () => {
    const section = btn.getAttribute('data-section');
    document.querySelectorAll('.section').forEach((sectionNode) => sectionNode.classList.add('hidden'));
    document.getElementById(section).classList.remove('hidden');

    document.querySelectorAll('.nav-btn').forEach((navigationButton) => navigationButton.classList.remove('bg-yellow-100', 'text-yellow-800'));
    btn.classList.add('bg-yellow-100', 'text-yellow-800');

    if (section === 'predictions') loadPredictions();
    if (section === 'banana-info') loadBananas();
    if (section === 'export') loadExportData();
  });
});

document.querySelector('.nav-btn').click();
updateBananaInfoLayout();
window.addEventListener('resize', updateBananaInfoLayout);

// Predictions Section
async function loadPredictions() {
  try {
    const res = await fetch('/api/admin/predictions');
    const data = await res.json();
    allPredictions = data.items || [];
    applyPredictionFilters();
  } catch (err) {
    console.error(err);
    document.getElementById('predictionsList').innerHTML = '<p class="text-red-500 text-sm">Lỗi tải dữ liệu</p>';
  }
}

function renderPredictions(items) {
  const html = items.length
    ? items.map((item, index) => `
      <button type="button" class="prediction-row w-full text-left border border-gray-200 rounded-xl p-3 flex gap-3 hover:bg-yellow-50/70 transition" data-index="${index}">
        <img src="${item.image_url}" alt="prediction" class="w-16 h-16 object-cover rounded-lg">
        <div class="flex-1 min-w-0">
          <div class="font-bold text-gray-800">${item.banana_name}</div>
          <div class="text-xs text-gray-500">Dạng: ${toDisplayLabel(item.structure_type)} · Chín: ${toDisplayLabel(item.ripeness_level)}</div>
          <div class="text-xs text-gray-500 mt-1">${item.created_at ? new Date(item.created_at).toLocaleString() : ''}</div>
        </div>
        <div class="shrink-0 text-right">
          <div class="text-xs font-bold text-emerald-700">${((item.type_confidence || 0) * 100).toFixed(1)}%</div>
          <div class="text-xs text-gray-400 mt-1">Xem card</div>
        </div>
      </button>
    `).join('')
    : '<p class="text-gray-400 text-sm">Chưa có dự đoán nào</p>';

  document.getElementById('predictionsList').innerHTML = html;

  document.querySelectorAll('.prediction-row').forEach((button) => {
    button.addEventListener('click', () => {
      const index = Number(button.getAttribute('data-index'));
      const item = items[index];
      if (!item) return;

      openDetailModal(
        `
          <div class="flex items-start justify-between mb-4">
            <div class="text-xs font-bold uppercase tracking-wider text-yellow-600">Kết quả nhận diện</div>
            <button type="button" id="closePredictionModal" class="w-8 h-8 rounded-full bg-gray-100 hover:bg-gray-200 text-gray-700 font-bold text-lg">✕</button>
          </div>
          
          <div class="bg-gray-50 p-2.5 md:p-3 rounded-[1.25rem] space-y-2.5 w-[min(82vw,700px)] border border-gray-200">
            <div class="bg-white p-2.5 md:p-3 rounded-[1.25rem] shadow-sm border border-gray-100">
              <div class="flex flex-col items-start gap-3 w-full">
                <div class="w-full rounded-[0.9rem] overflow-hidden shadow-lg border-2 border-white relative shrink-0 bg-gray-100">
                  <img src="${item.image_url}" alt="banana" class="block w-full h-auto" />
                </div>
                <div class="min-w-0">
                  <span class="px-2.5 py-1 ${item.can_review ? 'bg-red-100 text-red-600' : 'bg-green-100 text-green-600'} rounded-full text-[11px] font-bold">
                    ${item.can_review ? 'CẦN KIỂM TRA' : 'NHẬN DIỆN TỐT'}
                  </span>
                  <h3 class="text-lg lg:text-xl font-bold text-gray-800 mt-1.5 break-words">${item.banana_name || 'Đang cập nhật'}</h3>
                  <p class="text-[11px] text-gray-700 font-extrabold mt-1">Độ tin cậy: <span class="text-emerald-600 text-sm">${((item.type_confidence || 0) * 100).toFixed(1)}%</span></p>
                </div>
              </div>
            </div>

            <div class="rounded-lg bg-white border border-gray-200 p-3 space-y-1.5 text-xs md:text-sm text-gray-700">
              <p><span class="font-bold">Loại:</span> ${item.banana_name || 'N/A'}</p>
              <p><span class="font-bold">Dạng:</span> ${toDisplayLabel(item.structure_type)}</p>
              <p><span class="font-bold">Độ chín:</span> ${toDisplayLabel(item.ripeness_level)}</p>
              <p><span class="font-bold">Thời gian:</span> ${item.created_at ? new Date(item.created_at).toLocaleString('vi-VN') : 'Đang cập nhật'}</p>
            </div>

            <a href="${item.image_url}" download class="block w-full text-center px-3 py-2 rounded-lg bg-blue-500 text-white font-bold hover:bg-blue-600 transition text-[11px] uppercase tracking-widest"><i class="fas fa-download mr-1.5"></i>Tải ảnh dự đoán</a>
          </div>
        `
      );

      // Close button for prediction modal
      const closePredictionBtn = document.getElementById('closePredictionModal');
      closePredictionBtn?.addEventListener('click', closeDetailModal);
    });
  });
}

function applyPredictionFilters() {
  const query = (document.getElementById('searchInput')?.value || '').toLowerCase();
  const structure = filterStructure?.value || '';
  const ripeness = filterRipeness?.value || '';

  const filtered = allPredictions.filter((prediction) => {
    const byName = (prediction.banana_name || '').toLowerCase().includes(query);
    const byStructure = !structure || toDisplayLabel(prediction.structure_type) === structure || prediction.structure_type === structure;
    const byRipeness = !ripeness || toDisplayLabel(prediction.ripeness_level) === ripeness || prediction.ripeness_level === ripeness;
    const byDate = matchesDateRange(prediction.created_at, 'predictions');
    return byName && byStructure && byRipeness && byDate;
  });

  renderPredictions(filtered);
}

document.getElementById('searchInput')?.addEventListener('input', (event) => {
  applyPredictionFilters();
});
filterStructure?.addEventListener('change', applyPredictionFilters);
filterRipeness?.addEventListener('change', applyPredictionFilters);

document.getElementById('refreshBtn')?.addEventListener('click', loadPredictions);
clearPredictionDateFilter?.addEventListener('click', () => {
  if (predictionsFrom) predictionsFrom.value = '';
  if (predictionsTo) predictionsTo.value = '';
  applyPredictionFilters();
});
predictionsFrom?.addEventListener('change', applyPredictionFilters);
predictionsTo?.addEventListener('change', applyPredictionFilters);

// Banana Info Section
async function loadBananas(selectedId = '') {
  try {
    const res = await fetch('/api/admin/bananas');
    const data = await res.json();
    allBananas = data.items || [];
    renderBananaSelect(allBananas);

    if (selectedId) {
      await loadBananaDetail(selectedId);
    } else {
      clearBananaForm();
      if (bananaForm) {
        bananaForm.classList.add('hidden');
      }
    }
    updateBananaInfoLayout();
  } catch (err) {
    console.error(err);
  }
}

async function loadBananaDetail(bId) {
  try {
    const res = await fetch(`/api/admin/banana/${bId}`);
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    fillBananaForm(data.item || {});
  } catch (err) {
    console.error(err);
    alert('Không tải được thông tin chuối');
  }
}

newBananaBtn?.addEventListener('click', () => {
  currentBananaId = null;
  if (bananaForm) {
    bananaForm.classList.add('hidden');
  }
  updateBananaInfoLayout();
  if (bananaList) {
    bananaList.querySelectorAll('.banana-row').forEach((row) => row.classList.remove('ring-2', 'ring-amber-400', 'bg-amber-50'));
  }

  openDetailModal(
    `
      <div class="flex items-start justify-between mb-4">
        <h2 class="text-2xl font-extrabold text-gray-800">🍌 Thêm chuối mới</h2>
        <button type="button" id="closeCreateBananaModalBtn" class="w-8 h-8 rounded-full bg-gray-100 hover:bg-gray-200 text-gray-700 font-bold text-lg">✕</button>
      </div>

      <form id="bananaCreateModalForm" class="space-y-4 max-h-[calc(85vh-150px)] overflow-y-auto pr-2">
        <div class="bg-gradient-to-r from-yellow-50 to-amber-50 p-4 rounded-2xl border border-yellow-200">
          <h3 class="text-sm font-bold text-yellow-700 mb-3 uppercase tracking-widest">Thông tin cơ bản</h3>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="text-xs font-bold text-gray-700">Tên loại *</label>
              <input type="text" id="createBName" class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm" placeholder="VD: Chuối cau" required>
            </div>
            <div>
              <label class="text-xs font-bold text-gray-700">Tên khoa học</label>
              <input type="text" id="createScientificName" class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm">
            </div>
          </div>
          <div class="mt-3">
            <label class="text-xs font-bold text-gray-700">Mô tả</label>
            <textarea id="createDescription" rows="2" class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm"></textarea>
          </div>
        </div>

        <div class="bg-gradient-to-r from-green-50 to-emerald-50 p-4 rounded-2xl border border-green-200">
          <h3 class="text-sm font-bold text-green-700 mb-3 uppercase tracking-widest">Địa lý & Hương vị</h3>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="text-xs font-bold text-gray-700">Xuất xứ</label>
              <input type="text" id="createOrigin" class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm">
            </div>
            <div>
              <label class="text-xs font-bold text-gray-700">Độ ngọt / Hương vị</label>
              <input type="text" id="createTaste" class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm">
            </div>
          </div>
        </div>

        <div class="bg-gradient-to-r from-blue-50 to-cyan-50 p-4 rounded-2xl border border-blue-200">
          <h3 class="text-sm font-bold text-blue-700 mb-3 uppercase tracking-widest">Sử dụng & Bảo quản</h3>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="text-xs font-bold text-gray-700">Cách dùng</label>
              <input type="text" id="createRecommendedUsage" class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm">
            </div>
            <div>
              <label class="text-xs font-bold text-gray-700">Hợp nhất với</label>
              <input type="text" id="createBestFor" class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm">
            </div>
          </div>
          <div class="mt-3">
            <label class="text-xs font-bold text-gray-700">Lưu ý bảo quản</label>
            <textarea id="createStorageTip" rows="2" class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm"></textarea>
          </div>
        </div>

        <div class="bg-gradient-to-r from-orange-50 to-yellow-50 p-4 rounded-2xl border border-orange-200">
          <h3 class="text-sm font-bold text-orange-700 mb-3 uppercase tracking-widest">Dinh dưỡng</h3>
          <div class="grid grid-cols-3 gap-3">
            <div>
              <label class="text-xs font-bold text-gray-700">Calo / 100g</label>
              <input type="number" id="createCaloriesPer100g" step="0.01" class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm">
            </div>
            <div>
              <label class="text-xs font-bold text-gray-700">Carbs (g)</label>
              <input type="number" id="createCarbsG" step="0.01" class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm">
            </div>
            <div>
              <label class="text-xs font-bold text-gray-700">Đường (g)</label>
              <input type="number" id="createSugarG" step="0.01" class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm">
            </div>
          </div>
          <div class="grid grid-cols-3 gap-3 mt-3">
            <div>
              <label class="text-xs font-bold text-gray-700">Chất xơ (g)</label>
              <input type="number" id="createFiberG" step="0.01" class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm">
            </div>
            <div>
              <label class="text-xs font-bold text-gray-700">Protein (g)</label>
              <input type="number" id="createProteinG" step="0.01" class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm">
            </div>
            <div>
              <label class="text-xs font-bold text-gray-700">Fat (g)</label>
              <input type="number" id="createFatG" step="0.01" class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm">
            </div>
          </div>
          <div class="grid grid-cols-2 gap-3 mt-3">
            <div>
              <label class="text-xs font-bold text-gray-700">Vitamin C (mg)</label>
              <input type="number" id="createVitaminCMg" step="0.01" class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm">
            </div>
            <div>
              <label class="text-xs font-bold text-gray-700">Kali (mg)</label>
              <input type="number" id="createPotassiumMg" step="0.01" class="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm">
            </div>
          </div>
        </div>
      </form>

      <div class="h-4"></div>
      <div class="flex gap-3 pt-6 justify-center sticky bottom-0 bg-gradient-to-t from-white via-white to-transparent p-4 -m-4 mt-0">
        <button type="submit" form="bananaCreateModalForm" class="px-8 py-3 bg-green-500 text-white rounded-full font-bold hover:bg-green-600 shadow-lg hover:shadow-xl transition text-sm uppercase tracking-widest"><i class="fas fa-save mr-2"></i>Thêm chuối</button>
      </div>
    `
  );

  const closeCreateBtn = document.getElementById('closeCreateBananaModalBtn');
  closeCreateBtn?.addEventListener('click', closeDetailModal);

  const createForm = document.getElementById('bananaCreateModalForm');
  createForm?.addEventListener('submit', async (event) => {
    event.preventDefault();

    const payload = {
      b_name: document.getElementById('createBName').value.trim(),
      b_scientific_name: document.getElementById('createScientificName').value.trim(),
      description: document.getElementById('createDescription').value.trim(),
      origin: document.getElementById('createOrigin').value.trim(),
      taste: document.getElementById('createTaste').value.trim(),
      recommended_usage: document.getElementById('createRecommendedUsage').value.trim(),
      best_for: document.getElementById('createBestFor').value.trim(),
      storage_tip: document.getElementById('createStorageTip').value.trim(),
      calories_per_100g: toNullableNumber(document.getElementById('createCaloriesPer100g').value),
      carbs_g: toNullableNumber(document.getElementById('createCarbsG').value),
      sugar_g: toNullableNumber(document.getElementById('createSugarG').value),
      fiber_g: toNullableNumber(document.getElementById('createFiberG').value),
      protein_g: toNullableNumber(document.getElementById('createProteinG').value),
      fat_g: toNullableNumber(document.getElementById('createFatG').value),
      vitamin_c_mg: toNullableNumber(document.getElementById('createVitaminCMg').value),
      potassium_mg: toNullableNumber(document.getElementById('createPotassiumMg').value),
    };

    if (!payload.b_name) {
      alert('Vui lòng nhập tên chuối');
      return;
    }

    try {
      const res = await fetch('/api/admin/banana', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error(await res.text());
      closeDetailModal();
      await loadBananas();
    } catch (err) {
      console.error(err);
      alert('Lỗi khi thêm chuối: ' + err.message);
    }
  });
});

bananaForm?.addEventListener('submit', async (event) => {
  event.preventDefault();

  const payload = bananaPayloadFromForm();
  if (!payload.b_name) {
    alert('Vui lòng nhập tên chuối');
    return;
  }

  const isEditing = Boolean(currentBananaId);
  const url = isEditing ? `/api/admin/banana/${currentBananaId}` : '/api/admin/banana';
  const method = isEditing ? 'PUT' : 'POST';

  try {
    const res = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      throw new Error(await res.text());
    }

    const data = await res.json();
    const savedId = data.b_id || currentBananaId;
    alert(isEditing ? 'Đã lưu thay đổi' : 'Đã thêm chuối mới');
    await loadBananas(savedId);
    if (bananaForm) {
      bananaForm.classList.remove('hidden');
    }
    updateBananaInfoLayout();
  } catch (err) {
    console.error(err);
    alert('Lỗi hệ thống khi lưu chuối');
  }
});

deleteBananaBtn?.addEventListener('click', async () => {
  if (!currentBananaId) return;
  if (!confirm('Xóa loại chuối này? Dữ liệu dinh dưỡng liên quan cũng sẽ bị xóa.')) return;

  try {
    const res = await fetch(`/api/admin/banana/${currentBananaId}`, { method: 'DELETE' });
    if (!res.ok) throw new Error(await res.text());
    alert('Đã xóa chuối');
    clearBananaForm();
    await loadBananas();
    if (bananaForm) {
      bananaForm.classList.add('hidden');
    }
    updateBananaInfoLayout();
  } catch (err) {
    console.error(err);
    alert('Không xóa được chuối');
  }
});

// Export Section
async function loadExportData() {
  try {
    const res = await fetch('/api/admin/predictions');
    const data = await res.json();
    exportPredictions = data.items || [];
    applyExportFilters();
  } catch (err) {
    console.error(err);
  }
}

function applyExportFilters() {
  const filtered = exportPredictions.filter((item) => matchesDateRange(item.created_at, 'export'));
  renderExportList(filtered);
}

function renderExportList(items) {
  const list = document.getElementById('exportList');
  if (!list) return;

  if (!items.length) {
    list.innerHTML = '<p class="text-sm text-gray-400">Không có ảnh nào trong khoảng thời gian này.</p>';
    return;
  }

  list.innerHTML = items.slice(0, 120).map((item) => `
    <div class="flex items-center gap-3 p-2 rounded-lg border border-gray-100 hover:bg-gray-50">
      <img src="${item.image_url}" alt="export" class="w-12 h-12 object-cover rounded-md shrink-0">
      <div class="min-w-0 flex-1">
        <div class="text-sm font-bold text-gray-800 truncate">${item.banana_name}</div>
        <div class="text-xs text-gray-500 truncate">${item.structure_type} · ${item.ripeness_level}</div>
        <div class="text-xs text-gray-500">${item.created_at ? new Date(item.created_at).toLocaleString() : ''}</div>
      </div>
      <button class="text-blue-500 hover:text-blue-700 text-sm font-bold" onclick="downloadImage('${item.image_url}')">
        <i class="fas fa-download"></i>
      </button>
    </div>
  `).join('');
}

function refreshExportList() {
  loadExportData();
}

document.getElementById('exportFrom')?.addEventListener('change', applyExportFilters);
document.getElementById('exportTo')?.addEventListener('change', applyExportFilters);
document.getElementById('reloadExportList')?.addEventListener('click', loadExportData);

document.getElementById('exportBtn')?.addEventListener('click', async () => {
  const params = buildQuery(getDateRangeParams('export'));
  window.location.href = `/api/admin/export/download${params ? `?${params}` : ''}`;
});

function downloadImage(url) {
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = url.split('/').pop();
  anchor.click();
}
