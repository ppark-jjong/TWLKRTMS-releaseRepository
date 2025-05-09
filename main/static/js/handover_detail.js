document.addEventListener("DOMContentLoaded", function () {
  const deleteBtn = document.getElementById("deleteHandoverBtn");
  const deleteDialog = document.getElementById("deleteConfirmDialog");
  const cancelDeleteBtn = document.getElementById("cancelDeleteBtn");
  const deleteForm = document.getElementById("deleteHandoverForm");
  const mainEditBtn = document.querySelector(
    '.header-actions a[href*="/edit"]'
  ); // 헤더의 수정 버튼

  // 페이지에서 인수인계 ID 추출 (URL 또는 데이터 속성 활용)
  let handoverId = "";
  try {
    // 1. 데이터 속성 시도 (더 안정적)
    const detailContainer = document.querySelector("[data-handover-id]");
    if (detailContainer) {
      handoverId = detailContainer.getAttribute("data-handover-id");
    }
    // 2. URL 파싱 시도 (대체)
    if (!handoverId) {
      const currentUrl = window.location.pathname;
      const parts = currentUrl.split("/");
      const potentialId = parts[parts.length - 1];
      const potentialIdBeforeEdit = parts[parts.length - 2];
      if (!isNaN(parseInt(potentialId))) {
        handoverId = potentialId;
      } else if (
        parts[parts.length - 1] === "edit" &&
        !isNaN(parseInt(potentialIdBeforeEdit))
      ) {
        handoverId = potentialIdBeforeEdit;
      }
    }
    console.log("Handover ID 추출됨:", handoverId);
  } catch (error) {
    console.error("Handover ID 추출 중 오류:", error);
  }

  if (!handoverId) {
    console.error("인수인계 ID(handover_id)를 찾을 수 없습니다.");
    Utils.alerts.showError("인수인계 정보를 식별할 수 없습니다.");
    return; // ID 없으면 이후 로직 실행 불가
  }

  // --- 메인 수정 버튼 클릭 이벤트 ---
  // 수정버튼 클릭 시 서버에서 락 획득을 시도하므로 별도 처리 불필요
  // 서버에서 락을 처리하기 때문에 기본 링크 동작 유지
  if (mainEditBtn) {
    // 기존 코드 제거 - 서버에서 직접 락 획득 처리
    console.log("수정 버튼 이벤트: 서버에서 락 처리");
  }

  // --- 삭제 버튼 관련 로직 ---
  // 삭제 버튼 클릭 시 대화상자 표시
  deleteBtn?.addEventListener("click", async (e) => {
    e.preventDefault(); // 기본 동작 방지

    console.log(`삭제 버튼 클릭: 확인 대화상자 표시 (ID: ${handoverId})`);

    // 삭제 확인 대화상자 표시
    deleteDialog?.classList.add("active");
  });

  // 취소 버튼 클릭 시 대화상자 닫기
  cancelDeleteBtn?.addEventListener("click", () => {
    deleteDialog?.classList.remove("active");
  });

  // 다이얼로그 외부 클릭 시 닫기
  deleteDialog?.addEventListener("click", (e) => {
    if (e.target === deleteDialog) {
      deleteDialog.classList.remove("active");
    }
  });

  // 삭제 폼 제출 처리 (락 확인은 서버에서 수행)
  deleteForm?.addEventListener("submit", (e) => {
    console.log("삭제 폼 제출");
    // 기본 제출 동작 진행 -> 서버에서 처리
  });

  // base.js에서 이미 URL 파라미터를 처리하므로 여기서는 호출하지 않음
  // 이 줄을 제거하거나 주석 처리하여 중복 알림 방지
  // Utils.ui.showPageMessages();
});
