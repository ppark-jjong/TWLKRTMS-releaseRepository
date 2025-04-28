console.log('[로드] dashboard/filter.js 로드됨 - ' + new Date().toISOString());

/**
 * 대시보드 필터 모듈
 * 필터링 기능을 처리합니다.
 */
(function() {
  // Dashboard 객체가 존재하는지 확인
  if (!window.Dashboard) {
    console.error('[대시보드/filter] Dashboard 객체가 초기화되지 않았습니다.');
    return;
  }
  
  // 필터 객체 정의
  const filter = {
    /**
     * 초기화 함수
     */
    init: function() {
      console.log('[대시보드/filter] 초기화 시작');
      
      this.initDateRangePicker();
      this.bindFilterEvents();
      this.setupInitialFilters();
      
      console.log('[대시보드/filter] 초기화 완료');
      return true;
    },
    
    /**
     * Air Datepicker 초기화
     */
    initDateRangePicker: function() {
      const self = this;
      const today = this.getTodayDate();
      
      // URL 매개변수에서 날짜 가져오기 (대소문자 구분 없이 처리)
      const urlParams = new URLSearchParams(window.location.search);
      let startDate = today;
      let endDate = today;
      
      // 대소문자 무관하게 URL 파라미터 탐색
      for (const [key, value] of urlParams.entries()) {
        if (key.toLowerCase() === 'startdate' || key.toLowerCase() === 'start_date') {
          startDate = value;
        }
        if (key.toLowerCase() === 'enddate' || key.toLowerCase() === 'end_date') {
          endDate = value;
        }
      }
      
      console.log('[대시보드/filter] 초기 날짜 설정:', startDate, endDate);
      
      // 히든 필드에 초기값 설정
      document.getElementById('startDate').value = startDate;
      document.getElementById('endDate').value = endDate;
      
      // 날짜 표시 포맷
      const formatDate = (date) => {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
      };
      
      // 초기 표시 텍스트 설정
      const dateRangePicker = document.getElementById('dateRangePicker');
      if (dateRangePicker) {
        if (startDate === endDate) {
          dateRangePicker.value = startDate;
        } else {
          dateRangePicker.value = `${startDate} ~ ${endDate}`;
        }
        
        // Air Datepicker 초기화
        new AirDatepicker('#dateRangePicker', {
          range: true,
          multipleDates: true,
          multipleDatesSeparator: ' ~ ',
          dateFormat: 'yyyy-MM-dd',
          autoClose: true,
          minDate: new Date('2020-01-01'), // 필요에 따라 조정
          locale: { // 한국어 로케일 직접 설정
            days: ['일요일', '월요일', '화요일', '수요일', '목요일', '금요일', '토요일'],
            daysShort: ['일', '월', '화', '수', '목', '금', '토'],
            daysMin: ['일', '월', '화', '수', '목', '금', '토'],
            months: ['1월', '2월', '3월', '4월', '5월', '6월', '7월', '8월', '9월', '10월', '11월', '12월'],
            monthsShort: ['1월', '2월', '3월', '4월', '5월', '6월', '7월', '8월', '9월', '10월', '11월', '12월'],
            today: '오늘',
            clear: '초기화',
            dateFormat: 'yyyy-MM-dd',
            timeFormat: 'hh:mm aa',
            firstDay: 0
          },
          selectedDates: [new Date(startDate), new Date(endDate)],
          buttons: ['today', 'clear'],
          
          onSelect({date, formattedDate, datepicker}) {
            console.log('[대시보드/filter] 날짜 선택:', formattedDate);
            
            // 날짜가 두 개 선택되었는지 확인
            if (Array.isArray(date) && date.length === 2) {
              const start = formatDate(date[0]);
              const end = formatDate(date[1]);
              
              // 히든 필드 업데이트
              document.getElementById('startDate').value = start;
              document.getElementById('endDate').value = end;
              
              // 자동으로 조회 실행
              self.applyDateFilter();
            }
          }
        });
      }
    },
    
    /**
     * 필터 이벤트를 바인딩합니다.
     */
    bindFilterEvents: function() {
      // 검색 버튼 클릭 이벤트
      const searchBtn = document.getElementById('searchBtn');
      if (searchBtn) {
        searchBtn.addEventListener('click', () => {
          this.applyDateFilter();
        });
      }
      
      // 오늘 버튼 클릭 이벤트
      const todayBtn = document.getElementById('todayBtn');
      if (todayBtn) {
        todayBtn.addEventListener('click', () => {
          this.setTodayFilter();
        });
      }
      
      // 주문번호 검색 이벤트
      const orderSearchBtn = document.getElementById('orderSearchBtn');
      if (orderSearchBtn) {
        orderSearchBtn.addEventListener('click', () => {
          this.applyOrderNoFilter();
        });
      }
      
      // 주문번호 입력 필드 엔터 키 이벤트
      const orderNoSearch = document.getElementById('orderNoSearch');
      if (orderNoSearch) {
        orderNoSearch.addEventListener('keypress', (event) => {
          if (event.key === 'Enter') {
            this.applyOrderNoFilter();
          }
        });
      }
      
      // 상태 필터 변경 이벤트
      const statusFilter = document.getElementById('statusFilter');
      if (statusFilter) {
        statusFilter.addEventListener('change', () => {
          this.applyCSRFilters();
        });
      }
      
      // 부서 필터 변경 이벤트
      const departmentFilter = document.getElementById('departmentFilter');
      if (departmentFilter) {
        departmentFilter.addEventListener('change', () => {
          this.applyCSRFilters();
        });
      }
      
      // 창고 필터 변경 이벤트
      const warehouseFilter = document.getElementById('warehouseFilter');
      if (warehouseFilter) {
        warehouseFilter.addEventListener('change', () => {
          this.applyCSRFilters();
        });
      }
      
      // 필터 초기화 버튼 클릭 이벤트
      const resetFilterBtn = document.getElementById('resetFilterBtn');
      if (resetFilterBtn) {
        resetFilterBtn.addEventListener('click', () => {
          this.resetFilters();
        });
      }
      
      // 새로고침 버튼 클릭 이벤트
      const refreshBtn = document.getElementById('refreshBtn');
      if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
          this.refreshData();
        });
      }
    },
    
    /**
     * 초기 필터를 설정합니다.
     */
    setupInitialFilters: function() {
      // URL 매개변수에서 필터 값 가져오기
      const orderNo = this.getUrlParam('order_no');
      const status = this.getUrlParam('status');
      const department = this.getUrlParam('department');
      const warehouse = this.getUrlParam('warehouse');
      
      // 주문번호 검색 설정
      const orderNoSearch = document.getElementById('orderNoSearch');
      if (orderNoSearch && orderNo) {
        orderNoSearch.value = orderNo;
      }
      
      // 상태 필터 설정
      const statusFilter = document.getElementById('statusFilter');
      if (statusFilter && status) {
        statusFilter.value = status;
      }
      
      // 부서 필터 설정
      const departmentFilter = document.getElementById('departmentFilter');
      if (departmentFilter && department) {
        departmentFilter.value = department;
      }
      
      // 창고 필터 설정
      const warehouseFilter = document.getElementById('warehouseFilter');
      if (warehouseFilter && warehouse) {
        warehouseFilter.value = warehouse;
      }
    },
    
    /**
     * 날짜 필터를 적용합니다.
     */
    applyDateFilter: function() {
      const startDate = document.getElementById('startDate')?.value;
      const endDate = document.getElementById('endDate')?.value;
      
      console.log('[대시보드/filter] 날짜 필터 적용:', startDate, endDate);
      
      if (!startDate || !endDate) {
        if (window.Alerts) {
          Alerts.warning('시작일과 종료일을 모두 선택해주세요.');
        } else {
          alert('시작일과 종료일을 모두 선택해주세요.');
        }
        return;
      }
      
      // 페이지 새로고침 (서버 필터링) - 백엔드의 파라미터명과 일치시킴
      window.location.href = `?startDate=${startDate}&endDate=${endDate}`;
    },
    
    /**
     * 오늘 날짜 필터를 설정합니다.
     */
    setTodayFilter: function() {
      const today = this.getTodayDate();
      
      // 날짜 입력 필드 업데이트
      document.getElementById('startDate').value = today;
      document.getElementById('endDate').value = today;
      
      // DateRangePicker 표시 업데이트
      const dateRangePicker = document.getElementById('dateRangePicker');
      if (dateRangePicker) {
        dateRangePicker.value = today;
        
        // Air Datepicker 인스턴스 접근 및 업데이트
        const datepickers = document.querySelectorAll('.air-datepicker');
        if (datepickers.length > 0) {
          const datepicker = datepickers[0];
          if (datepicker && datepicker._datepicker) {
            datepicker._datepicker.selectDate([new Date(today), new Date(today)]);
          }
        }
      }
      
      // 페이지 직접 이동 (필터 적용 대신 직접 URL 구성)
      window.location.href = `?startDate=${today}&endDate=${today}`;
    },
    
    /**
     * 주문번호 필터를 적용합니다.
     */
    applyOrderNoFilter: function() {
      const orderNo = document.getElementById('orderNoSearch')?.value?.trim();
      
      if (!orderNo) {
        if (window.Alerts) {
          Alerts.warning('검색할 주문번호를 입력해주세요.');
        } else {
          alert('검색할 주문번호를 입력해주세요.');
        }
        return;
      }
      
      // 페이지 새로고침 (서버 필터링)
      window.location.href = `?order_no=${orderNo}`;
    },
    
    /**
     * CSR 필터를 적용합니다 (클라이언트 사이드 필터링).
     */
    applyCSRFilters: function() {
      const status = document.getElementById('statusFilter')?.value;
      const department = document.getElementById('departmentFilter')?.value;
      const warehouse = document.getElementById('warehouseFilter')?.value;
      
      // URL 매개변수 업데이트 (페이지 새로고침 없음)
      const params = {};
      if (status) params.status = status;
      if (department) params.department = department;
      if (warehouse) params.warehouse = warehouse;
      
      // 기존 날짜 필터 유지
      const startDate = this.getUrlParam('start_date');
      const endDate = this.getUrlParam('end_date');
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;
      
      // 기존 주문번호 검색 유지
      const orderNo = this.getUrlParam('order_no');
      if (orderNo) params.order_no = orderNo;
      
      // URL 업데이트
      if (window.Dashboard.utils && typeof Dashboard.utils.updateUrlParams === 'function') {
        Dashboard.utils.updateUrlParams(params);
      } else {
        const url = new URL(window.location.href);
        url.search = new URLSearchParams(params).toString();
        window.history.pushState({}, '', url);
      }
      
      // 테이블 행 필터링
      this.filterTableRows(status, department, warehouse);
    },
    
    /**
     * 테이블 행을 필터링합니다.
     * @param {string} status - 상태 필터
     * @param {string} department - 부서 필터
     * @param {string} warehouse - 창고 필터
     */
    filterTableRows: function(status, department, warehouse) {
      const tableRows = document.querySelectorAll('#orderTable tbody tr');
      
      let visibleCount = 0;
      
      tableRows.forEach(row => {
        // 'no-data-row' 클래스가 있는 행은 건너뜁니다.
        if (row.classList.contains('no-data-row')) {
          return;
        }
        
        const rowStatus = row.querySelector('.column-status .status-badge')?.dataset.status || row.querySelector('.column-status .status-badge')?.textContent.trim();
        const rowDepartment = row.querySelector('.column-department')?.textContent.trim();
        const rowWarehouse = row.querySelector('.column-warehouse')?.textContent.trim();
        
        // 필터 조건에 따라 행 표시/숨김
        const statusMatch = !status || rowStatus === status || rowStatus?.includes(status);
        const departmentMatch = !department || rowDepartment === department;
        const warehouseMatch = !warehouse || rowWarehouse === warehouse;
        
        const shouldShow = statusMatch && departmentMatch && warehouseMatch;
        
        // 행 표시/숨김 처리
        row.style.display = shouldShow ? '' : 'none';
        
        // 보이는 행 수 카운트
        if (shouldShow) {
          visibleCount++;
        }
      });
      
      // 결과가 없는 경우 처리
      const noDataRow = document.querySelector('#orderTable .no-data-row');
      if (noDataRow) {
        if (visibleCount === 0) {
          // 결과가 없으면 '데이터 없음' 행 표시
          noDataRow.style.display = '';
          noDataRow.querySelector('.no-data-cell').textContent = '검색 결과가 없습니다';
        } else {
          // 결과가 있으면 '데이터 없음' 행 숨김
          noDataRow.style.display = 'none';
        }
      }
      
      // 페이지네이션 업데이트 처리
      if (window.Dashboard && window.Dashboard.pagination && typeof window.Dashboard.pagination.reset === 'function') {
        window.Dashboard.pagination.reset();
      }
      
      return visibleCount;
    },
    
    /**
     * 오늘 날짜를 YYYY-MM-DD 형식으로 반환합니다.
     * @returns {string} - 오늘 날짜 문자열
     */
    getTodayDate: function() {
      const today = new Date();
      const year = today.getFullYear();
      const month = String(today.getMonth() + 1).padStart(2, '0');
      const day = String(today.getDate()).padStart(2, '0');
      return `${year}-${month}-${day}`;
    },
    
    /**
     * URL 쿼리 매개변수를 가져옵니다.
     * @param {string} paramName - 매개변수 이름
     * @returns {string} - 매개변수 값 또는 빈 문자열
     */
    getUrlParam: function(paramName) {
      const url = new URL(window.location.href);
      return url.searchParams.get(paramName) || '';
    },
    
    /**
     * 필터를 초기화합니다.
     */
    resetFilters: function() {
      // 필터 요소 초기화
      const statusFilter = document.getElementById('statusFilter');
      const departmentFilter = document.getElementById('departmentFilter');
      const warehouseFilter = document.getElementById('warehouseFilter');
      
      if (statusFilter) statusFilter.value = '';
      if (departmentFilter) departmentFilter.value = '';
      if (warehouseFilter) warehouseFilter.value = '';
      
      // 날짜 필터 초기화 (오늘 날짜로)
      const today = this.getTodayDate();
      document.getElementById('startDate').value = today;
      document.getElementById('endDate').value = today;
      
      // DateRangePicker 표시 업데이트
      const dateRangePicker = document.getElementById('dateRangePicker');
      if (dateRangePicker) {
        dateRangePicker.value = today;
        
        // Air Datepicker 인스턴스 접근 및 업데이트
        const datepickers = document.querySelectorAll('.air-datepicker');
        if (datepickers.length > 0) {
          const datepicker = datepickers[0];
          if (datepicker && datepicker._datepicker) {
            datepicker._datepicker.selectDate([new Date(today), new Date(today)]);
          }
        }
      }
      
      // 주문번호 검색 초기화
      const orderNoSearch = document.getElementById('orderNoSearch');
      if (orderNoSearch) orderNoSearch.value = '';
      
      // 페이지 새로고침 - 기본 상태로 (오늘 날짜)
      window.location.href = `${window.location.pathname}?startDate=${today}&endDate=${today}`;
    },
    
    /**
     * 데이터를 새로고침합니다.
     */
    refreshData: function() {
      // 페이지 새로고침 (현재 URL 유지)
      window.location.reload();
    }
  };
  
  // Dashboard 객체에 필터 모듈 등록
  Dashboard.registerModule('filter', filter);
})();
