"""
인증 관련 라우터
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request, Response, Form, status
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
import os
import logging
from datetime import datetime

from main.utils.database import get_db
from main.utils.security import get_current_user
from main.utils.config import get_settings
from main.schema.auth_schema import LoginRequest, LoginResponse
from main.service.auth_service import authenticate_user
from main.core.templating import templates

# 설정 로드
settings = get_settings()

# 라우터 생성
router = APIRouter()


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """
    로그인 페이지 렌더링
    """
    # 함수 진입점 로깅
    # logging.debug(f"login_page 시작: URL={request.url}")

    # return_to 파라미터가 있는 경우 템플릿에 전달
    return_to = request.query_params.get("return_to", "/dashboard")

    # 이미 로그인된 경우 return_to로 리다이렉션
    if request.session.get("user"):
        logging.info(
            f"로그인된 사용자 리다이렉트: {request.session.get('user').get('user_id', 'N/A')}"
        )
        return RedirectResponse(url=return_to, status_code=status.HTTP_303_SEE_OTHER)

    # 중간 포인트 로깅
    # logging.debug(f"login_page 렌더링: return_to={return_to}")

    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "debug": settings.DEBUG,
            "return_to": return_to,
            "current_year": datetime.now().year,  # 현재 연도 추가
        },
    )


@router.post("/login")
async def login(
    request: Request,
    response: Response,
    user_id: str = Form(...),
    user_password: str = Form(...),
    return_to: str = Form("/dashboard"),
    db: Session = Depends(get_db),
):
    """
    로그인 처리 (폼 데이터 방식)
    쿠키 기반 세션(SessionMiddleware) 사용
    """
    # 함수 진입점 로깅
    logging.info(f"login 시작: 사용자 ID={user_id}, return_to={return_to}")

    authenticated, user_data = authenticate_user(db, user_id, user_password)

    if not authenticated or not user_data:
        # 중간 포인트 로깅 - 인증 실패
        logging.warning(f"로그인 실패: 사용자 ID={user_id}")

        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "사용자 ID 또는 비밀번호가 일치하지 않습니다.",
                "debug": settings.DEBUG,
                "return_to": return_to,
                "current_year": datetime.now().year,  # 현재 연도 추가
            },
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    # 쿠키 기반 세션에 사용자 정보 저장
    request.session["user"] = user_data

    # 중간 포인트 로깅 - 로그인 성공
    logging.info(
        f"로그인 성공: 사용자 '{user_id}', 권한='{user_data.get('user_role')}'"
    )

    return RedirectResponse(url=return_to, status_code=status.HTTP_303_SEE_OTHER)


@router.get("/logout")
async def logout(request: Request):
    """
    로그아웃 처리
    쿠키 기반 세션 제거
    """
    # 함수 진입점 로깅
    user_id = request.session.get("user", {}).get("user_id", "알 수 없음")
    logging.info(f"logout 시작: 사용자 ID={user_id}")

    # 쿠키 기반 세션 클리어
    request.session.clear()

    # 중간 포인트 로깅 - 로그아웃 성공
    logging.info(f"로그아웃 성공: 사용자 ID={user_id}")

    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/me")
async def get_me(request: Request):
    """
    현재 로그인된 사용자 정보 반환
    """
    # 함수 진입점 로깅
    # logging.debug(f"get_me 시작: IP={request.client.host}")

    user = request.session.get("user")
    if not user:
        logging.warning(f"인증되지 않은 사용자 접근: IP={request.client.host}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증되지 않은 사용자입니다.",
        )

    # 중간 포인트 로깅 - 사용자 정보 반환
    # logging.debug(f"사용자 정보 반환: 사용자 ID={user.get('user_id')}")

    return user


@router.get("/api/check-session")
async def check_session(request: Request):
    """
    현재 세션 유효성 확인 API
    클라이언트에서 주기적으로 호출하여 세션 상태를 확인합니다.
    """
    # 함수 진입점 로깅
    # logging.debug(f"세션 체크 API 호출: IP={request.client.host}")

    user = request.session.get("user")
    if not user:
        logging.info(f"세션 체크 실패: 세션 없음 (IP={request.client.host})")
        return {"authenticated": False, "message": "세션이 만료되었습니다."}

    # 세션이 유효한 경우 사용자 정보 반환 (민감한 정보 제외)
    # logging.debug(
    #     f"세션 체크 성공: 사용자={user.get('user_id')}, 권한={user.get('user_role')}"
    # )
    return {
        "authenticated": True,
        "message": "세션이 유효합니다.",
        "user": {
            "user_id": user.get("user_id"),
            "user_name": user.get("user_name"),
            "user_role": user.get("user_role"),
            "department": user.get("department"),
        },
    }
