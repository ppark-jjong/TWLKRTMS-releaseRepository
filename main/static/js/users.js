/**
 * 사용자 관리 페이지 스크립트
 * 간소화된 사용자 생성 및 삭제 기능
 */
document.addEventListener('DOMContentLoaded', function () {
  // 사용자 관리 모듈
  const UserManagement = {
    userIdToDelete: null, // 삭제 대상 ID 저장용

    /**
     * 초기화 함수
     */
    init() {
      // 관리자 권한 확인
      if (!Utils.auth.isAdmin()) {
        Utils.message.error('관리자만 접근할 수 있는 페이지입니다.');
        setTimeout(() => {
          window.location.href = '/dashboard';
        }, 1500);
        return;
      }

      // 이벤트 리스너 설정
      this.initEventListeners();
      this.checkUrlParamsForNotifications(); // 페이지 로드 시 알림 확인 추가
    },

    /**
     * URL 쿼리 파라미터를 확인하여 알림 표시
     */
    checkUrlParamsForNotifications() {
      const urlParams = new URLSearchParams(window.location.search);
      const successMessage = urlParams.get('success');
      const errorMessage = urlParams.get('error');

      if (successMessage) {
        // 성공 메시지가 있으면 표시 (Utils.alerts 사용)
        Utils.alerts.showSuccess(decodeURIComponent(successMessage));
        // URL에서 파라미터 제거 (선택적)
        window.history.replaceState(
          {},
          document.title,
          window.location.pathname
        );
      }
      if (errorMessage) {
        // 오류 메시지가 있으면 표시
        Utils.alerts.showError(decodeURIComponent(errorMessage));
        window.history.replaceState(
          {},
          document.title,
          window.location.pathname
        );
      }
    },

    /**
     * 이벤트 리스너 설정
     */
    initEventListeners() {
      // 새로고침 버튼
      const refreshBtn = document.getElementById('refreshBtn');
      if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
          window.location.reload();
        });
      }

      // 신규 사용자 추가 버튼
      const newUserBtn = document.getElementById('newUserBtn');
      if (newUserBtn) {
        newUserBtn.addEventListener('click', () => {
          this.openUserDialog();
        });
      }

      // 비밀번호 보기/감추기 토글 버튼
      const togglePasswordBtn = document.getElementById('togglePasswordBtn');
      if (togglePasswordBtn) {
        togglePasswordBtn.addEventListener('click', () => {
          this.togglePasswordVisibility();
        });
      }

      // 사용자 삭제 버튼들
      const deleteButtons = document.querySelectorAll('.delete-user');
      deleteButtons.forEach((button) => {
        button.addEventListener('click', (e) => {
          const userId = e.currentTarget.dataset.userid;
          if (userId) {
            this.confirmDeleteUser(userId);
          }
        });
      });

      // 다이얼로그 내부 버튼
      const cancelUserBtn = document.getElementById('cancelUserBtn');
      const saveUserBtn = document.getElementById('saveUserBtn');
      const cancelDeleteBtn = document.getElementById('cancelDeleteBtn');
      const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');

      if (cancelUserBtn) {
        cancelUserBtn.addEventListener('click', () => {
          this.closeUserDialog();
        });
      }

      if (saveUserBtn) {
        // 폼 제출 처리
        const userForm = document.getElementById('userForm');
        if (userForm) {
          userForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveUser();
          });
        }
      }

      if (cancelDeleteBtn) {
        cancelDeleteBtn.addEventListener('click', () => {
          this.closeDeleteConfirm();
        });
      }

      if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', () => {
          this.deleteUser();
        });
      }
    },

    /**
     * 신규 사용자 추가 다이얼로그 표시
     */
    openUserDialog() {
      const dialog = document.getElementById('userFormDialog');
      if (dialog) {
        // 폼 초기화
        const form = document.getElementById('userForm');
        if (form) {
          form.reset();
        }

        // 다이얼로그 제목 설정
        const dialogTitle = document.getElementById('dialogTitle');
        if (dialogTitle) {
          dialogTitle.textContent = '신규 사용자 추가';
        }

        // 다이얼로그 표시
        dialog.classList.add('active');
      }
    },

    /**
     * 사용자 다이얼로그 닫기
     */
    closeUserDialog() {
      const dialog = document.getElementById('userFormDialog');
      if (dialog) {
        dialog.classList.remove('active');
      }
    },

    /**
     * 비밀번호 보기/감추기 토글
     */
    togglePasswordVisibility() {
      const passwordInput = document.getElementById('userPassword');
      const toggleBtn = document.getElementById('togglePasswordBtn');

      if (!passwordInput || !toggleBtn) return;

      // 입력 필드 타입 전환
      if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        toggleBtn.innerHTML = '<i class="fa-solid fa-eye-slash"></i>';
      } else {
        passwordInput.type = 'password';
        toggleBtn.innerHTML = '<i class="fa-solid fa-eye"></i>';
      }
    },

    /**
     * 사용자 추가/수정 저장
     */
    async saveUser() {
      try {
        const form = document.getElementById('userForm');
        if (!form) return;

        const formData = new FormData(form);

        if (
          !formData.get('user_id') ||
          !formData.get('user_name') ||
          !formData.get('user_password')
        ) {
          Utils.alerts.showWarning(
            '필수 입력 항목(ID, 이름, 비밀번호)을 모두 입력해주세요.'
          );
          return;
        }

        Utils.ui.showLoading();

        const response = await fetch('/api/admin/users', {
          method: 'POST',
          body: formData,
        });

        if (!response.ok && !response.redirected) {
          const errorData = await response.json().catch(() => ({}));
          const errorMessage =
            errorData.detail || errorData.message || '사용자 저장 실패';
          Utils.alerts.showError(errorMessage);
        } else {
          // 성공 알림 추가
          Utils.alerts.showSuccess(
            `사용자 ${formData.get('user_id')}가 성공적으로 생성되었습니다.`
          );

          // 리다이렉트 처리 또는 페이지 새로고침
          if (response.redirected) {
            window.location.href = response.url;
          } else {
            setTimeout(() => {
              window.location.reload();
            }, 1500);
          }
        }
      } catch (error) {
        console.error('사용자 저장 오류:', error);
        Utils.alerts.showError(
          error.message || '사용자 저장 중 오류가 발생했습니다.'
        );
      } finally {
        Utils.ui.hideLoading();
        this.closeUserDialog();
      }
    },

    /**
     * 사용자 삭제 확인 다이얼로그 표시
     */
    confirmDeleteUser(userId) {
      // 삭제할 사용자 ID 저장
      this.userIdToDelete = userId;

      // 삭제 확인 다이얼로그 표시
      const dialog = document.getElementById('deleteConfirmDialog');
      if (dialog) {
        dialog.classList.add('active');
      } else {
        // 다이얼로그가 없으면 window.confirm 사용
        if (
          confirm(
            '정말로 이 사용자를 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.'
          )
        ) {
          this.deleteUser();
        }
      }
    },

    /**
     * 삭제 확인 다이얼로그 닫기
     */
    closeDeleteConfirm() {
      const dialog = document.getElementById('deleteConfirmDialog');
      if (dialog) {
        dialog.classList.remove('active');
      }
      this.userIdToDelete = null;
    },

    /**
     * 사용자 삭제 처리
     */
    async deleteUser() {
      if (!this.userIdToDelete) {
        this.closeDeleteConfirm();
        return;
      }

      try {
        Utils.ui.showLoading();

        const response = await fetch(
          `/api/admin/users/${this.userIdToDelete}/delete`,
          {
            method: 'POST',
          }
        );

        if (!response.ok && !response.redirected) {
          const errorData = await response.json().catch(() => ({}));
          Utils.alerts.showError(
            errorData.detail || '사용자 삭제 중 오류가 발생했습니다.'
          );
        } else {
          // 성공 알림 추가
          Utils.alerts.showSuccess(
            `사용자 ${this.userIdToDelete}가 성공적으로 삭제되었습니다.`
          );

          // 리다이렉트 처리 또는 페이지 새로고침
          if (response.redirected) {
            window.location.href = response.url;
          } else {
            setTimeout(() => {
              window.location.reload();
            }, 1500);
          }
        }
      } catch (error) {
        console.error('사용자 삭제 오류:', error);
        Utils.alerts.showError('사용자 삭제 중 오류가 발생했습니다.');
      } finally {
        Utils.ui.hideLoading();
        this.closeDeleteConfirm();
      }
    },
  };

  // 사용자 관리 모듈 초기화
  UserManagement.init();

  // 글로벌 스코프 노출 제거 (필요 시 유지)
  // window.UserManagement = UserManagement;
});
