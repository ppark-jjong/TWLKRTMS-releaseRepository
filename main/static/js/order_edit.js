/**
 * 주문 수정 페이지 스크립트
 * 주문 수정 기능 처리
 */
document.addEventListener('DOMContentLoaded', function () {
  // 주문 수정 관리 모듈
  const OrderEdit = {
    // 주문 ID
    orderId: null,

    /**
     * 초기화 함수
     */
    init() {
      // URL에서 주문 ID 추출
      this.setOrderIdFromUrl();

      // 이벤트 리스너 설정
      this.initEventListeners();

      // 폼 유효성 검사 설정
      this.initFormValidation();

      // 수정 모드인 경우, 데이터 로드
      if (this.orderId) {
        this.loadOrderData();
      }
    },

    /**
     * URL에서 주문 ID 추출 및 설정
     */
    setOrderIdFromUrl() {
      const pathParts = window.location.pathname.split('/');
      // URL이 /orders/{id}/edit 형태라고 가정
      if (pathParts.length >= 3 && pathParts[pathParts.length - 2] !== 'new') {
        this.orderId = pathParts[pathParts.length - 2];
      }
    },

    /**
     * 이벤트 리스너 설정
     */
    initEventListeners() {
      // const form = document.getElementById('editOrderForm'); // 폼 참조 제거
      // if (form) { ... } // 폼 submit 리스너 관련 코드 전체 제거

      // 기타 필요한 이벤트 리스너 (예: 우편번호 검색 버튼)
      const searchPostalCodeBtn = document.getElementById(
        'searchPostalCodeBtn'
      );
      if (searchPostalCodeBtn) {
        searchPostalCodeBtn.addEventListener('click', () => {
          OrderForm.searchPostalCode(); // OrderForm 유틸리티 사용 (OrderForm 객체가 정의되어 있어야 함)
        });
      }
    },

    /**
     * 폼 유효성 검사 초기화 (간단한 예시)
     */
    initFormValidation() {
      // 필요한 경우, 각 필드에 대한 유효성 검사 로직 추가
    },

    /**
     * 폼 유효성 검사 (간단한 예시)
     */
    validateForm(form) {
      // 필수 필드들이 채워져 있는지 확인
      let isValid = true;
      const requiredFields = form.querySelectorAll('[required]');
      requiredFields.forEach((field) => {
        if (!field.value.trim()) {
          isValid = false;
          // 간단한 시각적 피드백 (실제 프로젝트에서는 더 나은 UI 필요)
          field.style.border = '1px solid red';
          Utils.message.error(
            `${
              field.previousElementSibling?.textContent || field.name
            }은(는) 필수 항목입니다.`
          );
        } else {
          field.style.border = '';
        }
      });
      return isValid;
    },

    /**
     * 우편번호 유효성 검사
     */
    validatePostalCode(postalCode) {
      if (!/^[0-9]{5}$/.test(postalCode)) {
        throw new Error('우편번호는 5자리 숫자여야 합니다.');
      }
      return postalCode;
    },

    /**
     * 주문 데이터 로드 (수정 모드 시)
     */
    async loadOrderData() {
      if (!this.orderId) return;
      try {
        Utils.http.showLoading();
        const data = await Utils.http.get(`/api/orders/${this.orderId}/data`); // API 엔드포인트 확인 필요

        // 폼 필드 채우기
        this.fillFormData(data.order);
      } catch (error) {
        Utils.message.error(
          error.message || '주문 데이터를 불러오는 중 오류가 발생했습니다.'
        );
        setTimeout(() => {
          window.location.href = '/dashboard';
        }, 2000);
      } finally {
        Utils.http.hideLoading();
      }
    },

    /**
     * 폼 데이터 채우기
     */
    fillFormData(orderData) {
      const form = document.getElementById('editOrderForm');
      if (!form || !orderData) return;

      for (const key in orderData) {
        if (Object.prototype.hasOwnProperty.call(orderData, key)) {
          const field = form.elements[key];
          if (field) {
            if (field.type === 'datetime-local' && orderData[key]) {
              // UTC 문자열을 KST로 변환하여 YYYY-MM-DDTHH:MM 형식으로 설정
              field.value = Utils.date.formatToLocalDateTime(orderData[key]);
            } else if (field.tagName === 'SELECT') {
              field.value = orderData[key];
            } else {
              field.value = orderData[key] === null ? '' : orderData[key];
            }
          }
        }
      }
      // version 필드도 설정 (hidden input)
      const versionField = form.elements['version'];
      if (versionField && orderData.version) {
        versionField.value = orderData.version;
      }
    },

    /**
     * 주문 저장 (saveOrder 함수 완전 제거)
     */
    // async saveOrder(form) { ... } // 함수 정의 자체를 제거
  };

  // 주문 수정 모듈 초기화
  OrderEdit.init();

  // 전역 접근을 위해 window 객체에 할당 (필요한 경우)
  window.OrderEdit = OrderEdit;
});
