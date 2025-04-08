/**
 * 인수인계 페이지 모듈
 */
const HandoverPage = {
  // 페이지 상태 관리
  state: {
    // 공지사항 상태
    notice: {
      currentPage: 1,
      pageSize: 10,
      totalPages: 1,
      currentData: [],
      filteredData: [],
    },
    // 인수인계 상태
    handover: {
      currentPage: 1,
      pageSize: 10,
      totalPages: 1,
      currentData: [],
      filteredData: [],
    },
    // 현재 활성화된 탭
    activeTab: 'notice-section',
    // 현재 편집 중인 인수인계 ID
    editingHandoverId: null,
    // 모달이 수정 모드인지 여부
    isEditMode: false,
  },

  /**
   * 페이지 초기화
   */
  init: function () {
    console.log('인수인계 페이지 초기화...');

    // 이벤트 리스너 등록
    this.registerEventListeners();

    // 데이터 로드되었으면 테이블 업데이트
    if (TMS.store.isDataLoaded) {
      this.updateLists();
    } else {
      // 데이터 로드 대기
      document.addEventListener('tms:dataLoaded', () => {
        this.updateLists();
      });
    }

    // 데이터 변경 이벤트 리스닝
    document.addEventListener('tms:handoverDataChanged', () => {
      this.updateLists();
    });
  },

  /**
   * 이벤트 리스너 등록
   */
  registerEventListeners: function () {
    // 탭 전환
    document.querySelectorAll('.tab').forEach((tab) => {
      tab.addEventListener('click', this.handleTabChange.bind(this));
    });

    // 액션 버튼
    document
      .getElementById('refreshHandoverBtn')
      .addEventListener('click', this.refreshData.bind(this));
    document
      .getElementById('newHandoverBtn')
      .addEventListener('click', this.openNewHandoverModal.bind(this));

    // 페이지네이션 - 공지사항
    document
      .querySelectorAll('.page-btn[data-section="notice"]')
      .forEach((btn) => {
        btn.addEventListener('click', (e) => {
          const direction = e.currentTarget.getAttribute('data-page');
          this.handlePageChange(direction, 'notice');
        });
      });

    // 페이지네이션 - 인수인계
    document
      .querySelectorAll('.page-btn[data-section="handover"]')
      .forEach((btn) => {
        btn.addEventListener('click', (e) => {
          const direction = e.currentTarget.getAttribute('data-page');
          this.handlePageChange(direction, 'handover');
        });
      });

    // 모달 버튼
    document
      .getElementById('submitHandoverBtn')
      .addEventListener('click', this.handleSubmitHandover.bind(this));
    document
      .getElementById('editHandoverBtn')
      .addEventListener('click', this.openEditModal.bind(this));
    document
      .getElementById('deleteHandoverBtn')
      .addEventListener('click', this.confirmDeleteHandover.bind(this));
  },

  /**
   * 탭 변경 처리
   */
  handleTabChange: function (e) {
    const tabName = e.currentTarget.getAttribute('data-tab');

    // 모든 탭에서 active 클래스 제거
    document.querySelectorAll('.tab').forEach((tab) => {
      tab.classList.remove('active');
    });

    // 클릭한 탭에 active 클래스 추가
    e.currentTarget.classList.add('active');

    // 모든 컨텐츠 섹션 숨기기
    document.querySelectorAll('.content-section').forEach((section) => {
      section.classList.remove('active');
    });

    // 해당 탭의 컨텐츠 섹션 표시
    document.getElementById(tabName).classList.add('active');

    // 현재 활성화된 탭 상태 저장
    this.state.activeTab = tabName;
  },

  /**
   * 모든 목록 업데이트
   */
  updateLists: function () {
    // 데이터 필터링
    this.filterData();

    // 공지사항 목록 업데이트
    this.updateCurrentPageData('notice');
    this.renderTable('notice');
    this.updatePagination('notice');

    // 인수인계 목록 업데이트
    this.updateCurrentPageData('handover');
    this.renderTable('handover');
    this.updatePagination('handover');
  },

  /**
   * 데이터 필터링
   */
  filterData: function () {
    // 전체 데이터 가져오기
    const allData = TMS.getHandoverData();

    // 최신순 정렬
    allData.sort((a, b) => {
      return new Date(b.created_at) - new Date(a.created_at);
    });

    // 공지사항 필터링
    this.state.notice.filteredData = allData.filter(
      (item) => item.is_notice === true
    );

    // 인수인계 필터링
    this.state.handover.filteredData = allData.filter(
      (item) => item.is_notice === false
    );
  },

  /**
   * 현재 페이지 데이터 업데이트
   */
  updateCurrentPageData: function (section) {
    const state = this.state[section];
    const start = (state.currentPage - 1) * state.pageSize;
    const end = start + state.pageSize;

    state.currentData = state.filteredData.slice(start, end);
    state.totalPages =
      Math.ceil(state.filteredData.length / state.pageSize) || 1;

    // 페이지가 범위를 벗어나면 첫 페이지로
    if (state.currentPage > state.totalPages) {
      state.currentPage = 1;
      this.updateCurrentPageData(section);
    }
  },

  /**
   * 테이블 렌더링
   */
  renderTable: function (section) {
    const tableId =
      section === 'notice' ? 'noticeTableBody' : 'handoverTableBody';
    const tableBody = document.getElementById(tableId);
    const state = this.state[section];

    // 테이블 내용 초기화
    tableBody.innerHTML = '';

    // 데이터가 없는 경우
    if (state.currentData.length === 0) {
      const emptyRow = document.createElement('tr');
      emptyRow.innerHTML = `<td colspan="4" class="empty-table">조회된 ${
        section === 'notice' ? '공지사항' : '인수인계'
      }이 없습니다.</td>`;
      tableBody.appendChild(emptyRow);
      return;
    }

    // 행 추가
    state.currentData.forEach((item) => {
      const row = document.createElement('tr');
      row.setAttribute('data-id', item.handover_id);

      // 작성자 셀
      const authorCell = document.createElement('td');
      authorCell.textContent = item.created_by;
      row.appendChild(authorCell);

      // 작성일시 셀
      const dateCell = document.createElement('td');
      dateCell.textContent = this.formatDateString(item.created_at);
      row.appendChild(dateCell);

      // 제목 셀
      const titleCell = document.createElement('td');
      titleCell.className = 'title-cell';
      const titleText = document.createElement('span');
      titleText.className = 'text-ellipsis';
      titleText.textContent = item.title;
      titleCell.appendChild(titleText);
      row.appendChild(titleCell);

      // 내용 셀
      const contentCell = document.createElement('td');
      contentCell.className = 'content-cell';
      const contentText = document.createElement('span');
      contentText.className = 'text-ellipsis';
      contentText.textContent = item.content.replace(/\n/g, ' '); // 줄바꿈 제거
      contentCell.appendChild(contentText);
      row.appendChild(contentCell);

      // 클릭 이벤트 리스너
      row.addEventListener('click', () => {
        this.openDetailModal(item.handover_id);
      });

      tableBody.appendChild(row);
    });
  },

  /**
   * 날짜 문자열 포맷팅
   */
  formatDateString: function (dateStr) {
    if (!dateStr) return '';

    try {
      const date = new Date(dateStr.replace(' ', 'T'));
      return date.toLocaleDateString('ko-KR');
    } catch (e) {
      return dateStr;
    }
  },

  /**
   * 페이지네이션 업데이트
   */
  updatePagination: function (section) {
    const state = this.state[section];
    const infoId = section === 'notice' ? 'noticePageInfo' : 'handoverPageInfo';

    document.getElementById(
      infoId
    ).textContent = `${state.currentPage} / ${state.totalPages}`;
  },

  /**
   * 페이지 변경 처리
   */
  handlePageChange: function (direction, section) {
    const state = this.state[section];

    if (direction === 'prev' && state.currentPage > 1) {
      state.currentPage--;
    } else if (direction === 'next' && state.currentPage < state.totalPages) {
      state.currentPage++;
    }

    this.updateCurrentPageData(section);
    this.renderTable(section);
    this.updatePagination(section);
  },

  /**
   * 데이터 새로고침 처리
   */
  refreshData: function () {
    // 인수인계 데이터 다시 로드
    TMS.initHandoverData();
    // 화면 업데이트는 이벤트로 자동 처리

    messageUtils.success('목록이 새로고침되었습니다.');
  },

  /**
   * 상세 모달 열기
   */
  openDetailModal: function (handoverId) {
    const item = TMS.getHandoverItemById(handoverId);

    if (!item) {
      messageUtils.error('정보를 찾을 수 없습니다.');
      return;
    }

    // 모달 제목 설정
    const modalTitle = item.is_notice
      ? '공지사항 상세 정보'
      : '인수인계 상세 정보';
    document.getElementById('detailTitle').textContent = modalTitle;

    // 모달 데이터 채우기
    document.getElementById('detailTitle2').textContent = item.title || '-';
    document.getElementById('detailAuthor').textContent =
      item.created_by || '-';

    // 날짜 포맷팅
    const dateStr = item.created_at;
    const dateDisplay = dateStr ? this.formatDateString(dateStr) : '-';
    document.getElementById('detailDate').textContent = dateDisplay;

    // 공지여부
    document.getElementById('detailIsNotice').textContent = item.is_notice
      ? '예'
      : '아니오';

    // 내용
    document.getElementById('detailContent').textContent = item.content || '-';

    // 선택된 인수인계 ID 저장
    this.selectedHandoverId = handoverId;

    // 모달 열기
    modalUtils.openModal('handoverDetailModal');

    // 권한 체크 (본인이 작성한 경우만 수정/삭제 가능)
    const currentUser = TMS.store.userData.userName;
    const editBtn = document.getElementById('editHandoverBtn');
    const deleteBtn = document.getElementById('deleteHandoverBtn');

    const isAuthor = currentUser === item.created_by;
    editBtn.style.display = isAuthor ? 'inline-block' : 'none';
    deleteBtn.style.display = isAuthor ? 'inline-block' : 'none';
  },

  /**
   * 수정 모달 열기
   */
  openEditModal: function () {
    const handoverId = this.selectedHandoverId;
    if (!handoverId) return;

    const item = TMS.getHandoverItemById(handoverId);
    if (!item) return;

    // 모달 제목 변경
    document.getElementById('handoverModalTitle').textContent = '인수인계 수정';
    document.getElementById('submitBtnText').textContent = '수정하기';

    // ID를 hidden 필드에 저장
    document.getElementById('handoverId').value = handoverId;

    // 폼 필드에 데이터 채우기
    document.getElementById('handoverTitle').value = item.title;
    document.getElementById('handoverContent').value = item.content;

    // 공지 여부 설정
    document.getElementById('isNotice').checked = item.is_notice;

    // 수정 모드로 설정
    this.state.isEditMode = true;

    // 상세 모달 닫기 및 수정 모달 열기
    modalUtils.closeModal('handoverDetailModal');
    modalUtils.openModal('newHandoverModal');
  },

  /**
   * 인수인계 등록 모달 열기
   */
  openNewHandoverModal: function () {
    // 모달 제목 변경
    document.getElementById('handoverModalTitle').textContent = '인수인계 등록';
    document.getElementById('submitBtnText').textContent = '등록하기';

    // 입력 필드 초기화
    document.getElementById('handoverId').value = '';
    document.getElementById('handoverTitle').value = '';
    document.getElementById('handoverContent').value = '';
    document.getElementById('isNotice').checked = false;

    // 신규 등록 모드로 설정
    this.state.isEditMode = false;

    // 모달 열기
    modalUtils.openModal('newHandoverModal');
  },

  /**
   * 인수인계 등록/수정 처리
   */
  handleSubmitHandover: function () {
    // 입력 값 가져오기
    const handoverId = document.getElementById('handoverId').value.trim();
    const title = document.getElementById('handoverTitle').value.trim();
    const content = document.getElementById('handoverContent').value.trim();
    const isNotice = document.getElementById('isNotice').checked;

    // 필수 필드 확인
    if (!title || !content) {
      messageUtils.warning('제목과 내용을 입력해주세요.');
      return;
    }

    if (this.state.isEditMode) {
      // 수정 로직
      this.updateHandoverItem(handoverId, {
        title,
        content,
        is_notice: isNotice,
      });
    } else {
      // 신규 등록 로직
      this.createNewHandover({
        title,
        content,
        is_notice: isNotice,
      });
    }

    // 모달 닫기
    modalUtils.closeModal('newHandoverModal');
  },

  /**
   * 새 인수인계 생성
   */
  createNewHandover: function (data) {
    // 데이터 생성
    const newHandover = {
      handover_id: 'H' + Date.now(),
      title: data.title,
      content: data.content,
      is_notice: data.is_notice,
      created_by: TMS.store.userData.userName,
      created_at: new Date().toISOString(),
    };

    // 스토어에 추가
    if (!TMS.store.handoverData) {
      TMS.store.handoverData = [];
    }

    TMS.store.handoverData.push(newHandover);

    // 변경 이벤트 발생
    document.dispatchEvent(new CustomEvent('tms:handoverDataChanged'));

    // 성공 메시지
    messageUtils.success(
      `${data.is_notice ? '공지사항' : '인수인계'}이 등록되었습니다.`
    );

    // 공지사항일 경우 공지 탭으로 전환
    if (data.is_notice && this.state.activeTab !== 'notice-section') {
      document.querySelector('.tab[data-tab="notice-section"]').click();
    }
    // 인수인계일 경우 인수인계 탭으로 전환
    else if (!data.is_notice && this.state.activeTab !== 'handover-section') {
      document.querySelector('.tab[data-tab="handover-section"]').click();
    }
  },

  /**
   * 인수인계 항목 수정
   */
  updateHandoverItem: function (handoverId, data) {
    // 기존 데이터 가져오기
    const index = TMS.store.handoverData.findIndex(
      (item) => item.handover_id === handoverId
    );

    if (index === -1) {
      messageUtils.error('수정할 항목을 찾을 수 없습니다.');
      return false;
    }

    // 기존 데이터 복사 및 수정
    const updatedItem = {
      ...TMS.store.handoverData[index],
      title: data.title,
      content: data.content,
      is_notice: data.is_notice,
    };

    // 데이터 업데이트
    TMS.store.handoverData[index] = updatedItem;

    // 변경 이벤트 발생
    document.dispatchEvent(new CustomEvent('tms:handoverDataChanged'));

    // 성공 메시지
    messageUtils.success('정보가 수정되었습니다.');

    // 공지여부가 변경된 경우 해당 탭으로 전환
    if (data.is_notice && this.state.activeTab !== 'notice-section') {
      document.querySelector('.tab[data-tab="notice-section"]').click();
    } else if (!data.is_notice && this.state.activeTab !== 'handover-section') {
      document.querySelector('.tab[data-tab="handover-section"]').click();
    }

    return true;
  },

  /**
   * 삭제 확인
   */
  confirmDeleteHandover: function () {
    const handoverId = this.selectedHandoverId;
    if (!handoverId) return;

    const item = TMS.getHandoverItemById(handoverId);
    if (!item) {
      messageUtils.error('삭제할 항목을 찾을 수 없습니다.');
      return;
    }

    // 삭제 확인
    if (
      confirm(
        `정말로 이 ${
          item.is_notice ? '공지사항' : '인수인계'
        }을 삭제하시겠습니까?`
      )
    ) {
      this.deleteHandoverItem(handoverId);
    }
  },

  /**
   * 인수인계 항목 삭제
   */
  deleteHandoverItem: function (handoverId) {
    // 기존 데이터 가져오기
    const index = TMS.store.handoverData.findIndex(
      (item) => item.handover_id === handoverId
    );

    if (index === -1) {
      messageUtils.error('삭제할 항목을 찾을 수 없습니다.');
      return false;
    }

    // 데이터 삭제
    const deletedItem = TMS.store.handoverData.splice(index, 1)[0];

    // 모달 닫기
    modalUtils.closeModal('handoverDetailModal');

    // 변경 이벤트 발생
    document.dispatchEvent(new CustomEvent('tms:handoverDataChanged'));

    // 성공 메시지
    messageUtils.success(
      `${deletedItem.is_notice ? '공지사항' : '인수인계'}이 삭제되었습니다.`
    );

    return true;
  },
};

// 전역 객체에 페이지 모듈 할당
window.HandoverPage = HandoverPage;

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', function () {
  HandoverPage.init();
});
