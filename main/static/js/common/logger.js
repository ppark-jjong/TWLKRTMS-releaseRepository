console.log('[로드] logger.js 로드됨 - ' + new Date().toISOString());

/**
 * 로깅 유틸리티
 * 일관된 방식의 콘솔 로그를 제공합니다.
 */
window.Logger = (function() {
  // 로그 레벨
  const LOG_LEVEL = {
    DEBUG: 0,
    INFO: 1,
    WARN: 2,
    ERROR: 3
  };
  
  // 현재 환경 설정 (개발/운영)
  let currentLogLevel = LOG_LEVEL.DEBUG;
  
  // 개발 환경 여부 확인
  function isDevelopment() {
    return window.location.hostname === 'localhost' || 
           window.location.hostname === '127.0.0.1' ||
           window.location.hostname.includes('dev-');
  }
  
  // 로그 포맷팅
  function formatLog(module, message) {
    const timestamp = new Date().toISOString().substring(11, 19);
    return `[${timestamp}] [${module}] ${message}`;
  }
  
  // 로그 메서드
  function debug(module, message, data) {
    if (currentLogLevel <= LOG_LEVEL.DEBUG) {
      if (data !== undefined) {
        console.debug(formatLog(module, message), data);
      } else {
        console.debug(formatLog(module, message));
      }
    }
  }
  
  function info(module, message, data) {
    if (currentLogLevel <= LOG_LEVEL.INFO) {
      if (data !== undefined) {
        console.info(formatLog(module, message), data);
      } else {
        console.info(formatLog(module, message));
      }
    }
  }
  
  function warn(module, message, data) {
    if (currentLogLevel <= LOG_LEVEL.WARN) {
      if (data !== undefined) {
        console.warn(formatLog(module, message), data);
      } else {
        console.warn(formatLog(module, message));
      }
    }
  }
  
  function error(module, message, data) {
    if (currentLogLevel <= LOG_LEVEL.ERROR) {
      if (data !== undefined) {
        console.error(formatLog(module, message), data);
      } else {
        console.error(formatLog(module, message));
      }
    }
  }
  
  // 운영 환경에서는 info 수준 이상 로그만 표시
  if (!isDevelopment()) {
    currentLogLevel = LOG_LEVEL.INFO;
  }
  
  // 디버깅용 로그 함수들
  const debugLog = {
    load: function(fileName) {
      console.log('[로드] ' + fileName + ' 로드됨 - ' + new Date().toISOString());
    },
    init: function(moduleName, stage) {
      console.log('[초기화] ' + moduleName + (stage ? ' - ' + stage : ''));
    },
    dependency: function(dependencyName, exists) {
      console.log('[의존성] ' + dependencyName + ' 객체 확인: ' + !!exists);
      if (!exists) {
        console.error('[의존성 오류] ' + dependencyName + ' 객체가 없습니다.');
      }
      return !!exists;
    },
    error: function(moduleName, error) {
      console.error('[오류] ' + moduleName + ': ' + (error.message || error));
    }
  };

  // 공개 API
  return {
    debug, info, warn, error,
    
    // 로그 레벨 설정
    setLevel: function(level) {
      if (LOG_LEVEL[level] !== undefined) {
        currentLogLevel = LOG_LEVEL[level];
      }
    },
    
    // 디버깅용 로그 함수들
    debug: debugLog
  };
})();
