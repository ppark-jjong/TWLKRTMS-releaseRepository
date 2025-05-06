/**
 * 로그인 페이지 스크립트
 * 세션 기반 인증을 처리하고 백엔드 API와 연동
 */
document.addEventListener('DOMContentLoaded', function() {
  // 폼 요소 찾기
  const loginForm = document.querySelector('form.login-form');
  
  // 폼 제출 이벤트 처리 - 클라이언트측 유효성 검증만 수행
  if (loginForm) {
    loginForm.addEventListener('submit', function(event) {
      // 폼 데이터 수집 및 유효성 검증
      const userId = document.getElementById('user_id').value;
      const userPassword = document.getElementById('user_password').value;
      
      // 필수 입력 확인 - 비어있으면 제출 중단
      if (!userId || !userPassword) {
        event.preventDefault(); // 폼 제출 중단
        showErrorMessage('아이디와 비밀번호를 모두 입력해주세요.');
        return;
      }
      
      // 로그인 진행 중 UI 표시
      const loginButton = loginForm.querySelector('.login-button');
      if (loginButton) {
        loginButton.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> 로그인 중...';
        loginButton.disabled = true;
      }
      
      // 유효성 검사에 통과하면 폼이 정상적으로 서버로 제출됨
      // 서버 측에서 PRG 패턴으로 처리하므로 여기서 추가 코드 필요 없음
    });
  }
  
  /**
   * 오류 메시지 표시
   * @param {string} message - 표시할 메시지
   */
  function showErrorMessage(message) {
    // 기존 알림이 있으면 제거
    const existingAlert = document.querySelector('.alert');
    if (existingAlert) {
      existingAlert.remove();
    }
    
    // 새 알림 생성
    const alert = document.createElement('div');
    alert.className = 'alert alert-error';
    alert.innerHTML = `<i class="fa-solid fa-exclamation-circle"></i><span>${message}</span>`;
    
    // 알림 삽입
    const loginHeader = document.querySelector('.login-header');
    loginHeader.insertAdjacentElement('afterend', alert);
  }
  
  /**
   * 성공 메시지 표시
   * @param {string} message - 표시할 메시지
   */
  function showSuccessMessage(message) {
    // 기존 알림이 있으면 제거
    const existingAlert = document.querySelector('.alert');
    if (existingAlert) {
      existingAlert.remove();
    }
    
    // 새 알림 생성
    const alert = document.createElement('div');
    alert.className = 'alert alert-success';
    alert.innerHTML = `<i class="fa-solid fa-check-circle"></i><span>${message}</span>`;
    
    // 알림 삽입
    const loginHeader = document.querySelector('.login-header');
    loginHeader.insertAdjacentElement('afterend', alert);
  }
  
  /**
   * 폼 비활성화/활성화
   * @param {boolean} disabled - 비활성화 여부
   */
  function disableForm(disabled) {
    // 폼 내 모든 입력 요소 찾기
    const inputs = loginForm.querySelectorAll('input, button');
    
    // 비활성화 상태 설정
    inputs.forEach(input => {
      input.disabled = disabled;
    });
    
    // 로그인 버튼 업데이트
    const loginButton = loginForm.querySelector('.login-button');
    if (loginButton) {
      if (disabled) {
        loginButton.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> 로그인 중...';
      } else {
        loginButton.innerHTML = '<i class="fa-solid fa-sign-in-alt"></i> 로그인';
      }
    }
  }
  
  // URL에서 오류 메시지 확인
  const urlParams = new URLSearchParams(window.location.search);
  const errorMsg = urlParams.get('error');
  if (errorMsg) {
    showErrorMessage(decodeURIComponent(errorMsg));
  }
  
  // 페이지 로드 시 아이디 필드에 포커스
  const userIdInput = document.getElementById('user_id');
  if (userIdInput) {
    userIdInput.focus();
  }
});
