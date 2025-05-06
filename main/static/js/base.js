/**
 * 기본 레이아웃 스크립트
 * 모든 페이지에서 공통으로 사용되는 기능을 구현합니다.
 */
document.addEventListener("DOMContentLoaded", function () {
  // 기본 모듈
  const BaseApp = {
    // 세션 체크 타이머
    sessionCheckTimer: null,

    // 세션 체크 간격 (5분)
    SESSION_CHECK_INTERVAL: 5 * 60 * 1000,

    /**
     * 초기화 함수
     */
    init() {
      // 사용자 정보 초기화
      this.initUserInfo();

      // 로그아웃 이벤트 핸들러 추가
      this.initLogoutButton();

      // 세션 만료 대화상자 버튼 이벤트
      this.initSessionExpiredDialog();

      // 세션 체크 타이머 시작
      this.startSessionCheck();

      // 권한 필요한 페이지 체크
      this.checkPagePermission();

      // URL 파라미터에서 알림 메시지 확인 (모든 페이지 공통)
      this.checkUrlParamsForNotifications();


    },

    /**
     * URL 파라미터에서 알림 메시지 확인
     * 모든 페이지에서 한 번만 실행하여 중복 알림 방지
     */
    checkUrlParamsForNotifications() {
      if (Utils && Utils.ui) {
        // Utils.ui.showPageMessages 함수가 이미 중복 방지 로직을 포함하고 있음
        Utils.ui.showPageMessages();

      }
    },

    /**
     * 사용자 정보 초기화
     */
    initUserInfo() {
      // 전역 사용자 객체 - base 템플릿에서 data-user-* 속성으로 전달받음
      const userInfoContainer = document.getElementById("userInfo");

      if (userInfoContainer && Utils && Utils.auth) {
        const userData = {
          user_id: userInfoContainer.dataset.userId || "",
          user_role: userInfoContainer.dataset.userRole || "",
          department: userInfoContainer.dataset.department || "",
        };

        // 유효한 사용자 정보가 있는 경우에만 설정
        if (userData.user_id) {
          Utils.auth.setCurrentUser(userData);


          // UI 요소 업데이트
          const userIdDisplay = document.getElementById("userDisplayId");
          const userRoleDisplay = document.getElementById("userDisplayRole");

          if (userIdDisplay) {
            userIdDisplay.innerHTML = `<strong>ID:</strong> ${userData.user_id}`;
          }

          if (userRoleDisplay) {
            let roleText = `<strong>권한:</strong> ${userData.user_role}`;
            if (userData.department) {
              roleText += ` / ${userData.department}`;
            }
            userRoleDisplay.innerHTML = roleText;
          }
        }
      }
    },

    /**
     * 로그아웃 버튼 이벤트 핸들러
     */
    initLogoutButton() {
      const logoutBtn = document.getElementById("logoutBtn");

      if (logoutBtn) {
        logoutBtn.addEventListener("click", function () {
          if (confirm("로그아웃 하시겠습니까?")) {
            if (Utils && Utils.auth) {
              Utils.auth.logout();
            } else {
              window.location.href = "/logout";
            }
          }
        });


      }
    },

    /**
     * 세션 만료 대화상자 설정
     */
    initSessionExpiredDialog() {
      const sessionLoginBtn = document.getElementById("sessionLoginBtn");
      const sessionExpiredDialog = document.getElementById(
        "sessionExpiredDialog"
      );

      if (sessionLoginBtn) {
        sessionLoginBtn.addEventListener("click", function () {
          window.location.href =
            "/login?return_to=" + encodeURIComponent(window.location.pathname);
        });


      }
    },

    /**
     * 세션 체크 타이머 시작
     */
    startSessionCheck() {
      // 로그인 페이지에서는 세션 체크 하지 않음
      if (window.location.pathname === "/login") {
        return;
      }

      // 기존 타이머 정리
      if (this.sessionCheckTimer) {
        clearInterval(this.sessionCheckTimer);
      }

      // 새로운 타이머 설정
      this.sessionCheckTimer = setInterval(() => {
        this.checkSession();
      }, this.SESSION_CHECK_INTERVAL);

      // 최초 1회 세션 체크
      this.checkSession();


    },

    /**
     * 세션 유효성 체크
     */
    async checkSession() {
      try {


        // 세션 체크 API 호출
        const response = await fetch("/api/check-session");

        if (response.status === 401) {

          this.handleSessionExpired();
          return;
        }

        // 응답이 성공적이지 않은 경우 무시
        if (!response.ok) {

          return;
        }

        // 응답 처리
        const result = await response.json();

        // 인증 상태 확인
        if (!result.authenticated) {

          this.handleSessionExpired();
        }
      } catch (error) {
        // 오류 무시 (네트워크 오류는 세션 만료로 간주하지 않음)

      }
    },

    /**
     * 세션 만료 처리
     */
    handleSessionExpired() {
      // 세션 체크 중지
      if (this.sessionCheckTimer) {
        clearInterval(this.sessionCheckTimer);
        this.sessionCheckTimer = null;
      }

      // 세션 만료 대화상자 표시
      const dialog = document.getElementById("sessionExpiredDialog");
      if (dialog) {
        dialog.classList.add("active");
      } else {
        // 대화상자가 없으면 즉시 리다이렉트
        alert("세션이 만료되었습니다. 다시 로그인해주세요.");
        window.location.href =
          "/login?return_to=" + encodeURIComponent(window.location.pathname);
      }
    },

    /**
     * 현재 페이지의 접근 권한 체크
     */
    checkPagePermission() {
      // 사용자 관리 페이지는 관리자만 접근 가능
      if (
        window.location.pathname.startsWith("/users") &&
        Utils &&
        Utils.auth
      ) {
        const currentUser = Utils.auth.getCurrentUser();
        if (!currentUser || currentUser.user_role !== "ADMIN") {
          console.warn(
            "권한 없음: 사용자 관리 페이지는 관리자만 접근 가능합니다."
          );

          // 알림 메시지 표시
          if (Utils.alerts) {
            Utils.alerts.showError(
              "권한이 없습니다. 관리자만 접근 가능한 페이지입니다."
            );
          }

          // 3초 후 대시보드로 리다이렉트
          setTimeout(() => {
            window.location.href = "/dashboard";
          }, 3000);
        }
      }
    },
  };

  // 기본 앱 초기화
  BaseApp.init();

  // 전역 접근을 위해 window에 할당
  window.BaseApp = BaseApp;
});
