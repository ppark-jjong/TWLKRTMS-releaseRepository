/**
 * 공통 유틸리티 함수 모음
 */

// 날짜 관련 유틸리티
const dateUtils = {
  /**
   * 오늘 날짜를 YYYY-MM-DD 형식의 문자열로 반환
   */
  getCurrentDate() {
    const today = new Date();
    return this.formatDate(today);
  },
  
  /**
   * Date 객체를 YYYY-MM-DD 형식의 문자열로 변환
   */
  formatDate(date) {
    if (!(date instanceof Date) || isNaN(date.getTime())) {
      console.warn('유효하지 않은 날짜:', date);
      return '';
    }
    
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    
    return `${year}-${month}-${day}`;
  },
  
  /**
   * YYYY-MM-DD 형식의 문자열을 Date 객체로 변환
   */
  parseDate(dateString) {
    try {
      if (!dateString) return null;
      
      // YYYY-MM-DD 형식 확인
      if (!/^\d{4}-\d{2}-\d{2}$/.test(dateString)) {
        console.warn('날짜 형식이 올바르지 않습니다:', dateString);
        return null;
      }
      
      const [year, month, day] = dateString.split('-').map(num => parseInt(num, 10));
      const date = new Date(year, month - 1, day);
      
      // 유효한 날짜인지 확인
      if (isNaN(date.getTime())) {
        console.warn('유효하지 않은 날짜:', dateString);
        return null;
      }
      
      return date;
    } catch (error) {
      console.error('날짜 파싱 오류:', error);
      return null;
    }
  },
  
  /**
   * Excel 날짜 값을 JS Date 객체로 변환
   * Excel 날짜는 1900년 1월 1일부터 일수로 저장됨 (윤년 버그 포함)
   */
  excelDateToDate(excelDate) {
    try {
      if (!excelDate || isNaN(excelDate)) return null;
      
      // Excel 날짜는 1900년 1월 0일부터 시작하므로 1900년 1월 1일로 변환
      const jsDate = new Date(1900, 0, excelDate - 1);
      
      // 유효한 날짜인지 확인
      if (isNaN(jsDate.getTime())) {
        console.warn('Excel 날짜 변환 실패:', excelDate);
        return null;
      }
      
      return jsDate;
    } catch (error) {
      console.error('Excel 날짜 변환 오류:', error);
      return null;
    }
  },
  
  /**
   * 두 날짜 사이의 일수 계산
   */
  daysBetween(date1, date2) {
    if (!(date1 instanceof Date) || !(date2 instanceof Date)) {
      return 0;
    }
    
    // UTC 시간으로 변환하여 시간대 차이 제거
    const utc1 = Date.UTC(date1.getFullYear(), date1.getMonth(), date1.getDate());
    const utc2 = Date.UTC(date2.getFullYear(), date2.getMonth(), date2.getDate());
    
    // 일수로 변환 (밀리초를 일로 변환)
    const diffDays = Math.floor((utc2 - utc1) / (1000 * 60 * 60 * 24));
    
    return diffDays;
  }
};

// 메시지 유틸리티
const messageUtils = {
  messageTimer: null,
  
  /**
   * 메시지 표시
   */
  showMessage(message, type = 'info', duration = 3000) {
    const messageEl = document.getElementById('messagePopup');
    if (!messageEl) return;
    
    const messageText = messageEl.querySelector('.message-text');
    const messageIcon = messageEl.querySelector('.message-icon');
    
    // 타입에 따른 아이콘과 클래스 설정
    let iconClass = 'fa-info-circle';
    messageEl.className = 'message-popup';
    
    if (type === 'success') {
      iconClass = 'fa-check-circle';
      messageEl.classList.add('message-success');
    } else if (type === 'error') {
      iconClass = 'fa-times-circle';
      messageEl.classList.add('message-error');
    } else if (type === 'warning') {
      iconClass = 'fa-exclamation-triangle';
      messageEl.classList.add('message-warning');
    } else {
      messageEl.classList.add('message-info');
    }
    
    // 아이콘 및 메시지 설정
    messageIcon.className = `fa-solid ${iconClass} message-icon`;
    messageText.textContent = message;
    
    // 메시지 표시
    messageEl.classList.add('active');
    
    // 타이머 설정
    if (this.messageTimer) {
      clearTimeout(this.messageTimer);
    }
    
    this.messageTimer = setTimeout(() => {
      messageEl.classList.remove('active');
    }, duration);
  },
  
  /**
   * 성공 메시지
   */
  success(message, duration = 3000) {
    this.showMessage(message, 'success', duration);
  },
  
  /**
   * 에러 메시지
   */
  error(message, duration = 3000) {
    this.showMessage(message, 'error', duration);
  },
  
  /**
   * 경고 메시지
   */
  warning(message, duration = 3000) {
    this.showMessage(message, 'warning', duration);
  },
  
  /**
   * 정보 메시지
   */
  info(message, duration = 3000) {
    this.showMessage(message, 'info', duration);
  }
};

// 상태 유틸리티
const statusUtils = {
  // 상태 텍스트 매핑 (요청대로 5가지 상태로 제한)
  statusText: {
    'PENDING': '대기',
    'IN_PROGRESS': '진행',
    'COMPLETE': '완료',
    'ISSUE': '이슈',
    'CANCEL': '취소'
  },
  
  // 상태 색상 매핑
  statusColors: {
    'PENDING': '',
    'IN_PROGRESS': '',
    'COMPLETE': '',
    'ISSUE': '',
    'CANCEL': ''
  },
  
  /**
   * 상태에 따른 텍스트 반환
   */
  getStatusText(status) {
    return this.statusText[status] || status;
  },
  
  /**
   * 상태에 따른 색상 클래스 반환
   */
  getStatusClass(status) {
    return this.statusColors[status] || 'bg-gray';
  },
  
  // 우선순위 텍스트 매핑
  priorityText: {
    'LOW': '낮음',
    'MEDIUM': '중간',
    'HIGH': '높음',
    'URGENT': '긴급'
  },
  
  // 우선순위 클래스 매핑
  priorityClasses: {
    'LOW': 'priority-low',
    'MEDIUM': 'priority-medium',
    'HIGH': 'priority-high',
    'URGENT': 'priority-urgent'
  },
  
  /**
   * 우선순위에 따른 텍스트 반환
   */
  getPriorityText(priority) {
    return this.priorityText[priority] || priority;
  },
  
  /**
   * 우선순위에 따른 클래스 반환
   */
  getPriorityClass(priority) {
    return this.priorityClasses[priority] || 'priority-medium';
  }
};

// 모달 제어 유틸
const modalUtils = {
  /**
   * 모달 열기
   */
  openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.add('active');
    }
  },
  
  /**
   * 모달 닫기
   */
  closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.remove('active');
    }
  },
  
  /**
   * 모든 모달 닫기
   */
  closeAllModals() {
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
      modal.classList.remove('active');
    });
  },
  
  /**
   * 모달 초기화 (모든 모달에 닫기 이벤트 추가)
   */
  initModals() {
    // 모달 닫기 버튼에 이벤트 리스너 추가
    const closeButtons = document.querySelectorAll('[data-modal]');
    closeButtons.forEach(button => {
      button.addEventListener('click', () => {
        const modalId = button.getAttribute('data-modal');
        this.closeModal(modalId);
      });
    });
    
    // 모달 바깥 영역 클릭 시 닫기
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
      modal.addEventListener('click', (e) => {
        if (e.target === modal) {
          modal.classList.remove('active');
        }
      });
    });
  }
};

// 데이터 관리자
const dataManager = {
  dashboards: [],
  handovers: [],
  isLoaded: false,
  
  /**
   * 데이터 로드
   */
  async loadData() {
    try {
      console.log('데이터 매니저: 데이터 로드 중...');
      
      // 대시보드 데이터 로드
      await this.loadDashboardData();
      
      // 데이터 로드 상태 업데이트
      this.isLoaded = true;
      console.log('데이터 매니저: 모든 데이터 로드 완료');
      
      return true;
    } catch (error) {
      console.error('데이터 매니저: 데이터 로드 오류:', error);
      return false;
    }
  },
  
  /**
   * 대시보드 데이터 로드
   */
  async loadDashboardData() {
    try {
      const response = await fetch('dashboard_data.json');
      
      if (!response.ok) {
        throw new Error(`대시보드 데이터 로드 실패: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (data && data.dashboard && Array.isArray(data.dashboard)) {
        this.dashboards = data.dashboard.map(item => {
          // 상태 필드 표준화 (status 또는 delivery_status)
          if (!item.status && item.delivery_status) {
            item.status = item.delivery_status;
          } else if (!item.delivery_status && item.status) {
            item.delivery_status = item.status;
          }
          
          // ETA 날짜 파싱
          if (item.eta && typeof item.eta === 'string') {
            try {
              item.eta_date = new Date(item.eta);
            } catch (error) {
              console.warn(`ETA 날짜 파싱 오류 (${item.order_no}):`, error);
            }
          }
          
          return item;
        });
        
        console.log(`데이터 매니저: 대시보드 데이터 ${this.dashboards.length}건 로드 완료`);
      } else {
        console.warn('데이터 매니저: 대시보드 데이터 형식이 유효하지 않습니다.');
        this.dashboards = [];
      }
    } catch (error) {
      console.error('데이터 매니저: 대시보드 데이터 로드 실패:', error);
      this.dashboards = [];
    }
  },
  
  /**
   * 인수인계 데이터 추가
   */
  addHandover(handoverData) {
    try {
      if (!handoverData || !handoverData.title || !handoverData.content) {
        console.warn('데이터 매니저: 유효하지 않은 인수인계 데이터');
        return null;
      }
      
      // 현재 날짜/시간
      const now = new Date();
      const dateStr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')} ${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
      
      // 새 인수인계 객체 생성
      const newHandover = {
        handover_id: `H${String(this.handovers.length + 1).padStart(3, '0')}`,
        title: handoverData.title,
        category: handoverData.category || '일반',
        priority: handoverData.priority || 'MEDIUM',
        content: handoverData.content,
        created_by: 'CSAdmin',
        created_at: dateStr,
        confirmations: []
      };
      
      // 배열에 추가
      this.handovers.push(newHandover);
      
      console.log('데이터 매니저: 새 인수인계 추가 완료:', newHandover.handover_id);
      
      return newHandover;
    } catch (error) {
      console.error('데이터 매니저: 인수인계 추가 오류:', error);
      return null;
    }
  },
  
  /**
   * 인수인계 데이터 조회
   */
  getHandovers() {
    return this.handovers;
  },
  
  /**
   * ID로 인수인계 데이터 조회
   */
  getHandoverById(id) {
    return this.handovers.find(item => String(item.handover_id) === String(id));
  }
};
