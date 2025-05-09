/**
 * 대시보드 일괄 작업 관련 스크립트
 */
document.addEventListener('DOMContentLoaded', function () {
  // --- DOM 요소 ---
  const selectAllCheckbox = document.getElementById('selectAllCheckbox');
  const tableBody = document.getElementById('dashboardTableBody');
  const batchActionsDiv = document.getElementById('batchActions');
  const selectedCountSpan = document.getElementById('selectedCount');
  const batchStatusUpdateBtn = document.getElementById('batchStatusUpdateBtn');
  const batchDriverAssignBtn = document.getElementById('batchDriverAssignBtn');

  // 모달 요소 (추후 사용)
  const batchStatusUpdateModal = document.getElementById(
    'batchStatusUpdateModal'
  );
  const batchDriverAssignModal = document.getElementById(
    'batchDriverAssignModal'
  );
  const confirmBatchStatusUpdateBtn = document.getElementById(
    'confirmBatchStatusUpdateBtn'
  );
  const confirmBatchDriverAssignBtn = document.getElementById(
    'confirmBatchDriverAssignBtn'
  );
  const batchNewStatusSelect = document.getElementById('batchNewStatus');
  const batchDriverNameInput = document.getElementById('batchDriverName');
  const batchDriverContactInput = document.getElementById('batchDriverContact');
  const batchDeliveryCompanySelect = document.getElementById(
    'batchDeliveryCompany'
  );
  const batchStatusUpdateCountSpan = document.getElementById(
    'batchStatusUpdateCount'
  );
  const batchDriverAssignCountSpan = document.getElementById(
    'batchDriverAssignCount'
  );

  // --- 상태 변수 ---
  let selectedOrderIds = [];

  // --- 상태 전이 규칙 객체 (백엔드와 일치하도록 관리 - 재정의된 규칙) ---
  const statusTransitions = {
    // 일반 사용자
    WAITING: ['IN_PROGRESS'],
    IN_PROGRESS: ['COMPLETE', 'ISSUE', 'CANCEL'],
    COMPLETE: ['ISSUE', 'CANCEL'],
    ISSUE: ['COMPLETE', 'CANCEL'],
    CANCEL: ['COMPLETE', 'ISSUE'],
  };
  const adminStatusTransitions = {
    // 관리자
    WAITING: ['IN_PROGRESS'],
    IN_PROGRESS: ['WAITING', 'COMPLETE', 'ISSUE', 'CANCEL'],
    COMPLETE: ['IN_PROGRESS', 'ISSUE', 'CANCEL'],
    ISSUE: ['IN_PROGRESS', 'COMPLETE', 'CANCEL'],
    CANCEL: ['IN_PROGRESS', 'COMPLETE', 'ISSUE'],
  };

  // --- 함수 ---

  // 선택 상태 업데이트 및 UI 반영
  function updateSelectionState() {
    const rowCheckboxes = tableBody.querySelectorAll('.rowCheckbox');
    selectedOrderIds = [];
    let allChecked = rowCheckboxes.length > 0;
    let anyChecked = false;

    rowCheckboxes.forEach((checkbox) => {
      if (checkbox.checked) {
        selectedOrderIds.push(checkbox.dataset.id);
        anyChecked = true;
      } else {
        allChecked = false;
      }
    });

    // 전체 선택 체크박스 상태 업데이트
    if (selectAllCheckbox) {
      selectAllCheckbox.checked = allChecked;
      selectAllCheckbox.disabled = rowCheckboxes.length === 0;
    }

    // 선택된 개수 표시 업데이트 (이 부분은 제거해도 무방)
    // if (selectedCountSpan) {
    //     selectedCountSpan.textContent = `${selectedOrderIds.length}개 선택됨`;
    // }

    // 일괄 작업 버튼 활성화/비활성화
    const enableButtons = anyChecked; // 하나라도 체크되면 true
    if (batchStatusUpdateBtn) {
      batchStatusUpdateBtn.disabled = !enableButtons;
    }
    if (batchDriverAssignBtn) {
      batchDriverAssignBtn.disabled = !enableButtons;
    }
    // 기존 batchActionsDiv 표시/숨김 로직 제거
    // if (batchActionsDiv) {
    //     batchActionsDiv.style.display = anyChecked ? 'flex' : 'none';
    // }
  }

  // 모달 열기 함수 (dialog 방식으로 통일)
  function openDialog(dialogElement) {
    if (dialogElement) {
      // dialog 클래스를 사용하여 활성화
      dialogElement.classList.add('active');

      // 선택된 주문 정보 가져오기 (ID, 주문번호, 상태)
      const selectedOrdersInfo = selectedOrderIds.map((id) => {
        const row = tableBody.querySelector(`tr[data-id="${id}"]`);
        return {
          id: id,
          orderNo: row ? row.dataset.orderNo : 'N/A',
          status: row ? row.dataset.status : 'N/A',
        };
      });

      // 표시할 주문번호 목록 생성 (최대 5개 + ...외 N건)
      const maxDisplay = 5;
      let orderNoDisplay = selectedOrdersInfo
        .slice(0, maxDisplay)
        .map((o) => o.orderNo)
        .join(', ');
      if (selectedOrdersInfo.length > maxDisplay) {
        orderNoDisplay += ` ...외 ${selectedOrdersInfo.length - maxDisplay}건`;
      }

      if (dialogElement.id === 'batchStatusUpdateModal') {
        batchStatusUpdateCountSpan.textContent = selectedOrdersInfo.length;
        // 주문번호 표시
        const orderNosStatusElement = document.getElementById(
          'selectedOrderNosStatus'
        );
        if (orderNosStatusElement) {
          orderNosStatusElement.textContent = `대상 주문: ${orderNoDisplay}`;
        }
        loadAndSetStatusOptions(); // 공통 상태 옵션 로드
      } else if (dialogElement.id === 'batchDriverAssignModal') {
        batchDriverAssignCountSpan.textContent = selectedOrdersInfo.length;
        // 주문번호 표시
        const orderNosDriverElement = document.getElementById(
          'selectedOrderNosDriver'
        );
        if (orderNosDriverElement) {
          orderNosDriverElement.textContent = `대상 주문: ${orderNoDisplay}`;
        }

        // 폼 필드 초기화
        batchDriverNameInput.value = '';
        batchDriverContactInput.value = '';
        batchDeliveryCompanySelect.value = '';
      }
    }
  }

  // 모달 닫기 함수 (dialog 방식으로 통일)
  function closeDialog(dialogElement) {
    if (dialogElement) {
      // dialog 클래스를 사용하여 비활성화
      dialogElement.classList.remove('active');
    }
  }

  // 상태 옵션 로드 및 설정
  async function loadAndSetStatusOptions() {
    if (selectedOrderIds.length === 0) {
      batchNewStatusSelect.innerHTML =
        '<option value="">주문을 선택하세요</option>';
      return;
    }

    // 사용자 역할 가져오기 (BaseApp 또는 다른 전역 객체 사용 가정)
    const currentUserRole = window.BaseApp?.userData?.user_role || 'USER';
    const isAdmin = currentUserRole === 'ADMIN';

    try {
      Utils.alerts.showLoading('상태 옵션 로딩 중...');

      // 선택된 행들의 상태 값 확인
      const selectedRows = [];
      let allSameStatus = true;
      let firstStatus = null;
      
      selectedOrderIds.forEach((id) => {
        const row = tableBody.querySelector(`tr[data-id="${id}"]`);
        if (row) {
          const status = row.getAttribute('data-status');
          selectedRows.push({
            id,
            status,
            orderNo: row.getAttribute('data-order-no') || 'N/A'
          });
          
          if (firstStatus === null) {
            firstStatus = status;
          } else if (status !== firstStatus) {
            allSameStatus = false;
          }
        }
      });
      
      // 상태가 다른 경우 알림 표시 후 종료
      if (!allSameStatus) {
        Utils.alerts.hideLoading();
        Utils.alerts.showWarning('서로 다른 상태의 주문은 함께 상태 변경할 수 없습니다. 같은 상태의 주문만 선택해주세요.');
        closeDialog(batchStatusUpdateModal);
        return;
      }

      // 백엔드 API 호출 URL 생성 방식 수정
      const params = new URLSearchParams();
      selectedOrderIds.forEach((id) => params.append('ids', id));
      const queryString = params.toString(); // 예: "ids=2&ids=1"

      const response = await fetch(
        `/api/orders/batch-get-common-statuses?${queryString}`
      );
      if (!response.ok) {
        const errorData = await response
          .json()
          .catch(() => ({ detail: '상태 옵션 조회 실패' }));
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      const result = await response.json();

      if (result.success && result.common_statuses && result.labels) {
        const commonStatuses = result.common_statuses;
        const labels = result.labels;

        batchNewStatusSelect.innerHTML = ''; // 기존 옵션 제거

        if (commonStatuses.length === 0) {
          // 공통으로 변경 가능한 상태가 없는 경우
          batchNewStatusSelect.innerHTML =
            '<option value="">변경 가능한 상태 없음</option>';
          batchNewStatusSelect.disabled = true;
          // 확인 버튼도 비활성화 (선택적)
          if (confirmBatchStatusUpdateBtn)
            confirmBatchStatusUpdateBtn.disabled = true;
        } else {
          // 공통 상태 옵션 추가
          commonStatuses.forEach((statusValue) => {
            const option = document.createElement('option');
            option.value = statusValue;
            option.text = labels[statusValue] || statusValue; // 라벨 사용
            batchNewStatusSelect.add(option);
          });
          batchNewStatusSelect.disabled = false;
          if (confirmBatchStatusUpdateBtn)
            confirmBatchStatusUpdateBtn.disabled = false;
          // 첫 번째 옵션을 기본값으로 선택
          if (batchNewStatusSelect.options.length > 0) {
            batchNewStatusSelect.selectedIndex = 0;
          }
        }

        // TODO: 만약 선택된 주문들의 "현재 상태"도 표시하고 싶다면?
        // 현재 이 로직은 "다음" 변경 가능한 상태만 보여줌
        // (예: WAITING만 선택 시 IN_PROGRESS, ISSUE, CANCEL 만 표시됨)
        // 필요하다면, 선택된 주문들의 현재 상태를 가져와서 (API 응답 또는 테이블 데이터)
        // 현재 상태도 옵션에 포함시킬지 결정 (단, 모든 주문의 현재 상태가 동일할 때만 의미있음)
      } else {
        throw new Error(result.message || '잘못된 응답 형식');
      }
    } catch (error) {
      Utils.alerts.showError(`상태 옵션 로드 실패: ${error.message}`);
      batchNewStatusSelect.innerHTML = '<option value="">오류 발생</option>';
      batchNewStatusSelect.disabled = true;
      if (confirmBatchStatusUpdateBtn)
        confirmBatchStatusUpdateBtn.disabled = true;
    } finally {
      Utils.alerts.hideLoading();
    }
  }

  // --- 이벤트 리스너 ---

  // 전체 선택 체크박스
  if (selectAllCheckbox) {
    selectAllCheckbox.addEventListener('change', function () {
      const isChecked = this.checked;
      tableBody.querySelectorAll('.rowCheckbox').forEach((checkbox) => {
        checkbox.checked = isChecked;
      });
      updateSelectionState();
    });
  }

  // 개별 체크박스 (이벤트 위임 사용)
  if (tableBody) {
    tableBody.addEventListener('change', function (e) {
      if (e.target.classList.contains('rowCheckbox')) {
        updateSelectionState();
      }
    });
  }

  // 테이블 내용 변경 후 선택 상태 재설정 (MutationObserver 사용)
  // dashboard.js에서 테이블 내용을 다시 그릴 때 이 함수를 호출해주어야 함
  // 또는 MutationObserver를 사용하여 tableBody의 변경을 감지
  const observer = new MutationObserver((mutations) => {
    // 테이블 내용이 변경될 때마다 선택 상태 및 UI 업데이트
    updateSelectionState();
    // 필요하다면, 체크박스에 대한 추가적인 초기화나 이벤트 리스너 재설정
  });
  if (tableBody) {
    observer.observe(tableBody, { childList: true, subtree: true });
  }

  // 일괄 상태 변경 버튼
  if (batchStatusUpdateBtn) {
    batchStatusUpdateBtn.addEventListener('click', () => {
      if (selectedOrderIds.length === 0) {
        Utils.alerts.showWarning('먼저 주문을 선택해주세요.');
        return;
      }
      openDialog(batchStatusUpdateModal);
    });
  }

  // 일괄 기사 배정 버튼
  if (batchDriverAssignBtn) {
    batchDriverAssignBtn.addEventListener('click', () => {
      if (selectedOrderIds.length === 0) {
        Utils.alerts.showWarning('먼저 주문을 선택해주세요.');
        return;
      }
      openDialog(batchDriverAssignModal);
    });
  }

  // 모달 닫기 버튼 (취소 버튼)
  const cancelStatusBtn = document.getElementById('cancelStatusBtn');
  if (cancelStatusBtn) {
    cancelStatusBtn.addEventListener('click', () => {
      closeDialog(batchStatusUpdateModal);
    });
  }

  const cancelDriverBtn = document.getElementById('cancelDriverBtn');
  if (cancelDriverBtn) {
    cancelDriverBtn.addEventListener('click', () => {
      closeDialog(batchDriverAssignModal);
    });
  }

  // 모달 외부 클릭 시 닫기
  window.addEventListener('click', (event) => {
    if (event.target.classList.contains('dialog')) {
      closeDialog(event.target);
    }
  });

  // --- 일괄 처리 실행 로직 (추후 상세 구현) ---

  // 상태 변경 확인 버튼
  if (confirmBatchStatusUpdateBtn) {
    confirmBatchStatusUpdateBtn.addEventListener('click', async () => {
      const newStatus = batchNewStatusSelect.value;
      if (!newStatus) {
        Utils.alerts.showWarning('변경할 상태를 선택해주세요.');
        return;
      }

      console.log(
        `선택된 ${selectedOrderIds.length}개 주문 상태를 ${newStatus}(으)로 변경 시도`
      );
      // TODO: API 호출 (/api/orders/batch-status-update)
      try {
        Utils.alerts.showLoading('상태 변경 중...');
        const response = await fetch('/api/orders/batch-status-update', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            // CSRF 토큰 등 필요시 추가
          },
          body: JSON.stringify({
            dashboard_ids: selectedOrderIds,
            new_status: newStatus,
          }),
        });

        const results = await response.json();

        if (!response.ok) {
          // API 레벨 에러 (예: 500 서버 에러)
          throw new Error(
            results.detail || `상태 변경 실패 (HTTP ${response.status})`
          );
        }

        // 결과 처리 (성공/부분 성공/실패 메시지 표시)
        let successCount = results.filter((r) => r.success).length;
        let failCount = results.length - successCount;
        let message = `${successCount}건 성공`;
        if (failCount > 0) {
          message += `, ${failCount}건 실패`;
          // 실패 상세 내용 로깅 또는 표시 (선택적)
          console.warn(
            '상태 변경 실패 상세:',
            results.filter((r) => !r.success)
          );
          Utils.alerts.showWarning(
            `${message}. 실패 사유는 로그를 확인하세요.`
          );
        } else {
          Utils.alerts.showSuccess(message);
        }

        closeDialog(batchStatusUpdateModal);
        // 테이블 데이터 새로고침 (dashboard.js의 함수 호출 또는 직접 API 호출)
        if (
          window.fetchAllOrders &&
          window.startDateInput &&
          window.endDateInput
        ) {
          window.fetchAllOrders(
            window.startDateInput.value,
            window.endDateInput.value
          );
        } else {
          console.warn(
            'fetchAllOrders 함수를 찾을 수 없어 테이블을 새로고치지 못했습니다.'
          );
          // window.location.reload(); // 최후의 수단
        }
      } catch (error) {
        Utils.alerts.showError(`상태 변경 중 오류 발생: ${error.message}`);
      } finally {
        Utils.alerts.hideLoading();
      }
    });
  }

  // 기사 배정 확인 버튼
  if (confirmBatchDriverAssignBtn) {
    confirmBatchDriverAssignBtn.addEventListener('click', async () => {
      const driverName = batchDriverNameInput.value.trim();
      const driverContact = batchDriverContactInput.value.trim();
      const deliveryCompany = batchDeliveryCompanySelect.value;

      if (!driverName) {
        Utils.alerts.showWarning('기사명을 입력해주세요.');
        batchDriverNameInput.focus();
        return;
      }

      // 기사 연락처 유효성 검증 (숫자, 하이픈, 공백 허용, 선택 사항)
      if (driverContact && !/^[0-9\s\-]+$/.test(driverContact)) {
        Utils.alerts.showWarning(
          '유효하지 않은 연락처 형식입니다. (숫자, 하이픈, 공백만 입력 가능)'
        );
        batchDriverContactInput.focus();
        return;
      }

      console.log(
        `선택된 ${selectedOrderIds.length}개 주문에 기사 ${driverName} (${
          deliveryCompany || '-'
        }) 배정 시도`
      );
      // TODO: API 호출 (/api/orders/batch-driver-assign)
      try {
        Utils.alerts.showLoading('기사 배정 중...');
        const response = await fetch('/api/orders/batch-driver-assign', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            dashboard_ids: selectedOrderIds,
            driver_name: driverName,
            driver_contact: driverContact || null, // 빈 문자열은 null로
            delivery_company: deliveryCompany || null, // 빈 문자열은 null로
          }),
        });

        const results = await response.json();

        if (!response.ok) {
          throw new Error(
            results.detail || `기사 배정 실패 (HTTP ${response.status})`
          );
        }

        let successCount = results.filter((r) => r.success).length;
        let failCount = results.length - successCount;
        let message = `${successCount}건 성공`;
        if (failCount > 0) {
          message += `, ${failCount}건 실패`;
          console.warn(
            '기사 배정 실패 상세:',
            results.filter((r) => !r.success)
          );
          Utils.alerts.showWarning(
            `${message}. 실패 사유는 로그를 확인하세요.`
          );
        } else {
          Utils.alerts.showSuccess(message);
        }

        closeDialog(batchDriverAssignModal);
        // 테이블 데이터 새로고침
        if (
          window.fetchAllOrders &&
          window.startDateInput &&
          window.endDateInput
        ) {
          window.fetchAllOrders(
            window.startDateInput.value,
            window.endDateInput.value
          );
        } else {
          console.warn(
            'fetchAllOrders 함수를 찾을 수 없어 테이블을 새로고치지 못했습니다.'
          );
        }
      } catch (error) {
        Utils.alerts.showError(`기사 배정 중 오류 발생: ${error.message}`);
      } finally {
        Utils.alerts.hideLoading();
      }
    });
  }

  // 초기 상태 업데이트 (페이지 로드 시 버튼 비활성화)
  updateSelectionState();
});
