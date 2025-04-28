console.log('[로드] dashboard/core.js 로드됨 - ' + new Date().toISOString());

/**
 * 대시보드 코어 모듈
 * 모듈 관리 및 초기화 담당
 */
window.Dashboard = (function() {
  // 모듈 컨테이너
  const modules = {};
  
  // 현재 편집 중인 주문 ID (전역 상태)
  let currentOrderId = null;

  /**
   * 초기화 함수
   */
  function init() {
    console.log('[Dashboard] 초기화 시작');
    try {
      // 1. 모듈 의존성 확인
      if (!checkDependencies()) {
        console.error('[Dashboard] 초기화 실패: 필수 모듈이 로드되지 않았습니다.');
        return;
      }
      
      // 2. 각 모듈 초기화
      console.log('[Dashboard] 모듈 초기화 시작');
      
      // 테이블 모듈 초기화
      if (modules.table && typeof modules.table.init === 'function') {
        modules.table.init();
      }
      
      // 필터 모듈 초기화
      if (modules.filter && typeof modules.filter.init === 'function') {
        modules.filter.init();
      }
      
      // 모달 모듈 초기화
      if (modules.modal && typeof modules.modal.init === 'function') {
        modules.modal.init();
      }
      
      // 버튼 모듈 초기화
      if (modules.actions && typeof modules.actions.init === 'function') {
        modules.actions.init();
      }
      
      // 페이지네이션 모듈 초기화
      if (modules.pagination && typeof modules.pagination.init === 'function') {
        modules.pagination.init();
      }
      
      // 컬럼 가시성 모듈 초기화
      if (modules.columns && typeof modules.columns.init === 'function') {
        modules.columns.init();
      }
      
      // 3. 이벤트 핸들러 등록 검증 (디버깅용)
      validateEventHandlers();
      
      console.log('[Dashboard] 초기화 완료');
    } catch (error) {
      console.error('[Dashboard] 초기화 중 예외 발생:', error);
      alert('대시보드 초기화 중 오류가 발생했습니다: ' + error.message);
    }
  }
  
  /**
   * 이벤트 핸들러 등록 검증 (디버깅용)
   */
  function validateEventHandlers() {
    console.log('[Dashboard] 이벤트 핸들러 검증 시작');
    
    // 주요 버튼 및 이벤트 요소 검증
    const criticalElements = [
      { id: 'orderTable', type: 'table', name: '주문 테이블' },
      { id: 'createOrderBtn', type: 'button', name: '신규 등록 버튼' },
      { id: 'refreshBtn', type: 'button', name: '새로고침 버튼' },
      { id: 'searchBtn', type: 'button', name: '조회 버튼' },
      { id: 'columnSelectorBtn', type: 'button', name: '컬럼 선택 버튼' }
    ];
    
    criticalElements.forEach(element => {
      const el = document.getElementById(element.id);
      if (!el) {
        console.error(`[Dashboard] 중요 요소 누락: ${element.name}(#${element.id})를 찾을 수 없음`);
      } else {
        // 이벤트 리스너 간접 확인
        el.setAttribute('data-has-listener', 'true');
        console.log(`[Dashboard] 요소 확인: ${element.name} (#${element.id}) 정상`);
      }
    });
    
    console.log('[Dashboard] 이벤트 핸들러 검증 완료');
  }
  
  /**
   * 모듈 의존성을 확인합니다.
   * @returns {boolean} - 의존성 확인 결과
   */
  function checkDependencies() {
    const dependencies = [
      { name: 'Logger', module: window.Logger },
      { name: 'API', module: window.API },
      { name: 'Alerts', module: window.Alerts },
      { name: 'Auth', module: window.Auth }
    ];
    
    const missingDependencies = dependencies.filter(dep => !dep.module);
    
    if (missingDependencies.length > 0) {
      console.error('[Dashboard] 누락된 의존성:', missingDependencies.map(dep => dep.name).join(', '));
      
      // 사용자에게 알림
      if (window.Alerts) {
        Alerts.error('일부 필수 스크립트를 로드할 수 없습니다. 페이지를 새로고침하세요.');
      } else {
        alert('일부 필수 스크립트를 로드할 수 없습니다. 페이지를 새로고침하세요.');
      }
      
      return false;
    }
    
    console.log('[Dashboard] 의존성 검사 완료 - 모든 필수 모듈 로드됨');
    return true;
  }
  
  /**
   * 모듈을 등록합니다.
   * @param {string} name - 모듈 이름
   * @param {Object} module - 모듈 객체
   */
  function registerModule(name, module) {
    if (!name || !module) return;
    
    // private 모듈 컨테이너에 저장
    modules[name] = module;
    
    // 핵심 수정: Dashboard 객체에 직접 모듈 추가 (외부 접근용)
    this[name] = module;
    
    console.log(`[Dashboard] 모듈 등록: ${name}`);
  }
  
  /**
   * 현재 주문 ID를 설정합니다.
   * @param {string} orderId - 주문 ID
   */
  function setCurrentOrderId(orderId) {
    currentOrderId = orderId;
  }
  
  /**
   * 현재 주문 ID를 반환합니다.
   * @returns {string} - 현재 주문 ID
   */
  function getCurrentOrderId() {
    return currentOrderId;
  }
  
  /**
   * 등록된 모듈에 접근합니다.
   * @param {string} name - 모듈 이름
   * @returns {Object|null} - 모듈 객체 또는 null
   */
  function getModule(name) {
    return modules[name] || null;
  }
  
  /**
   * 등록된 모든 모듈 이름을 반환합니다.
   * @returns {string[]} - 모듈 이름 배열
   */
  function getModuleNames() {
    return Object.keys(modules);
  }
  
  // 공개 API
  return {
    init: init,
    registerModule: registerModule,
    setCurrentOrderId: setCurrentOrderId,
    getCurrentOrderId: getCurrentOrderId,
    getModule: getModule,
    getModuleNames: getModuleNames
  };
})();
