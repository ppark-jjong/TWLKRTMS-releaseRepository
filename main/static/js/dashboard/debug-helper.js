console.log('[로드] dashboard/debug-helper.js 로드됨 - ' + new Date().toISOString());

/**
 * 디버그 헬퍼 모듈
 * 모듈 로딩 및 초기화 순서를 추적하는 도구
 */
window.DashboardDebug = (function() {
  // 디버그 모드 활성화 여부
  let isDebugMode = true;
  
  // 모듈 상태 추적
  const modulesStatus = {
    loaded: {},   // 로드된 모듈
    registered: {}, // 등록된 모듈
    initialized: {} // 초기화된 모듈
  };
  
  // 타임스탬프 로그
  const timeStamps = [];
  
  /**
   * 디버그 로그를 기록합니다.
   * @param {string} module - 모듈 이름
   * @param {string} action - 수행된 작업
   * @param {string} message - 메시지
   * @param {Object} data - 추가 데이터
   */
  function log(module, action, message, data) {
    if (!isDebugMode) return;
    
    const timestamp = new Date().toISOString();
    const timeStr = timestamp.substring(11, 23); // HH:MM:SS.mmm 형식
    
    // 타임스탬프 기록
    timeStamps.push({
      time: timestamp,
      module,
      action,
      message
    });
    
    // 콘솔 출력
    const formattedMsg = `[${timeStr}] [${module}] [${action}] ${message}`;
    
    if (data) {
      console.log(formattedMsg, data);
    } else {
      console.log(formattedMsg);
    }
  }
  
  /**
   * 모듈 로드를 기록합니다.
   * @param {string} moduleName - 모듈 이름
   */
  function logModuleLoaded(moduleName) {
    modulesStatus.loaded[moduleName] = new Date();
    log('모듈 로더', 'LOAD', `${moduleName} 로드됨`);
  }
  
  /**
   * 모듈 등록을 기록합니다.
   * @param {string} moduleName - 모듈 이름
   */
  function logModuleRegistered(moduleName) {
    modulesStatus.registered[moduleName] = new Date();
    log('모듈 관리자', 'REGISTER', `${moduleName} 등록됨`);
  }
  
  /**
   * 모듈 초기화를 기록합니다.
   * @param {string} moduleName - 모듈 이름
   * @param {boolean} success - 초기화 성공 여부
   * @param {string} message - 추가 메시지
   */
  function logModuleInitialized(moduleName, success, message) {
    modulesStatus.initialized[moduleName] = {
      time: new Date(),
      success,
      message
    };
    
    const status = success ? 'SUCCESS' : 'FAILED';
    log('초기화 관리자', status, `${moduleName} 초기화 ${success ? '성공' : '실패'}${message ? ': ' + message : ''}`);
  }
  
  /**
   * 모듈 초기화 순서를 분석합니다.
   * @returns {Object} - 모듈 초기화 분석 결과
   */
  function analyzeInitOrder() {
    const moduleNames = Object.keys(modulesStatus.loaded);
    
    // 초기화 순서 분석
    const initSequence = moduleNames
      .filter(name => modulesStatus.initialized[name]?.success)
      .map(name => ({
        name,
        loadTime: modulesStatus.loaded[name],
        registerTime: modulesStatus.registered[name],
        initTime: modulesStatus.initialized[name]?.time
      }))
      .sort((a, b) => a.initTime - b.initTime);
    
    // 초기화되지 않은 모듈
    const uninitialized = moduleNames
      .filter(name => !modulesStatus.initialized[name])
      .map(name => ({
        name,
        loadTime: modulesStatus.loaded[name],
        registerTime: modulesStatus.registered[name] || null
      }));
    
    // 초기화 실패 모듈
    const failed = moduleNames
      .filter(name => modulesStatus.initialized[name] && !modulesStatus.initialized[name].success)
      .map(name => ({
        name,
        loadTime: modulesStatus.loaded[name],
        registerTime: modulesStatus.registered[name],
        message: modulesStatus.initialized[name].message
      }));
    
    return {
      sequence: initSequence,
      uninitialized,
      failed,
      totals: {
        loaded: Object.keys(modulesStatus.loaded).length,
        registered: Object.keys(modulesStatus.registered).length,
        initialized: Object.values(modulesStatus.initialized).filter(v => v?.success).length,
        failed: failed.length
      }
    };
  }
  
  /**
   * 모듈 초기화 상태를 콘솔에 출력합니다.
   */
  function printStatus() {
    const analysis = analyzeInitOrder();
    
    console.group('🔍 대시보드 모듈 초기화 상태');
    
    console.log(`총 모듈 수: ${analysis.totals.loaded}, 등록됨: ${analysis.totals.registered}, 초기화됨: ${analysis.totals.initialized}, 실패: ${analysis.totals.failed}`);
    
    if (analysis.sequence.length > 0) {
      console.group('✅ 초기화 성공 모듈 (순서대로)');
      analysis.sequence.forEach((module, index) => {
        console.log(`${index + 1}. ${module.name}`);
      });
      console.groupEnd();
    }
    
    if (analysis.uninitialized.length > 0) {
      console.group('⚠️ 미초기화 모듈');
      analysis.uninitialized.forEach(module => {
        console.log(`❗ ${module.name} - 로드됨${module.registerTime ? ', 등록됨' : ', 등록안됨'}`);
      });
      console.groupEnd();
    }
    
    if (analysis.failed.length > 0) {
      console.group('❌ 초기화 실패 모듈');
      analysis.failed.forEach(module => {
        console.log(`❌ ${module.name} - ${module.message || '오류 메시지 없음'}`);
      });
      console.groupEnd();
    }
    
    console.groupEnd();
    
    return analysis;
  }
  
  /**
   * 디버그 모드를 활성화/비활성화합니다.
   * @param {boolean} enable - 활성화 여부
   */
  function setDebugMode(enable) {
    isDebugMode = !!enable;
    log('디버그 관리자', 'CONFIG', `디버그 모드 ${isDebugMode ? '활성화' : '비활성화'}`);
  }
  
  // 초기화
  log('디버그 관리자', 'INIT', '디버그 헬퍼 모듈 초기화됨');
  
  // 공개 API
  return {
    log,
    logModuleLoaded,
    logModuleRegistered,
    logModuleInitialized,
    analyzeInitOrder,
    printStatus,
    setDebugMode,
    isDebugEnabled: () => isDebugMode
  };
})();

// 전역 변수에 쉽게 접근할 수 있는 별칭 추가
window.DD = window.DashboardDebug;
