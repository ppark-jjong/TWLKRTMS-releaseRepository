/**
 * 대시보드 페이지 기능 구현
 * 주문 목록 조회 및 필터링 기능을 제공합니다.
 */
document.addEventListener('DOMContentLoaded', function () {
  // --- DOM 요소 가져오기 ---
  const loadingOverlay = document.getElementById('loadingOverlay');
  const startDateInput = document.getElementById('startDate');
  const endDateInput = document.getElementById('endDate');
  const dateSearchBtn = document.getElementById('dateSearchBtn');
  const orderNoInput = document.getElementById('orderNoSearch');
  const orderSearchBtn = document.getElementById('orderSearchBtn');
  const statusFilter = document.getElementById('statusFilter');
  const departmentFilter = document.getElementById('departmentFilter');
  const resetFilterBtn = document.getElementById('resetFilterBtn');
  const refreshBtn = document.getElementById('refreshBtn');
  const rowsPerPageSelect = document.getElementById('rowsPerPageSelect');
  const dashboardTableHead = document.getElementById('dashboardTableHead');
  const dashboardTableBody = document.getElementById('dashboardTableBody');
  const paginationControls = document.getElementById('paginationControls');
  const pageInfo = document.getElementById('pageInfo');
  const prevPageBtn = paginationControls.querySelector('[data-page="prev"]');
  const nextPageBtn = paginationControls.querySelector('[data-page="next"]');
  const errorMessageContainer = document.getElementById(
    'errorMessageContainer'
  );
  const errorMessageText = document.getElementById('errorMessageText');
  const customizeColumnsBtn = document.getElementById('customizeColumnsBtn');
  const columnDialog = document.getElementById('columnDialog');
  const columnSettingsGrid = document.getElementById('columnSettingsGrid');
  const cancelColumnsBtn = document.getElementById('cancelColumnsBtn');
  const applyColumnsBtn = document.getElementById('applyColumnsBtn');
  const todayBtn = document.getElementById('todayBtn');
  const driverNameFilterInput = document.getElementById('driverNameFilter');

  // --- 상태 변수 ---
  let allOrders = [];
  let filteredOrders = [];
  let currentPage = 1;
  let rowsPerPage = 30; // 기본값
  let totalItems = 0;
  let totalPages = 1;
  let initialLoadComplete = false; // 전체 데이터 로드 완료 여부
  let etaSortDirection = null; // 'asc', 'desc', null(정렬안함)
  // Flatpickr 인스턴스
  let startDatePicker = null;
  let endDatePicker = null;

  // 컬럼 정보 (표시 순서 및 기본 표시 여부 정의)
  const columnDefinitions = [
    {
      key: 'orderNo',
      label: '주문번호',
      width: '15%',
      visible: true,
      required: true,
    },
    { key: 'typeLabel', label: '유형', width: '8%', visible: true },
    { key: 'department', label: '부서', width: '10%', visible: true },
    { key: 'warehouse', label: '창고', width: '10%', visible: true },
    { key: 'sla', label: 'SLA', width: '8%', visible: true },
    { key: 'region', label: '지역', width: '15%', visible: true },
    { key: 'eta', label: 'ETA', width: '15%', visible: true, sortable: true },
    { key: 'customer', label: '고객', width: '10%', visible: true },
    { key: 'statusLabel', label: '상태', width: '10%', visible: true },
    { key: 'driverName', label: '배송기사', width: '12%', visible: true },
    // { key: 'postalCode', label: '우편번호', width: '10%', visible: false }, // 우편번호 제거
  ];
  let visibleColumns = loadVisibleColumns();

  // 상태 라벨 매핑 (템플릿 필터 대신 JS에서 사용)
  const statusLabels = {
    WAITING: '대기',
    IN_PROGRESS: '진행',
    COMPLETE: '완료',
    ISSUE: '이슈',
    CANCEL: '취소',
  };
  const typeLabels = { DELIVERY: '배송', RETURN: '회수' };

  // --- 초기화 함수 ---
  function initDashboard() {
    showLoading();

    // CSR 방식으로 변경 - 서버에서 데이터를 받아오는 대신 직접 API 호출

    // 날짜 초기화 - localStorage에서 먼저 확인하고, 없으면 오늘 날짜 사용
    const savedDates = loadDateRangeFromStorage();
    if (savedDates.startDate && savedDates.endDate) {
      // localStorage에 날짜가 있으면 우선 사용
      startDateInput.value = savedDates.startDate;
      endDateInput.value = savedDates.endDate;
    } else {
      // 없으면 오늘 날짜로 초기화
      const today = getTodayDate();
      startDateInput.value = today;
      endDateInput.value = today;
    }

    // Flatpickr 초기화
    initDatePickers();

    // 페이지당 행 수 초기화
    rowsPerPage = parseInt(rowsPerPageSelect.value);

    // 컬럼 설정 초기화 및 헤더 렌더링
    renderColumnSettings();
    renderTableHeader();

    // 로딩 메시지 표시하기
    dashboardTableBody.innerHTML = renderEmptyRow('데이터를 로딩 중입니다...');

    // 비동기적으로 전체 데이터 로드
    fetchAllOrders(startDateInput.value, endDateInput.value)
      .then(() => {
        initialLoadComplete = true;
        hideLoading();
      })
      .catch((error) => {
        showError('전체 데이터를 불러오는 중 오류 발생');
        hideLoading();
      });

    // 이벤트 리스너 설정
    setupEventListeners();
  }

  // Flatpickr 달력 초기화
  function initDatePickers() {
    // 공통 옵션
    const commonOptions = {
      locale: 'ko',
      dateFormat: 'Y-m-d',
      allowInput: true,
      disableMobile: true, // 모바일에서도 일관된 UI 사용
      showMonths: 1,
      prevArrow: '<i class="fa fa-chevron-left"></i>',
      nextArrow: '<i class="fa fa-chevron-right"></i>',
    };

    // 시작일 Flatpickr
    startDatePicker = flatpickr(startDateInput, {
      ...commonOptions,
      onChange: function (selectedDates, dateStr) {
        // 종료일의 최소 날짜를 시작일로 설정
        if (endDatePicker) {
          endDatePicker.set('minDate', dateStr);
        }
      },
    });

    // 종료일 Flatpickr
    endDatePicker = flatpickr(endDateInput, {
      ...commonOptions,
      onChange: function (selectedDates, dateStr) {
        // 시작일의 최대 날짜를 종료일로 설정
        if (startDatePicker) {
          startDatePicker.set('maxDate', dateStr);
        }
      },
    });

    // 시작 및 종료일 관계 설정
    if (startDateInput.value) {
      endDatePicker.set('minDate', startDateInput.value);
    }
    if (endDateInput.value) {
      startDatePicker.set('maxDate', endDateInput.value);
    }
  }

  // --- 데이터 처리 함수 ---
  // 날짜 범위로 전체 주문 데이터 가져오기
  async function fetchAllOrders(startDate, endDate) {
    showLoading();
    clearError();

    // 날짜 범위를 localStorage에 저장
    saveDateRangeToStorage(startDate, endDate);

    try {
      const response = await fetch(
        `/api/dashboard/list?start_date=${startDate}&end_date=${endDate}`
      );
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const result = await response.json();
      if (result.success && result.data) {
        allOrders = addLabelsToOrders(result.data);
        totalItems = allOrders.length;
        currentPage = 1;
        applyFiltersAndRender();
      } else {
        throw new Error(result.message || 'Failed to fetch data');
      }
    } catch (error) {
      showError(`데이터 조회 실패: ${error.message}`);
      allOrders = [];
      applyFiltersAndRender();
      throw error;
    } finally {
      if (initialLoadComplete) {
        hideLoading();
      }
    }
  }

  // 전역 스코프에 fetchAllOrders 함수 노출 (일괄 변경 기능에서 사용)
  window.fetchAllOrders = fetchAllOrders;

  // 주문 데이터에 라벨 추가
  function addLabelsToOrders(orders) {
    return orders.map((order) => ({
      ...order,
      statusLabel: statusLabels[order.status] || order.status,
      typeLabel: typeLabels[order.type] || order.type,
      // order.order_no가 템플릿에서 사용될 수 있도록 camelCase 변환 추가
      orderNo: order.order_no,
      driverName: order.driver_name,
      // ETA는 ISO 형식 그대로 사용
      etaFormatted: order.eta || '-',
    }));
  }

  // 현재 필터 및 페이지 상태에 따라 테이블 렌더링
  function applyFiltersAndRender() {
    // 1. 필터 적용
    const status = statusFilter.value;
    const department = departmentFilter.value;
    const driverNameQuery = driverNameFilterInput.value.toLowerCase();

    filteredOrders = allOrders.filter((order) => {
      const statusMatch = !status || order.status === status;
      const departmentMatch = !department || order.department === department;
      const driverNameMatch =
        !driverNameQuery ||
        (order.driverName &&
          order.driverName.toLowerCase().includes(driverNameQuery));
      return statusMatch && departmentMatch && driverNameMatch;
    });

    // ETA 정렬 적용
    if (etaSortDirection) {
      filteredOrders.sort((a, b) => {
        const dateA = a.eta ? new Date(a.eta) : new Date(0);
        const dateB = b.eta ? new Date(b.eta) : new Date(0);

        if (etaSortDirection === 'asc') {
          return dateA - dateB;
        } else {
          return dateB - dateA;
        }
      });
    }

    totalItems = filteredOrders.length; // 필터링된 결과로 전체 아이템 수 업데이트

    // 2. 페이지네이션 계산
    totalPages = Math.ceil(totalItems / rowsPerPage) || 1;
    currentPage = Math.max(1, Math.min(currentPage, totalPages)); // 현재 페이지 보정

    // 3. 현재 페이지 데이터 슬라이싱
    const startIndex = (currentPage - 1) * rowsPerPage;
    const endIndex = startIndex + rowsPerPage;
    const pageOrders = filteredOrders.slice(startIndex, endIndex);

    // 4. 테이블 렌더링
    renderTableRows(pageOrders);

    // 5. 페이지네이션 UI 업데이트
    updatePaginationUI();
  }

  // 테이블 행 HTML 생성 및 업데이트
  function renderTableRows(orders) {
    if (!dashboardTableBody) return;

    if (orders.length === 0) {
      dashboardTableBody.innerHTML =
        renderEmptyRow('조건에 맞는 주문이 없습니다.');
      return;
    }

    let tableHTML = '';
    orders.forEach((order) => {
      const statusClass = `status-${order.status.toLowerCase()}`;
      const orderId = order.dashboard_id;

      // 상태 클래스와 선택 클래스를 행에 적용
      let rowHTML = `<tr data-id="${orderId}" class="order-row ${statusClass}">`;

      Object.keys(visibleColumns)
        .filter((key) => visibleColumns[key])
        .forEach((colKey) => {
          const column = columnDefinitions.find((col) => col.key === colKey);
          if (!column) return;

          // 주문번호 필드에 복사 버튼 추가
          if (colKey === 'orderNo') {
            rowHTML += `<td>
              <div class="order-no-with-copy">
                <span>${order[colKey] || '-'}</span>
                <button type="button" class="copy-btn" onclick="copyOrderNumber(event, '${
                  order[colKey]
                }')">
                  <i class="fa-regular fa-copy"></i>
                </button>
              </div>
            </td>`;
          }
          // 상태 필드는 배지로 표시
          else if (colKey === 'statusLabel') {
            rowHTML += `<td><span class="status-badge ${statusClass}">${order[colKey]}</span></td>`;
          } else if (colKey === 'eta' || colKey === 'etaFormatted') {
            // ETA는 포맷팅된 값 사용
            rowHTML += `<td>${order.etaFormatted || '-'}</td>`;
          } else {
            // 일반 텍스트 필드
            rowHTML += `<td>${order[colKey] || '-'}</td>`;
          }
        });

      rowHTML += '</tr>';
      tableHTML += rowHTML;
    });

    dashboardTableBody.innerHTML = tableHTML;

    // 행 클릭 이벤트 핸들러 등록
    const rows = dashboardTableBody.querySelectorAll('tr.order-row');
    rows.forEach((row) => {
      row.addEventListener('click', function (e) {
        // 체크박스나 복사 버튼 클릭은 별도 처리
        if (
          e.target.classList.contains('copy-btn') ||
          e.target.closest('.copy-btn')
        ) {
          return;
        }

        const orderId = this.getAttribute('data-id');

        if (orderId) {
          // data-id 속성에서 주문 ID를 가져와 상세 페이지로 이동
          window.location.href = `/orders/${orderId}`;
        }
      });
    });
  }

  // 테이블 헤더 렌더링
  function renderTableHeader() {
    if (!dashboardTableHead) return;
    let headerHTML = '<tr>';
    columnDefinitions.forEach((col) => {
      // 제거된 컬럼은 렌더링하지 않음
      if (col.key === 'postalCode') return;
      if (visibleColumns[col.key]) {
        // ETA 컬럼에만 정렬 기능 추가
        if (col.key === 'eta' && col.sortable) {
          let sortIcon = '';
          if (etaSortDirection === 'asc') {
            sortIcon = '<i class="fa-solid fa-sort-up"></i>';
          } else if (etaSortDirection === 'desc') {
            sortIcon = '<i class="fa-solid fa-sort-down"></i>';
          } else {
            sortIcon = '<i class="fa-solid fa-sort"></i>';
          }

          headerHTML += `
            <th width="${col.width}" class="sortable-header" data-sort="eta">
              ${col.label} ${sortIcon}
            </th>`;
        } else {
          headerHTML += `<th width="${col.width}">${col.label}</th>`;
        }
      }
    });
    headerHTML += '</tr>';
    dashboardTableHead.innerHTML = headerHTML;

    // ETA 헤더에 정렬 이벤트 추가
    const etaHeader = dashboardTableHead.querySelector(
      '.sortable-header[data-sort="eta"]'
    );
    if (etaHeader) {
      etaHeader.addEventListener('click', function () {
        // 정렬 방향 순환: null -> asc -> desc -> null
        if (!etaSortDirection) {
          etaSortDirection = 'asc';
        } else if (etaSortDirection === 'asc') {
          etaSortDirection = 'desc';
        } else {
          etaSortDirection = null;
        }

        // 헤더 다시 그리고 데이터 정렬
        renderTableHeader();
        applyFiltersAndRender();
      });
    }
  }

  // 빈 결과 행 HTML 생성
  function renderEmptyRow(message) {
    const colspan = Object.values(visibleColumns).filter((v) => v).length;
    return `
          <tr class="empty-data-row">
            <td colspan="${colspan}" class="empty-table">
            <div class="empty-placeholder">
              <i class="fa-solid fa-inbox"></i>
                <p>${message}</p>
            </div>
          </td>
          </tr>`;
  }

  // 페이지네이션 UI 업데이트
  function updatePaginationUI() {
    if (!pageInfo || !prevPageBtn || !nextPageBtn) return;
    pageInfo.textContent = `${currentPage} / ${totalPages}`;
    prevPageBtn.disabled = currentPage <= 1;
    nextPageBtn.disabled = currentPage >= totalPages;
  }

  // 주문번호 검색 결과 렌더링
  function renderSearchResult(order) {
    if (order) {
      const singleOrder = addLabelsToOrders([order])[0]; // 라벨 추가
      renderTableRows([singleOrder]);
      pageInfo.textContent = '1 / 1';
      prevPageBtn.disabled = true;
      nextPageBtn.disabled = true;
      paginationControls.style.display = 'none'; // 페이지네이션 숨김
    } else {
      dashboardTableBody.innerHTML = renderEmptyRow('검색 결과가 없습니다.');
      pageInfo.textContent = '0 / 0';
      prevPageBtn.disabled = true;
      nextPageBtn.disabled = true;
      paginationControls.style.display = 'none';
    }
  }

  // --- 컬럼 커스터마이징 관련 함수 ---
  // 로컬 스토리지에서 컬럼 설정 로드
  function loadVisibleColumns() {
    const saved = localStorage.getItem('dashboardVisibleColumns');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        // 기본값과 병합하여 반환 (새 컬럼 추가 대비)
        const defaults = columnDefinitions.reduce((acc, col) => {
          acc[col.key] = col.visible;
          return acc;
        }, {});
        return { ...defaults, ...parsed };
      } catch (e) {
        // 오류 처리 (콘솔 로그 제거)
      }
    }
    // 저장된 설정 없으면 기본값 반환
    return columnDefinitions.reduce((acc, col) => {
      acc[col.key] = col.visible;
      return acc;
    }, {});
  }

  // 로컬 스토리지에 컬럼 설정 저장
  function saveVisibleColumns() {
    localStorage.setItem(
      'dashboardVisibleColumns',
      JSON.stringify(visibleColumns)
    );
  }

  // 컬럼 설정 대화상자 렌더링
  function renderColumnSettings() {
    if (!columnSettingsGrid) return;
    columnSettingsGrid.innerHTML = ''; // 기존 내용 초기화
    columnDefinitions.forEach((col) => {
      const isChecked = visibleColumns[col.key];
      const isDisabled = col.required;
      const div = document.createElement('div');
      div.className = 'checkbox-container';
      div.innerHTML = `
              <input
                type="checkbox"
                id="col_${col.key}"
                name="columns"
                value="${col.key}"
                ${isChecked ? 'checked' : ''}
                ${isDisabled ? 'disabled' : ''}
              />
              <label for="col_${col.key}">${col.label} ${
        isDisabled ? '(필수)' : ''
      }</label>
          `;
      columnSettingsGrid.appendChild(div);
    });
  }

  // --- 유틸리티 함수 ---
  function showLoading() {
    loadingOverlay?.classList.add('active');
  }
  function hideLoading() {
    loadingOverlay?.classList.remove('active');
  }
  function showError(message) {
    if (!errorMessageContainer || !errorMessageText) return;
    errorMessageText.textContent = message;
    errorMessageContainer.style.display = 'block';
  }
  function clearError() {
    if (!errorMessageContainer || !errorMessageText) return;
    errorMessageText.textContent = '';
    errorMessageContainer.style.display = 'none';
  }
  function getTodayDate() {
    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  }

  // 날짜 범위를 localStorage에 저장
  function saveDateRangeToStorage(startDate, endDate) {
    try {
      localStorage.setItem('dashboardStartDate', startDate);
      localStorage.setItem('dashboardEndDate', endDate);
    } catch (e) {
      // 오류 처리 (콘솔 로그 제거)
    }
  }

  // localStorage에서 날짜 범위 불러오기
  function loadDateRangeFromStorage() {
    try {
      const startDate = localStorage.getItem('dashboardStartDate');
      const endDate = localStorage.getItem('dashboardEndDate');
      if (startDate && endDate) {
        return { startDate, endDate };
      }
    } catch (e) {
      // 오류 처리 (콘솔 로그 제거)
    }
    return { startDate: null, endDate: null };
  }

  // --- 이벤트 리스너 설정 ---
  function setupEventListeners() {
    // 날짜 및 필터링 관련 이벤트
    setupDateFilterEvents();

    // 페이지네이션 이벤트
    setupPaginationEvents();

    // 컬럼 설정 관련 이벤트
    setupColumnSettingsEvents();

    // 주문번호 검색 관련 이벤트
    setupSearchEvents();
  }

  // 날짜 및 필터링 관련 이벤트
  function setupDateFilterEvents() {
    // 엑셀 다운로드 버튼 (관리자용)
    const exportExcelBtn = document.getElementById('exportExcelBtn');
    if (exportExcelBtn) {
      exportExcelBtn.addEventListener('click', () => {
        const startDate = startDateInput.value;
        const endDate = endDateInput.value;

        // 날짜 유효성 검사
        if (startDate && endDate && new Date(endDate) < new Date(startDate)) {
          showError('종료일은 시작일보다 같거나 늦어야 합니다.');
          return;
        }

        // 엑셀 다운로드 URL 생성 및 이동
        const downloadUrl = `/api/dashboard/export-excel?start_date=${encodeURIComponent(
          startDate
        )}&end_date=${encodeURIComponent(endDate)}`;

        // 새 창에서 열지 않고 다운로드하기 위해 임시 링크 생성
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.setAttribute('download', ''); // 다운로드로 처리
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      });
    }

    // 날짜 조회 버튼
    dateSearchBtn?.addEventListener('click', () => {
      const startDate = startDateInput.value;
      const endDate = endDateInput.value;
      if (startDate && endDate && new Date(endDate) < new Date(startDate)) {
        showError('종료일은 시작일보다 같거나 늦어야 합니다.');
        return;
      }
      fetchAllOrders(startDate, endDate);
    });

    // 오늘 버튼 클릭 이벤트
    todayBtn?.addEventListener('click', () => {
      const today = getTodayDate();
      startDatePicker.setDate(today);
      endDatePicker.setDate(today);
      fetchAllOrders(today, today);
    });

    // 필터 변경 (상태, 부서)
    statusFilter?.addEventListener('change', () => {
      currentPage = 1; // 필터 변경 시 첫 페이지로
      applyFiltersAndRender();
    });

    departmentFilter?.addEventListener('change', () => {
      currentPage = 1;
      applyFiltersAndRender();
    });

    // 필터 초기화
    resetFilterBtn?.addEventListener('click', () => {
      statusFilter.value = '';
      departmentFilter.value = '';
      driverNameFilterInput.value = '';
      // 검색 결과 상태 해제 (선택적)
      if (paginationControls.style.display === 'none') {
        paginationControls.style.display = ''; // 페이지네이션 다시 표시
        fetchAllOrders(startDateInput.value, endDateInput.value); // 원래 데이터 다시 로드
      } else {
        currentPage = 1;
        applyFiltersAndRender();
      }
    });

    // 새로고침 버튼
    refreshBtn?.addEventListener('click', () => {
      fetchAllOrders(startDateInput.value, endDateInput.value);
    });

    // 기사명 필터 입력 이벤트 리스너 추가 (실시간 필터링)
    driverNameFilterInput?.addEventListener('input', () => {
      currentPage = 1; // 필터 변경 시 첫 페이지로
      applyFiltersAndRender();
    });
  }

  // 페이지네이션 관련 이벤트
  function setupPaginationEvents() {
    // 페이지네이션 버튼
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

    // 행 개수 변경
    rowsPerPageSelect?.addEventListener('change', (e) => {
      rowsPerPage = parseInt(e.target.value);
      currentPage = 1; // 첫 페이지로 이동
      applyFiltersAndRender();
    });
  }

  // 컬럼 설정 관련 이벤트
  function setupColumnSettingsEvents() {
    // 컬럼 설정 버튼
    customizeColumnsBtn?.addEventListener('click', () => {
      renderColumnSettings(); // 대화상자 열 때 최신 상태 반영
      columnDialog?.classList.add('active');
    });

    cancelColumnsBtn?.addEventListener('click', () => {
      columnDialog?.classList.remove('active');
    });

    applyColumnsBtn?.addEventListener('click', () => {
      const checkboxes = columnSettingsGrid.querySelectorAll(
        'input[name="columns"]'
      );
      checkboxes.forEach((cb) => {
        visibleColumns[cb.value] = cb.checked;
      });
      saveVisibleColumns(); // 변경사항 저장
      renderTableHeader(); // 헤더 다시 렌더링
      applyFiltersAndRender(); // 테이블 내용 다시 렌더링
      columnDialog?.classList.remove('active');
    });
  }

  // 주문번호 검색 관련 이벤트
  function setupSearchEvents() {
    // 주문번호 검색 버튼
    orderSearchBtn?.addEventListener('click', async () => {
      const orderNo = orderNoInput.value.trim();
      if (!orderNo) {
        showError('주문번호를 입력해주세요.');
        return;
      }
      showLoading();
      clearError();
      try {
        const response = await fetch(
          `/api/dashboard/search?order_no=${encodeURIComponent(orderNo)}`
        );
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const result = await response.json();
        if (result.success) {
          renderSearchResult(result.data.order);
        } else {
          throw new Error(result.message || 'Search failed');
        }
      } catch (error) {
        showError(`검색 실패: ${error.message}`);
        renderSearchResult(null);
      } finally {
        hideLoading();
      }
    });

    // 주문번호 엔터키 검색
    orderNoInput?.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        orderSearchBtn.click();
      }
    });

    // 테이블 행 클릭 (이벤트 위임) - 복사 버튼 클릭 제외
    dashboardTableBody?.addEventListener('click', (e) => {
      // 클릭된 요소가 복사 버튼이 아닐 경우에만 행 이동 처리
      if (!e.target.closest('.copy-btn')) {
        const row = e.target.closest('tr.order-row');
        if (row) {
          const orderId = row.dataset.id;
          if (orderId) {
            window.location.href = `/orders/${orderId}`;
          }
        }
      }
    });
  }

  // --- 초기화 실행 ---
  initDashboard();
});

/**
 * 주문번호 복사 기능
 * @param {Event} event - 클릭 이벤트
 * @param {string} orderNo - 복사할 주문번호
 */
function copyOrderNumber(event, orderNo) {
  event.stopPropagation(); // 행 클릭 이벤트 전파 방지
  if (!orderNo) return;
  navigator.clipboard.writeText(orderNo).then(
    () => {
      // 복사 성공 알림
      Utils.alerts.showSuccess('주문번호가 복사되었습니다.');
      const button = event.currentTarget;
      const originalIcon = button.innerHTML;
      button.innerHTML = '<i class="fa-solid fa-check"></i>';
      setTimeout(() => {
        button.innerHTML = originalIcon;
      }, 1500);
    },
    (err) => {
      Utils.alerts.showError('주문번호 복사에 실패했습니다.');
    }
  );
}
