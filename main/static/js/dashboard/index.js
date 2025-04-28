console.log('[로드] dashboard/index.js 로드됨 - ' + new Date().toISOString());

/**
 * 대시보드 진입점 모듈
 * 대시보드 페이지의 초기화를 담당합니다.
 */
(function() {
  // Dashboard 객체가 존재하는지 확인
  if (!window.Dashboard) {
    console.error('[대시보드] Dashboard 객체가 초기화되지 않았습니다.');
    return;
  }
  
  // 모듈 초기화 여부를 확인하는 플래그
  let isInitialized = false;
  
  /**
   * 대시보드 초기화 함수
   */
  function initDashboard() {
    console.log('[대시보드] 초기화 시작');
    
    // 이미 초기화된 경우 중복 초기화 방지
    if (isInitialized) {
      console.warn('[대시보드] 이미 초기화되었습니다.');
      return;
    }
    
    try {
      // 의존성 확인
      const dependencies = [
        { name: 'Logger', module: window.Logger },
        { name: 'API', module: window.API },
        { name: 'Alerts', module: window.Alerts },
        { name: 'Auth', module: window.Auth }
      ];
      
      const missingDeps = dependencies.filter(dep => !dep.module);
      if (missingDeps.length > 0) {
        console.error('[대시보드] 누락된 의존성:', missingDeps.map(d => d.name).join(', '));
        alert('필요한 모듈을 로드할 수 없습니다. 페이지를 새로고침하세요.');
        return;
      }
      
      // 직접 필요한 모듈 초기화
      initDashboardModules();
      
      // 초기화 완료 표시
      isInitialized = true;
      console.log('[대시보드] 초기화 완료');
    } catch (error) {
      console.error('[대시보드] 초기화 중 오류 발생:', error);
      alert('대시보드 초기화 중 오류가 발생했습니다: ' + error.message);
    }
  }
  
  /**
   * 대시보드 모듈 직접 초기화
   * 중앙 집중식 초기화 대신 각 모듈을 직접 초기화
   */
  function initDashboardModules() {
    // 테이블 모듈 초기화
    if (Dashboard.table && typeof Dashboard.table.init === 'function') {
      try {
        Dashboard.table.init();
      } catch (e) {
        console.error('[대시보드] 테이블 모듈 초기화 실패:', e);
      }
    }
    
    // 필터 모듈 초기화
    if (Dashboard.filter && typeof Dashboard.filter.init === 'function') {
      try {
        Dashboard.filter.init();
      } catch (e) {
        console.error('[대시보드] 필터 모듈 초기화 실패:', e);
      }
    }
    
    // 페이지네이션 모듈 초기화
    if (Dashboard.pagination && typeof Dashboard.pagination.init === 'function') {
      try {
        Dashboard.pagination.init();
      } catch (e) {
        console.error('[대시보드] 페이지네이션 모듈 초기화 실패:', e);
      }
    }
    
    // 컬럼 모듈 초기화
    if (Dashboard.columns && typeof Dashboard.columns.init === 'function') {
      try {
        Dashboard.columns.init();
      } catch (e) {
        console.error('[대시보드] 컬럼 모듈 초기화 실패:', e);
      }
    }
    
    // 액션 모듈 초기화
    if (Dashboard.actions && typeof Dashboard.actions.init === 'function') {
      try {
        Dashboard.actions.init();
      } catch (e) {
        console.error('[대시보드] 액션 모듈 초기화 실패:', e);
      }
    }
    
    // 체크박스 모듈 초기화
    if (Dashboard.checkbox && typeof Dashboard.checkbox.init === 'function') {
      try {
        Dashboard.checkbox.init();
      } catch (e) {
        console.error('[대시보드] 체크박스 모듈 초기화 실패:', e);
      }
    }
  }
  
  // 페이지 로드 시 초기화
  document.addEventListener('DOMContentLoaded', initDashboard);
  
  // 이미 DOM이 로드된 경우를 대비한 처리
  if (document.readyState === 'complete' || document.readyState === 'interactive') {
    // DOM이 이미 로드된 상태이면 즉시 초기화
    initDashboard();
  }
})();
