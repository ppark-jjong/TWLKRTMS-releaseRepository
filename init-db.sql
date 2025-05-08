-- 1. 데이터베이스 생성 및 사용 (기존 유지)
CREATE DATABASE IF NOT EXISTS delivery_system
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE=utf8mb4_unicode_ci;
USE delivery_system;

-- 2. 기본 지역 정보를 저장할 postal_code 테이블 (기존 유지)
CREATE TABLE IF NOT EXISTS postal_code (
  postal_code VARCHAR(5) NOT NULL PRIMARY KEY,
  city VARCHAR(100) NULL,
  county VARCHAR(100) NULL,
  district VARCHAR(100) NULL
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;

-- 3. 통합된 postal_code_detail 테이블 (기존 유지)
CREATE TABLE IF NOT EXISTS postal_code_detail (
   postal_code VARCHAR(5) NOT NULL,
   warehouse ENUM('SEOUL', 'BUSAN', 'GWANGJU', 'DAEJEON') NOT NULL,
   distance INT NOT NULL,
   duration_time INT NOT NULL,
   PRIMARY KEY (postal_code, warehouse),
   FOREIGN KEY (postal_code) REFERENCES postal_code(postal_code),
   INDEX idx_warehouse_postal (warehouse)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;

-- 4. 사용자 정보를 저장할 user 테이블 (user_name 필드 추가)
CREATE TABLE IF NOT EXISTS user (
  user_id VARCHAR(50) NOT NULL PRIMARY KEY,
  user_name VARCHAR(50) NOT NULL,  -- 사용자 이름 필드 추가
  user_password VARCHAR(255) NOT NULL,
  user_department ENUM('CS', 'HES', 'LENOVO') NOT NULL,
  user_role ENUM('ADMIN', 'USER') NOT NULL
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;

-- 6. 대시보드 정보를 저장할 dashboard 테이블 (락 제거, 배송사 및 버전 필드 추가)
CREATE TABLE IF NOT EXISTS dashboard (
  dashboard_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  order_no varchar(255) NOT NULL,
  type ENUM('DELIVERY', 'RETURN') NOT NULL,
  status ENUM('WAITING', 'IN_PROGRESS', 'COMPLETE', 'ISSUE', 'CANCEL') NOT NULL DEFAULT 'WAITING',
  department ENUM('CS', 'HES', 'LENOVO') NOT NULL,
  warehouse ENUM('SEOUL', 'BUSAN', 'GWANGJU', 'DAEJEON') NOT NULL,
  sla VARCHAR(10) NOT NULL,
  eta DATETIME NOT NULL,
  create_time DATETIME NOT NULL,
  depart_time DATETIME NULL,
  complete_time DATETIME NULL,
  postal_code VARCHAR(5) NOT NULL,
  city VARCHAR(21) NULL,
  county VARCHAR(51) NULL,
  district VARCHAR(51) NULL, 
  region VARCHAR(153) GENERATED ALWAYS AS (CONCAT(city, ' ', county, ' ', district)) STORED,
  distance INT NULL,
  duration_time INT NULL,
  address TEXT NOT NULL,
  customer VARCHAR(150) NOT NULL,
  contact VARCHAR(20) NULL, 
  driver_name VARCHAR(153) NULL,
  driver_contact VARCHAR(50) NULL,
  update_by VARCHAR(50) NULL,
  remark TEXT NULL,
  update_at DATETIME NULL,
  delivery_company ENUM('로얄', '서경', '택화') DEFAULT NULL,
  version INT NOT NULL DEFAULT 1,
  FOREIGN KEY (postal_code) REFERENCES postal_code(postal_code),
  FOREIGN KEY (update_by) REFERENCES user(user_id) ON DELETE SET NULL,
  INDEX idx_eta (eta),
  INDEX idx_department (department),
  INDEX idx_order_no (order_no)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;

-- 9. 인수인계 정보를 저장할 handover 테이블 (락 제거, 상태 및 버전 필드 추가)
CREATE TABLE IF NOT EXISTS handover (
    handover_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    department ENUM('CS', 'HES', 'LENOVO') NOT NULL,
    content TEXT NOT NULL,
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    update_at DATETIME NOT NULL,
    update_by VARCHAR(50) NOT NULL,
    create_by VARCHAR(50) NOT NULL,
    is_notice BOOLEAN DEFAULT FALSE,
    status ENUM('OPEN', 'CLOSE') NOT NULL DEFAULT 'OPEN',
    version INT NOT NULL DEFAULT 1,
    FOREIGN KEY (update_by) REFERENCES user(user_id) ON DELETE CASCADE,
    FOREIGN KEY (create_by) REFERENCES user(user_id) ON DELETE CASCADE
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;

-- 10. 트리거 생성: dashboard 테이블 INSERT 시 지역정보와 해당 허브별 거리/소요시간 자동 설정 (기존 유지)
DELIMITER //

CREATE TRIGGER trg_dashboard_before_insert_postal
BEFORE INSERT ON dashboard
FOR EACH ROW
BEGIN
  DECLARE v_city VARCHAR(100);
  DECLARE v_county VARCHAR(100);
  DECLARE v_district VARCHAR(100);
  DECLARE v_distance INT;
  DECLARE v_duration_time INT;
  DECLARE v_count INT;
  DECLARE v_postal_exists INT;

  -- 우편번호가 존재하는지 확인
  SELECT COUNT(*) INTO v_postal_exists FROM postal_code WHERE postal_code = NEW.postal_code;
  
  -- 우편번호가 존재하면 지역 정보 가져오기
  IF v_postal_exists > 0 THEN
    SELECT city, county, district
    INTO v_city, v_county, v_district
    FROM postal_code
    WHERE postal_code = NEW.postal_code;
    
    SET NEW.city = v_city;
    SET NEW.county = v_county;
    SET NEW.district = v_district;
    
    -- postal_code_detail에서 거리/시간 정보 조회
    SELECT COUNT(*) INTO v_count 
    FROM postal_code_detail 
    WHERE postal_code = NEW.postal_code AND warehouse = NEW.warehouse;
    
    IF v_count > 0 THEN
      SELECT distance, duration_time INTO v_distance, v_duration_time
      FROM postal_code_detail 
      WHERE postal_code = NEW.postal_code AND warehouse = NEW.warehouse;
      
      SET NEW.distance = v_distance;
      SET NEW.duration_time = v_duration_time;
    ELSE
      -- 해당 허브 정보가 없으면 기본값 0 설정
      SET NEW.distance = 0;
      SET NEW.duration_time = 0;
    END IF;
  ELSE
    -- 우편번호가 존재하지 않으면 기본값 설정
    SET NEW.distance = 0;
    SET NEW.duration_time = 0;
  END IF;
END//

DELIMITER ;

DELIMITER //

CREATE TRIGGER trg_dashboard_before_update_postal
BEFORE UPDATE ON dashboard
FOR EACH ROW
BEGIN
  DECLARE v_city VARCHAR(100);
  DECLARE v_county VARCHAR(100);
  DECLARE v_district VARCHAR(100);
  DECLARE v_distance INT;
  DECLARE v_duration_time INT;
  DECLARE v_count INT;
  DECLARE v_postal_exists INT;

  -- 우편번호 또는 창고가 변경되었는지 확인
  IF NEW.postal_code <> OLD.postal_code OR NEW.warehouse <> OLD.warehouse THEN
    -- 새 우편번호가 존재하는지 확인
    SELECT COUNT(*) INTO v_postal_exists FROM postal_code WHERE postal_code = NEW.postal_code;
    
    -- 우편번호가 존재하면 지역 정보 가져오기
    IF v_postal_exists > 0 THEN
      SELECT city, county, district
      INTO v_city, v_county, v_district
      FROM postal_code
      WHERE postal_code = NEW.postal_code;
      
      SET NEW.city = v_city;
      SET NEW.county = v_county;
      SET NEW.district = v_district;
      
      -- postal_code_detail에서 거리/시간 정보 조회 (새 우편번호와 새 창고 기준)
      SELECT COUNT(*) INTO v_count 
      FROM postal_code_detail 
      WHERE postal_code = NEW.postal_code AND warehouse = NEW.warehouse;
      
      IF v_count > 0 THEN
        SELECT distance, duration_time INTO v_distance, v_duration_time
        FROM postal_code_detail 
        WHERE postal_code = NEW.postal_code AND warehouse = NEW.warehouse;
        
        SET NEW.distance = v_distance;
        SET NEW.duration_time = v_duration_time;
      ELSE
        -- 해당 허브 정보가 없으면 기본값 0 설정
        SET NEW.distance = 0;
        SET NEW.duration_time = 0;
      END IF;
    ELSE
      -- 새 우편번호가 존재하지 않으면 city, county, district 및 거리/시간 기본값 설정
      SET NEW.city = NULL; 
      SET NEW.county = NULL;
      SET NEW.district = NULL;
      SET NEW.distance = 0;
      SET NEW.duration_time = 0;
    END IF;
  END IF; -- postal_code 또는 warehouse 변경 시 조건 끝
END//

DELIMITER ;