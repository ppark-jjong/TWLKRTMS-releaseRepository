/**
 * 전역 공통 모듈
 * 애플리케이션 전체에서 사용되는 공통 기능
 */
window.App = (function() {
  /**
   * 초기화 함수
   */
  function init() {
    setupGlobalEventHandlers();
    setupMobileDetection();
    checkAuthentication();
  }
  
  /**
   * 전역 이벤트 핸들러를 설정합니다.
   */
  function setupGlobalEventHandlers() {
    // 세션 만료 처리
    document.addEventListener('click', function(event) {
      const logoutBtn = event.target.closest('#logoutBtn');
      if (logoutBtn) {
        event.preventDefault();
        logout();
      }
    });
    
    // AJAX 요청 오류 공통 처리
    window.addEventListener('error', function(event) {
      console.error('전역 오류 발생:', event.error);
    });
    
    // 네트워크 상태 모니터링
    window.addEventListener('online', function() {
      if (window.Alerts) {
        Alerts.info('네트워크 연결이 복구되었습니다.');
      }
    });
    
    window.addEventListener('offline', function() {
      if (window.Alerts) {
        Alerts.warning('네트워크 연결이 끊겼습니다. 일부 기능이 제한될 수 있습니다.');
      }
    });
  }
  
  /**
   * 모바일 기기 감지를 설정합니다.
   */
  function setupMobileDetection() {
    const isMobile = window.innerWidth < 768;
    document.body.classList.toggle('is-mobile', isMobile);
    
    window.addEventListener('resize', function() {
      const isMobile = window.innerWidth < 768;
      document.body.classList.toggle('is-mobile', isMobile);
    });
  }
  
  /**
   * 인증 상태를 확인합니다.
   */
  function checkAuthentication() {
    // 로그인 페이지에서는 확인 불필요
    if (window.location.pathname === '/auth/login') {
      return;
    }
    
    // Auth 모듈이 있는 경우만 실행
    if (window.Auth) {
      Auth.checkLoginStatus().catch(error => {
        console.error('인증 확인 오류:', error);
      });
    }
  }
  
  /**
   * 로그아웃 처리를 수행합니다.
   */
  function logout() {
    // Auth 모듈이 있으면 해당 모듈의 로그아웃 함수 사용
    if (window.Auth) {
      Auth.logout();
      return;
    }
    
    // Auth 모듈이 없는 경우 직접 구현
    try {
      fetch('/auth/logout', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest',
          'Accept': 'application/json'
        },
        credentials: 'include'
      })
      .then(response => {
        if (response.ok || response.redirected) {
          // 성공 케이스
          return response.json().catch(() => {
            // JSON 파싱 실패 시 리다이렉트로 처리
            window.location.href = '/auth/login?reason=logout_success';
            return { success: true };
          });
        } else {
          console.error('로그아웃 실패');
          throw new Error('로그아웃 중 오류가 발생했습니다.');
        }
      })
      .then(data => {
        // 응답이 JSON이고 성공적이면 리다이렉트
        if (data.success) {
          window.location.href = '/auth/login?reason=logout_success';
        } else {
          throw new Error(data.message || '로그아웃 처리 중 오류가 발생했습니다.');
        }
      })
      .catch(error => {
        console.error('로그아웃 처리 중 오류:', error);
        
        // 알림 표시 (Alerts 모듈 있으면 사용)
        if (window.Alerts) {
          Alerts.error('로그아웃 중 오류가 발생했습니다. 새로고침 후 다시 시도해주세요.');
        } else {
          alert('로그아웃 중 오류가 발생했습니다. 새로고침 후 다시 시도해주세요.');
        }
      });
    } catch (error) {
      console.error('로그아웃 함수 실행 중 오류:', error);
      
      // 알림 표시 (Alerts 모듈 있으면 사용)
      if (window.Alerts) {
        Alerts.error('로그아웃 처리 중 예상치 못한 오류가 발생했습니다.');
      } else {
        alert('로그아웃 처리 중 예상치 못한 오류가 발생했습니다.');
      }
    }
  }
  
  /**
   * 알림 메시지를 표시합니다.
   * @param {string} message - 표시할 메시지
   * @param {string} type - 알림 유형 (success, error, warning, info)
   * @param {number} duration - 표시 시간 (밀리초)
   */
  function showAlert(message, type = 'info', duration = 5000) {
    if (window.Alerts) {
      Alerts.show(message, type, { duration });
    } else {
      // 기본 알림 함수 사용
      const alertContainer = document.getElementById('alertContainer');
      
      if (!alertContainer) {
        console.error('알림 컨테이너를 찾을 수 없습니다.');
        alert(message);
        return;
      }
      
      // 중복 알림 확인 (동일 메시지, 동일 타입)
      const existingAlerts = alertContainer.querySelectorAll(`.alert-${type}`);
      for (const existingAlert of existingAlerts) {
        if (existingAlert.querySelector('.alert-message').textContent === message) {
          return; // 중복 알림 방지
        }
      }
      
      // 알림 요소 생성
      const alert = document.createElement('div');
      alert.className = `alert alert-${type} fade-in`;
      
      // 아이콘 선택
      let icon = 'info-circle';
      if (type === 'success') icon = 'check-circle';
      if (type === 'error') icon = 'exclamation-circle';
      if (type === 'warning') icon = 'exclamation-triangle';
      
      // 내용 추가
      alert.innerHTML = `
        <div class="alert-icon">
          <i class="fas fa-${icon}"></i>
        </div>
        <div class="alert-content">
          <p class="alert-message">${message}</p>
        </div>
        <button type="button" class="alert-close">
          <i class="fas fa-times"></i>
        </button>
      `;
      
      // 닫기 버튼 이벤트
      const closeBtn = alert.querySelector('.alert-close');
      if (closeBtn) {
        closeBtn.addEventListener('click', function() {
          alert.style.opacity = '0';
          setTimeout(() => {
            if (alert.parentNode) {
              alert.parentNode.removeChild(alert);
            }
          }, 300);
        });
      }
      
      // 컨테이너에 추가
      alertContainer.appendChild(alert);
      
      // 일정 시간 후 자동 제거 (error 타입은 자동 제거 안함)
      if (type !== 'error' && duration > 0) {
        setTimeout(() => {
          alert.style.opacity = '0';
          setTimeout(() => {
            if (alert.parentNode) {
              alert.parentNode.removeChild(alert);
            }
          }, 300);
        }, duration);
      }
    }
  }
  
  /**
   * 로딩 인디케이터를 표시하거나 숨깁니다.
   * @param {boolean} show - 표시 여부
   */
  function toggleLoading(show) {
    if (window.Utils) {
      Utils.toggleLoading(show);
    } else {
      // 기본 로딩 함수 사용
      const loadingOverlay = document.querySelector('.loading-overlay');
      
      if (loadingOverlay) {
        loadingOverlay.style.display = show ? 'flex' : 'none';
      }
    }
  }
  
  /**
   * 날짜를 지정된 형식으로 포맷팅합니다.
   * @param {Date|string} date - 포맷팅할 날짜 (Date 객체 또는 문자열)
   * @param {string} format - 날짜 형식 (YYYY-MM-DD, YY-MM-DD HH:mm 등)
   * @returns {string} - 포맷팅된 날짜 문자열
   */
  function formatDate(date, format = 'YYYY-MM-DD') {
    if (window.Utils) {
      return Utils.formatDate(date, format);
    } else {
      try {
        if (!date) return '-';
        
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
        const seconds = String(dateObj.getSeconds()).padStart(2, '0');
        
        // 포맷에 따라 날짜 문자열 생성
        let formattedDate = format;
        formattedDate = formattedDate.replace('YYYY', year);
        formattedDate = formattedDate.replace('YY', String(year).slice(-2));
        formattedDate = formattedDate.replace('MM', month);
        formattedDate = formattedDate.replace('DD', day);
        formattedDate = formattedDate.replace('HH', hours);
        formattedDate = formattedDate.replace('mm', minutes);
        formattedDate = formattedDate.replace('ss', seconds);
        
        return formattedDate;
      } catch (error) {
        console.error('날짜 포맷팅 중 오류 발생:', error);
        return date; // 오류 시 원본 반환
      }
    }
  }
  
  /**
   * 우편번호 형식을 처리합니다 (4자리 → 5자리).
   * @param {string} postalCode - 우편번호
   * @returns {string} - 처리된 우편번호
   */
  function formatPostalCode(postalCode) {
    if (window.Utils) {
      return Utils.formatPostalCode(postalCode);
    } else {
      try {
        if (!postalCode) return '';
        
        // 숫자만 추출
        const digits = postalCode.toString().replace(/\D/g, '');
        
        // 4자리인 경우 앞에 0 추가
        if (digits.length === 4) {
          return '0' + digits;
        }
        
        return digits;
      } catch (error) {
        console.error('우편번호 포맷팅 중 오류 발생:', error);
        return postalCode; // 오류 시 원본 반환
      }
    }
  }
  
  // 페이지 로드 시 초기화
  document.addEventListener('DOMContentLoaded', init);
  
  // 공개 API
  return {
    init,
    logout,
    showAlert,
    toggleLoading,
    formatDate,
    formatPostalCode
  };
})();
