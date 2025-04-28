console.log('[로드] dashboard/table.js 로드됨 - ' + new Date().toISOString());

/**
 * 단순화된 대시보드 테이블 모듈
 * 주문 테이블 관련 기능을 처리합니다.
 */
(function() {
  // Dashboard 객체가 존재하는지 확인
  if (!window.Dashboard) {
    console.error('[대시보드/table] Dashboard 객체가 초기화되지 않았습니다.');
    return;
  }
  
  // 테이블 객체 정의
  const table = {
    /**
     * 초기화 함수
     */
    init: function() {
      console.log('[대시보드/table] 초기화 시작');
      
      this.bindTableEvents();
      
      console.log('[대시보드/table] 초기화 완료');
    },
    
    /**
     * 테이블 이벤트를 바인딩합니다.
     */
    bindTableEvents: function() {
      const tableElement = document.getElementById('orderTable');
      if (!tableElement) {
        console.error('[대시보드/table] 테이블 요소를 찾을 수 없습니다.');
        return;
      }
      
      // 행 클릭 이벤트 삭제 (dashboard.html에서 직접 처리)
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
     * 테이블을 새로고침합니다.
     */
    refresh: function() {
      // 현재 페이지 새로고침
      window.location.reload();
    }
  };
  
  // Dashboard 객체에 테이블 모듈 등록
  Dashboard.registerModule('table', table);
})();
