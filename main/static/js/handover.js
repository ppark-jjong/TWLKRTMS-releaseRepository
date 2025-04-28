/**
 * 인수인계 페이지 관리 모듈
 * 인수인계 목록, 상세, 생성, 수정, 삭제 기능을 제공합니다.
 */
window.Handover = (function() {
  /**
   * 현재 데이터 상태
   */
  const state = {
    currentHandover: null,
    isEditing: false
  };
  
  /**
   * 초기화 함수
   */
  function init() {
    console.log('[Handover] 초기화 시작');
    
    // 모듈 의존성 확인
    if (!checkDependencies()) {
      console.error('[Handover] 초기화 실패: 필수 모듈이 로드되지 않았습니다.');
      return;
    }
    
    // 이벤트 리스너 설정
    setupEventListeners();
    
    console.log('[Handover] 초기화 완료');
  }
  
  /**
   * 모듈 의존성을 확인합니다.
   * @returns {boolean} - 의존성 확인 결과
   */
  function checkDependencies() {
    const dependencies = [
      { name: 'Utils', module: window.Utils },
      { name: 'API', module: window.API },
      { name: 'Alerts', module: window.Alerts },
      { name: 'Modal', module: window.Modal }
    ];
    
    const missingDependencies = dependencies.filter(dep => !dep.module);
    
    if (missingDependencies.length > 0) {
      console.error('[Handover] 누락된 의존성:', missingDependencies.map(dep => dep.name).join(', '));
      
      // 사용자에게 알림
      if (window.Alerts) {
        Alerts.error('일부 필수 스크립트를 로드할 수 없습니다. 페이지를 새로고침하세요.');
      } else {
        alert('일부 필수 스크립트를 로드할 수 없습니다. 페이지를 새로고침하세요.');
      }
      
      return false;
    }
    
    return true;
  }
  
  /**
   * 이벤트 리스너를 설정합니다.
   */
  function setupEventListeners() {
    // 패널 토글 이벤트 (모든 패널에 적용)
    document.querySelectorAll('.panel-toggle').forEach(toggle => {
      toggle.addEventListener('click', function() {
        const panelContent = this.closest('.panel').querySelector('.panel-content');
        if (panelContent) {
          panelContent.classList.toggle('collapsed');
          
          // 화살표 아이콘 변경
          const icon = this.querySelector('i');
          if (icon) {
            if (panelContent.classList.contains('collapsed')) {
              icon.className = 'fas fa-chevron-down';
            } else {
              icon.className = 'fas fa-chevron-up';
            }
          }
        }
      });
    });
    
    // ESC 키로 모달 닫기
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape') {
        closeModal();
      }
    });
    
    // 모달 외부 클릭 시 닫기
    document.querySelectorAll('.modal').forEach(modal => {
      modal.addEventListener('click', function(e) {
        if (e.target === this) {
          closeModal();
        }
      });
    });
  }
  
  /**
   * 패널을 토글합니다.
   * @param {Element} toggleElement - 토글 버튼 요소
   * @param {string} contentClass - 패널 내용 클래스명
   */
  function togglePanel(toggleElement, contentClass) {
    const panelContent = document.querySelector('.' + contentClass);
    if (panelContent) {
      panelContent.classList.toggle('collapsed');
      
      // 화살표 아이콘 변경
      const icon = toggleElement.querySelector('i');
      if (icon) {
        if (panelContent.classList.contains('collapsed')) {
          icon.className = 'fas fa-chevron-down';
        } else {
          icon.className = 'fas fa-chevron-up';
        }
      }
    }
  }
  
  /**
   * 인수인계 작성 모달을 엽니다.
   */
  function openCreateModal() {
    // 폼 초기화
    const form = document.getElementById('handoverForm');
    if (form) {
      form.reset();
      document.getElementById('handoverId').value = '';
    }
    
    // 모달 제목 설정
    const modalTitle = document.getElementById('modalTitle');
    if (modalTitle) {
      modalTitle.innerHTML = '<i class="fas fa-pen"></i> 인수인계 작성';
    }
    
    state.isEditing = false;
    
    // 모달 표시
    Modal.show('handoverCreateModal');
  }
  
  /**
   * 인수인계를 수정합니다.
   * @param {string} id - 인수인계 ID
   */
  async function editHandover(id) {
    try {
      state.isEditing = true;
      
      // 모달 제목 설정
      const modalTitle = document.getElementById('modalTitle');
      if (modalTitle) {
        modalTitle.innerHTML = '<i class="fas fa-edit"></i> 인수인계 수정';
      }
      
      // 로딩 표시
      Utils.toggleLoading(true);
      
      // 인수인계 데이터 로드
      const response = await API.get(`/handover/items/${id}`);
      
      if (response.success) {
        // 폼에 데이터 채우기
        const form = document.getElementById('handoverForm');
        if (form) {
          document.getElementById('handoverId').value = response.item.id;
          document.getElementById('title').value = response.item.title;
          document.getElementById('content').value = response.item.content;
          
          // 공지사항 체크박스 (관리자만 해당)
          const isNoticeCheckbox = document.getElementById('isNotice');
          if (isNoticeCheckbox) {
            isNoticeCheckbox.checked = response.item.is_notice;
          }
        }
        
        // 모달 표시
        Modal.show('handoverCreateModal');
      } else {
        Alerts.error(response.message || '인수인계 정보를 불러오는데 실패했습니다.');
      }
    } catch (error) {
      console.error('[Handover] 인수인계 수정 중 오류:', error);
      Alerts.error('인수인계 정보를 불러오는데 실패했습니다.');
    } finally {
      // 로딩 숨김
      Utils.toggleLoading(false);
    }
  }
  
  /**
   * 인수인계 상세 정보를 조회합니다.
   * @param {string} id - 인수인계 ID
   */
  async function viewHandover(id) {
    try {
      // 로딩 표시
      const loader = document.querySelector('.modal-loader');
      if (loader) {
        loader.style.display = 'flex';
      }
      
      // 내용 영역 초기화
      const contentDiv = document.getElementById('handoverDetailContent');
      if (contentDiv) {
        contentDiv.innerHTML = '';
      }
      
      // 액션 버튼 초기화
      const actionsDiv = document.getElementById('detailModalActions');
      if (actionsDiv) {
        actionsDiv.innerHTML = '';
      }
      
      // 모달 표시
      Modal.show('handoverDetailModal');
      
      // 인수인계 데이터 로드
      const response = await API.get(`/handover/items/${id}`);
      
      if (response.success) {
        state.currentHandover = response.item;
        
        // 상세 정보 표시
        if (contentDiv) {
          const item = response.item;
          
          // 공지사항 태그 표시
          const noticeTag = item.is_notice ? 
            '<span class="notice-tag"><i class="fas fa-bullhorn"></i> 공지사항</span>' : '';
          
          // HTML 이스케이프 및 줄바꿈 처리
          const content = Utils.escapeHtml(item.content).replace(/\n/g, '<br>');
          
          contentDiv.innerHTML = `
            <div class="detail-header">
              <h2 class="detail-title">${Utils.escapeHtml(item.title)} ${noticeTag}</h2>
              <div class="detail-meta">
                <span class="writer"><i class="fas fa-user"></i> ${Utils.escapeHtml(item.writer)}</span>
                <span class="date"><i class="fas fa-clock"></i> ${Utils.formatDate(item.update_at, 'YYYY-MM-DD HH:mm')}</span>
              </div>
            </div>
            <div class="detail-content">
              ${content}
            </div>
          `;
        }
        
        // 수정/삭제 버튼 (작성자 또는 관리자만 표시)
        if (actionsDiv && (response.item.editable || (Auth && Auth.hasRole('ADMIN')))) {
          actionsDiv.innerHTML = `
            <button class="btn btn-primary" onclick="Handover.editHandover('${id}')">수정하기</button>
            <button class="btn btn-danger" onclick="Handover.deleteHandover('${id}')">삭제하기</button>
          `;
        }
      } else {
        Alerts.error(response.message || '인수인계 정보를 불러오는데 실패했습니다.');
      }
    } catch (error) {
      console.error('[Handover] 인수인계 상세 조회 중 오류:', error);
      Alerts.error('인수인계 정보를 불러오는데 실패했습니다.');
    } finally {
      // 로딩 숨김
      const loader = document.querySelector('.modal-loader');
      if (loader) {
        loader.style.display = 'none';
      }
    }
  }
  
  /**
   * 인수인계 폼을 제출합니다.
   */
  async function submitHandoverForm() {
    const form = document.getElementById('handoverForm');
    if (!form) return;
    
    // 유효성 검사
    if (!validateForm(form)) {
      return;
    }
    
    try {
      // 로딩 표시
      Utils.toggleLoading(true);
      
      // 폼 데이터 수집
      const formData = Utils.getFormData(form);
      
      // 체크박스 특수 처리 (is_notice)
      if (formData.is_notice === 'on') {
        formData.is_notice = true;
      }
      
      // API 호출 URL 및 메서드 설정
      const id = document.getElementById('handoverId').value;
      const isUpdate = id && state.isEditing;
      
      // API 호출
      let response;
      if (isUpdate) {
        response = await API.put(`/handover/items/${id}`, formData);
      } else {
        response = await API.post('/handover/items', formData);
      }
      
      if (response.success) {
        // 모달 닫기
        Modal.hide('handoverCreateModal');
        
        // 성공 메시지 표시
        const message = isUpdate ? 
          '인수인계가 성공적으로 수정되었습니다.' : 
          '인수인계가 성공적으로 작성되었습니다.';
        
        Alerts.success(message);
        
        // 페이지 새로고침 (데이터 갱신)
        setTimeout(() => {
          window.location.reload();
        }, 1000);
      } else {
        Alerts.error(response.message || '인수인계 저장에 실패했습니다.');
      }
    } catch (error) {
      console.error('[Handover] 인수인계 저장 중 오류:', error);
      Alerts.error('인수인계 저장 중 오류가 발생했습니다.');
    } finally {
      // 로딩 숨김
      Utils.toggleLoading(false);
    }
  }
  
  /**
   * 인수인계 삭제 모달을 엽니다.
   * @param {string} id - 인수인계 ID
   */
  function deleteHandover(id) {
    // 삭제할 ID 설정
    const idField = document.getElementById('deleteHandoverId');
    if (idField) {
      idField.value = id;
    }
    
    // 모달 닫기 (이전 모달이 열려있을 경우)
    closeModal();
    
    // 삭제 확인 모달 표시
    Modal.show('deleteConfirmModal');
  }
  
  /**
   * 인수인계 삭제를 확인합니다.
   */
  async function confirmDelete() {
    const id = document.getElementById('deleteHandoverId').value;
    if (!id) return;
    
    try {
      // 로딩 표시
      Utils.toggleLoading(true);
      
      // API 호출
      const response = await API.delete(`/handover/items/${id}`);
      
      if (response.success) {
        // 모달 닫기
        Modal.hide('deleteConfirmModal');
        
        // 성공 메시지 표시
        Alerts.success('인수인계가 성공적으로 삭제되었습니다.');
        
        // 페이지 새로고침 (데이터 갱신)
        setTimeout(() => {
          window.location.reload();
        }, 1000);
      } else {
        Alerts.error(response.message || '인수인계 삭제에 실패했습니다.');
      }
    } catch (error) {
      console.error('[Handover] 인수인계 삭제 중 오류:', error);
      Alerts.error('인수인계 삭제 중 오류가 발생했습니다.');
    } finally {
      // 로딩 숨김
      Utils.toggleLoading(false);
    }
  }
  
  /**
   * 모달을 닫습니다.
   */
  function closeModal() {
    // 모든 모달 숨기기
    document.querySelectorAll('.modal').forEach(modal => {
      modal.style.display = 'none';
    });
  }
  
  /**
   * 폼 유효성을 검사합니다.
   * @param {HTMLFormElement} form - 폼 요소
   * @returns {boolean} - 유효성 검사 결과
   */
  function validateForm(form) {
    if (!form || !(form instanceof HTMLFormElement)) {
      return false;
    }
    
    // 기본 브라우저 검증 사용
    if (!form.checkValidity()) {
      form.reportValidity();
      return false;
    }
    
    return true;
  }
  
  // 전역 함수 노출 (원래 함수는 유지하되, 클로저의 함수로 처리)
  window.openCreateModal = openCreateModal;
  window.editHandover = function(id) { editHandover(id); };
  window.viewHandover = function(id) { viewHandover(id); };
  window.deleteHandover = function(id) { deleteHandover(id); };
  window.confirmDelete = confirmDelete;
  window.closeModal = closeModal;
  window.togglePanel = togglePanel;
  
  // 공개 API
  return {
    init,
    openCreateModal,
    editHandover,
    viewHandover,
    deleteHandover,
    confirmDelete,
    closeModal,
    togglePanel
  };
})();