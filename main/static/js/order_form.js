/**
 * 주문 생성/수정 폼 스크립트
 * 주문의 생성 및 수정 기능 처리
 */
document.addEventListener('DOMContentLoaded', function() {
  // 주문 폼 관리 모듈
  const OrderForm = {
    // 폼 모드 (create 또는 edit)
    mode: 'create',
    
    // 편집 중인 주문 ID (수정 모드일 때)
    orderId: null,
    
    /**
     * 초기화 함수
     */
    init() {
      // 현재 페이지 URL 확인하여 모드 설정
      this.setModeFromUrl();
      
      // 폼 요소 참조 초기화
      this.initFormRefs();
      
      // 이벤트 리스너 설정
      this.initEventListeners();
      
      // 우편번호 입력 처리 설정
      this.initPostalCodeHandler();
      
      // 수정 모드일 경우 데이터 로드
      if (this.mode === 'edit' && this.orderId) {
        this.loadOrderData();
      }
      
      // 기본 날짜/시간 설정 (생성 모드일 경우)
      if (this.mode === 'create') {
        this.setDefaultDateTime();
      }
    },
    
    /**
     * URL에서 모드 확인
     */
    setModeFromUrl() {
      const path = window.location.pathname;
      
      if (path.includes('/edit')) {
        this.mode = 'edit';
        // URL에서 주문 ID 추출 (예: /orders/123/edit)
        const matches = path.match(/\/orders\/(\d+)\/edit/);
        if (matches && matches[1]) {
          this.orderId = matches[1];
        }
      } else {
        this.mode = 'create';
      }
      

    },
    
    /**
     * 폼 요소 참조 초기화
     */
    initFormRefs() {
      // 폼 요소
      this.form = document.querySelector('.order-form');
      
      // 주요 입력 필드
      this.els = {
        orderNo: document.getElementById('order_no'),
        type: document.getElementById('type'),
        department: document.getElementById('department'),
        warehouse: document.getElementById('warehouse'),
        sla: document.getElementById('sla'),
        eta: document.getElementById('eta'),
        postalCode: document.getElementById('postal_code'),
        address: document.getElementById('address'),
        customer: document.getElementById('customer'),
        contact: document.getElementById('contact'),
        status: document.getElementById('status'),
        driverName: document.getElementById('driver_name'),
        driverContact: document.getElementById('driver_contact'),
        remark: document.getElementById('remark')
      };
      
      // 숨겨진 필드 (수정 모드용)
      if (this.mode === 'edit') {
        this.dashboardIdField = document.querySelector('input[name="dashboard_id"]');
      }
    },
    
    /**
     * 이벤트 리스너 설정
     */
    initEventListeners() {
      // 폼 제출 이벤트
      if (this.form) {
        this.form.addEventListener('submit', (e) => {
          e.preventDefault();
          this.submitForm();
        });
      }
      
      // 취소 버튼 이벤트
      const cancelBtn = document.querySelector('.btn.secondary-btn');
      if (cancelBtn) {
        cancelBtn.addEventListener('click', (e) => {
          e.preventDefault();
          this.cancelForm();
        });
      }
    },
    
    /**
     * 우편번호 입력 처리 설정
     */
    initPostalCodeHandler() {
      // 우편번호 4자리 -> 5자리 자동 변환
      if (this.els.postalCode) {
        this.els.postalCode.addEventListener('change', () => {
          const value = this.els.postalCode.value.trim();
          if (value && value.length === 4) {
            this.els.postalCode.value = '0' + value;
          }
        });
        
        // 숫자만 입력 가능하도록 설정
        this.els.postalCode.addEventListener('input', (e) => {
          e.target.value = e.target.value.replace(/[^0-9]/g, '');
          if (e.target.value.length > 5) {
            e.target.value = e.target.value.slice(0, 5);
          }
        });
      }
    },
    
    /**
     * 기본 날짜/시간 설정 (생성 모드)
     */
    setDefaultDateTime() {
      if (this.els.eta) {
        // 현재 시간 + 1시간으로 설정
        const now = new Date();
        now.setHours(now.getHours() + 1);
        
        // ISO 형식 변환 (YYYY-MM-DDTHH:MM)
        const defaultEta = now.toISOString().substring(0, 16);
        this.els.eta.value = defaultEta;
      }
    },
    
    /**
     * 주문 데이터 로드 (수정 모드)
     */
    async loadOrderData() {
      try {
        // 로딩 표시
        Utils.http.showLoading();
        
        // 주문 데이터 조회 API 호출
        const data = await Utils.http.get(`/orders/${this.orderId}`);
        
        // 락 확인 (수정 가능 여부)
        if (!data.editable) {
          Utils.message.warning(`이 주문은 현재 다른 사용자(${data.update_by || '알 수 없음'})가 수정 중입니다.`);
          
          // 수정 불가 시 폼 비활성화
          this.disableForm();
        }
        
        // 폼 필드 설정
        this.fillFormData(data);
      } catch (error) {

        Utils.message.error('주문 데이터를 불러오는 중 오류가 발생했습니다.');
        
        // 오류 발생 시 목록 페이지로 돌아가기
        setTimeout(() => {
          window.location.href = '/dashboard';
        }, 2000);
      } finally {
        // 로딩 숨김
        Utils.http.hideLoading();
      }
    },
    
    /**
     * 폼 데이터 채우기
     * @param {Object} data - 주문 데이터
     */
    fillFormData(data) {
      // 숨겨진 필드 설정
      if (this.dashboardIdField) {
        this.dashboardIdField.value = data.dashboardId;
      }
      
      // 입력 필드 설정
      if (this.els.orderNo) this.els.orderNo.value = data.orderNo || '';
      if (this.els.type) this.els.type.value = data.type || 'DELIVERY';
      if (this.els.department) this.els.department.value = data.department || '';
      if (this.els.warehouse) this.els.warehouse.value = data.warehouse || '';
      if (this.els.sla) this.els.sla.value = data.sla || '';
      
      // 날짜 필드 처리
      if (this.els.eta && data.eta) {
        // 서버 날짜 형식 (YYYY-MM-DD HH:MM)을 input[type="datetime-local"] 형식으로 변환
        const etaDate = new Date(data.eta);
        if (!isNaN(etaDate.getTime())) {
          // YYYY-MM-DDTHH:MM 형식으로 변환
          const localDate = etaDate.toISOString().substring(0, 16);
          this.els.eta.value = localDate;
        }
      }
      
      // 기타 필드
      if (this.els.postalCode) this.els.postalCode.value = data.postalCode || '';
      if (this.els.address) this.els.address.value = data.address || '';
      if (this.els.customer) this.els.customer.value = data.customer || '';
      if (this.els.contact) this.els.contact.value = data.contact || '';
      if (this.els.status) this.els.status.value = data.status || 'WAITING';
      if (this.els.driverName) this.els.driverName.value = data.driverName || '';
      if (this.els.driverContact) this.els.driverContact.value = data.driverContact || '';
      if (this.els.remark) this.els.remark.value = data.remark || '';
    },
    
    /**
     * 폼 비활성화 (수정 불가능한 경우)
     */
    disableForm() {
      // 모든 입력 필드 비활성화
      const inputs = this.form.querySelectorAll('input, select, textarea');
      inputs.forEach(input => {
        input.disabled = true;
      });
      
      // 제출 버튼 비활성화
      const submitBtn = this.form.querySelector('button[type="submit"]');
      if (submitBtn) {
        submitBtn.disabled = true;
      }
    },
    
    /**
     * 폼 데이터 검증
     * @returns {boolean} 유효성 여부
     */
    validateForm() {
      // HTML5 내장 유효성 검사 사용
      if (!this.form.checkValidity()) {
        // 첫 번째 오류 필드에 포커스
        const invalidField = this.form.querySelector(':invalid');
        if (invalidField) {
          invalidField.focus();
          
          // 오류 메시지 표시
          Utils.message.error('필수 입력 항목을 확인해주세요.');
        }
        return false;
      }
      
      // 우편번호 검증
      const postalCode = this.els.postalCode.value.trim();
      if (postalCode.length < 5 || !/^\d{5}$/.test(postalCode)) {
        this.els.postalCode.focus();
        Utils.message.error('우편번호는 5자리 숫자로 입력해주세요.');
        return false;
      }
      
      return true;
    },
    
    /**
     * 폼 데이터 수집
     * @returns {Object} 수집된 데이터
     */
    collectFormData() {
      const formData = new FormData(this.form);
      const data = {};
      
      // FormData를 일반 객체로 변환
      for (const [key, value] of formData.entries()) {
        data[key] = value;
      }
      
      return data;
    },
    
    /**
     * 폼 제출 처리
     */
    async submitForm() {
      // 폼 유효성 검사
      if (!this.validateForm()) {
        return;
      }
      
      try {
        // 로딩 표시
        Utils.http.showLoading();
        
        // 폼 데이터 수집
        const formData = this.collectFormData();
        
        // API 호출 (모드에 따라 POST 또는 PUT)
        let response;
        
        if (this.mode === 'create') {
          // 주문 생성 API
          response = await Utils.http.post('/orders', formData);
        } else {
          // 주문 업데이트 API
          response = await Utils.http.put(`/orders/${this.orderId}`, formData);
        }
        
        // 성공 처리
        if (response && response.success) {
          Utils.message.success(response.message || '주문이 성공적으로 저장되었습니다.');
          
          // 성공 시 상세 페이지 또는 목록으로 이동
          setTimeout(() => {
            if (this.mode === 'create') {
              window.location.href = '/dashboard';
            } else {
              window.location.href = `/orders/${this.orderId}`;
            }
          }, 1500);
        } else {
          throw new Error(response.message || '저장 실패');
        }
      } catch (error) {

        Utils.message.error(error.message || '주문 저장 중 오류가 발생했습니다.');
      } finally {
        // 로딩 숨김
        Utils.http.hideLoading();
      }
    },
    
    /**
     * 폼 취소 처리
     */
    cancelForm() {
      if (confirm('작성 중인 내용이 저장되지 않습니다. 취소하시겠습니까?')) {
        if (this.mode === 'edit') {
          window.location.href = `/orders/${this.orderId}`;
        } else {
          window.location.href = '/dashboard';
        }
      }
    }
  };
  
  // 주문 폼 초기화
  OrderForm.init();
  
  // 글로벌 스코프에 노출
  window.OrderForm = OrderForm;
});
