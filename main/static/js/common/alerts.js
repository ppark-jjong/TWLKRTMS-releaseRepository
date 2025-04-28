console.log('[로드] alerts.js 로드됨 - ' + new Date().toISOString());

/**
 * 알림 시스템 모듈
 * 사용자에게 알림 메시지를 표시하는 기능 제공
 */
window.Alerts = {
  /**
   * 알림 컨테이너 요소
   * @type {Element}
   */
  container: null,
  
  /**
   * 알림 모듈을 초기화합니다.
   */
  init: function() {
    console.log('[초기화] Alerts.init 시작');
    
    this.container = document.getElementById('alertContainer');
    
    if (!this.container) {
      console.error('알림 컨테이너를 찾을 수 없습니다.');
      
      // 알림 컨테이너 생성
      this.container = document.createElement('div');
      this.container.id = 'alertContainer';
      this.container.className = 'alert-container';
      document.body.appendChild(this.container);
    }
    
    // 이벤트 위임으로 닫기 버튼 클릭 처리
    this.container.addEventListener('click', function(event) {
      if (event.target.closest('.alert-close')) {
        const alert = event.target.closest('.alert');
        if (alert) {
          Alerts.hide(alert);
        }
      }
    });
    
    console.log('[초기화] Alerts.init 완료');
  },
  
  /**
   * 알림을 표시합니다.
   * @param {string} message - 알림 메시지
   * @param {string} type - 알림 유형 (success, error, warning, info)
   * @param {Object} options - 추가 옵션
   * @param {number} options.duration - 표시 시간 (밀리초, 0이면 자동으로 닫히지 않음)
   * @param {boolean} options.dismissible - 사용자가 닫을 수 있는지 여부
   * @returns {Element} - 생성된 알림 요소
   */
  show: function(message, type = 'info', options = {}) {
    // 옵션 기본값 설정
    const settings = {
      duration: type === 'error' ? 0 : 5000, // 오류는 자동으로 닫히지 않음
      dismissible: true,
      ...options
    };
    
    // 컨테이너 확인
    if (!this.container) {
      this.init();
    }
    
    // 중복 알림 확인 (동일 메시지, 동일 타입)
    const existingAlerts = this.container.querySelectorAll(`.alert-${type}`);
    for (const existingAlert of existingAlerts) {
      if (existingAlert.querySelector('.alert-message').textContent === message) {
        // 이미 표시된 알림 강조
        existingAlert.classList.add('alert-highlight');
        setTimeout(() => {
          existingAlert.classList.remove('alert-highlight');
        }, 500);
        return existingAlert;
      }
    }
    
    // 아이콘 선택
    let icon = 'info-circle';
    if (type === 'success') icon = 'check-circle';
    if (type === 'error') icon = 'exclamation-circle';
    if (type === 'warning') icon = 'exclamation-triangle';
    
    // 알림 요소 생성
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} fade-in`;
    
    // 내용 추가
    alert.innerHTML = `
      <div class="alert-icon">
        <i class="fas fa-${icon}"></i>
      </div>
      <div class="alert-content">
        <p class="alert-message">${message}</p>
      </div>
      ${settings.dismissible ? '<button type="button" class="alert-close"><i class="fas fa-times"></i></button>' : ''}
    `;
    
    // 컨테이너에 추가
    this.container.appendChild(alert);
    
    // 일정 시간 후 자동 제거
    if (settings.duration > 0) {
      alert.dataset.timeout = setTimeout(() => {
        this.hide(alert);
      }, settings.duration);
    }
    
    return alert;
  },
  
  /**
   * 알림을 숨깁니다.
   * @param {Element} alert - 알림 요소
   */
  hide: function(alert) {
    if (!alert) return;
    
    // 타임아웃 제거
    if (alert.dataset.timeout) {
      clearTimeout(parseInt(alert.dataset.timeout));
    }
    
    // 페이드 아웃 애니메이션
    alert.classList.remove('fade-in');
    alert.classList.add('fade-out');
    
    // 애니메이션 완료 후 요소 제거
    setTimeout(() => {
      if (alert.parentNode) {
        alert.parentNode.removeChild(alert);
      }
    }, 300);
  },
  
  /**
   * 모든 알림을 숨깁니다.
   */
  hideAll: function() {
    const alerts = this.container.querySelectorAll('.alert');
    alerts.forEach(alert => {
      this.hide(alert);
    });
  },
  
  /**
   * 성공 알림을 표시합니다.
   * @param {string} message - 알림 메시지
   * @param {Object} options - 추가 옵션
   * @returns {Element} - 생성된 알림 요소
   */
  success: function(message, options = {}) {
    return this.show(message, 'success', options);
  },
  
  /**
   * 오류 알림을 표시합니다.
   * @param {string} message - 알림 메시지
   * @param {Object} options - 추가 옵션
   * @returns {Element} - 생성된 알림 요소
   */
  error: function(message, options = {}) {
    return this.show(message, 'error', options);
  },
  
  /**
   * 경고 알림을 표시합니다.
   * @param {string} message - 알림 메시지
   * @param {Object} options - 추가 옵션
   * @returns {Element} - 생성된 알림 요소
   */
  warning: function(message, options = {}) {
    return this.show(message, 'warning', options);
  },
  
  /**
   * 정보 알림을 표시합니다.
   * @param {string} message - 알림 메시지
   * @param {Object} options - 추가 옵션
   * @returns {Element} - 생성된 알림 요소
   */
  info: function(message, options = {}) {
    return this.show(message, 'info', options);
  },
  
  /**
   * API 응답에 기반한 알림을 표시합니다.
   * @param {Object} response - API 응답 객체
   * @param {string} successMessage - 성공 시 메시지 (옵션)
   * @returns {Element|null} - 생성된 알림 요소 또는 null
   */
  fromResponse: function(response, successMessage = null) {
    if (!response) return null;
    
    if (response.success) {
      // 성공 응답
      return this.success(successMessage || response.message || '작업이 성공적으로 완료되었습니다.');
    } else {
      // 오류 응답
      return this.error(response.message || '작업 중 오류가 발생했습니다.');
    }
  }
};

// 페이지 로드 시 알림 모듈 초기화
document.addEventListener('DOMContentLoaded', function() {
  Alerts.init();
});
