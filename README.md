# 🚚 TWLKR 배송 실시간 관제 시스템 README&#x20;

> **계속 수정 중이며 본 공유 코드는 수정 개발 중에 있습니다. 25년 5월 중으로 서버 배포 시 url 공유 예정입니다.**

---

## 1. 프로젝트 개요 및 활용 아키텍처

### 1-1. 프로젝트 목적

- **실시간 배송 주문 관리**: ETA(예상 도착 시간) 기준으로 주문을 조회·제어합니다.
- **효율적 배차**: 기사 배정·상태 전이를 통합 제공합니다.
- **권한 구분**: 일반 사용자 **USER** / 관리자 **ADMIN** 두 역할로 기능을 분리합니다.



### 1-2. 기술 스택

| 레이어                | 사용 기술                                                  | 비고                       |
| ------------------ | ------------------------------------------------------ | ------------------------ |
| **Backend**        | Python 3.12 · FastAPI · Jinja2(SSR)                    | 단일 애플리케이션 컨테이너           |
| **Frontend**       | HTML + CSS · 모듈형 JavaScript(전역 네임스페이스 최소화)             | CSR 인터랙션 모듈화             |
| **Database**       | MySQL 8.0(스키마: `init-db.sql`) · Cloud SQL              | Private IP · IAM DB Auth |
| **Infrastructure** | Docker → Google App Engine Flexible(`runtime: custom`) | Cloud Armor / Firewall   |

### 1-3. 요청 흐름 (로그인 → SSR → CSR)

```mermaid
flowchart TD
    A[Client Browser] --> B{Session or Cookie?}
    B -- No --> C[Redirect to /login]
    B -- Yes --> D[SSR Render HTML]
    D --> A
    A --> E["Client-side JS or (CSR) API Calls"]
```

---

## 2. 배포 아키텍처 및 보안 사항

### 2-1. 인프라 개요

```mermaid
flowchart TD
    subgraph GCP
        CA[Cloud Armor / TLS]
        FW[Firewall Allow-list]
        GAE["GAE Flex (Docker Container)"]
        Log[Logging & Monitoring]
        SQL["Cloud SQL (MySQL 8.0)"]
        CA --> FW --> GAE --> Log
        GAE --> SQL
    end
```

### 2-2. 애플리케이션 보안

| 영역                   | 조치 사항                                                                     |
| -------------------- | ------------------------------------------------------------------------- |
| **GAE Flex**         | Cloud Armor / Firewall, HSTS, `X-Content-Type-Options`, `X-Frame-Options` |
| **CORS**             | 최소 허용 도메인 화이트리스트만 허용                                                      |
| **Sessions**         | 서버-사이드 세션, `HttpOnly`+`Secure` 쿠키, 만료 시 자동 로그아웃                           |
| **Cloud SQL**        | Private IP, SSL/TLS, IAM DB Auth, 자동 백업, 최소 권한 파라미터                       |
| **Input Validation** | 서버 핵심 검증 + 클라이언트 보조 검증, SQL 인젝션·XSS 방지                                    |
| **Logging**          | PII 저장 금지, `{success, error_code, message}` 단일 JSON 스키마                   |

### 2-3. 배포 파이프라인

1. 단일 **Dockerfile** 빌드 → GAE Flex `gcloud app deploy`.
2. 환경 변수로 비밀·구성 관리.
3. Cloud SQL 연결은 **Cloud SQL Auth Proxy**를 로컬 개발 시 사용.

---

## 3. 주요 기능 (User Perspective)

### 3-1. Dashboard

- **실시간 배송 주문 목록 조회**
  ![스크린샷 2025-04-29 140553](https://github.com/user-attachments/assets/c27c893f-2f02-4430-aff5-7c536ed8445f)
- **배송 주문 생성**
  ![스크린샷 2025-04-29 140601](https://github.com/user-attachments/assets/fe484ca4-a5e9-4d97-b1f0-4abd447c0c74)
- **배차 operation 사용자를 위한 기사 배차 처리 및 배송 상태 변경**
- ![스크린샷 2025-04-29 140624](https://github.com/user-attachments/assets/b9458347-aaca-48b0-ae84-60f354676491)
- ![스크린샷 2025-04-29 140643](https://github.com/user-attachments/assets/83e79242-d051-42e0-9838-61c8f894c09b)

- **주문 상세 정보 확인**
- ![스크린샷 2025-04-29 140607](https://github.com/user-attachments/assets/e73a5ef9-f2ce-47af-99fd-6c78e7fc8426)

- **간단한 데이터 시각화**
- ![스크린샷 2025-04-29 140734](https://github.com/user-attachments/assets/5d493136-78ba-46f5-9bca-0f4c9e8e3f23)



---



> 문의·제안은 Issues 탭을 통해 남겨 주세요.

