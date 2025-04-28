console.log('[로드] dashboard/checkbox.js 로드됨 - ' + new Date().toISOString());

/**
 * 체크박스 관리 모듈
 * 테이블 내 체크박스 선택 상태 관리 및 일괄 처리 제공
 */
(function() {
  // 선택된 항목 ID 저장
  const selectedIds = new Set();
  
  // 액션 패널 요소
  let actionPanel = null;
  
  /**
   * 초기화 함수
   */
  function init() {
    console.log('[Dashboard.Checkbox] 체크박스 모듈 초기화 시작');
    
    // 중복 실행 방지
    if (document.querySelector('th.column-checkbox')) {
      console.warn('[Dashboard.Checkbox] 체크박스 열이 이미 존재합니다. 초기화를 건너뜁니다.');
      return;
    }
    
    // 테이블에 체크박스 열 추가
    addCheckboxColumn();
    
    // 액션 패널 초기화
    initActionPanel();
    
    // 이벤트 리스너 등록
    registerEventListeners();
    
    console.log('[Dashboard.Checkbox] 체크박스 모듈 초기화 완료');
    return true;
  }
  
  /**
   * 테이블에 체크박스 열 추가
   */
  function addCheckboxColumn() {
    // 테이블 헤더에 체크박스 열 추가
    const thead = document.querySelector('#orderTable thead tr');
    if (thead) {
      const checkboxTh = document.createElement('th');
      checkboxTh.className = 'column-checkbox checkbox-column';
      checkboxTh.style.width = '40px';
      
      const headerCheckbox = document.createElement('input');
      headerCheckbox.type = 'checkbox';
      headerCheckbox.id = 'selectAllCheckbox';
      headerCheckbox.className = 'table-checkbox';
      
      checkboxTh.appendChild(headerCheckbox);
      thead.insertBefore(checkboxTh, thead.firstChild);
    }
    
    // 각 행에 체크박스 추가
    const rows = document.querySelectorAll('#orderTable tbody tr:not(.no-data-row)');
    rows.forEach(row => {
      const id = row.dataset.id;
      if (id) {
        const checkboxTd = document.createElement('td');
        checkboxTd.className = 'column-checkbox checkbox-column';
        
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.className = 'row-checkbox';
        checkbox.dataset.id = id;
        
        checkboxTd.appendChild(checkbox);
        row.insertBefore(checkboxTd, row.firstChild);
      }
    });
  }
  
  /**
   * 일괄 처리 액션 패널 초기화
   */
  function initActionPanel() {
    // 액션 패널 생성
    actionPanel = document.createElement('div');
    actionPanel.className = 'bulk-action-panel';
    actionPanel.style.display = 'none';
    
    actionPanel.innerHTML = `
      <div class="bulk-action-info">
        <span class="selected-count">0</span>개 항목 선택됨
      </div>
      <div class="bulk-action-buttons">
        <button type="button" class="bulk-btn status-btn" id="bulkStatusBtn">
          <i class="fas fa-exchange-alt"></i> 상태 변경
        </button>
        <button type="button" class="bulk-btn driver-btn" id="bulkDriverBtn">
          <i class="fas fa-user"></i> 기사 배정
        </button>
        <!-- 일괄 삭제 버튼 제거 -->
      </div>
      <button type="button" class="bulk-action-clear" id="clearSelectionBtn">
        <i class="fas fa-times"></i>
      </button>
    `;
    
    // 액션 패널을 테이블 위에 추가
    const tableContainer = document.querySelector('.order-table-container');
    if (tableContainer) {
      tableContainer.parentNode.insertBefore(actionPanel, tableContainer);
    }
  }
  
  /**
   * 이벤트 리스너 등록
   */
  function registerEventListeners() {
    // 전체 선택 체크박스 이벤트
    const selectAllCheckbox = document.getElementById('selectAllCheckbox');
    if (selectAllCheckbox) {
      selectAllCheckbox.addEventListener('change', function() {
        selectAll(this.checked);
      });
    }
    
    // 개별 체크박스 이벤트 위임
    const orderTable = document.getElementById('orderTable');
    if (orderTable) {
      orderTable.addEventListener('change', function(event) {
        const checkbox = event.target;
        if (checkbox.classList.contains('row-checkbox')) {
          const id = checkbox.dataset.id;
          if (id) {
            toggleSelection(id, checkbox.checked);
          }
        }
      });
      
      // 행 클릭 시 체크박스 토글 방지 (체크박스 영역 제외)
      orderTable.addEventListener('click', function(event) {
        // 체크박스 또는 체크박스 컬럼을 직접 클릭한 경우는 제외
        if (event.target.classList.contains('row-checkbox') || 
            event.target.classList.contains('column-checkbox') ||
            event.target.closest('.column-checkbox')) {
          event.stopPropagation(); // 이벤트 전파 중지
          return;
        }
        
        // 행 내부의 다른 요소 클릭 시 이벤트 전파 방지 안함
        // 체크박스와 행 클릭은 분리된 기능으로 동작
      });
    }
    
    // 액션 버튼 이벤트 등록
    const bulkStatusBtn = document.getElementById('bulkStatusBtn');
    const bulkDriverBtn = document.getElementById('bulkDriverBtn');
    const clearSelectionBtn = document.getElementById('clearSelectionBtn');
    
    if (bulkStatusBtn) {
      bulkStatusBtn.addEventListener('click', function() {
        if (selectedIds.size > 0) {
          if (window.statusChangeModal && typeof window.statusChangeModal.show === 'function') {
            window.statusChangeModal.show(Array.from(selectedIds));
          } else {
            console.warn('[Dashboard.Checkbox] 상태 변경 모달이 없습니다.');
          }
        }
      });
    }
    
    if (bulkDriverBtn) {
      bulkDriverBtn.addEventListener('click', function() {
        if (selectedIds.size > 0) {
          if (window.driverAssignModal && typeof window.driverAssignModal.show === 'function') {
            window.driverAssignModal.show(Array.from(selectedIds));
          } else {
            console.warn('[Dashboard.Checkbox] 기사 배정 모달이 없습니다.');
          }
        }
      });
    }
    
    if (clearSelectionBtn) {
      clearSelectionBtn.addEventListener('click', function() {
        clearSelection();
      });
    }
  }
  
  /**
   * 전체 항목 선택/해제
   * @param {boolean} checked - 선택 여부
   */
  function selectAll(checked) {
    const checkboxes = document.querySelectorAll('.row-checkbox');
    
    checkboxes.forEach(checkbox => {
      checkbox.checked = checked;
      const id = checkbox.dataset.id;
      if (id) {
        toggleSelection(id, checked, false); // 업데이트 안함
      }
    });
    
    // 선택 상태 업데이트
    updateSelection();
  }
  
  /**
   * 개별 항목 선택/해제
   * @param {string} id - 항목 ID
   * @param {boolean} checked - 선택 여부
   * @param {boolean} updateUI - UI 업데이트 여부
   */
  function toggleSelection(id, checked, updateUI = true) {
    if (checked) {
      selectedIds.add(id);
    } else {
      selectedIds.delete(id);
    }
    
    if (updateUI) {
      updateSelection();
    }
  }
  
  /**
   * 선택 항목 수에 따른 UI 업데이트
   */
  function updateSelection() {
    // 선택 개수 표시
    const selectedCount = selectedIds.size;
    const countElement = document.querySelector('.selected-count');
    if (countElement) {
      countElement.textContent = selectedCount;
    }
    
    // 액션 패널 표시/숨김
    if (actionPanel) {
      actionPanel.style.display = selectedCount > 0 ? 'flex' : 'none';
    }
    
    // 전체 선택 체크박스 상태 업데이트
    const selectAllCheckbox = document.getElementById('selectAllCheckbox');
    const checkboxes = document.querySelectorAll('.row-checkbox');
    
    if (selectAllCheckbox && checkboxes.length > 0) {
      selectAllCheckbox.checked = selectedCount > 0 && selectedCount === checkboxes.length;
      selectAllCheckbox.indeterminate = selectedCount > 0 && selectedCount < checkboxes.length;
    }
    
    // 삭제 버튼 제거 - 상세정보에서만 삭제 가능하도록 함
    
    // 상단 메인 버튼 활성화/비활성화 처리
    const mainStatusBtn = document.getElementById('mainStatusBtn');
    const mainDriverBtn = document.getElementById('mainDriverBtn');
    
    if (mainStatusBtn) {
      if (selectedCount > 0) {
        mainStatusBtn.classList.remove('disabled');
        mainStatusBtn.onclick = function() {
          if (window.statusChangeModal && typeof window.statusChangeModal.show === 'function') {
            window.statusChangeModal.show(Array.from(selectedIds));
          } else if (window.bulkStatusBtn && window.bulkStatusBtn.click) {
            window.bulkStatusBtn.click(); // 기존 버튼 클릭 이벤트 트리거
          }
        };
      } else {
        mainStatusBtn.classList.add('disabled');
        mainStatusBtn.onclick = null;
      }
    }
    
    if (mainDriverBtn) {
      if (selectedCount > 0) {
        mainDriverBtn.classList.remove('disabled');
        mainDriverBtn.onclick = function() {
          if (window.driverAssignModal && typeof window.driverAssignModal.show === 'function') {
            window.driverAssignModal.show(Array.from(selectedIds));
          } else if (window.bulkDriverBtn && window.bulkDriverBtn.click) {
            window.bulkDriverBtn.click(); // 기존 버튼 클릭 이벤트 트리거
          }
        };
      } else {
        mainDriverBtn.classList.add('disabled');
        mainDriverBtn.onclick = null;
      }
    }
  }
  
  /**
   * 선택 초기화
   */
  function clearSelection() {
    // 모든 체크박스 해제
    const checkboxes = document.querySelectorAll('.row-checkbox');
    checkboxes.forEach(checkbox => {
      checkbox.checked = false;
    });
    
    // 전체 선택 체크박스 해제
    const selectAllCheckbox = document.getElementById('selectAllCheckbox');
    if (selectAllCheckbox) {
      selectAllCheckbox.checked = false;
      selectAllCheckbox.indeterminate = false;
    }
    
    // 선택 항목 초기화
    selectedIds.clear();
    
    // UI 업데이트
    updateSelection();
  }
  
  /**
   * 선택된 항목 ID 배열 반환
   * @returns {Array<string>} - 선택된 항목 ID 배열
   */
  function getSelectedIds() {
    return Array.from(selectedIds);
  }
  
  // 대시보드 모듈에 등록
  if (window.Dashboard) {
    window.Dashboard.registerModule('checkbox', {
      init: init,
      getSelectedIds: getSelectedIds,
      clearSelection: clearSelection
    });
  }
})();