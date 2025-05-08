/**
 * 주문 생성/수정 폼 스크립트
 * 주문의 생성 및 수정 기능 처리
 */
document.addEventListener('DOMContentLoaded', function () {
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

      // 사용자 정보 로드 (추가)
      this.userData = this.loadUserData();

      // 수정 모드일 경우 처리 (데이터 로드 방식은 템플릿 의존 가정)
      if (this.mode === 'edit') {
        // this.loadOrderData(); // 비동기 로드 방식 사용 시 여기에配置
        // 템플릿에서 바로 데이터를 받는 경우 아래 로직 실행
        this.setupStatusDropdown(); // 상태 드롭다운 설정 호출
      } else {
        // 생성 모드일 경우
        this.setDefaultDateTime();
      }

      // 상태 드롭다운 설정 (init 마지막에 호출하는 것으로 변경 - 생성/수정 모두 적용 가능성 고려)
      // this.setupStatusDropdown();
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
        remark: document.getElementById('remark'),
      };

      // 숨겨진 필드 (수정 모드용)
      if (this.mode === 'edit') {
        this.dashboardIdField = document.querySelector(
          'input[name="dashboard_id"]'
        );
      }
    },

    /**
     * 이벤트 리스너 설정
     */
    initEventListeners() {
      // 폼 제출 이벤트 리스너 제거!
      // if (this.form) {
      //   this.form.addEventListener('submit', (e) => {
      //     e.preventDefault();
      //     this.submitForm();
      //   });
      // }

      // 취소 버튼 이벤트 리스너는 유지
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
      if (!this.orderId && this.mode === 'edit') {
        console.error('수정 모드이지만 주문 ID가 없습니다.');
        Utils.message.error('주문 정보를 불러올 수 없습니다: 주문 ID 없음');
        return;
      }
      if (!this.orderId) return; // 생성 모드이거나 ID 없으면 로드 안함

      try {
        Utils.http.showLoading();
        // API 엔드포인트는 /api/orders/{id}/data 와 같이 실제 데이터만 반환하는 곳을 가정합니다.
        // 또는, 템플릿에서 이미 모든 데이터를 전달받았다면 이 함수는 필요 없을 수 있습니다.
        const orderData = await Utils.http.get(
          `/api/orders/${this.orderId}/data`
        );

        // 명시적 락 확인 로직 제거: editable 플래그에 따른 폼 비활성화 및 경고 메시지 제거
        // if (!orderData.editable) {
        //   Utils.message.warning(
        //     `이 주문은 현재 다른 사용자(${orderData.update_by || '알 수 없음'})가 수정 중입니다.`
        //   );
        //   this.disableForm();
        //   // return; // 폼 비활성화 후 더 이상 진행하지 않도록 할 수 있음
        // }

        // 폼 필드 설정
        this.fillFormData(orderData); // API 응답이 order 객체 자체라고 가정
      } catch (error) {
        Utils.message.error(
          error.message || '주문 데이터를 불러오는 중 오류가 발생했습니다.'
        );
        // 필요시 목록 페이지로 리다이렉트
        // setTimeout(() => { window.location.href = '/dashboard'; }, 2000);
      } finally {
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
      if (this.els.department)
        this.els.department.value = data.department || '';
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
      if (this.els.postalCode)
        this.els.postalCode.value = data.postalCode || '';
      if (this.els.address) this.els.address.value = data.address || '';
      if (this.els.customer) this.els.customer.value = data.customer || '';
      if (this.els.contact) this.els.contact.value = data.contact || '';
      if (this.els.status) this.els.status.value = data.status || 'WAITING';
      if (this.els.driverName)
        this.els.driverName.value = data.driverName || '';
      if (this.els.driverContact)
        this.els.driverContact.value = data.driverContact || '';
      if (this.els.remark) this.els.remark.value = data.remark || '';
    },

    /**
     * 폼 비활성화 (수정 불가능한 경우)
     */
    disableForm() {
      // 모든 입력 필드 비활성화
      const inputs = this.form.querySelectorAll('input, select, textarea');
      inputs.forEach((input) => {
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
          if (Utils && Utils.alerts) {
            Utils.alerts.showError('필수 입력 항목을 확인해주세요.');
          } else {
            alert('필수 입력 항목을 확인해주세요.');
          }
        }
        return false;
      }

      // 우편번호 검증
      const postalCode = this.els.postalCode.value.trim();
      if (postalCode.length < 5 || !/^\d{5}$/.test(postalCode)) {
        this.els.postalCode.focus();
        if (Utils && Utils.alerts) {
          Utils.alerts.showError('우편번호는 5자리 숫자로 입력해주세요.');
        } else {
          alert('우편번호는 5자리 숫자로 입력해주세요.');
        }
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
     * 폼 제출 처리 함수 제거!
     */
    // async submitForm() { ... } // 함수 정의 자체를 제거

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
    },

    // 사용자 정보 로드 함수 추가
    loadUserData() {
      const userInfoEl = document.getElementById('userInfo'); // base.html 에 정의된 userInfo div 가정
      if (
        userInfoEl &&
        userInfoEl.dataset.userId &&
        userInfoEl.dataset.userRole
      ) {
        return {
          user_id: userInfoEl.dataset.userId,
          user_role: userInfoEl.dataset.userRole,
          department: userInfoEl.dataset.department || '',
        };
      }
      // Fallback or error handling if user info is not found in DOM
      console.warn(
        '사용자 정보를 DOM에서 찾을 수 없습니다. 기본값(USER)을 사용합니다.'
      );
      return { user_id: '', user_role: 'USER', department: '' };
    },

    // --- 새로운 상태 드롭다운 옵션 제한 로직 추가 ---
    setupStatusDropdown() {
      const statusSelect = this.els.status;
      if (!statusSelect) return;

      const currentUserRole = this.userData.user_role;
      const isAdmin = currentUserRole === 'ADMIN';
      const initialStatus =
        statusSelect.value || (this.mode === 'create' ? 'WAITING' : null);

      if (initialStatus) {
        // 초기 상태값이 있을 때만 업데이트
        this.updateStatusOptions(initialStatus, isAdmin);
      }
      // 생성 모드이고, 초기 상태가 WAITING이면 (기본값), 해당 옵션만 보여주거나, 관리자/사용자에 따라 다르게 설정
      // 또는, 주문 로드 후 현재 상태를 기준으로 항상 updateStatusOptions 호출하도록 수정
    },

    // --- 상태 전이 규칙 (백엔드와 일치 - 재정의된 규칙) ---
    statusTransitions: {
      // 일반 사용자
      WAITING: ['IN_PROGRESS', 'ISSUE', 'CANCEL'],
      IN_PROGRESS: ['COMPLETE', 'ISSUE', 'CANCEL'],
      COMPLETE: ['ISSUE', 'CANCEL'],
      ISSUE: ['COMPLETE', 'CANCEL'],
      CANCEL: ['COMPLETE', 'ISSUE'],
    },
    adminStatusTransitions: {
      // 관리자
      WAITING: ['IN_PROGRESS', 'ISSUE', 'CANCEL'],
      IN_PROGRESS: ['WAITING', 'COMPLETE', 'ISSUE', 'CANCEL'],
      COMPLETE: ['IN_PROGRESS', 'ISSUE', 'CANCEL'],
      ISSUE: ['IN_PROGRESS', 'COMPLETE', 'CANCEL'],
      CANCEL: ['IN_PROGRESS', 'COMPLETE', 'ISSUE'],
    },

    // 드롭다운 옵션 업데이트 함수
    updateStatusOptions(currentStatus, isAdmin) {
      const statusSelect = this.els.status;
      if (!statusSelect) return;

      let allowedNextStates = [];
      if (isAdmin) {
        allowedNextStates = this.adminStatusTransitions[currentStatus] || [];
      } else {
        allowedNextStates = this.statusTransitions[currentStatus] || [];
      }

      // 현재 상태는 항상 선택지에 포함
      const displayOptions = [currentStatus, ...allowedNextStates];
      // 중복 제거 (이미 currentStatus가 allowedNextStates에 있을 수 있으므로)
      const uniqueDisplayOptions = [...new Set(displayOptions)];

      const statusLabels = {
        WAITING: '대기',
        IN_PROGRESS: '진행',
        COMPLETE: '완료',
        ISSUE: '이슈',
        CANCEL: '취소',
      };

      // 기존 옵션 모두 제거
      while (statusSelect.options.length > 0) {
        statusSelect.remove(0);
      }

      // 유효한 옵션만 추가
      uniqueDisplayOptions.forEach((statusValue) => {
        if (statusLabels[statusValue]) {
          // 정의된 상태만 추가
          const option = document.createElement('option');
          option.value = statusValue;
          option.text = statusLabels[statusValue];
          if (statusValue === currentStatus) {
            option.selected = true;
          }
          statusSelect.add(option);
        }
      });

      // 만약 uniqueDisplayOptions의 길이가 1이고 (즉, 현재 상태에서 변경 가능한 상태가 없음)
      // 현재 상태가 COMPLETE, ISSUE, CANCEL 중 하나라면 select 자체를 disabled 처리 (선택)
      if (
        uniqueDisplayOptions.length === 1 &&
        ['COMPLETE', 'ISSUE', 'CANCEL'].includes(currentStatus) &&
        !isAdmin
      ) {
        // statusSelect.disabled = true; // 일반 사용자가 최종 상태에 도달하면 변경 불가함을 명시
      } else {
        // statusSelect.disabled = false;
      }
    },
    // --- 상태 드롭다운 로직 끝 ---
  };

  // 주문 폼 초기화
  OrderForm.init();

  // --- 페이지 로드 시 버전 경고 확인 ---
  const urlParams = new URLSearchParams(window.location.search);
  const warningMsg = urlParams.get('warning');
  if (warningMsg) {
    // 페이지 상단 등에 경고 메시지 표시
    const notificationArea =
      document.getElementById('notificationArea') || document.body; // 알림 영역 선택
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-warning'; // 경고 스타일
    // 메시지 형식 변경: "다른 사용자({user_name})가 ({update_time})에 먼저 수정했습니다. 저장된 내용을 확인하세요."
    alertDiv.innerHTML = `<i class="fa-solid fa-triangle-exclamation"></i> <strong>${decodeURIComponent(
      warningMsg
    )}</strong> 저장된 내용을 확인하세요.`;
    // 기존 알림 삭제 후 추가 또는 맨 위에 추가
    const existingAlert = notificationArea.querySelector('.alert-warning');
    if (existingAlert) existingAlert.remove();
    notificationArea.prepend(alertDiv);
    // URL에서 warning 파라미터 제거 (새로고침 시 다시 안 보이도록)
    urlParams.delete('warning');
    history.replaceState(
      null,
      '',
      `${window.location.pathname}?${urlParams.toString()}`
    );
  }

  // 글로벌 스코프에 노출
  window.OrderForm = OrderForm;
});
