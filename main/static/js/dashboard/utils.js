console.log('[로드] dashboard/utils.js 로드됨 - ' + new Date().toISOString());

/**
 * 대시보드 유틸리티 모듈
 * 대시보드 페이지에서 사용되는 유틸리티 함수 모음
 */
(function() {
  // Dashboard 객체가 존재하는지 확인
  if (!window.Dashboard) {
    console.error('[대시보드/utils] Dashboard 객체가 초기화되지 않았습니다.');
    return;
  }
  
  // 유틸리티 객체 정의
  const utils = {
    /**
     * 초기화 함수
     */
    init: function() {
      console.log('[대시보드/utils] 초기화 시작');
      
      // 페이지 로드 시 자동 날짜 설정 및 조회
      this.autoInitDateFilter();
      
      console.log('[대시보드/utils] 초기화 완료');
      return true;
    },
    
    /**
     * 페이지 로드 시 자동으로 날짜 필터를 초기화하고 데이터를 조회합니다.
     */
    autoInitDateFilter: function() {
      // 지연 실행하여 모든 모듈이 로드될 때까지 기다림
      setTimeout(() => {
        // URL에 날짜 파라미터가 없는 경우에만 자동 설정
        const hasDateParams = this.getUrlParam('start_date') || this.getUrlParam('end_date');
        const hasOrderNoParam = this.getUrlParam('order_no');
        
        if (!hasDateParams && !hasOrderNoParam) {
          console.log('[대시보드/utils] 자동 날짜 설정: 오늘');
          
          // 오늘 날짜 가져오기
          const today = this.getTodayDate();
          
          // 날짜 입력 필드에 설정
          const startDateInput = document.getElementById('startDate');
          const endDateInput = document.getElementById('endDate');
          
          if (startDateInput) startDateInput.value = today;
          if (endDateInput) endDateInput.value = today;
          
          // URL 파라미터에 날짜 추가
          this.updateUrlParams({
            start_date: today,
            end_date: today
          }, true);
          
          // 페이지 새로고침 (서버에서 데이터 재조회)
          window.location.href = `?start_date=${today}&end_date=${today}`;
        } else {
          console.log('[대시보드/utils] 자동 날짜 설정 건너뜀: URL 파라미터 있음');
        }
      }, 500); // 500ms 지연
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
     * 날짜를 형식화합니다.
     * @param {string|Date} date - 날짜 문자열 또는 Date 객체
     * @param {string} format - 형식 (기본값: YYYY-MM-DD)
     * @returns {string} - 형식화된 날짜 문자열
     */
    formatDate: function(date, format = 'YYYY-MM-DD') {
      if (!date) return '-';
      
      try {
        // 문자열을 Date 객체로 변환
        const dateObj = typeof date === 'string' ? new Date(date) : date;
        
        // 유효한 날짜인지 확인
        if (isNaN(dateObj.getTime())) {
          return date; // 원본 반환
        }
        
        const year = dateObj.getFullYear();
        const month = String(dateObj.getMonth() + 1).padStart(2, '0');
        const day = String(dateObj.getDate()).padStart(2, '0');
        const hours = String(dateObj.getHours()).padStart(2, '0');
        const minutes = String(dateObj.getMinutes()).padStart(2, '0');
        
        // 포맷에 따라 날짜 문자열 생성
        let formattedDate = format;
        formattedDate = formattedDate.replace('YYYY', year);
        formattedDate = formattedDate.replace('MM', month);
        formattedDate = formattedDate.replace('DD', day);
        formattedDate = formattedDate.replace('HH', hours);
        formattedDate = formattedDate.replace('mm', minutes);
        
        return formattedDate;
      } catch (error) {
        console.error('[대시보드/utils] 날짜 포맷팅 오류:', error);
        return date; // 오류 시 원본 반환
      }
    },
    
    /**
     * 우편번호를 형식화합니다 (4자리 -> 5자리).
     * @param {string} postalCode - 우편번호
     * @returns {string} - 형식화된 우편번호
     */
    formatPostalCode: function(postalCode) {
      if (!postalCode) return '';
      
      try {
        // 숫자만 추출
        const digits = postalCode.toString().replace(/\D/g, '');
        
        // 4자리인 경우 앞에 0 추가
        if (digits.length === 4) {
          return '0' + digits;
        }
        
        return digits;
      } catch (error) {
        console.error('[대시보드/utils] 우편번호 포맷팅 오류:', error);
        return postalCode; // 오류 시 원본 반환
      }
    },
    
    /**
     * 주문 상태에 따른 배경색 클래스를 반환합니다.
     * @param {string} status - 주문 상태
     * @returns {string} - 상태에 해당하는 CSS 클래스
     */
    getStatusClass: function(status) {
      switch(status?.toLowerCase()) {
        case 'waiting':
          return 'status-waiting';
        case 'in_progress':
          return 'status-in-progress';
        case 'complete':
          return 'status-complete';
        case 'issue':
          return 'status-issue';
        case 'cancel':
          return 'status-cancel';
        default:
          return '';
      }
    },
    
    /**
     * 주문 상태 라벨을 반환합니다.
     * @param {string} status - 주문 상태
     * @returns {string} - 한글 상태 라벨
     */
    getStatusLabel: function(status) {
      switch(status?.toLowerCase()) {
        case 'waiting':
          return '대기';
        case 'in_progress':
          return '진행';
        case 'complete':
          return '완료';
        case 'issue':
          return '이슈';
        case 'cancel':
          return '취소';
        default:
          return status || '-';
      }
    },
    
    /**
     * URL 쿼리 매개변수를 가져옵니다.
     * @param {string} paramName - 매개변수 이름
     * @param {string} defaultValue - 기본값
     * @returns {string} - 매개변수 값 또는 기본값
     */
    getUrlParam: function(paramName, defaultValue = '') {
      const url = new URL(window.location.href);
      return url.searchParams.get(paramName) || defaultValue;
    },
    
    /**
     * URL 쿼리 매개변수를 업데이트합니다.
     * @param {Object} params - 쿼리 매개변수 객체
     * @param {boolean} merge - 기존 매개변수와 병합 여부
     */
    updateUrlParams: function(params, merge = true) {
      const url = new URL(window.location.href);
      
      if (!merge) {
        // 기존 매개변수 제거
        [...url.searchParams.keys()].forEach(key => {
          url.searchParams.delete(key);
        });
      }
      
      // 새 매개변수 추가
      Object.entries(params).forEach(([key, value]) => {
        if (value !== null && value !== undefined && value !== '') {
          url.searchParams.set(key, value);
        } else {
          url.searchParams.delete(key);
        }
      });
      
      // URL 업데이트 (페이지 새로고침 없음)
      window.history.pushState({}, '', url);
    },
    
    /**
     * 모달을 표시합니다.
     * @param {HTMLElement} modal - 모달 요소
     */
    showModal: function(modal) {
      if (!modal) return;
      
      // 모달 표시
      modal.style.display = 'flex';
      document.body.classList.add('modal-open');
      
      // 애니메이션 효과
      setTimeout(function() {
        modal.classList.add('show');
      }, 10);
    },
    
    /**
     * 모달을 숨깁니다.
     * @param {HTMLElement} modal - 모달 요소
     */
    hideModal: function(modal) {
      if (!modal) return;
      
      // 애니메이션 효과
      modal.classList.remove('show');
      
      // 약간의 지연 후 완전히 숨김
      setTimeout(function() {
        modal.style.display = 'none';
        document.body.classList.remove('modal-open');
      }, 300);
    },
    
    /**
     * 알림 메시지를 표시합니다.
     * @param {string} message - 메시지 내용
     * @param {string} type - 알림 유형 (success, warning, error, info)
     */
    showAlert: function(message, type = 'info') {
      if (window.Alerts && typeof window.Alerts[type] === 'function') {
        window.Alerts[type](message);
      } else {
        alert(message);
      }
    }
  };
  
  // Dashboard 객체에 유틸리티 모듈 등록
  Dashboard.registerModule('utils', utils);
})();
