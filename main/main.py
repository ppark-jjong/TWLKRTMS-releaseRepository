import time
import uuid
import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse
from contextlib import asynccontextmanager

# --- 프로젝트 모듈 임포트 ---
# 주의: utils 내부 모듈들의 import 경로가 'backend.' 로 시작하는 경우,
# 실제 프로젝트 구조('main.')에 맞게 수정 필요할 수 있음.
# 여기서는 main.py 기준으로 올바른 경로 사용.
from main.utils.config import get_settings
from main.utils.database import test_db_connection
from main.utils.logger import logger
from main.routes import auth_route, dashboard_route
from main.core.templating import templates

# --- 설정 로드 ---
settings = get_settings()

# --- Jinja2 템플릿 설정 (제거) ---
# templates = Jinja2Templates(directory="main/templates") # 제거


# --- Lifespan 이벤트 핸들러 ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 애플리케이션 시작 시
    logger.info("애플리케이션 시작 (lifespan)...")
    test_db_connection()
    yield
    # 애플리케이션 종료 시
    logger.info("애플리케이션 종료 (lifespan)...")


# --- FastAPI 앱 생성 (lifespan 적용) ---
app = FastAPI(
    title="Teckwah TMS",
    description="배송 실시간 관제 시스템 API",
    version="0.1.0",
    debug=settings.DEBUG,
    lifespan=lifespan,  # lifespan 핸들러 적용
)


# --- 미들웨어 설정 ---


# 0. 사용자 정보 미들웨어 (템플릿에 user 제공)
@app.middleware("http")
async def inject_user_middleware(request: Request, call_next):
    """
    모든 요청에 대해 템플릿에 user 정보를 제공하기 위한 미들웨어
    """
    # 요청에서 세션 정보 가져오기
    user = request.session.get("user", {"user_role": "USER"})

    # 요청 객체에 user 정보 저장 (템플릿에서 접근 가능)
    request.state.user = user

    # 다음 미들웨어 호출
    response = await call_next(request)
    return response


# 1. 로깅 미들웨어 (규칙 6)
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """
    모든 HTTP 요청/응답을 로깅하는 미들웨어입니다.
    요청 ID, 클라이언트 IP, 요청 경로, 처리 시간, 상태 코드를 로깅합니다.
    """
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()

    # 클라이언트 IP 확인 (로드밸런서/프록시 고려)
    client_host = request.headers.get("x-forwarded-for") or request.client.host

    logger.info(
        f"[Request Start] ID: {request_id}, IP: {client_host}, Method: {request.method}, Path: {request.url.path}"
    )

    try:
        response: Response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Request-ID"] = request_id
        logger.info(
            f"[Request End] ID: {request_id}, Status: {response.status_code}, Time: {process_time:.4f}s"
        )
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"[Request Error] ID: {request_id}, Error: {str(e)}, Time: {process_time:.4f}s",
            exc_info=True,
        )
        # 기본 오류 응답 반환 (FastAPI의 기본 Exception Handler가 처리하도록 re-raise)
        raise e


# 2. 세션 미들웨어 (규칙 4.5)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET,
    max_age=settings.SESSION_EXPIRE_HOURS * 60 * 60,  # 시간 단위를 초 단위로 변환
    https_only=False,  # 로컬 테스트 및 GAE 환경 고려 (GAE가 TLS 처리)
    same_site="lax",
)

# 3. CORS 미들웨어 (규칙 4.3)
# 주의: 실제 배포 시에는 ALLOWED_ORIGINS를 더 엄격하게 설정해야 합니다.
app.add_middleware(
    CORSMiddleware,
    allow_origins=(
        settings.ALLOWED_ORIGINS if settings.ALLOWED_ORIGINS else ["*"]
    ),  # .env 설정이 없을 경우 모든 출처 허용 (개발 편의용, 배포시 수정)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 라우터 포함 ---
# 주의: 라우터 파일 내부에 APIRouter 인스턴스가 'router' 변수명으로 정의되어 있어야 합니다.
from main.routes import auth_route, dashboard_route, handover_route, users_route

app.include_router(auth_route.router, prefix="/auth", tags=["Authentication"])
app.include_router(dashboard_route.router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(handover_route.router, prefix="/handover", tags=["Handover"])
app.include_router(users_route.router, prefix="/users", tags=["Users"])


# --- 정적 파일 서빙 --- (규칙 4.3.1)
# React 빌드 결과물 등 정적 파일을 '/main/static' 디렉토리에서 서빙합니다.
# Dockerfile에서 해당 경로에 파일이 복사되도록 구성해야 합니다.
# 경로 "/static"으로 접근
app.mount("/static", StaticFiles(directory="main/static"), name="static")


# --- 기본 루트 엔드포인트 (수정) ---
@app.get("/", tags=["Root"], summary="Entry Point / Login Redirect")
async def root(request: Request):
    """
    서비스 진입점.
    로그인 상태를 확인하여 로그인 페이지 또는 대시보드로 리다이렉션합니다.
    """
    user = request.session.get("user")
    if user:
        # 로그인 상태이면 대시보드로 리다이렉션
        logger.debug(
            f"로그인 사용자 감지 ({user.get('user_id', 'N/A')}), 대시보드로 리다이렉션"
        )
        return RedirectResponse(url="/dashboard", status_code=302)
    else:
        # 로그아웃 상태이면 로그인 페이지 렌더링
        logger.debug("로그아웃 상태 감지, 로그인 페이지 렌더링")
        return templates.TemplateResponse("login.html", {"request": request})


# --- Uvicorn 실행 (Dockerfile의 CMD와 연동) ---
if __name__ == "__main__":
    # Dockerfile의 CMD ["python", "main/main.py"] 실행을 위해
    # uvicorn 직접 실행 로직을 여기에 배치합니다.
    # 실제 GAE 배포 등에서는 gunicorn과 uvicorn worker를 사용할 수 있습니다.
    logger.info(f"서버를 http://0.0.0.0:{settings.PORT} 에서 시작합니다.")
    uvicorn.run(
        "main.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG,  # DEBUG 모드일 때만 코드 변경 시 자동 리로드
        workers=1,  # 단일 프로세스로 실행 (간단한 앱 기준)
    )
