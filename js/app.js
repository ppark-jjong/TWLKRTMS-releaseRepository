/**
 * 공통 애플리케이션 코드
 * 모든 페이지에서 공유되는 기능을 제공합니다.
 */

// TMS 애플리케이션 네임스페이스
const TMS = {
  // 앱 상태 저장소
  store: {
    dashboardData: null,
    handoverData: [],
    userData: {
      userName: 'CSAdmin',
      userRole: 'CS',
    },
    isDataLoaded: false,
  },

  /**
   * 애플리케이션 초기화 함수
   */
  init: async function () {
    console.log('TMS 애플리케이션 초기화 중...');

    // 공통 UI 요소 초기화
    this.initCommonUI();

    // 데이터 로드
    await this.loadData();

    // 현재 페이지 식별 및 초기화
    this.initCurrentPage();

    console.log('TMS 애플리케이션 초기화 완료');
  },

  /**
   * 공통 UI 요소 초기화
   */
  initCommonUI: function () {
    // 로그아웃 버튼 이벤트
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
      logoutBtn.addEventListener('click', function () {
        if (confirm('로그아웃 하시겠습니까?')) {
          messageUtils.success('로그아웃되었습니다.');
          setTimeout(() => {
            window.location.reload();
          }, 1500);
        }
      });
    }

    // 사용자 정보 업데이트
    const userDisplayName = document.getElementById('userDisplayName');
    const userDisplayRole = document.getElementById('userDisplayRole');

    if (userDisplayName) {
      userDisplayName.textContent = this.store.userData.userName;
    }

    if (userDisplayRole) {
      userDisplayRole.textContent = this.store.userData.userRole;
    }

    // 데이터 관리 기능 초기화
    this.initDataManagement();

    // 모달 초기화
    modalUtils.initModals();
  },

  /**
   * 데이터 관리 기능 초기화
   */
  initDataManagement: function () {
    // 데이터 초기화 기능 삭제
  },

  /**
   * 데이터 로드 함수
   */
  loadData: async function () {
    try {
      console.log('데이터 로드 중...');

      // 대시보드 데이터 로드
      await this.loadDashboardData();

      // 인수인계 데이터 로드
      await this.initHandoverData();

      // 데이터 로드 상태 업데이트
      this.store.isDataLoaded = true;
      console.log('모든 데이터 로드 완료');

      // 커스텀 이벤트 발생 - 데이터 로드 완료
      document.dispatchEvent(new CustomEvent('tms:dataLoaded'));

      return true;
    } catch (error) {
      console.error('데이터 로드 오류:', error);
      messageUtils.error('데이터를 불러오는 중 오류가 발생했습니다.');
      return false;
    }
  },

  /**
   * 대시보드 데이터 로드
   */
  loadDashboardData: async function () {
    try {
      // 1. 먼저 localStorage에서 데이터 확인
      const savedData = localStorage.getItem('tms_dashboard_data');

      if (savedData) {
        try {
          const parsedData = JSON.parse(savedData);
          if (
            parsedData &&
            parsedData.dashboard &&
            Array.isArray(parsedData.dashboard)
          ) {
            console.log('localStorage에서 대시보드 데이터 로드 성공');
            this.store.dashboardData = parsedData.dashboard;
            console.log(
              `대시보드 데이터 ${this.store.dashboardData.length}건 로드 완료`
            );

            // 데이터가 변경되었음을 알리는 이벤트
            document.dispatchEvent(new CustomEvent('tms:dashboardDataChanged'));
            return;
          }
        } catch (localStorageError) {
          console.warn('localStorage 데이터 파싱 오류:', localStorageError);
        }
      }

      // 2. localStorage에 데이터가 없거나 유효하지 않은 경우 JSON 파일 로드
      console.log('JSON 파일에서 대시보드 데이터 로드 시도...');
      const response = await fetch('dashboard_data.json');

      if (!response.ok) {
        throw new Error(
          `대시보드 데이터 로드 실패: ${response.status} ${response.statusText}`
        );
      }

      const data = await response.json();

      if (data && data.dashboard && Array.isArray(data.dashboard)) {
        // 데이터 정규화 및 저장
        this.store.dashboardData = data.dashboard.map((item) => {
          // 필요한 경우 데이터 보강
          if (!item.dashboard_id) {
            item.dashboard_id = `D${Math.floor(Math.random() * 10000)
              .toString()
              .padStart(4, '0')}`;
          }

          // 날짜 필드 보강
          if (item.eta && typeof item.eta === 'string') {
            item.eta_date = new Date(item.eta);
          }
          if (item.create_time && typeof item.create_time === 'string') {
            item.create_date = new Date(item.create_time);
          }

          return item;
        });

        console.log(
          `JSON 파일에서 대시보드 데이터 ${this.store.dashboardData.length}건 로드 완료`
        );

        // JSON에서 로드한 데이터를 localStorage에도 저장하여 다음에 사용할 수 있게 함
        this.saveDashboardData();

        // 데이터가 변경되었음을 알리는 이벤트
        document.dispatchEvent(new CustomEvent('tms:dashboardDataChanged'));
      } else {
        console.warn('대시보드 데이터 형식이 유효하지 않습니다.');
        this.store.dashboardData = [];
      }
    } catch (error) {
      console.error('대시보드 데이터 로드 실패:', error);
      this.store.dashboardData = [];
    }
  },

  /**
   * 인수인계 데이터 초기화 및 로드
   */
  initHandoverData: async function () {
    try {
      // handover_data.json 파일에서 데이터 로드 시도
      const response = await fetch('handover_data.json');

      if (!response.ok) {
        throw new Error(
          `인수인계 데이터 로드 실패: ${response.status} ${response.statusText}`
        );
      }

      const data = await response.json();

      if (data && data.handovers && Array.isArray(data.handovers)) {
        this.store.handoverData = data.handovers;
        console.log(
          `인수인계 데이터 ${this.store.handoverData.length}건 로드 완료`
        );
      } else {
        console.warn(
          '인수인계 데이터 형식이 유효하지 않습니다. 기본 데이터를 사용합니다.'
        );
        this.initDefaultHandoverData();
      }
    } catch (error) {
      console.error('인수인계 데이터 로드 실패:', error);
      // 파일 로드 실패 시 기본 데이터 사용
      this.initDefaultHandoverData();
    }

    // 데이터가 변경되었음을 알리는 이벤트
    document.dispatchEvent(new CustomEvent('tms:handoverDataChanged'));
  },

  /**
   * 기본 인수인계 데이터 초기화 (파일 로드 실패 시 사용)
   */
  initDefaultHandoverData: function () {
    // 기본 인수인계 데이터
    this.store.handoverData = [
      {
        handover_id: 'H001',
        title: '서버 점검 안내',
        category: '일반',
        priority: 'MEDIUM',
        content:
          '오늘 저녁 10시부터 서버 점검이 예정되어 있습니다. 업무에 참고 바랍니다.',
        created_by: 'CSAdmin',
        created_at: '2025-03-05 14:30',
        confirmations: [{ user: 'CSAdmin', confirmed_at: '2025-03-05 14:35' }],
      },
      {
        handover_id: 'H002',
        title: '배송 지연 안내',
        category: '배송',
        priority: 'HIGH',
        content:
          '도로 공사로 인해 강남 지역 배송이 지연될 수 있습니다. 고객에게 미리 안내 바랍니다.',
        created_by: 'CSAdmin',
        created_at: '2025-03-06 09:15',
        confirmations: [],
      },
      {
        handover_id: 'H003',
        title: '안전 교육 일정 안내',
        category: '안전',
        priority: 'MEDIUM',
        content:
          '3월 10일 오전 10시 안전 교육이 진행될 예정입니다. 전 직원 참석 필수입니다.',
        created_by: 'CSAdmin',
        created_at: '2025-03-06 11:20',
        confirmations: [],
      },
    ];

    console.log(
      `기본 인수인계 데이터 ${this.store.handoverData.length}건 초기화 완료`
    );
  },

  /**
   * 현재 페이지 식별 및 초기화
   */
  initCurrentPage: function () {
    const pathname = window.location.pathname;

    if (pathname.includes('handover.html')) {
      console.log('현재 페이지: 인수인계');
      // 인수인계 페이지 모듈이 있으면 초기화
      if (window.HandoverPage) {
        window.HandoverPage.init();
      }
    } else if (pathname.includes('visualization.html')) {
      console.log('현재 페이지: 시각화');
      // 시각화 페이지 모듈이 있으면 초기화
      if (window.VisualizationPage) {
        window.VisualizationPage.init();
      }
    } else {
      console.log('현재 페이지: 대시보드');
      // 대시보드 페이지 모듈이 있으면 초기화
      if (window.DashboardPage) {
        window.DashboardPage.init();
      }
    }
  },

  /**
   * 대시보드 데이터 가져오기
   */
  getDashboardData: function (filters = {}) {
    if (!this.store.dashboardData) {
      console.warn('대시보드 데이터가 로드되지 않았습니다.');
      return [];
    }

    console.log('TMS.getDashboardData 필터링 시작:', filters);
    let filteredData = [...this.store.dashboardData];
    console.log(`필터링 전 전체 데이터: ${filteredData.length}건`);

    // 상태 필터 적용
    if (filters.status) {
      console.log(`상태 필터 적용: ${filters.status}`);
      filteredData = filteredData.filter(
        (item) => item.status === filters.status
      );
      console.log(`상태 필터 후 데이터: ${filteredData.length}건`);
    }

    // 부서 필터 적용
    if (filters.department) {
      console.log(`부서 필터 적용: ${filters.department}`);
      filteredData = filteredData.filter(
        (item) => item.department === filters.department
      );
      console.log(`부서 필터 후 데이터: ${filteredData.length}건`);
    }

    // 창고 필터 적용
    if (filters.warehouse) {
      console.log(`창고 필터 적용: ${filters.warehouse}`);
      filteredData = filteredData.filter(
        (item) => item.warehouse === filters.warehouse
      );
      console.log(`창고 필터 후 데이터: ${filteredData.length}건`);
    }

    // 키워드 검색 적용
    if (filters.keyword) {
      const keyword = filters.keyword.toLowerCase();
      console.log(`키워드 검색 적용: ${keyword}`);

      filteredData = filteredData.filter((item) => {
        const orderNo = String(item.order_no || '').toLowerCase();
        const customer = String(item.customer || '').toLowerCase();
        return orderNo.includes(keyword) || customer.includes(keyword);
      });

      console.log(`키워드 검색 후 데이터: ${filteredData.length}건`);
    }

    // 날짜 필터 적용
    if (filters.startDate && filters.endDate) {
      console.log(`날짜 필터 적용: ${filters.startDate} ~ ${filters.endDate}`);
      const startDate = new Date(filters.startDate);
      const endDate = new Date(filters.endDate);
      endDate.setHours(23, 59, 59, 999); // 종료일 끝까지 포함

      filteredData = filteredData.filter((item) => {
        if (!item.eta) {
          return false;
        }

        const etaDate = new Date(item.eta);
        if (isNaN(etaDate.getTime())) {
          console.log(
            `날짜 변환 실패: ${item.eta}, 주문번호: ${item.order_no}`
          );
          return false;
        }

        return etaDate >= startDate && etaDate <= endDate;
      });

      console.log(`날짜 필터 후 데이터: ${filteredData.length}건`);
    }

    console.log(`최종 필터링된 데이터: ${filteredData.length}건`);
    return filteredData;
  },

  /**
   * 대시보드 항목을 ID로 가져오기
   */
  getDashboardItemById: function (orderId) {
    if (!this.store.dashboardData || !orderId) {
      return null;
    }

    return (
      this.store.dashboardData.find((item) => item.order_no === orderId) || null
    );
  },

  /**
   * 대시보드 항목 업데이트
   */
  updateDashboardItem: function (orderId, updateData) {
    if (!this.store.dashboardData || !orderId) {
      return false;
    }

    const index = this.store.dashboardData.findIndex(
      (item) => item.order_no === orderId
    );

    if (index === -1) {
      console.warn(`주문 ID '${orderId}'를 찾을 수 없습니다.`);
      return false;
    }

    try {
      // 기존 데이터에 업데이트 적용
      this.store.dashboardData[index] = {
        ...this.store.dashboardData[index],
        ...updateData,
        update_at: new Date().toISOString(),
        updated_by: this.store.userData.userName,
      };

      // 변경 이벤트 발생
      document.dispatchEvent(new CustomEvent('tms:dashboardDataChanged'));

      return true;
    } catch (error) {
      console.error('대시보드 항목 업데이트 실패:', error);
      return false;
    }
  },

  /**
   * 인수인계 데이터 가져오기
   */
  getHandoverData: function (filters = {}) {
    if (!this.store.handoverData) {
      console.warn('인수인계 데이터가 로드되지 않았습니다.');
      return [];
    }

    // 필터 적용이 필요한 경우
    if (filters && (filters.priority || filters.keyword)) {
      return this.store.handoverData.filter((item) => {
        // 우선순위 필터
        if (filters.priority && filters.priority !== '') {
          if (item.priority !== filters.priority) {
            return false;
          }
        }

        // 검색어 필터
        if (filters.keyword && filters.keyword !== '') {
          const keyword = filters.keyword.toLowerCase();
          return (
            item.title.toLowerCase().includes(keyword) ||
            item.content.toLowerCase().includes(keyword)
          );
        }

        return true;
      });
    }

    // 필터 없는 경우 모든 데이터 반환
    return this.store.handoverData;
  },

  /**
   * ID로 인수인계 항목 가져오기
   */
  getHandoverItemById: function (handoverId) {
    if (!this.store.handoverData) {
      console.warn('인수인계 데이터가 로드되지 않았습니다.');
      return null;
    }

    return (
      this.store.handoverData.find((item) => item.handover_id === handoverId) ||
      null
    );
  },

  /**
   * 새 인수인계 추가
   */
  addHandoverItem: function (handoverData) {
    if (!this.store.handoverData) {
      this.store.handoverData = [];
    }

    // 새 인수인계 ID 생성
    const newId = `H${String(this.store.handoverData.length + 1).padStart(
      3,
      '0'
    )}`;

    // 현재 날짜/시간
    const now = new Date();
    const dateStr = now.toISOString().replace('T', ' ').substring(0, 16);

    // 새 인수인계 객체 생성
    const newHandover = {
      handover_id: newId,
      title: handoverData.title,
      priority: handoverData.priority || '일반',
      content: handoverData.content,
      created_by: this.store.userData.userName,
      created_at: dateStr,
    };

    // 배열에 추가
    this.store.handoverData.push(newHandover);

    // 변경 이벤트 발생
    document.dispatchEvent(new CustomEvent('tms:handoverDataChanged'));

    return newHandover;
  },

  /**
   * 대시보드 데이터 저장 함수
   * 변경된 데이터를 localStorage에 저장하여 지속성 유지
   */
  saveDashboardData: function () {
    try {
      console.log('대시보드 데이터 저장 중...');

      // 저장할 데이터 구조 생성
      const saveData = {
        dashboard: this.store.dashboardData,
        lastUpdated: new Date().toISOString(),
      };

      // 데이터를 JSON 문자열로 변환
      const jsonData = JSON.stringify(saveData, null, 2);

      // localStorage에 저장
      localStorage.setItem('tms_dashboard_data', jsonData);

      console.log(
        '대시보드 데이터 저장 완료:',
        `${this.store.dashboardData.length}건`
      );

      // 데이터가 저장되었음을 알리는 이벤트 발생
      document.dispatchEvent(new CustomEvent('tms:dashboardDataSaved'));

      return true;
    } catch (error) {
      console.error('대시보드 데이터 저장 실패:', error);
      messageUtils.error('데이터를 저장하는 중 오류가 발생했습니다.');
      return false;
    }
  },

  /**
   * 데이터 업데이트 함수
   * 대시보드 데이터 수정 후 저장
   */
  updateDashboardData: function (updatedItems) {
    if (!Array.isArray(updatedItems) && updatedItems) {
      // 단일 아이템인 경우 배열로 변환
      updatedItems = [updatedItems];
    }

    if (!updatedItems || updatedItems.length === 0) {
      console.warn('업데이트할 데이터가 없습니다.');
      return false;
    }

    // 데이터가 아직 로드되지 않은 경우
    if (!this.store.dashboardData) {
      console.warn('대시보드 데이터가 아직 로드되지 않았습니다.');
      return false;
    }

    try {
      // 각 업데이트 항목 처리
      updatedItems.forEach((item) => {
        const index = this.store.dashboardData.findIndex(
          (existing) => existing.order_no === item.order_no
        );

        if (index !== -1) {
          // 기존 항목 업데이트
          this.store.dashboardData[index] = {
            ...this.store.dashboardData[index],
            ...item,
            updated_at: new Date().toISOString(),
          };
        } else {
          // 새 항목 추가
          this.store.dashboardData.push({
            ...item,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          });
        }
      });

      // 데이터 저장 - 즉시 localStorage에 저장하여 지속성 보장
      this.saveDashboardData();

      // 데이터가 변경되었음을 알리는 이벤트
      document.dispatchEvent(new CustomEvent('tms:dashboardDataChanged'));

      return true;
    } catch (error) {
      console.error('대시보드 데이터 업데이트 실패:', error);
      return false;
    }
  },
};

// DOM이 로드되면 애플리케이션 초기화
document.addEventListener('DOMContentLoaded', function () {
  TMS.init();
});
