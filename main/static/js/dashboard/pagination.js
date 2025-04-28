console.log('[로드] dashboard/pagination.js 로드됨 - ' + new Date().toISOString());

/**
 * 페이지네이션 관련 모듈
 * 테이블 페이지네이션 기능 담당
 */
(function() {
  /**
   * 초기화 함수
   */
  function init() {
    console.log('[Dashboard.Pagination] 페이지네이션 모듈 초기화');
    
    // 페이지네이션 영역 참조
    const pagination = document.querySelector('.pagination');
    if (!pagination) {
      console.warn('[Dashboard.Pagination] 페이지네이션 영역을 찾을 수 없습니다.');
      return false;
    }
    
    try {
      // 이벤트 리스너 설정
      setupEventListeners();
      
      // 기본 페이지 크기 설정 (로컬 스토리지에서 값 복원)
      const savedPageSize = localStorage.getItem('dashboardPageSize');
      const pageSizeSelect = document.getElementById('pageSizeSelect');
      
      if (pageSizeSelect) {
        // 저장된 값이 있으면 복원
        if (savedPageSize && !isNaN(parseInt(savedPageSize))) {
          pageSizeSelect.value = savedPageSize;
        }
        
        const pageSize = parseInt(pageSizeSelect.value) || 10;
        setTimeout(() => changePageSize(pageSize), 100);
      }
      
      return true;
    } catch (error) {
      console.error('[Dashboard.Pagination] 초기화 중 오류 발생', error);
      return false;
    }
  }
  
  /**
   * 이벤트 리스너 설정
   */
  function setupEventListeners() {
    const pagination = document.querySelector('.pagination');
    const pageNumberContainer = document.getElementById('pageNumberContainer');
    const prevPageBtn = document.getElementById('prevPageBtn');
    const nextPageBtn = document.getElementById('nextPageBtn');
    const pageSizeSelect = document.getElementById('pageSizeSelect');
    
    if (!pagination || !pageNumberContainer || !prevPageBtn || !nextPageBtn) {
      console.warn('[Dashboard.Pagination] 페이지네이션 요소를 찾을 수 없습니다.');
      return;
    }
    
    // 페이지네이션 영역에 이벤트 위임 적용
    pagination.addEventListener('click', function(e) {
      const button = e.target.closest('.page-number-btn');
      if (button) {
        const page = parseInt(button.dataset.page);
        if (!isNaN(page)) {
          goToPage(page);
        }
      }
    });
    
    // 이전 페이지 버튼
    prevPageBtn.addEventListener('click', function() {
      const currentPage = parseInt(pagination.dataset.currentPage) || 1;
      if (currentPage > 1) {
        goToPage(currentPage - 1);
      }
    });
    
    // 다음 페이지 버튼
    nextPageBtn.addEventListener('click', function() {
      const currentPage = parseInt(pagination.dataset.currentPage) || 1;
      const totalPages = parseInt(pagination.dataset.totalPages) || 1;
      if (currentPage < totalPages) {
        goToPage(currentPage + 1);
      }
    });
    
    // 페이지 크기 변경 이벤트
    if (pageSizeSelect) {
      pageSizeSelect.addEventListener('change', function() {
        const pageSize = parseInt(this.value);
        if (!isNaN(pageSize) && pageSize > 0) {
          changePageSize(pageSize);
          
          // 페이지 크기 변경 시 로그 추가
          console.log('[Dashboard.Pagination] 페이지 크기 변경됨:', pageSize);
        }
      });
    }
  }
  
  /**
   * 페이지 크기 변경
   * @param {number} pageSize - 페이지당 표시할 행 수
   */
  function changePageSize(pageSize) {
    if (!pageSize || pageSize < 1) {
      console.warn('[Dashboard.Pagination] 유효하지 않은 페이지 크기:', pageSize);
      return;
    }
    
    console.log('[Dashboard.Pagination] 페이지 크기 변경:', pageSize);
    
    try {
      // 모든 테이블 행
      const allRows = document.querySelectorAll('#orderTable tbody tr[data-id]');
      const totalRows = allRows.length;
      
      if (totalRows === 0) {
        console.log('[Dashboard.Pagination] 표시할 행이 없습니다.');
        return;
      }
      
      // 현재 표시되는 행만 고려 (필터링이 적용된 상태일 수 있음)
      const visibleRows = Array.from(allRows).filter(row => {
        // style.display가 ''(빈 문자열) 또는 'table-row'인 경우 보이는 행으로 간주
        return row.style.display === '' || row.style.display === 'table-row' || 
               (row.style.display !== 'none' && !row.classList.contains('no-data-row'));
      });
      const visibleRowCount = visibleRows.length;
      
      console.log(`[Dashboard.Pagination] 전체 행: ${totalRows}, 필터 후 표시 행: ${visibleRowCount}`);
      
      // 페이지네이션 정보 업데이트
      const totalPages = Math.ceil(visibleRowCount / pageSize) || 1; // 최소 1페이지
      const currentPage = 1; // 페이지 크기 변경 시 첫 페이지로 이동
      
      // 페이지 번호 UI 업데이트
      updatePaginationUI(currentPage, totalPages, pageSize);
      
      // 행 표시/숨김 처리
      updateVisibleRows(visibleRows, currentPage, pageSize);
      
      // 페이지네이션 정보 텍스트 업데이트
      updatePaginationInfo(visibleRowCount, currentPage, pageSize);
      
      // 페이지 크기 선택 요소 값 업데이트
      const pageSizeSelect = document.getElementById('pageSizeSelect');
      if (pageSizeSelect) {
        pageSizeSelect.value = pageSize.toString();
      }
      
      // 로컬 스토리지에 설정 저장 (페이지 새로고침 후에도 유지)
      localStorage.setItem('dashboardPageSize', pageSize.toString());
    } catch (error) {
      console.error('[Dashboard.Pagination] 페이지 크기 변경 중 오류', error);
    }
  }
  
  /**
   * 페이지네이션 UI 업데이트
   * @param {number} currentPage - 현재 페이지
   * @param {number} totalPages - 전체 페이지 수
   * @param {number} pageSize - 페이지 크기
   */
  function updatePaginationUI(currentPage, totalPages, pageSize) {
    const pagination = document.querySelector('.pagination');
    const pageNumberContainer = document.getElementById('pageNumberContainer');
    const prevPageBtn = document.getElementById('prevPageBtn');
    const nextPageBtn = document.getElementById('nextPageBtn');
    
    if (!pageNumberContainer || !prevPageBtn || !nextPageBtn) {
      console.warn('[Dashboard.Pagination] 페이지네이션 UI 요소를 찾을 수 없습니다.');
      return;
    }
    
    // 페이지 번호 버튼 생성
    pageNumberContainer.innerHTML = '';
    
    // 표시할 페이지 번호 범위 계산 (최대 5개)
    let startPage = Math.max(1, currentPage - 2);
    let endPage = Math.min(totalPages, startPage + 4);
    
    // 범위 조정 (5개 이상 표시하도록)
    if (endPage - startPage < 4) {
      startPage = Math.max(1, endPage - 4);
    }
    
    // 페이지 번호 버튼 생성
    for (let i = startPage; i <= endPage; i++) {
      const pageButton = document.createElement('button');
      pageButton.type = 'button';
      pageButton.className = `page-number-btn ${i === currentPage ? 'active' : ''}`;
      pageButton.textContent = i;
      pageButton.dataset.page = i;
      pageNumberContainer.appendChild(pageButton);
    }
    
    // 이전/다음 버튼 상태 업데이트
    prevPageBtn.disabled = currentPage <= 1;
    nextPageBtn.disabled = currentPage >= totalPages;
    
    // 페이지네이션 데이터 저장 (이벤트 위임에서 사용)
    pagination.dataset.currentPage = currentPage;
    pagination.dataset.totalPages = totalPages;
    pagination.dataset.pageSize = pageSize;
  }
  
  /**
   * 지정된 페이지로 이동
   * @param {number} page - 이동할 페이지 번호
   */
  function goToPage(page) {
    if (!page || page < 1) {
      console.warn('[Dashboard.Pagination] 유효하지 않은 페이지:', page);
      return;
    }
    
    console.log('[Dashboard.Pagination] 페이지 이동:', page);
    
    try {
      // 현재 표시되는 행만 고려 (필터링이 적용된 상태일 수 있음)
      const allRows = document.querySelectorAll('#orderTable tbody tr[data-id]');
      const visibleRows = Array.from(allRows).filter(row => {
        return row.dataset.id && 
              (row.style.display === '' || row.style.display === 'table-row' || row.style.display !== 'none') && 
              !row.classList.contains('no-data-row');
      });
      
      const visibleRowCount = visibleRows.length;
      const pagination = document.querySelector('.pagination');
      const pageSize = parseInt(pagination.dataset.pageSize) || 10;
      const totalPages = Math.ceil(visibleRowCount / pageSize);
      
      // 페이지 범위 확인
      if (page > totalPages) {
        page = totalPages || 1; // 최소 1페이지
      }
      
      // 페이지네이션 UI 업데이트
      updatePaginationUI(page, totalPages, pageSize);
      
      // 행 표시/숨김 처리
      updateVisibleRows(visibleRows, page, pageSize);
      
      // 페이지네이션 정보 텍스트 업데이트
      updatePaginationInfo(visibleRowCount, page, pageSize);
    } catch (error) {
      console.error('[Dashboard.Pagination] 페이지 이동 중 오류', error);
    }
  }
  
  /**
   * 표시할 행 업데이트
   * @param {Array<HTMLElement>} visibleRows - 표시 가능한 행 배열
   * @param {number} currentPage - 현재 페이지
   * @param {number} pageSize - 페이지 크기
   */
  function updateVisibleRows(visibleRows, currentPage, pageSize) {
    const startIndex = (currentPage - 1) * pageSize;
    const endIndex = Math.min(startIndex + pageSize, visibleRows.length);
    
    // 모든 행 숨김 (no-data-row 제외)
    visibleRows.forEach(row => {
      row.style.display = 'none';
    });
    
    // 현재 페이지에 해당하는 행만 표시
    for (let i = startIndex; i < endIndex; i++) {
      if (visibleRows[i]) {
        visibleRows[i].style.display = '';
      }
    }
    
    // 데이터가 없는 경우 처리
    const noDataRow = document.querySelector('.no-data-row');
    if (visibleRows.length === 0) {
      // 데이터 없음 메시지 표시
      if (noDataRow) {
        noDataRow.style.display = '';
        noDataRow.querySelector('.no-data-cell').textContent = '표시할 데이터가 없습니다';
      }
    } else {
      // 데이터 없음 메시지 숨김
      if (noDataRow) {
        noDataRow.style.display = 'none';
      }
    }
    
    // 현재 표시된 행 상태 로그
    console.log(`[Dashboard.Pagination] 페이지 ${currentPage}: ${startIndex}-${endIndex} 행 표시 중 (총 ${visibleRows.length}개)`);
  }
  
  /**
   * 페이지네이션 정보 텍스트 업데이트
   * @param {number} totalItems - 전체 항목 수
   * @param {number} currentPage - 현재 페이지
   * @param {number} pageSize - 페이지 크기
   */
  function updatePaginationInfo(totalItems, currentPage, pageSize) {
    const paginationInfo = document.querySelector('.pagination-info');
    if (!paginationInfo) return;
    
    const startItem = totalItems === 0 ? 0 : (currentPage - 1) * pageSize + 1;
    const endItem = Math.min(startItem + pageSize - 1, totalItems);
    
    paginationInfo.textContent = `총 ${totalItems}개 항목 중 ${startItem}-${endItem} 표시`;
    
    // 데이터 속성 업데이트 (UI 외 데이터 저장용)
    paginationInfo.dataset.total = totalItems;
    paginationInfo.dataset.totalPages = Math.ceil(totalItems / pageSize) || 1;
    paginationInfo.dataset.current = currentPage;
    paginationInfo.dataset.pageSize = pageSize;
    paginationInfo.dataset.start = startItem;
    paginationInfo.dataset.end = endItem;
  }
  
  /**
   * 페이지네이션 리셋 (필터링 등으로 데이터 변경 시 호출)
   */
  function reset() {
    // 현재 페이지 크기 확인
    const pageSizeSelect = document.getElementById('pageSizeSelect');
    if (!pageSizeSelect) return;
    
    const pageSize = parseInt(pageSizeSelect.value);
    if (!pageSize || pageSize < 1) return;
    
    // 페이지네이션 업데이트
    changePageSize(pageSize);
  }
  
  // 대시보드 모듈에 등록
  Dashboard.registerModule('pagination', {
    init: init,
    changePageSize: changePageSize,
    goToPage: goToPage,
    reset: reset
  });
})();