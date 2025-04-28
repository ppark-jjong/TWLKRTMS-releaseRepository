"""
인증 관련 라우터
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request, Response, Form, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import os

from main.utils.database import get_db
from main.utils.security import delete_session, get_current_user
from main.utils.logger import logger
from main.utils.config import get_settings
from main.schema.auth_schema import LoginRequest, LoginResponse
from main.service.auth_service import authenticate_user, create_user_session
from main.core.templating import templates

# 설정 로드
settings = get_settings()

# 라우터 생성
router = APIRouter()

# 올바른 경로에서 get_session 임포트 (get_session 함수 존재 가정)
# from backend.utils.security import get_session -> 수정
try:
    from main.utils.security import get_session
except ImportError:
    # get_session 함수가 없을 경우를 대비한 임시 처리 (실제 구현 확인 필요)
    from main.utils.logger import logger  # logger 임포트 추가

    logger.warning("main.utils.security 모듈에서 get_session 함수를 찾을 수 없습니다.")
    get_session = None


@router.get("/login")
async def login_page(request: Request):
    """
    로그인 페이지 렌더링

    이미 로그인된 경우 대시보드로 리다이렉션
    """
    session_id = request.cookies.get("session_id")

    if session_id and get_session:  # get_session 함수가 임포트되었는지 확인
        try:
            session_data = get_session(session_id)
            if session_data:
                return RedirectResponse(
                    url="/dashboard", status_code=status.HTTP_303_SEE_OTHER
                )
        except Exception as e:
            logger.warning(f"세션 확인 중 오류 발생: {e}")
            pass

    return templates.TemplateResponse(
        "login.html", {"request": request, "debug": settings.DEBUG}
    )


@router.post("/login")
async def login(
    request: Request,
    response: Response,
    user_id: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    """
    로그인 처리 (폼 제출 방식)

    성공 시 대시보드로 리다이렉션, 실패 시 에러 메시지와 함께 로그인 페이지 렌더링
    """
    authenticated, user_data = authenticate_user(db, user_id, password)

    if not authenticated or not user_data:
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "사용자 ID 또는 비밀번호가 일치하지 않습니다.",
                "debug": settings.DEBUG,
            },
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    session_id = create_user_session(user_data)
    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        max_age=settings.SESSION_EXPIRE_HOURS * 3600,
        secure=not settings.DEBUG,
        samesite="lax",
    )
    logger.info(f"로그인 성공 및 리다이렉션: 사용자 '{user_id}'")
    return response


@router.post("/login/api", response_model=LoginResponse)
async def login_api(
    request: LoginRequest, response: Response, db: Session = Depends(get_db)
):
    """
    로그인 처리 (API 방식)

    JSON 요청을 처리하고 JSON 응답 반환
    """
    authenticated, user_data = authenticate_user(db, request.user_id, request.password)

    if not authenticated or not user_data:
        return LoginResponse(
            success=False,
            message="사용자 ID 또는 비밀번호가 일치하지 않습니다.",
        )

    session_id = create_user_session(user_data)
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        max_age=settings.SESSION_EXPIRE_HOURS * 3600,
        secure=not settings.DEBUG,
        samesite="lax",
    )

    logger.info(f"API 로그인 성공: 사용자 '{request.user_id}'")

    return LoginResponse(
        success=True,
        message="로그인 성공",
        userId=user_data.get("user_id"),
        userRole=user_data.get("user_role"),
        userDepartment=user_data.get("user_department"),
    )


@router.post("/logout")
async def logout(request: Request, response: Response):
    """
    로그아웃 처리

    세션을 삭제하고 로그인 페이지로 리다이렉션 또는 JSON 응답 반환
    """
    session_id = request.cookies.get("session_id", "")
    
    # AJAX/API 요청인지 확인
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest" or \
              request.headers.get("Accept") == "application/json"

    if session_id:
        delete_session(session_id)
    
    # 세션 쿠키 삭제
    response_data = {"success": True, "message": "로그아웃 성공"}
    
    if is_ajax:
        # AJAX 요청의 경우 JSON 응답
        from fastapi.responses import JSONResponse
        response = JSONResponse(content=response_data)
        response.delete_cookie(key="session_id")
        logger.info("로그아웃 성공 (AJAX)")
        return response
    else:
        # 일반 요청의 경우 리다이렉션
        response = RedirectResponse(
            url="/auth/login", status_code=status.HTTP_303_SEE_OTHER
        )
        response.delete_cookie(key="session_id")
        logger.info("로그아웃 성공 (리다이렉션)")
        return response


@router.get("/me")
async def get_me(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    현재 로그인된 사용자 정보 반환
    """
    return {
        "success": True,
        "userId": current_user.get("user_id"),
        "userRole": current_user.get("user_role"),
        "userDepartment": current_user.get("user_department"),
    }
