/**
 * 버튼 액션 관련 모듈
 * 대시보드 내 버튼 이벤트 처리 담당
 */
(function() {
  /**
   * 초기화 함수
   */
  function init() {
    console.log('[Dashboard.Actions] 액션 버튼 초기화 시작');
    
    // 중요 버튼 목록 정의
    const criticalButtons = [
      { 
        id: 'refreshBtn', 
        action: '새로고침', 
        handler: function() { 
          window.location.reload(); 
        } 
      },
      { 
        id: 'createOrderBtn', 
        action: '신규 등록', 
        handler: function() { 
          const modal = document.getElementById('createOrderModal');
          if (modal && window.Dashboard.utils) {
            window.Dashboard.utils.showModal(modal);
          } else {
            console.error('[Dashboard.Actions] createOrderModal 요소 또는 utils 모듈이 없습니다.');
          }
        } 
      },
      { 
        id: 'todayBtn', 
        action: '오늘 이동', 
        handler: function() { 
          window.location.href = '/dashboard'; 
        } 
      },
      { 
        id: 'orderSearchBtn', 
        action: '주문 검색', 
        handler: function() { 
          if (window.Dashboard.filter && typeof window.Dashboard.filter.applyOrderNoFilter === 'function') {
            window.Dashboard.filter.applyOrderNoFilter();
          }
        } 
      },
      { 
        id: 'resetFilterBtn', 
        action: '필터 초기화', 
        handler: function() { 
          if (window.Dashboard.filter && typeof window.Dashboard.filter.resetFilters === 'function') {
            window.Dashboard.filter.resetFilters();
          }
        } 
      }
    ];
    
    // 모든 버튼에 이벤트 핸들러 등록
    criticalButtons.forEach(button => {
      const btnElement = document.getElementById(button.id);
      if (btnElement) {
        console.log(`[Dashboard.Actions] 버튼 "${button.id}" 이벤트 등록`);
        
        // 기존 이벤트 리스너 제거 (중복 방지)
        btnElement.removeEventListener('click', button.handler);
        
        // 새 이벤트 리스너 등록
        btnElement.addEventListener('click', function(event) {
          console.log(`[Dashboard.Actions] 버튼 클릭: ${button.action}`);
          button.handler.call(this, event);
        });
        
        // 디버깅용 속성 추가
        btnElement.setAttribute('data-initialized', 'true');
      } else {
        console.warn(`[Dashboard.Actions] 버튼 "${button.id}"를 찾을 수 없음`);
      }
    });
    
    // 모달 창 닫기 버튼들 (공통)
    document.querySelectorAll('.close-btn, [data-dismiss="modal"]').forEach(btn => {
      btn.addEventListener('click', function() {
        const modal = this.closest('.modal');
        if (modal && window.Dashboard.utils) {
          console.log(`[Dashboard.Actions] 모달 닫기 버튼 클릭: ${modal.id || '이름 없음'}`);
          window.Dashboard.utils.hideModal(modal);
        }
      });
    });
    
    // 기타 초기화
    initMisc();
    
    console.log('[Dashboard.Actions] 액션 버튼 초기화 완료');
    return true;
  }
  
  /**
   * 기타 초기화 작업
   */
  function initMisc() {
    console.log('[Dashboard.Actions] 기타 초기화');
    
    // 우편번호 입력 필드 이벤트 (4자리 → 5자리 변환)
    document.querySelectorAll('input[name="postalCode"]').forEach(input => {
      input.addEventListener('blur', function() {
        const postalCode = this.value.trim();
        if (postalCode.length === 4 && /^\d{4}$/.test(postalCode)) {
          if (window.Dashboard.utils && typeof window.Dashboard.utils.formatPostalCode === 'function') {
            this.value = window.Dashboard.utils.formatPostalCode(postalCode);
          } else {
            // 기본 보완 기능
            this.value = '0' + postalCode;
          }
        }
      });
    });
  }
  
  // 대시보드 모듈에 등록
  Dashboard.registerModule('actions', {
    init: init
  });
})();
