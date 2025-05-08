import time
import uuid
import uvicorn
import traceback
from fastapi import FastAPI, Request, Response, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse, JSONResponse
from contextlib import asynccontextmanager
from fastapi.templating import Jinja2Templates
import os
import logging
from datetime import datetime
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional
from main.utils.config import get_settings
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

# --- 로깅 설정 초기화 ---
settings = get_settings()

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# --- 프로젝트 모듈 임포트 ---
# 실제 프로젝트 구조('main.')에 맞게 수정 필요할 수 있음.
# 여기서는 main.py 기준으로 올바른 경로 사용.
from main.utils.database import test_db_connection
from main.routes import (
    auth_route,
    dashboard_route,
    handover_route,
    users_route,
    excel_export,
    general_route,
)
from main.core.templating import templates

# --- 설정 로드 ---
# settings = get_settings() # 이 라인을 위로 이동시킴


# 템플릿 설정
templates = Jinja2Templates(directory="main/templates")


# --- Lifespan 이벤트 핸들러 ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 애플리케이션 시작 시
    logging.info("애플리케이션 시작 (lifespan)...")

    # DB 연결 진단 (개선된 버전)
    try:
        from main.utils.diagnostics.db_connection import diagnose_db_connection

        connection_success = diagnose_db_connection()
        if not connection_success:
            logging.warning(
                "데이터베이스 연결 진단 실패 - 애플리케이션 동작에 문제가 발생할 수 있습니다"
            )
            # 대체 연결 방법 시도
            from main.utils.diagnostics.db_connection import try_direct_mysql_connection

            direct_success = try_direct_mysql_connection()
            if direct_success:
                logging.info("대체 연결 방법으로 데이터베이스 연결 성공")
    except Exception as e:
        logging.error(f"DB 연결 진단 중 오류 발생: {str(e)}")

    # 기존 연결 테스트도 유지 (하위 호환성)
    test_db_connection()

    # 쿠키 기반 세션만 사용하므로 메모리 기반 세션 정리 비활성화
    # from main.utils.security import initialize_session_cleanup
    # initialize_session_cleanup()

    yield
    # 애플리케이션 종료 시
    logging.info("애플리케이션 종료 (lifespan)...")


# --- FastAPI 앱 생성 (lifespan 적용) ---
app = FastAPI(
    title="Teckwah TMS",
    description="배송 실시간 관제 시스템 API",
    version="0.1.0",
    debug=settings.DEBUG,
    lifespan=lifespan,  # lifespan 핸들러 적용
)

# 프록시 헤더 미들웨어 추가 (X-Forwarded-For, X-Forwarded-Proto 등)
# trusted_hosts는 App Engine 환경에 맞게 설정하거나, '*'로 모든 프록시를 신뢰할 수 있습니다.
# GAE 환경에서는 Google의 프록시만 존재하므로 '*'로 설정해도 일반적으로 안전합니다.
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")


# --- 미들웨어 클래스 정의 ---


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        client_host = request.headers.get("x-forwarded-for") or request.client.host

        logger.info(
            f"[Request Start] ID: {request_id}, IP: {client_host}, Method: {request.method}, Path: {request.url.path}"
        )

        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            # 응답이 StreamingResponse인 경우 헤더 추가 불가
            if not isinstance(response, Response):
                # StreamingResponse 등 헤더 설정이 불가능한 경우 로그만 남김
                pass
            elif hasattr(response, "headers"):
                response.headers["X-Request-ID"] = request_id

            status_code = (
                response.status_code if hasattr(response, "status_code") else "N/A"
            )
            logger.info(
                f"[Request End] ID: {request_id}, Status: {status_code}, Time: {process_time:.4f}s"
            )
            return response
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"[Request Error] ID: {request_id}, Error: {str(e)}, Time: {process_time:.4f}s",
                exc_info=True,
            )
            raise e


# --- 미들웨어 등록 (순서 중요! 역순으로 등록됨: 마지막 추가된 것이 가장 먼저 실행) ---

# 4. 인증 예외 처리 미들웨어 제거
# app.add_middleware(AuthExceptionMiddleware)

# 3. 로깅 미들웨어
app.add_middleware(LoggingMiddleware)

# 2. 세션 미들웨어
# GAE 환경에서는 HTTPS 강제, 로컬에서는 HTTP 허용
# is_production = os.getenv("GAE_ENV", "").startswith("standard") # 기존 로직
is_app_engine_env = bool(
    os.getenv("GAE_INSTANCE")
)  # App Engine 환경 (Standard/Flexible) 감지
logger.info(
    f"환경 감지: {'App Engine' if is_app_engine_env else '로컬/개발'} - 세션 쿠키 HTTPS 강제: {is_app_engine_env}"
)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET,
    max_age=settings.SESSION_EXPIRE_HOURS * 60 * 60,
    https_only=is_app_engine_env,  # App Engine 환경이면 항상 True
    same_site="lax",
    session_cookie="session",
)

# 1. CORS 미들웨어 (가장 안쪽)
app.add_middleware(
    CORSMiddleware,
    allow_origins=(settings.ALLOWED_ORIGINS if settings.ALLOWED_ORIGINS else ["*"]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- 라우터 포함 (수정) ---
# 각 라우터 파일에서 정의된 page_router, api_router, lock_router 등을 명시적으로 포함

# 인증 라우터 (로그인/로그아웃)
app.include_router(auth_route.router, tags=["Auth"])

# 대시보드 라우터
app.include_router(
    dashboard_route.page_router, tags=["Dashboard Pages"]
)  # 페이지 라우터
app.include_router(dashboard_route.api_router, tags=["Dashboard API"])  # API 라우터

# 엑셀 내보내기 라우터 (관리자 전용)
app.include_router(excel_export.api_router, tags=["Excel Export API"])


# 인수인계 라우터
app.include_router(handover_route.page_router, tags=["Handover Pages"])  # 페이지 라우터
app.include_router(handover_route.api_router, tags=["Handover API"])  # API 라우터

# 사용자 관리 라우터
app.include_router(users_route.page_router, tags=["User Admin Pages"])  # 페이지 라우터
app.include_router(users_route.api_router, tags=["User Admin API"])  # API 라우터

# 일반 페이지 라우터 (Vinfiniti 등)
app.include_router(general_route.page_router, tags=["General Pages"])


# --- 정적 파일 서빙 --- (규칙 4.3.1)
# Dockerfile에서 해당 경로에 파일이 복사되도록 구성해야 합니다.
# 경로 "/static"으로 접근
app.mount("/static", StaticFiles(directory="main/static"), name="static")


# --- 진단용 엔드포인트 ---
@app.get("/health", tags=["Diagnostics"])
async def health_check():
    """간단한 헬스 체크 엔드포인트"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.get("/db-test", tags=["Diagnostics"])
async def db_test():
    """데이터베이스 연결 진단 엔드포인트"""
    try:
        import socket
        import pymysql
        from main.utils.config import get_settings

        settings = get_settings()

        results = {
            "vpc_info": {},
            "socket_test": {},
            "mysql_test": {},
            "config": {
                "host": settings.MYSQL_HOST,
                "port": settings.MYSQL_PORT,
                "user": settings.MYSQL_USER,
                "database": settings.MYSQL_DATABASE,
                "gae_env": os.getenv("GAE_ENV", "없음"),
                "vpc_connector": os.getenv("VPC_CONNECTOR", "없음"),
            },
        }

        # 1. 소켓 연결 테스트
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)  # 3초 타임아웃
            start_time = time.time()
            result = sock.connect_ex((settings.MYSQL_HOST, settings.MYSQL_PORT))
            connect_time = time.time() - start_time
            sock.close()

            results["socket_test"] = {
                "success": result == 0,
                "result_code": result,
                "connect_time": f"{connect_time:.2f}s",
                "error": "없음" if result == 0 else f"소켓 오류 코드: {result}",
            }
        except Exception as e:
            results["socket_test"] = {"success": False, "error": str(e)}

        # 2. 직접 MySQL 연결 테스트
        if results["socket_test"].get("success", False):
            try:
                start_time = time.time()
                conn = pymysql.connect(
                    host=settings.MYSQL_HOST,
                    user=settings.MYSQL_USER,
                    password=settings.MYSQL_PASSWORD,
                    database=settings.MYSQL_DATABASE,
                    port=settings.MYSQL_PORT,
                    connect_timeout=5,
                    charset="utf8mb4",
                )
                connect_time = time.time() - start_time

                with conn.cursor() as cursor:
                    cursor.execute("SELECT VERSION()")
                    version = cursor.fetchone()[0]
                    cursor.execute("SELECT CURRENT_USER()")
                    current_user = cursor.fetchone()[0]
                    cursor.execute("SELECT 1")
                    ping = cursor.fetchone()[0]

                conn.close()

                results["mysql_test"] = {
                    "success": True,
                    "version": version,
                    "current_user": current_user,
                    "ping": ping,
                    "connect_time": f"{connect_time:.2f}s",
                }
            except Exception as e:
                results["mysql_test"] = {"success": False, "error": str(e)}

        # 3. 현재 환경 정보
        try:
            local_ip = socket.gethostbyname(socket.gethostname())
            results["vpc_info"] = {
                "local_ip": local_ip,
                "hostname": socket.gethostname(),
            }
        except Exception as e:
            results["vpc_info"] = {"error": str(e)}

        return results
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}


# --- 기본 루트 엔드포인트 (수정) ---
@app.get("/", tags=["Root"], summary="Entry Point / Login Redirect")
async def root(request: Request):
    """
    서비스 진입점.
    로그인 상태를 확인하여 로그인 페이지 또는 대시보드로 리다이렉션합니다.
    """
    try:
        # SessionMiddleware가 먼저 실행되므로 request.session 직접 사용
        user = request.session.get("user")
        if user:
            logger.info(
                f"인증된 사용자 대시보드 리다이렉트: {user.get('user_id', 'N/A')}"
            )
            return RedirectResponse(
                url="/dashboard", status_code=status.HTTP_303_SEE_OTHER
            )
        else:
            logger.info("미인증 사용자 로그인 페이지 리다이렉트")
            return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    except Exception as e:
        # request.session 접근 자체에서 오류가 날 수도 있음 (매우 드묾)
        logger.error(f"루트 경로 처리 중 오류 발생: {str(e)}", exc_info=True)
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)


# --- 글로벌 예외 핸들러 --- (401 처리 복구 및 수정)
@app.exception_handler(status.HTTP_401_UNAUTHORIZED)
async def unauthorized_exception_handler(request: Request, exc: HTTPException):
    """
    401 Unauthorized 에러를 처리하는 전역 예외 핸들러.
    API 요청 여부와 관계없이 무조건 로그인 페이지로 리디렉션합니다.
    """
    path = request.url.path
    detail = exc.detail if hasattr(exc, "detail") else "인증 필요 (상세 정보 없음)"

    logger.info(
        f"글로벌 401 핸들러: {path} (Detail: {detail}) -> 로그인 페이지 리디렉션"
    )

    # API/웹 구분 없이 무조건 로그인 페이지로 리디렉션
    return_url = f"/login?return_to={request.url.path}"
    return RedirectResponse(url=return_url, status_code=status.HTTP_303_SEE_OTHER)


# --- Uvicorn 실행 (Dockerfile의 CMD와 연동) ---
if __name__ == "__main__":
    # Dockerfile의 CMD ["python", "main/main.py"] 실행을 위해
    # uvicorn 직접 실행 로직을 여기에 배치합니다.
    # 실제 GAE 배포 등에서는 gunicorn과 uvicorn worker를 사용할 수 있습니다.
    logging.info(f"서버를 http://0.0.0.0:{settings.PORT} 에서 시작합니다.")
    uvicorn.run(
        "main.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG,  # DEBUG 모드일 때만 코드 변경 시 자동 리로드
        workers=1,  # 단일 프로세스로 실행 (간단한 앱 기준)
    )
