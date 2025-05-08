/**
 * 공통 유틸리티 함수 모음
 * 모든 페이지에서 재사용 가능한 헬퍼 함수들을 제공합니다.
 */
const Utils = {
  /**
   * NULL 값 처리 개선
   * null, 'None', undefined 값을 안전하게 처리
   * @param {any} value - 검사할 값
   * @param {string} defaultValue - 기본값 (생략 시 빈 문자열)
   * @returns {string} - 처리된 값
   */
  safeText: function (value, defaultValue = '') {
    // null, undefined, 'None' 문자열을 defaultValue로 변환
    if (value === null || value === undefined || value === 'None') {
      return defaultValue;
    }
    return value;
  },
  /**
   * 우편번호 포맷팅 (4자리 -> 5자리)
   * @param {string} code - 입력된 우편번호
   * @returns {string} - 포맷팅된 우편번호
   */
  formatPostalCode: function (code) {
    if (!code) return '';

    // 숫자만 추출
    const numericValue = code.replace(/[^\d]/g, '');

    // 4자리인 경우 앞에 0 추가
    if (numericValue.length === 4) {
      return '0' + numericValue;
    }

    return numericValue;
  },

  /**
   * 우편번호 유효성 검사
   * @param {string} code - 입력된 우편번호
   * @returns {boolean} - 유효한 우편번호인지 여부(5자리 숫자)
   */
  validatePostalCode: function (code) {
    if (!code) return false;
    const numericValue = code.replace(/[^\d]/g, '');
    return numericValue.length === 5;
  },

  /**
   * 연락처 자동 하이픈 포맷팅
   * @param {string} number - 원본 전화번호
   * @returns {string} - 하이픈이 포함된 전화번호
   */
  formatPhoneNumber: function (number) {
    if (!number) return '';

    // 숫자만 추출
    const numericValue = number.replace(/[^\d]/g, '');

    // 자릿수에 따라 다른 포맷 적용
    if (numericValue.length === 11) {
      // 휴대폰 (01012345678 -> 010-1234-5678)
      return numericValue.replace(/(\d{3})(\d{4})(\d{4})/, '$1-$2-$3');
    } else if (numericValue.length === 10) {
      // 지역번호 2자리 (0212345678 -> 02-1234-5678)
      if (numericValue.startsWith('02')) {
        return numericValue.replace(/(\d{2})(\d{4})(\d{4})/, '$1-$2-$3');
      }
      // 휴대폰 또는 지역번호 3자리 (0101234567 -> 010-123-4567)
      return numericValue.replace(/(\d{3})(\d{3})(\d{4})/, '$1-$2-$3');
    } else if (numericValue.length === 9) {
      // 지역번호 2자리 (021234567 -> 02-123-4567)
      if (numericValue.startsWith('02')) {
        return numericValue.replace(/(\d{2})(\d{3})(\d{4})/, '$1-$2-$3');
      }
      // 기타 9자리 (031123456 -> 031-12-3456)
      return numericValue.replace(/(\d{3})(\d{2})(\d{4})/, '$1-$2-$3');
    } else if (numericValue.length === 8) {
      // 8자리 전화번호 (12345678 -> 1234-5678)
      return numericValue.replace(/(\d{4})(\d{4})/, '$1-$2');
    }

    // 그 외의 경우 원래 숫자 반환
    return numericValue;
  },

  /**
   * 날짜 형식 변환 (ISO 8601 형식: YYYY-MM-DDTHH:MM)
   * @param {string|Date} dateString - 변환할 날짜 문자열 또는 Date 객체
   * @returns {string} - ISO 8601 형식의 날짜 문자열
   */
  formatDate: function (dateString) {
    if (!dateString) return '';

    let date;
    // 이미 ISO 문자열이면 그대로 반환
    if (typeof dateString === 'string' && dateString.includes('T')) {
      return dateString;
    }
    // Date 객체이거나 다른 형식의 문자열이면 변환
    else {
      date = dateString instanceof Date ? dateString : new Date(dateString);
    }

    // 유효한 날짜가 아니면 원래 값 반환
    if (isNaN(date.getTime())) return dateString;

    // ISO 8601 형식으로 변환 (YYYY-MM-DDTHH:MM)
    return date.toISOString().slice(0, 16);
  },

  /**
   * 알림 메시지 표시 관련 유틸리티
   */
  alerts: {
    /**
     * 성공 메시지 표시
     * @param {string} message - 표시할 메시지
     * @param {number} duration - 표시 지속 시간 (밀리초)
     */
    showSuccess: function (message, duration = 3000) {
      Utils.alerts._showAlert(message, 'success', duration);
    },

    /**
     * 오류 메시지 표시
     * @param {string} message - 표시할 메시지
     * @param {number} duration - 표시 지속 시간 (0이면 수동으로 닫을 때까지 유지)
     */
    showError: function (message, duration = 0) {
      Utils.alerts._showAlert(message, 'error', duration);
    },

    /**
     * 경고 메시지 표시
     * @param {string} message - 표시할 메시지
     * @param {number} duration - 표시 지속 시간 (밀리초)
     */
    showWarning: function (message, duration = 5000) {
      Utils.alerts._showAlert(message, 'warning', duration);
    },

    /**
     * 정보 메시지 표시
     * @param {string} message - 표시할 메시지
     * @param {number} duration - 표시 지속 시간 (밀리초)
     */
    showInfo: function (message, duration = 3000) {
      Utils.alerts._showAlert(message, 'info', duration);
    },

    /**
     * 로딩 표시
     * @param {string} message - 표시할 메시지 (기본값: "로딩 중...")
     */
    showLoading: function (message = '로딩 중...') {
      // 기존 로딩 제거
      Utils.alerts.hideLoading();

      // 로딩 오버레이 생성
      const overlay = document.createElement('div');
      overlay.id = 'loading-overlay';
      overlay.style.position = 'fixed';
      overlay.style.top = '0';
      overlay.style.left = '0';
      overlay.style.width = '100%';
      overlay.style.height = '100%';
      overlay.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
      overlay.style.display = 'flex';
      overlay.style.justifyContent = 'center';
      overlay.style.alignItems = 'center';
      overlay.style.zIndex = '2000';

      // 로딩 컨테이너
      const loadingContainer = document.createElement('div');
      loadingContainer.style.backgroundColor = 'white';
      loadingContainer.style.borderRadius = '5px';
      loadingContainer.style.padding = '20px';
      loadingContainer.style.display = 'flex';
      loadingContainer.style.flexDirection = 'column';
      loadingContainer.style.alignItems = 'center';
      loadingContainer.style.gap = '10px';

      // 스피너
      const spinner = document.createElement('div');
      spinner.className = 'loading-spinner';
      spinner.style.width = '30px';
      spinner.style.height = '30px';
      spinner.style.border = '3px solid rgba(0, 0, 0, 0.1)';
      spinner.style.borderRadius = '50%';
      spinner.style.borderTop = '3px solid #D72519'; // 포인트 색상 적용
      spinner.style.animation = 'spin 1s linear infinite';

      // 애니메이션 스타일 추가
      const style = document.createElement('style');
      style.textContent = `
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `;
      document.head.appendChild(style);

      // 메시지 텍스트
      const messageElement = document.createElement('div');
      messageElement.className = 'alert-message';
      messageElement.style.flex = '1';
      messageElement.style.paddingRight = '10px';
      messageElement.textContent = message;

      // 컴포넌트 조립
      loadingContainer.appendChild(spinner);
      loadingContainer.appendChild(messageElement);
      overlay.appendChild(loadingContainer);
      document.body.appendChild(overlay);
    },

    /**
     * 로딩 숨기기
     */
    hideLoading: function () {
      const overlay = document.getElementById('loading-overlay');
      if (overlay) {
        overlay.remove();
      }
    },

    /**
     * 알림 메시지 내부 표시 로직
     * @param {string} message - 표시할 메시지
     * @param {string} type - 알림 유형 (success, error, warning, info)
     * @param {number} duration - 표시 지속 시간 (밀리초, 0이면 무기한)
     * @private
     */
    _showAlert: function (message, type, duration) {
      // 이미 존재하는 알림 컨테이너 찾기 또는 생성
      let alertContainer = document.getElementById('custom-alert-container');

      if (!alertContainer) {
        alertContainer = document.createElement('div');
        alertContainer.id = 'custom-alert-container';
        alertContainer.style.position = 'fixed';
        alertContainer.style.top = '20px';
        alertContainer.style.right = '20px';
        alertContainer.style.zIndex = '1999';
        alertContainer.style.maxWidth = '400px';
        alertContainer.style.display = 'flex';
        alertContainer.style.flexDirection = 'column';
        alertContainer.style.gap = '10px';
        document.body.appendChild(alertContainer);
      }

      // 동일한 메시지와 타입을 가진 알림이 이미 존재하는지 확인
      const alertElements = alertContainer.querySelectorAll('.custom-alert');
      for (let i = 0; i < alertElements.length; i++) {
        const alert = alertElements[i];
        if (
          alert.getAttribute('data-type') === type &&
          alert.querySelector('.alert-message').textContent === message
        ) {
          return; // 중복 알림이면 새로 생성하지 않고 종료
        }
      }

      // 알림 ID 생성
      const alertId = 'alert-' + Date.now();

      // 알림 요소 생성
      const alertElement = document.createElement('div');
      alertElement.id = alertId;
      alertElement.className = 'custom-alert';
      alertElement.setAttribute('data-type', type); // 타입 저장
      alertElement.style.backgroundColor = 'white';
      alertElement.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.15)';
      alertElement.style.borderRadius = '4px';
      alertElement.style.padding = '15px';
      alertElement.style.marginBottom = '10px';
      alertElement.style.display = 'flex';
      alertElement.style.alignItems = 'flex-start';
      alertElement.style.opacity = '0';
      alertElement.style.transition = 'opacity 0.3s ease-in-out';

      // 타입별 테두리 색상과 아이콘 설정
      let iconClass, borderColor, iconColor;

      switch (type) {
        case 'success':
          iconClass = 'fa-solid fa-check-circle';
          borderColor = '#4CAF50';
          iconColor = '#4CAF50';
          break;
        case 'error':
          iconClass = 'fa-solid fa-exclamation-circle';
          borderColor = '#F44336';
          iconColor = '#F44336';
          break;
        case 'warning':
          iconClass = 'fa-solid fa-exclamation-triangle';
          borderColor = '#FF9800';
          iconColor = '#FF9800';
          break;
        case 'info':
        default:
          iconClass = 'fa-solid fa-info-circle';
          borderColor = '#2196F3';
          iconColor = '#2196F3';
          break;
      }

      // 락 관련 메시지인 경우 아이콘 변경
      if (
        message.includes('편집 중입니다') ||
        message.includes('님이 현재 편집 중')
      ) {
        iconClass = 'fa-solid fa-lock';
      }

      alertElement.style.borderLeft = `4px solid ${borderColor}`;

      // 아이콘 요소
      const iconElement = document.createElement('i');
      iconElement.className = iconClass;
      iconElement.style.marginRight = '10px';
      iconElement.style.color = iconColor;
      iconElement.style.fontSize = '18px';

      // 메시지 텍스트 요소
      const messageElement = document.createElement('div');
      messageElement.className = 'alert-message';
      messageElement.style.flex = '1';
      messageElement.style.paddingRight = '10px';
      messageElement.textContent = message;

      // 닫기 버튼 요소
      const closeButton = document.createElement('button');
      closeButton.innerHTML = '&times;';
      closeButton.style.background = 'none';
      closeButton.style.border = 'none';
      closeButton.style.cursor = 'pointer';
      closeButton.style.fontSize = '16px';
      closeButton.style.fontWeight = 'bold';
      closeButton.style.color = '#888';
      closeButton.style.padding = '0 5px';

      closeButton.addEventListener('click', function () {
        Utils.alerts._removeAlert(alertId);
      });

      // 요소들 조립
      alertElement.appendChild(iconElement);
      alertElement.appendChild(messageElement);
      alertElement.appendChild(closeButton);
      alertContainer.appendChild(alertElement);

      // 애니메이션 효과로 표시
      setTimeout(() => {
        alertElement.style.opacity = '1';
      }, 10);

      // 지정된 시간 후 자동 제거 (duration이 0보다 큰 경우)
      if (duration > 0) {
        setTimeout(() => {
          Utils.alerts._removeAlert(alertId);
        }, duration);
      }
    },

    /**
     * 알림 요소 제거
     * @param {string} alertId - 제거할 알림의 ID
     * @private
     */
    _removeAlert: function (alertId) {
      const alertElement = document.getElementById(alertId);
      if (alertElement) {
        // 페이드 아웃 효과
        alertElement.style.opacity = '0';

        // 애니메이션 완료 후 요소 제거
        setTimeout(() => {
          if (alertElement.parentNode) {
            alertElement.parentNode.removeChild(alertElement);
          }

          // 컨테이너에 알림이 없으면 컨테이너도 제거
          const alertContainer = document.getElementById(
            'custom-alert-container'
          );
          if (alertContainer && alertContainer.children.length === 0) {
            alertContainer.parentNode.removeChild(alertContainer);
          }
        }, 300);
      }
    },
  },

  /**
   * 폼 관련 공통 기능
   */
  forms: {
    /**
     * 폼 비활성화/활성화
     * @param {HTMLFormElement} form - 대상 폼 요소
     * @param {boolean} disabled - 비활성화 여부
     * @param {string} loadingText - 로딩 중 표시할 텍스트 (optional)
     * @param {string} originalText - 원래 버튼 텍스트 (optional)
     */
    disable: function (form, disabled, loadingText, originalText) {
      if (!form) return;

      // 폼 내 모든 입력 요소 찾기
      const inputs = form.querySelectorAll('input, select, textarea, button');

      // 비활성화 상태 설정
      inputs.forEach((input) => {
        input.disabled = disabled;
      });

      // 제출 버튼 업데이트 (제공된 경우)
      if (loadingText && originalText) {
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
          if (disabled) {
            submitBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> ${loadingText}`;
          } else {
            submitBtn.innerHTML = originalText;
          }
        }
      }
    },

    /**
     * 필수 입력 필드 검증
     * @param {HTMLFormElement} form - 검증할 폼
     * @returns {boolean} - 모든 필수 필드가 입력되었는지 여부
     */
    validateRequired: function (form) {
      if (!form) return false;

      // required 속성이 있는 모든 필드 검색
      const requiredFields = form.querySelectorAll('[required]');
      let isValid = true;

      // 각 필수 필드 검증
      requiredFields.forEach((field) => {
        if (!field.value.trim()) {
          isValid = false;
          // 오류 스타일 적용
          field.classList.add('input-error');

          // 오류 메시지 표시 (필드 아래)
          const fieldName = field.getAttribute('data-name') || field.name;
          const errorSpan = document.createElement('span');
          errorSpan.className = 'error-message';
          errorSpan.textContent = `${fieldName}을(를) 입력해주세요.`;

          // 기존 오류 메시지 제거
          const existingError =
            field.parentNode.querySelector('.error-message');
          if (existingError) {
            existingError.remove();
          }

          // 새 오류 메시지 추가
          field.parentNode.appendChild(errorSpan);

          // 입력 시 오류 스타일 제거
          field.addEventListener(
            'input',
            function () {
              if (field.value.trim()) {
                field.classList.remove('input-error');
                const error = field.parentNode.querySelector('.error-message');
                if (error) error.remove();
              }
            },
            { once: true }
          );
        }
      });

      return isValid;
    },
  },

  /**
   * API 요청 관련 공통 기능
   */
  api: {
    /**
     * GET 요청 수행
     * @param {string} url - 요청 URL
     * @param {Object} options - 추가 옵션
     * @returns {Promise<Object>} - 응답 데이터
     */
    get: async function (url, options = {}) {
      return Utils.api._request(url, {
        method: 'GET',
        ...options,
      });
    },

    /**
     * POST 요청 수행 (JSON 데이터)
     * @param {string} url - 요청 URL
     * @param {Object} data - 전송할 데이터
     * @param {Object} options - 추가 옵션
     * @returns {Promise<Object>} - 응답 데이터
     */
    post: async function (url, data, options = {}) {
      return Utils.api._request(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(options.headers || {}),
        },
        body: JSON.stringify(data),
        ...options,
      });
    },

    /**
     * 내부 요청 처리 함수
     * @private
     */
    _request: async function (url, options = {}) {
      try {
        const response = await fetch(url, {
          ...options,
          credentials: 'include',
        });

        // 세션 만료 체크 (401 상태 코드)
        if (response.status === 401) {
          Utils.api._handleSessionExpired();
          return null;
        }

        // 기타 오류 상태 처리
        if (!response.ok) {
          return Utils.api._handleErrorResponse(response);
        }

        // 성공 응답 처리
        return await response.json();
      } catch (error) {
        Utils.alerts.showError(
          '네트워크 오류가 발생했습니다. 다시 시도해주세요.'
        );

        return null;
      }
    },

    /**
     * 세션 만료 처리
     * @private
     */
    _handleSessionExpired: function () {
      Utils.alerts.showError('세션이 만료되었습니다. 다시 로그인해주세요.');

      // 현재 URL을 저장하여 로그인 후 돌아올 수 있도록 함
      const returnUrl = encodeURIComponent(window.location.pathname);

      // 잠시 후 로그인 페이지로 리다이렉트
      setTimeout(() => {
        window.location.href = `/login?return_to=${returnUrl}`;
      }, 1500);
    },

    /**
     * 오류 응답 처리
     * @private
     */
    _handleErrorResponse: async function (response) {
      let errorMessage = '요청 처리 중 오류가 발생했습니다.';

      try {
        const errorData = await response.json();
        if (errorData && errorData.message) {
          errorMessage = errorData.message;
        }

        Utils.alerts.showError(errorMessage);
        return errorData;
      } catch (parseError) {
        Utils.alerts.showError(errorMessage);

        return null;
      }
    },
  },

  /**
   * 인증 및 사용자 관련 공통 기능
   */
  auth: {
    /**
     * 현재 로그인한 사용자 정보 반환
     * (세션에서 window._currentUser를 통해 전달됨)
     * @returns {Object|null} - 사용자 정보 또는 null
     */
    getCurrentUser: function () {
      // 서버에서 렌더링 시 window._currentUser에 사용자 정보를 초기화해야 함
      return window._currentUser || null;
    },

    /**
     * 현재 사용자가 관리자인지 확인
     * @returns {boolean} - 관리자 여부
     */
    isAdmin: function () {
      const user = Utils.auth.getCurrentUser();
      return user && user.user_role === 'ADMIN';
    },

    /**
     * 현재 사용자가 특정 리소스의 소유자인지 확인
     * @param {string} resourceOwner - 리소스 소유자 ID
     * @returns {boolean} - 소유자 여부
     */
    isOwner: function (resourceOwner) {
      const user = Utils.auth.getCurrentUser();
      return user && user.user_id === resourceOwner;
    },

    /**
     * 현재 사용자 정보 설정/업데이트
     * @param {Object|null} user - 사용자 정보 또는 null(로그아웃)
     */
    setCurrentUser: function (user) {
      window._currentUser = user;
      // 사용자 정보가 변경되었을 때 UI 업데이트 등의 추가 로직을 여기에 구현할 수 있습니다.
    },

    /**
     * 로그아웃 기능
     * 사용자 정보를 삭제하고 서버 로그아웃 처리
     */
    logout: function () {
      // 서버 로그아웃 요청
      window.location.href = '/logout';
    },

    /**
     * 권한 확인 및 제한된 접근 처리
     * @param {string} requiredRole - 필요한 권한
     * @returns {boolean} - 권한 충족 여부
     */
    checkPermission: function (requiredRole) {
      const user = Utils.auth.getCurrentUser();
      const hasPermission = user && user.user_role === requiredRole;

      if (!hasPermission) {
        console.warn(
          `권한 부족: 필요한 권한 ${requiredRole}, 현재 역할: ${
            user ? user.user_role : '인증되지 않음'
          }`
        );
        Utils.alerts.showError('이 페이지에 접근할 권한이 없습니다.');

        // 3초 후 대시보드로 리다이렉트
        setTimeout(() => {
          window.location.href = '/dashboard';
        }, 3000);
      }

      return hasPermission;
    },
  },

  /**
   * UI 관련 공통 기능 (추가)
   */
  ui: {
    /**
     * 로딩 오버레이 표시
     */
    showLoading: function () {
      const overlay = document.getElementById('loadingOverlay');
      if (overlay) {
        overlay.classList.add('active');
      } else {
        console.warn('Loading overlay element not found.');
      }
    },

    /**
     * 로딩 오버레이 숨김
     */
    hideLoading: function () {
      const overlay = document.getElementById('loadingOverlay');
      if (overlay) {
        overlay.classList.remove('active');
      }
    },

    /**
     * URL 쿼리 파라미터의 success 또는 error 메시지를 알림으로 표시
     */
    showPageMessages: function () {
      // 이미 메시지가 표시되었는지 확인
      if (window._messagesShown) return;

      // URL에서 쿼리 파라미터 가져오기
      const urlParams = new URLSearchParams(window.location.search);
      const successMsg = urlParams.get('success');
      const errorMsg = urlParams.get('error');
      const warningMsg = urlParams.get('warning');

      // 메시지가 있으면 한 번만 표시하기 위한 플래그 설정
      if (successMsg || errorMsg || warningMsg) {
        window._messagesShown = true;

        // 성공 메시지가 있으면 표시
        if (successMsg) {
          Utils.alerts.showSuccess(decodeURIComponent(successMsg));
        }

        // 오류 메시지가 있으면 표시
        if (errorMsg) {
          Utils.alerts.showError(decodeURIComponent(errorMsg));
        }

        // 경고 메시지가 있으면 표시
        if (warningMsg) {
          Utils.alerts.showWarning(decodeURIComponent(warningMsg));
        }

        // 메시지 표시 후 URL에서 쿼리 파라미터 제거 (브라우저 새로고침 시 중복 표시 방지)
        const cleanUrl = window.location.pathname;
        history.replaceState({}, document.title, cleanUrl);
      }
    },
  },
};

// 글로벌 스코프에 Utils 공개
window.Utils = Utils;
