console.log('[로드] api.js 로드됨 - ' + new Date().toISOString());

/**
 * API 통신 모듈
 * 서버와의 HTTP 통신을 처리하는 공통 유틸리티
 */
window.API = {
  /**
   * HTTP GET 요청을 보냅니다.
   * @param {string} url - 요청 URL
   * @param {Object} params - 쿼리 매개변수 객체
   * @param {boolean} showLoading - 로딩 표시 여부
   * @returns {Promise<Object>} - 응답 데이터
   */
  get: async function(url, params = {}, showLoading = true) {
    try {
      // 로딩 표시 (Utils 존재 여부 확인)
      if (showLoading && this._toggleLoading) {
        this._toggleLoading(true);
      }
      
      // URL에 쿼리 매개변수 추가
      const queryUrl = new URL(url, window.location.origin);
      Object.entries(params).forEach(([key, value]) => {
        if (value !== null && value !== undefined && value !== '') {
          queryUrl.searchParams.append(key, value);
        }
      });
      
      const response = await fetch(queryUrl.toString(), {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest',
          'Accept': 'application/json'
        },
        credentials: 'include'
      });
      
      return await this._handleResponse(response);
    } catch (error) {
      return this._handleError(error);
    } finally {
      // 로딩 숨김 (Utils 존재 여부 확인)
      if (showLoading && this._toggleLoading) {
        this._toggleLoading(false);
      }
    }
  },
  
  /**
   * HTTP POST 요청을 보냅니다.
   * @param {string} url - 요청 URL
   * @param {Object} data - 요청 본문 데이터
   * @param {boolean} showLoading - 로딩 표시 여부
   * @returns {Promise<Object>} - 응답 데이터
   */
  post: async function(url, data = {}, showLoading = true) {
    try {
      // 로딩 표시 (Utils 존재 여부 확인)
      if (showLoading && this._toggleLoading) {
        this._toggleLoading(true);
      }
      
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest',
          'Accept': 'application/json'
        },
        body: JSON.stringify(data),
        credentials: 'include'
      });
      
      return await this._handleResponse(response);
    } catch (error) {
      return this._handleError(error);
    } finally {
      // 로딩 숨김 (Utils 존재 여부 확인)
      if (showLoading && this._toggleLoading) {
        this._toggleLoading(false);
      }
    }
  },
  
  /**
   * HTTP PUT 요청을 보냅니다.
   * @param {string} url - 요청 URL
   * @param {Object} data - 요청 본문 데이터
   * @param {boolean} showLoading - 로딩 표시 여부
   * @returns {Promise<Object>} - 응답 데이터
   */
  put: async function(url, data = {}, showLoading = true) {
    try {
      // 로딩 표시 (Utils 존재 여부 확인)
      if (showLoading && this._toggleLoading) {
        this._toggleLoading(true);
      }
      
      const response = await fetch(url, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest',
          'Accept': 'application/json'
        },
        body: JSON.stringify(data),
        credentials: 'include'
      });
      
      return await this._handleResponse(response);
    } catch (error) {
      return this._handleError(error);
    } finally {
      // 로딩 숨김 (Utils 존재 여부 확인)
      if (showLoading && this._toggleLoading) {
        this._toggleLoading(false);
      }
    }
  },
  
  /**
   * HTTP DELETE 요청을 보냅니다.
   * @param {string} url - 요청 URL
   * @param {Object} data - 요청 본문 데이터
   * @param {boolean} showLoading - 로딩 표시 여부
   * @returns {Promise<Object>} - 응답 데이터
   */
  delete: async function(url, data = {}, showLoading = true) {
    try {
      // 로딩 표시 (Utils 존재 여부 확인)
      if (showLoading && this._toggleLoading) {
        this._toggleLoading(true);
      }
      
      const response = await fetch(url, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest',
          'Accept': 'application/json'
        },
        body: JSON.stringify(data),
        credentials: 'include'
      });
      
      return await this._handleResponse(response);
    } catch (error) {
      return this._handleError(error);
    } finally {
      // 로딩 숨김 (Utils 존재 여부 확인)
      if (showLoading && this._toggleLoading) {
        this._toggleLoading(false);
      }
    }
  },
  
  /**
   * 응답을 처리합니다.
   * @param {Response} response - fetch API 응답 객체
   * @returns {Promise<Object>} - 처리된 응답 데이터
   * @private
   */
  _handleResponse: async function(response) {
    // 인증 오류 확인 (401 Unauthorized)
    if (response.status === 401) {
      // 세션 만료 이벤트 발생
      const unauthorizedEvent = new Event('UnauthorizedError');
      document.dispatchEvent(unauthorizedEvent);
      
      // 로그인 페이지로 리다이렉트
      if (window.Auth) {
        Auth.redirectToLogin('session_expired');
      } else {
        window.location.href = '/auth/login?reason=session_expired';
      }
      
      throw new Error('세션이 만료되었습니다. 다시 로그인해주세요.');
    }
    
    // 세션 만료 확인 (리다이렉트 응답)
    if (response.redirected) {
      const redirectUrl = new URL(response.url);
      
      // 로그인 페이지로 리다이렉트된 경우
      if (redirectUrl.pathname.includes('/auth/login')) {
        // 세션 만료 이벤트 발생
        const unauthorizedEvent = new Event('UnauthorizedError');
        document.dispatchEvent(unauthorizedEvent);
        
        // 로그인 페이지로 리다이렉트
        if (window.Auth) {
          Auth.redirectToLogin('session_expired');
        } else {
          window.location.href = '/auth/login?reason=session_expired';
        }
        
        throw new Error('세션이 만료되었습니다. 다시 로그인해주세요.');
      }
    }
    
    // JSON 응답 파싱
    let result;
    try {
      result = await response.json();
    } catch (error) {
      console.error('JSON 파싱 오류:', error);
      
      // 텍스트 응답 시도
      const text = await response.text();
      throw new Error(`응답 처리 중 오류가 발생했습니다. 서버 응답: ${text}`);
    }
    
    // 응답 상태코드 확인
    if (!response.ok) {
      const message = result.message || `HTTP 오류 ${response.status}: ${response.statusText}`;
      const error = new Error(message);
      error.response = response;
      error.data = result;
      throw error;
    }
    
    return result;
  },
  
  /**
   * 오류를 처리하고 적절한 응답을 반환합니다.
   * @param {Error} error - 발생한 오류
   * @returns {Promise<Object>} - 오류 응답 객체
   * @private
   */
  _handleError: function(error) {
    console.error('API 오류:', error);
    
    // UI에 오류 표시
    if (window.Alerts) {
      Alerts.error(error.message || '서버 통신 중 오류가 발생했습니다.');
    } else if (this._showAlert) {
      this._showAlert(error.message || '서버 통신 중 오류가 발생했습니다.', 'error');
    } else {
      alert(error.message || '서버 통신 중 오류가 발생했습니다.');
    }
    
    // 표준 오류 응답 형식 반환
    return Promise.resolve({
      success: false,
      error_code: error.code || 'UNKNOWN_ERROR',
      message: error.message || '알 수 없는 오류가 발생했습니다.'
    });
  },
  
  /**
   * 로딩 상태를 토글합니다.
   * @param {boolean} show - 로딩 표시 여부
   * @private
   */
  _toggleLoading: function(show) {
    const loadingElement = document.querySelector('.loading-overlay');
    if (!loadingElement) return;
    
    if (show) {
      loadingElement.style.display = 'flex';
    } else {
      loadingElement.style.display = 'none';
    }
  },
  
  /**
   * 알림 메시지를 표시합니다.
   * @param {string} message - 메시지 내용
   * @param {string} type - 알림 유형 (success, warning, error, info)
   * @private
   */
  _showAlert: function(message, type = 'info') {
    if (window.Alerts && typeof window.Alerts[type] === 'function') {
      window.Alerts[type](message);
    } else {
      alert(message);
    }
  }
};
