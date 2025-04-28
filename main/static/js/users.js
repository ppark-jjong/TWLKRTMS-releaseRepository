/**
 * 사용자 관리 페이지 모듈
 * 사용자 목록 조회, 생성, 삭제 기능을 제공합니다.
 */
window.UserManagement = (function() {
  /**
   * 사용자 관리 페이지를 초기화합니다.
   */
  function init() {
    // 인증 확인
    if (window.Auth) {
      Auth.checkLoginStatus().then(isLoggedIn => {
        if (isLoggedIn) {
          // 관리자 권한 확인
          if (!Auth.hasRole('ADMIN')) {
            // 관리자가 아니면 대시보드로 리다이렉트
            window.location.href = '/dashboard';
            return;
          }
        }
      }).catch(error => {
        console.error('인증 확인 오류:', error);
      });
    }
    
    // 이벤트 리스너 설정
    setupEventListeners();
    
    console.log('사용자 관리 페이지 초기화 완료');
  }
  
  /**
   * 이벤트 리스너를 설정합니다.
   */
  function setupEventListeners() {
    // 사용자 생성 버튼
    const createUserBtn = document.getElementById('createUserBtn');
    if (createUserBtn) {
      createUserBtn.addEventListener('click', () => {
        openCreateUserModal();
      });
    }
    
    // 사용자 생성 모달 폼 제출
    const submitUserBtn = document.getElementById('submitUserBtn');
    if (submitUserBtn) {
      submitUserBtn.addEventListener('click', () => {
        submitUserForm();
      });
    }
    
    // 모달 닫기 버튼들
    document.querySelectorAll('.modal-close, .cancel-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        closeModal();
      });
    });
    
    // 삭제 버튼 이벤트 위임
    const userTable = document.getElementById('userTable');
    if (userTable) {
      userTable.addEventListener('click', (event) => {
        const deleteBtn = event.target.closest('.delete-user-btn');
        if (deleteBtn) {
          const userId = deleteBtn.dataset.userId;
          if (userId) {
            confirmDeleteUser(userId);
          }
        }
      });
    }
    
    // 삭제 확인 버튼
    const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
    if (confirmDeleteBtn) {
      confirmDeleteBtn.addEventListener('click', () => {
        const userId = document.getElementById('deleteUserId').value;
        if (userId) {
          deleteUser(userId);
        }
      });
    }
    
    // ESC 키로 모달 닫기
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        closeModal();
      }
    });
    
    // 모달 외부 클릭 시 닫기
    document.querySelectorAll('.modal').forEach(modal => {
      modal.addEventListener('click', (e) => {
        if (e.target === modal) {
          closeModal();
        }
      });
    });
  }
  
  /**
   * 사용자 생성 모달을 엽니다.
   */
  function openCreateUserModal() {
    // 폼 초기화
    const form = document.getElementById('createUserForm');
    if (form) {
      form.reset();
    }
    
    // 모달 표시
    const modal = document.getElementById('createUserModal');
    if (modal) {
      modal.style.display = 'block';
    }
  }
  
  /**
   * 사용자 삭제 확인 모달을 엽니다.
   * @param {string} userId - 사용자 ID
   */
  function confirmDeleteUser(userId) {
    const modal = document.getElementById('deleteUserModal');
    const deleteUserIdField = document.getElementById('deleteUserId');
    const userIdSpan = document.getElementById('deleteUserIdDisplay');
    
    if (modal && deleteUserIdField && userIdSpan) {
      deleteUserIdField.value = userId;
      userIdSpan.textContent = userId;
      modal.style.display = 'block';
    }
  }
  
  /**
   * 모달을 닫습니다.
   */
  function closeModal() {
    document.querySelectorAll('.modal').forEach(modal => {
      modal.style.display = 'none';
    });
  }
  
  /**
   * 사용자 생성 폼을 제출합니다.
   */
  async function submitUserForm() {
    const form = document.getElementById('createUserForm');
    if (!form) return;
    
    // 유효성 검사
    if (!form.checkValidity()) {
      form.reportValidity();
      return;
    }
    
    // 비밀번호 확인
    const password = form.querySelector('#userPassword').value;
    const confirmPassword = form.querySelector('#userPasswordConfirm').value;
    
    if (password !== confirmPassword) {
      showAlert('비밀번호가 일치하지 않습니다.', 'error');
      return;
    }
    
    try {
      // 로딩 표시
      if (window.Utils) {
        Utils.toggleLoading(true);
      }
      
      // 폼 데이터 수집
      const formData = new FormData(form);
      const data = {};
      
      for (const [key, value] of formData.entries()) {
        data[key] = value;
      }
      
      // API 호출
      const response = await fetch('/users/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify(data),
        credentials: 'include'
      });
      
      const responseData = await response.json();
      
      if (responseData.success) {
        // 모달 닫기
        closeModal();
        
        // 성공 메시지 표시
        showAlert('사용자가 성공적으로 생성되었습니다.', 'success');
        
        // 페이지 새로고침 (데이터 갱신)
        setTimeout(() => {
          window.location.reload();
        }, 1000);
      } else {
        showAlert(responseData.message || '사용자 생성에 실패했습니다.', 'error');
      }
    } catch (error) {
      console.error('사용자 생성 중 오류:', error);
      showAlert('사용자 생성 중 오류가 발생했습니다.', 'error');
    } finally {
      // 로딩 숨김
      if (window.Utils) {
        Utils.toggleLoading(false);
      }
    }
  }
  
  /**
   * 사용자를 삭제합니다.
   * @param {string} userId - 사용자 ID
   */
  async function deleteUser(userId) {
    try {
      // 로딩 표시
      if (window.Utils) {
        Utils.toggleLoading(true);
      }
      
      // API 호출
      const response = await fetch('/users/delete', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({ user_id: userId }),
        credentials: 'include'
      });
      
      const data = await response.json();
      
      if (data.success) {
        // 모달 닫기
        closeModal();
        
        // 성공 메시지 표시
        showAlert('사용자가 성공적으로 삭제되었습니다.', 'success');
        
        // 페이지 새로고침 (데이터 갱신)
        setTimeout(() => {
          window.location.reload();
        }, 1000);
      } else {
        showAlert(data.message || '사용자 삭제에 실패했습니다.', 'error');
      }
    } catch (error) {
      console.error('사용자 삭제 중 오류:', error);
      showAlert('사용자 삭제 중 오류가 발생했습니다.', 'error');
    } finally {
      // 로딩 숨김
      if (window.Utils) {
        Utils.toggleLoading(false);
      }
    }
  }
  
  /**
   * 알림 메시지를 표시합니다.
   * @param {string} message - 표시할 메시지
   * @param {string} type - 알림 유형 (success, error, warning, info)
   */
  function showAlert(message, type = 'info') {
    if (window.Alerts) {
      Alerts.show(message, type);
    } else if (window.Utils && Utils.showAlert) {
      Utils.showAlert(message, type);
    } else {
      alert(message);
    }
  }
  
  // 페이지 로드 시 초기화
  document.addEventListener('DOMContentLoaded', init);
  
  // 전역 함수 노출
  window.openCreateUserModal = openCreateUserModal;
  window.confirmDeleteUser = confirmDeleteUser;
  window.closeModal = closeModal;
  
  // 공개 API
  return {
    init,
    openCreateUserModal,
    confirmDeleteUser,
    deleteUser
  };
})();
