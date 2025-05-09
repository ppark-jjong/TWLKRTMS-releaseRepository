document.addEventListener('DOMContentLoaded', function () {
  // --- DOM 요소 가져오기 ---
  const loadingOverlay = document.getElementById('loadingOverlay');
  const typeFilter = document.getElementById('typeFilter');
  const departmentFilter = document.getElementById('departmentFilter');
  const refreshBtn = document.getElementById('refreshBtn');
  const handoverTableHead = document.getElementById('handoverTableHead');
  const handoverTableBody = document.getElementById('handoverTableBody');
  const paginationControls = document.getElementById('paginationControls');
  const pageInfo = document.getElementById('pageInfo');
  const prevPageBtn = paginationControls?.querySelector('[data-page="prev"]'); // Optional chaining
  const nextPageBtn = paginationControls?.querySelector('[data-page="next"]'); // Optional chaining
  const statusFilter = document.getElementById('statusFilter'); // 상태 필터 DOM 요소 추가
  const errorMessageContainer = document.getElementById(
    'errorMessageContainer'
  );
  const errorMessageText = document.getElementById('errorMessageText');

  // --- 상태 변수 ---
  let allItems = [];
  let filteredItems = [];
  let currentPage = 1;
  let rowsPerPage = 30;
  let totalItems = 0;
  let totalPages = 1;
  let initialLoadComplete = false;
  let currentTypeFilter = 'all'; // 유형 필터 변수
  let currentDeptFilter = 'all'; // 부서 필터 변수 (all로 다시 변경)
  let currentStatusFilter = 'all'; // 상태 필터 변수 추가
  let sortField = 'update_at'; // 정렬 필드 (기본값: update_at)
  let sortDirection = 'desc'; // 정렬 방향 (기본값: 내림차순)

  // 날짜 포맷 함수 (dashboard.js 와 유사하게 추가)
  function formatDateTime(isoString) {
    if (!isoString) return '-';
    try {
      const date = new Date(isoString);
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      const hours = String(date.getHours()).padStart(2, '0');
      const minutes = String(date.getMinutes()).padStart(2, '0');
      return `${year}-${month}-${day} ${hours}:${minutes}`;
    } catch (e) {
      return '-';
    }
  }

  // 상태 라벨
  const statusLabels = { OPEN: 'OPEN', CLOSE: 'CLOSE' };

  // --- 초기화 함수 ---
  function initHandover() {
    showLoading();

    // 비동기적으로 전체 데이터 로드
    fetchAllItems()
      .then(() => {
        initialLoadComplete = true;
        console.log('Initial full data load complete.');
        applyFiltersAndRender();
        hideLoading();
      })
      .catch((error) => {
        console.error('Error fetching initial full data:', error);
        showError('데이터를 불러오는 중 오류가 발생했습니다.');
        hideLoading();
      });

    setupEventListeners();
    renderTableHeader(); // 테이블 헤더 렌더링 추가
  }

  // --- 데이터 처리 함수 ---
  async function fetchAllItems() {
    showLoading();
    clearError();
    console.log('Fetching all handovers and notices using Utils.api...');
    try {
      // Utils.api.get 사용
      const result = await Utils.api.get('/api/handover/list');

      if (result && result.success && result.data) {
        allItems = result.data;
        sortHandoverData(); // 정렬 적용
        totalItems = allItems.length;
        currentPage = 1;
        console.log(`Successfully fetched ${allItems.length} total items.`);
      } else {
        // Utils.api.get에서 실패 응답(success:false)을 반환했거나 데이터가 없는 경우
        throw new Error(
          result?.message || 'Failed to fetch handover/notice data'
        );
      }
    } catch (error) {
      // Utils.api.get 내부에서 throw된 에러 또는 위에서 throw한 에러 처리
      console.error('Error in fetchAllItems:', error);
      showError(`데이터 조회 실패: ${error.message || '알 수 없는 오류'}`);
      allItems = [];
      applyFiltersAndRender(); // 오류 시 빈 테이블 표시
      throw error;
    }
  }

  // 인수인계 데이터 정렬 함수
  function sortHandoverData() {
    if (!sortField) return;

    allItems.sort((a, b) => {
      let valA, valB;
      // 정렬 필드에 따라 값 가져오기
      if (sortField === 'update_at' || sortField === 'create_time') {
        // create_time 추가
        valA = new Date(a[sortField] || 0);
        valB = new Date(b[sortField] || 0);
      } else {
        // 다른 필드는 문자열로 비교 (필요시 확장)
        valA = a[sortField] || '';
        valB = b[sortField] || '';
      }

      // 비교 로직
      let comparison = 0;
      if (valA < valB) {
        comparison = -1;
      } else if (valA > valB) {
        comparison = 1;
      }

      return sortDirection === 'asc' ? comparison : comparison * -1;
    });
  }

  // 현재 필터 및 페이지 상태에 따라 테이블 렌더링
  function applyFiltersAndRender() {
    const selectedType = typeFilter ? typeFilter.value : 'all'; // typeFilter null 체크
    const selectedDept = departmentFilter ? departmentFilter.value : 'all'; // departmentFilter null 체크
    const selectedStatus = statusFilter ? statusFilter.value : 'all'; // 상태 필터 값 가져오기
    currentTypeFilter = selectedType;
    currentDeptFilter = selectedDept;
    currentStatusFilter = selectedStatus; // 현재 상태 필터 값 업데이트
    console.log(
      `Applying filter type='${selectedType}', dept='${selectedDept}', status='${selectedStatus}' and rendering page ${currentPage}`
    );

    filteredItems = allItems.filter((item) => {
      // 유형 필터링
      const typeMatch =
        currentTypeFilter === 'all'
          ? true
          : currentTypeFilter === 'notice'
          ? item.is_notice === true
          : item.is_notice === false;

      // 부서 필터링 (대소문자 구분 없이 처리)
      const deptMatch =
        currentDeptFilter === 'all'
          ? true
          : (item.department || '').toUpperCase() === 
            currentDeptFilter.toUpperCase();

      // 상태 필터링 추가
      const statusMatch =
        currentStatusFilter === 'all'
          ? true
          : (item.status || '').toUpperCase() ===
            currentStatusFilter.toUpperCase();

      // 모든 조건 충족해야 함
      return typeMatch && deptMatch && statusMatch;
    });

    totalItems = filteredItems.length;
    console.log(`Filtered items count: ${totalItems}`);

    totalPages = Math.ceil(totalItems / rowsPerPage) || 1;
    currentPage = Math.max(1, Math.min(currentPage, totalPages));

    const startIndex = (currentPage - 1) * rowsPerPage;
    const endIndex = startIndex + rowsPerPage;
    const pageItems = filteredItems.slice(startIndex, endIndex);
    console.log(`Rendering ${pageItems.length} items for page ${currentPage}`);

    renderHandoverTableRows(pageItems);
    updatePaginationUI();
  }

  // 테이블 헤더 렌더링
  function renderTableHeader() {
    if (!handoverTableHead) return;

    // 각 컬럼별 정렬 아이콘 결정 함수
    function getSortIcon(field) {
      if (field !== sortField) {
        return '<i class="fa-solid fa-sort"></i>';
      }
      return sortDirection === 'asc'
        ? '<i class="fa-solid fa-sort-up"></i>'
        : '<i class="fa-solid fa-sort-down"></i>';
    }

    // 헤더 HTML 생성
    let headerHTML = '<tr>';
    headerHTML += '<th class="col-title">제목</th>';
    headerHTML += '<th class="col-type">구분</th>';
    headerHTML += '<th class="col-dept">부서</th>';
    headerHTML += `<th class="col-date sortable-header" data-sort="create_time">생성일시 ${getSortIcon(
      'create_time'
    )}</th>`;
    headerHTML += `<th class="col-date sortable-header" data-sort="update_at">최종수정일 ${getSortIcon(
      'update_at'
    )}</th>`;
    headerHTML += '<th class="col-status">상태</th>';
    headerHTML += '<th class="col-writer">작성자</th>';
    headerHTML += '</tr>';

    handoverTableHead.innerHTML = headerHTML;

    // 모든 정렬 가능한 헤더에 이벤트 리스너 추가
    const sortHeaders = handoverTableHead.querySelectorAll('.sortable-header');
    if (sortHeaders && sortHeaders.length > 0) {
      sortHeaders.forEach((header) => {
        header.addEventListener('click', function () {
          const field = this.getAttribute('data-sort');

          // 같은 필드 클릭 시 정렬 방향 전환
          if (field === sortField) {
            sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
          } else {
            sortField = field;
            sortDirection = 'desc'; // 새 필드 처음 클릭 시 내림차순
          }

          sortHandoverData(); // 데이터 정렬
          renderTableHeader(); // 헤더 다시 그리기 (정렬 아이콘 업데이트)
          applyFiltersAndRender(); // 테이블 본문 다시 그리기
        });
      });
    }
  }

  // 테이블 행 HTML 생성 및 업데이트
  function renderHandoverTableRows(items) {
    if (!handoverTableBody) {
      console.error('handoverTableBody element not found');
      return;
    }

    // 데이터 없는 경우 처리
    if (!items || items.length === 0) {
      handoverTableBody.innerHTML = `
        <tr class="no-data-row">
          <td colspan="7" class="no-data-cell">데이터가 없습니다.</td>
        </tr>
      `;
      console.log('No items to render');
      return;
    }

    // 각 행 데이터 렌더링
    const rows = items.map((item) => {
      // 필요한 데이터 추출 및 포맷
      const id = item.handover_id || '';
      const title = item.title || '';
      const createAt = formatDateTime(item.create_time);
      const updateAt = formatDateTime(item.update_at);
      const creatorName = item.creator_name || '-';
      const department = item.department === 'ALL' ? '전체' : item.department || 'CS';
      const statusLabel = statusLabels[item.status] || item.status;

      // 공지사항 여부에 따라 스타일 다르게 적용
      const rowClass = item.is_notice ? 'notice-row' : 'handover-row';
      const typeText = item.is_notice ? '공지사항' : '인수인계';
      const deptText = department;

      return `
        <tr class="clickable-row ${rowClass}" data-id="${id}">
          <td class="col-title">${title}</td>
          <td class="col-type">${typeText}</td>
          <td class="col-dept">${deptText}</td>
          <td class="col-date">${createAt}</td>
          <td class="col-date">${updateAt}</td>
          <td class="col-status">${statusLabel}</td>
          <td class="col-writer">${creatorName}</td>
        </tr>
      `;
    });

    handoverTableBody.innerHTML = rows.join('');
  }

  // 페이지네이션 UI 업데이트
  function updatePaginationUI() {
    if (!pageInfo || !prevPageBtn || !nextPageBtn) return;
    pageInfo.textContent = `${currentPage} / ${totalPages}`;
    prevPageBtn.disabled = currentPage <= 1;
    nextPageBtn.disabled = currentPage >= totalPages;
  }

  // --- 유틸리티 함수 ---
  function showLoading() {
    // Utils.ui 사용
    Utils.ui?.showLoading();
  }
  function hideLoading() {
    // Utils.ui 사용
    Utils.ui?.hideLoading();
  }
  function showError(message) {
    // Utils.alerts 사용
    Utils.alerts?.showError(message);
  }
  function clearError() {
    // 오류는 Utils.alerts가 관리하므로 이 함수는 불필요하거나, 특정 UI를 직접 지우도록 수정
    if (errorMessageContainer) errorMessageContainer.style.display = 'none';
  }

  // --- 이벤트 리스너 설정 ---
  function setupEventListeners() {
    typeFilter?.addEventListener('change', () => {
      currentPage = 1; // 필터 변경 시 첫 페이지로
      applyFiltersAndRender();
    });

    departmentFilter?.addEventListener('change', () => {
      currentPage = 1; // 필터 변경 시 첫 페이지로
      applyFiltersAndRender();
    });

    statusFilter?.addEventListener('change', () => {
      // 상태 필터 이벤트 리스너 추가
      currentPage = 1;
      applyFiltersAndRender();
    });

    prevPageBtn?.addEventListener('click', () => {
      if (currentPage > 1) {
        currentPage--;
        applyFiltersAndRender();
      }
    });
    nextPageBtn?.addEventListener('click', () => {
      if (currentPage < totalPages) {
        currentPage++;
        applyFiltersAndRender();
      }
    });

    refreshBtn?.addEventListener('click', () => {
      fetchAllItems()
        .then(() => {
          applyFiltersAndRender(); // 데이터 로드 후 렌더링
          hideLoading();
          Utils.alerts?.showSuccess('데이터를 새로고침했습니다.');
        })
        .catch((err) => {
          // fetchAllItems 내부에서 오류 처리됨
          hideLoading();
        });
    });

    handoverTableBody?.addEventListener('click', (e) => {
      const row = e.target.closest('tr.clickable-row');
      if (row) {
        const handoverId = row.dataset.id;
        if (handoverId) {
          window.location.href = `/handover/${handoverId}`;
        }
      }
    });
  }

  // URL 파라미터에서 알림 확인
  function checkUrlParamsForNotifications() {
    const urlParams = new URLSearchParams(window.location.search);
    const successMessage = urlParams.get('success');
    const errorMessage = urlParams.get('error');
    const warningMessage = urlParams.get('warning');

    if (successMessage) {
      Utils.alerts?.showSuccess(decodeURIComponent(successMessage));
    }
    if (errorMessage) {
      Utils.alerts?.showError(decodeURIComponent(errorMessage));
    }
    if (warningMessage) {
      Utils.alerts?.showWarning(decodeURIComponent(warningMessage));
    }
  }

  // --- 초기화 실행 ---
  initHandover();
});
