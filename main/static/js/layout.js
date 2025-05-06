/**
 * 레이아웃 관련 스크립트
 * 사이드바 접기/펼치기, 반응형 레이아웃 등을 처리합니다.
 */
document.addEventListener('DOMContentLoaded', function () {
  // 레이아웃 모듈
  const Layout = {
    // 사이드바 상태 로컬 스토리지 키
    SIDEBAR_STATE_KEY: 'sidebar_collapsed',

    // DOM 요소
    sidebar: null,
    mainContent: null,
    sidebarToggle: null,

    /**
     * 초기화 함수
     */
    init() {
      // DOM 요소 참조 설정
      this.sidebar = document.querySelector('.sidebar');
      this.mainContent = document.querySelector('.main-content');
      this.sidebarToggle = document.getElementById('sidebarToggleBtn');

      // 저장된 사이드바 상태 불러오기
      this.loadSidebarState();

      // 이벤트 리스너 설정
      this.initEventListeners();

      console.log('레이아웃 모듈 초기화 완료');
    },

    /**
     * 저장된 사이드바 상태 불러오기
     */
    loadSidebarState() {
      if (!this.sidebar) return;

      // 로컬 스토리지에서 사이드바 상태 불러오기
      const isCollapsed =
        localStorage.getItem(this.SIDEBAR_STATE_KEY) === 'true';

      if (isCollapsed) {
        this.sidebar.classList.add('collapsed');
        // 토글 버튼 아이콘 업데이트
        if (this.sidebarToggle) {
          const icon = this.sidebarToggle.querySelector('i');
          if (icon) {
            icon.className = 'fa-solid fa-chevron-right';
            this.sidebarToggle.setAttribute('title', '사이드바 펼치기');
          }
        }
        console.log('사이드바 상태 복원: 접힘');
      } else {
        this.sidebar.classList.remove('collapsed');
        console.log('사이드바 상태 복원: 펼침');
      }
    },

    /**
     * 이벤트 리스너 설정
     */
    initEventListeners() {
      // 사이드바 토글 이벤트
      if (this.sidebarToggle) {
        this.sidebarToggle.addEventListener('click', () => {
          this.toggleSidebar();
        });
      } else {
        console.error('사이드바 토글 버튼을 찾을 수 없습니다.');
      }

      // 창 크기 변경 이벤트
      window.addEventListener('resize', () => {
        this.handleWindowResize();
      });
    },

    /**
     * 사이드바 접기/펼치기 토글
     */
    toggleSidebar() {
      if (!this.sidebar) return;

      // 사이드바 클래스 토글
      this.sidebar.classList.toggle('collapsed');

      // 토글 버튼 아이콘 변경
      if (this.sidebarToggle) {
        const icon = this.sidebarToggle.querySelector('i');
        if (icon) {
          if (this.sidebar.classList.contains('collapsed')) {
            icon.className = 'fa-solid fa-chevron-right';
            this.sidebarToggle.setAttribute('title', '사이드바 펼치기');
          } else {
            icon.className = 'fa-solid fa-chevron-left';
            this.sidebarToggle.setAttribute('title', '사이드바 접기');
          }
        }
      }

      // 접힘 상태 저장
      const isCollapsed = this.sidebar.classList.contains('collapsed');
      localStorage.setItem(this.SIDEBAR_STATE_KEY, isCollapsed);

      // 애니메이션 효과 추가
      this.sidebar.style.transition = 'width 0.3s ease';
      this.mainContent.style.transition = 'margin-left 0.3s ease';
      
      // 트랜지션 이후 제거 (불필요한 트랜지션 방지)
      setTimeout(() => {
        this.sidebar.style.transition = '';
        this.mainContent.style.transition = '';
      }, 300);

      console.log(`사이드바 상태 변경: ${isCollapsed ? '접힘' : '펼침'}`);
    },

    /**
     * 창 크기 변경 처리
     */
    handleWindowResize() {
      // 화면 너비에 따른 처리
      const isMobile = window.innerWidth <= 992;

      if (isMobile) {
        // 모바일 화면에서는 사이드바 자동 접기 (첫 방문 시)
        if (!localStorage.getItem(this.SIDEBAR_STATE_KEY)) {
          this.sidebar.classList.add('collapsed');
          
          // 토글 버튼 아이콘 업데이트
          if (this.sidebarToggle) {
            const icon = this.sidebarToggle.querySelector('i');
            if (icon) {
              icon.className = 'fa-solid fa-chevron-right';
              this.sidebarToggle.setAttribute('title', '사이드바 펼치기');
            }
          }
        }
      }
    },
  };

  // 레이아웃 모듈 초기화
  Layout.init();

  // 전역 접근을 위해 window에 할당 (다른 스크립트에서 접근 가능)
  window.Layout = Layout;
});