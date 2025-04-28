/**
 * 컬럼 가시성 관련 모듈
 * 테이블 컬럼 표시/숨김 기능 담당
 */
(function() {
  /**
   * 초기화 함수
   */
  function init() {
    console.log('[Dashboard.Columns] 컬럼 가시성 모듈 초기화');
    
    const columnSelectorBtn = document.getElementById('columnSelectorBtn');
    const columnSelectorDropdown = document.getElementById('columnSelectorDropdown');
    const columnSelectorContent = document.getElementById('columnSelectorContent');
    
    if (columnSelectorBtn && columnSelectorDropdown && columnSelectorContent) {
      // 칼럼 토글 버튼 이벤트
      columnSelectorBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        columnSelectorDropdown.style.display = columnSelectorDropdown.style.display === 'none' ? 'block' : 'none';
        
        // 첫 클릭 시에만 컬럼 체크박스 생성
        if (columnSelectorContent.children.length === 0) {
          loadColumnOptions();
        }
      });
      
      // 외부 클릭 시 드롭다운 닫기
      document.addEventListener('click', function(e) {
        if (!columnSelectorBtn.contains(e.target) && !columnSelectorDropdown.contains(e.target)) {
          columnSelectorDropdown.style.display = 'none';
        }
      });
    }
    
    // 저장된 컬럼 가시성 설정 로드
    loadColumnVisibility();
    
    return true;
  }
  
  /**
   * 컬럼 옵션을 로드합니다.
   */
  function loadColumnOptions() {
    const columnSelectorContent = document.getElementById('columnSelectorContent');
    if (!columnSelectorContent) return;
    
    // 모든 컬럼 헤더에서 컬럼 정보 추출
    const columns = [];
    document.querySelectorAll('#orderTable th').forEach(th => {
      // 체크박스 컬럼은 항상 표시하고 커스터마이징 옵션에서 제외
      if (th.classList.contains('column-checkbox') || th.classList.contains('checkbox-column')) return;
      
      const columnClass = Array.from(th.classList).find(cls => cls.startsWith('column-'));
      if (columnClass) {
        const columnName = columnClass.replace('column-', '');
        const columnLabel = th.textContent.trim();
        
        columns.push({
          name: columnName,
          label: columnLabel,
          class: columnClass
        });
      }
    });
    
    // 저장된 설정 로드
    const savedVisibility = localStorage.getItem('orderTableColumns');
    const visibilitySettings = savedVisibility ? JSON.parse(savedVisibility) : {};
    
    // 컬럼 체크박스 생성
    columns.forEach(column => {
      const isVisible = visibilitySettings[column.name] === undefined ? true : visibilitySettings[column.name];
      
      const checkboxContainer = document.createElement('div');
      checkboxContainer.className = 'column-checkbox-container';
      
      const checkbox = document.createElement('input');
      checkbox.type = 'checkbox';
      checkbox.id = `column-${column.name}`;
      checkbox.className = 'column-checkbox';
      checkbox.dataset.column = column.name;
      checkbox.dataset.class = column.class;
      checkbox.checked = isVisible;
      
      const label = document.createElement('label');
      label.htmlFor = `column-${column.name}`;
      label.textContent = column.label;
      
      checkboxContainer.appendChild(checkbox);
      checkboxContainer.appendChild(label);
      columnSelectorContent.appendChild(checkboxContainer);
      
      // 체크박스 변경 이벤트
      checkbox.addEventListener('change', function() {
        toggleColumnVisibility(column.name, column.class, this.checked);
      });
    });
  }
  
  /**
   * 컬럼 가시성 설정을 로드합니다.
   */
  function loadColumnVisibility() {
    const savedVisibility = localStorage.getItem('orderTableColumns');
    if (!savedVisibility) return;
    
    const visibilitySettings = JSON.parse(savedVisibility);
    
    // 각 컬럼에 가시성 설정 적용
    Object.entries(visibilitySettings).forEach(([columnName, isVisible]) => {
      const columnClass = `column-${columnName}`;
      toggleColumnVisibility(columnName, columnClass, isVisible, false);
    });
  }
  
  /**
   * 컬럼 가시성을 토글합니다.
   * @param {string} columnName - 컬럼 이름
   * @param {string} columnClass - 컬럼 클래스
   * @param {boolean} visible - 표시 여부
   * @param {boolean} [save=true] - 설정 저장 여부
   */
  function toggleColumnVisibility(columnName, columnClass, visible, save = true) {
    // 헤더와 셀에 가시성 적용
    document.querySelectorAll(`th.${columnClass}, td.${columnClass}`).forEach(el => {
      el.style.display = visible ? '' : 'none';
    });
    
    // 설정 저장
    if (save) {
      const savedVisibility = localStorage.getItem('orderTableColumns');
      const visibilitySettings = savedVisibility ? JSON.parse(savedVisibility) : {};
      
      visibilitySettings[columnName] = visible;
      localStorage.setItem('orderTableColumns', JSON.stringify(visibilitySettings));
    }
  }
  
  // 대시보드 모듈에 등록
  Dashboard.registerModule('columns', {
    init: init,
    toggleColumnVisibility: toggleColumnVisibility
  });
})();