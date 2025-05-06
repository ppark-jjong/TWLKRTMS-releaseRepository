/**
 * 주문 수정 페이지 스크립트
 * 락 관리 및 주문 수정 기능 처리
 */
document.addEventListener('DOMContentLoaded', function() {
  // 주문 수정 관리 모듈
  const OrderEdit = {
    // 주문 ID
    orderId: null,
    
    // 락 새로고침 타이머
    lockRefreshTimer: null,
    
    // 락 새로고침 간격 (2분 = 120초)
    LOCK_REFRESH_INTERVAL: 120 * 1000,
    
    /**
     * 초기화 함수
     */
    init() {
      // URL에서 주문 ID 추출
      this.setOrderIdFromUrl();
      
      // 이벤트 리스너 설정
      this.initEventListeners();
      
      // 락 새로고침 시작
      if (this.orderId) {
        this.startLockRefresh();
      }
    },
    
    /**
     * URL에서 주문 ID 추출
     */
    setOrderIdFromUrl() {
      const path = window.location.pathname;
      const matches = path.match(/\/orders\/(\d+)\/edit/);
      
      if (matches && matches[1]) {
        this.orderId = matches[1];
      }
    },
    
    /**
     * 이벤트 리스너 설정
     */
    initEventListeners() {
      // 우편번호 자동 보완
      const postalCodeInput = document.getElementById('postal_code');
      if (postalCodeInput) {
        postalCodeInput.addEventListener('blur', function() {
          // 4자리 우편번호 입력 시 5자리로 자동 보완
          const value = this.value.trim();
          if (value.length === 4 && /^\d{4}$/.test(value)) {
            this.value = '0' + value;
          }
        });
      }
      
      // 폼 제출 이벤트
      const orderForm = document.getElementById('editOrderForm');
      if (orderForm) {
        orderForm.addEventListener('submit', async (e) => {
          e.preventDefault();
          await this.saveOrder(orderForm);
        });
      }
      
      // 페이지 이탈 시 경고
      window.addEventListener('beforeunload', (e) => {
        const form = document.getElementById('editOrderForm');
        
        // 폼이 수정되었으면 경고 표시
        if (form && this.isFormDirty(form)) {
          const message = '저장되지 않은 변경사항이 있습니다. 페이지를 떠나시겠습니까?';
          e.returnValue = message;
          return message;
        }
      });
    },
    
    /**
     * 폼 수정 여부 확인
     */
    isFormDirty(form) {
      // 수정 여부 확인 로직 (간단한 구현)
      return false; // 실제 구현에서는 수정 확인 로직 추가
    },
    
    /**
     * 락 새로고침 시작
     */
    startLockRefresh() {
      // 기존 타이머 정리
      if (this.lockRefreshTimer) {
        clearInterval(this.lockRefreshTimer);
      }
      
      // 즉시 한 번 락 상태 확인
      this.refreshLock();
      
      // 주기적 락 새로고침 설정
      this.lockRefreshTimer = setInterval(() => {
        this.refreshLock();
      }, this.LOCK_REFRESH_INTERVAL);
    },
    
    /**
     * 락 새로고침 중지
     */
    stopLockRefresh() {
      if (this.lockRefreshTimer) {
        clearInterval(this.lockRefreshTimer);
        this.lockRefreshTimer = null;
      }
    },
    
    /**
     * 락 새로고침 수행
     */
    async refreshLock() {
      try {
        // 락 상태 확인 API 호출
        const lockStatus = await Utils.http.get(`/lock/${this.orderId}`);
        
        // 락 상태에 따른 처리
        if (!lockStatus.editable) {
          // 편집 불가능 상태 (다른 사용자가 수정 중)
          this.handleLockConflict(lockStatus.owner);
        }
      } catch (error) {
        // 오류 처리 (콘솔 로그 제거)
        // 오류 발생 시 타이머 중지하지 않고 계속 진행
      }
    },
    
    /**
     * 락 충돌 처리
     */
    handleLockConflict(owner) {
      // 경고 메시지 표시
      Utils.message.warning(`이 주문은 현재 ${owner}님이 수정 중입니다. 저장 버튼이 비활성화됩니다.`);
      
      // 폼 필드 비활성화
      this.disableFormFields();
      
      // 라우터를 통해 페이지 이동 (필요하면 활성화)
      /*
      setTimeout(() => {
        window.location.href = `/orders/${this.orderId}?lock_error=true`;
      }, 3000);
      */
    },
    
    /**
     * 폼 필드 비활성화
     */
    disableFormFields() {
      const form = document.getElementById('editOrderForm');
      if (!form) return;
      
      // 모든 입력 필드, 선택 필드, 버튼 비활성화
      const formElements = form.querySelectorAll('input, select, textarea, button[type="submit"]');
      formElements.forEach(element => {
        element.disabled = true;
      });
      
      // 저장 버튼에 메시지 표시
      const submitBtn = form.querySelector('button[type="submit"]');
      if (submitBtn) {
        submitBtn.innerHTML = '<i class="fa-solid fa-lock"></i> 저장 불가 (락 충돌)';
      }
    },
    
    /**
     * 우편번호 검증 및 포맷 처리
     */
    validatePostalCode(postalCode) {
      // 빈 값이면 그대로 반환
      if (!postalCode) return postalCode;
      
      // 4자리 우편번호를 5자리로 자동 변환
      if (postalCode.length === 4 && /^\d{4}$/.test(postalCode)) {
        return '0' + postalCode;
      }
      
      return postalCode;
    },
    
    /**
     * 주문 저장
     */
    async saveOrder(form) {
      try {
        // 폼 데이터 수집
        const formData = new FormData(form);
        const jsonData = {};
        
        for (const [key, value] of formData.entries()) {
          // _method와 dashboard_id는 제외
          if (key !== '_method' && key !== 'dashboard_id') {
            // 특수 필드 처리
            if (key === 'postal_code') {
              jsonData[key] = this.validatePostalCode(value);
            } else {
              jsonData[key] = value;
            }
          }
        }
        
        // 로딩 상태 표시
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
          submitBtn.disabled = true;
          submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> 저장 중...';
        }
        
        // 락 상태 한번 더 확인 (충돌 방지)
        try {
          const lockStatus = await Utils.http.get(`/lock/${this.orderId}`);
          if (lockStatus.locked && !lockStatus.editable) {
            throw new Error(`현재 다른 사용자(${lockStatus.owner})가 수정 중입니다. 나중에 다시 시도해주세요.`);
          }
        } catch (lockError) {
          // 락 확인 실패 시 원본 예외 그대로 throw
          if (lockError.message.includes('다른 사용자')) {
            throw lockError;
          }
          // 그 외 오류는 무시하고 계속 진행
        }
        
        // API 요청
        const response = await Utils.http.put(`/orders/${this.orderId}`, jsonData);
        
        // 성공 처리
        if (response && response.success) {
          Utils.message.success(response.message || '주문이 성공적으로 수정되었습니다.');
          
          // 락 새로고침 중지
          this.stopLockRefresh();
          
          // 상세 페이지로 이동
          setTimeout(() => {
            window.location.href = `/orders/${this.orderId}?success=1`;
          }, 1500);
        } else {
          throw new Error(response.message || '주문 수정 실패');
        }
      } catch (error) {
        Utils.message.error(error.message || '주문을 저장하는 중 오류가 발생했습니다.');
        
        // 버튼 상태 복원
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.innerHTML = '<i class="fa-solid fa-check"></i> 저장';
        }
      }
    }
  };
  
  // 주문 수정 모듈 초기화
  OrderEdit.init();
  
  // 글로벌 스코프에 노출
  window.OrderEdit = OrderEdit;
});
