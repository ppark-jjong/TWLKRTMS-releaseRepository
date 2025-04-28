console.log('[로드] auth.js 로드됨 - ' + new Date().toISOString());

/**
 * 인증 관리 모듈
 * 로그인, 로그아웃, 세션 관리 등의 기능을 제공합니다.
 */
window.Auth = {
  /**
   * 현재 로그인한 사용자 정보
   */
  currentUser: null,
  
  /**
   * 인증 모듈을 초기화합니다.
   */
  init: function() {
    console.log('[초기화] Auth.init 시작');
    this.setupLogoutHandler();
    this.setupSessionExpiry();
    this.checkLoginStatus();
    console.log('[초기화] Auth.init 완료');
  },
  
  /**
   * 로그아웃 핸들러를 설정합니다.
   */
  setupLogoutHandler: function() {
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
      logoutBtn.addEventListener('click', function(e) {
        e.preventDefault();
        Auth.logout();
      });
    }
  },
  
  /**
   * 세션 만료 감지를 설정합니다.
   */
  setupSessionExpiry: function() {
    // AJAX 요청 후 401 응답을 가로채서 세션 만료 처리
    document.addEventListener('UnauthorizedError', function(e) {
      Auth.handleSessionExpiry();
    });
  },
  
  /**
   * 현재 로그인 상태를 확인합니다.
   * @returns {Promise<boolean>} - 로그인 상태
   */
  checkLoginStatus: async function() {
    try {
      // 쿠키나 세션 존재 확인으로 대체
      // 백엔드에서 모든 페이지에 세션 검증을 수행하므로
      // 현재 페이지가 로드되었다면 이미 인증된 상태로 볼 수 있음
      const isLoggedIn = window.location.pathname !== '/auth/login';
      
      if (isLoggedIn) {
        // 현재 사용자 정보는 이미 백엔드에서 템플릿으로 전달됨
        const userRoleElement = document.body.getAttribute('data-user-role');
        if (userRoleElement) {
          this.currentUser = {
            user_role: userRoleElement
          };
        }
        return true;
      }
      
      return false;
    } catch (error) {
      console.error('로그인 상태 확인 오류:', error);
      return false;
    }
  },
  
  /**
   * 세션 만료 처리를 수행합니다.
   */
  handleSessionExpiry: function() {
    this.currentUser = null;
    this.redirectToLogin('session_expired');
  },
  
  /**
   * 로그인 페이지로 리다이렉션합니다.
   * @param {string} reason - 리다이렉션 이유
   */
  redirectToLogin: function(reason = 'auth_required') {
    window.location.href = `/auth/login?reason=${reason}`;
  },
  
  /**
   * 로그아웃을 수행합니다.
   */
  logout: function() {
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
        
        // 알림 표시
        if (window.Alerts) {
          Alerts.error('로그아웃 중 오류가 발생했습니다. 새로고침 후 다시 시도해주세요.');
        } else {
          alert('로그아웃 중 오류가 발생했습니다. 새로고침 후 다시 시도해주세요.');
        }
      });
    } catch (error) {
      console.error('로그아웃 함수 실행 중 오류:', error);
      
      // 알림 표시
      if (window.Alerts) {
        Alerts.error('로그아웃 처리 중 예상치 못한 오류가 발생했습니다.');
      } else {
        alert('로그아웃 처리 중 예상치 못한 오류가 발생했습니다.');
      }
    }
  },
  
  /**
   * 사용자 권한을 확인합니다.
   * @param {string} requiredRole - 필요한 권한
   * @returns {boolean} - 권한 보유 여부
   */
  hasRole: function(requiredRole) {
    if (!this.currentUser) return false;
    
    // 관리자는 모든 권한 보유
    if (this.currentUser.user_role === 'ADMIN') return true;
    
    // 필요한 권한이 현재 사용자 권한과 일치하는지 확인
    return this.currentUser.user_role === requiredRole;
  },
  
  /**
   * 현재 사용자 정보를 반환합니다.
   * @returns {Object|null} - 사용자 정보
   */
  getUser: function() {
    return this.currentUser;
  },
  
  /**
   * 사용자 정보를 설정합니다.
   * @param {Object} user - 사용자 정보
   */
  setUser: function(user) {
    this.currentUser = user;
  }
};

// 페이지 로드 시 인증 모듈 초기화 (로그인 페이지 제외)
document.addEventListener('DOMContentLoaded', function() {
  // 로그인 페이지에서는 초기화하지 않음
  if (window.location.pathname !== '/login' && window.location.pathname !== '/auth/login') {
    Auth.init();
  }
});
