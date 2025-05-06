"""
인증 및 보안 관련 유틸리티
"""

import bcrypt
from typing import Dict, Optional, Any
from fastapi import Depends, HTTPException, Request, status
from main.utils.config import get_settings
import logging

logger = logging.getLogger(__name__)

settings = get_settings()


def hash_password(password: str) -> str:
    """비밀번호를 안전하게 해시화합니다."""
    # 먼저 문자열을 바이트로 변환 (UTF-8 인코딩 사용)
    password_bytes = password.encode("utf-8")

    # 솔트 생성 및 해시 생성
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)

    # 바이트에서 문자열로 변환하여 반환
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """해시화된 비밀번호와 일반 텍스트 비밀번호를 비교합니다."""
    plain_password_bytes = plain_password.encode("utf-8")
    hashed_password_bytes = hashed_password.encode("utf-8")

    try:
        return bcrypt.checkpw(plain_password_bytes, hashed_password_bytes)
    except Exception as e:
        logger.error(f"비밀번호 검증 중 오류: {str(e)}")
        return False


def get_current_user(request: Request) -> Dict[str, Any]:
    """
    현재 요청의 세션에서 사용자 정보를 가져옵니다.

    SessionMiddleware가 제공하는 request.session을 사용합니다.
    이는 쿠키 기반 세션으로, GAE 환경에서도 안정적으로 동작합니다.

    Args:
        request: FastAPI 요청 객체

    Returns:
        dict: 사용자 정보

    Raises:
        HTTPException: 인증되지 않은 경우 (401)
    """
    user = request.session.get("user")

    if user:
        # logger.debug(f"세션에서 사용자 정보 확인: {user.get('user_id')}") # 프로덕션에서 불필요한 로그 제거
        pass  # user가 있을 때 debug 로그만 있었으므로 pass 추가
    else:
        logger.warning(f"인증되지 않은 접근 시도: {request.url.path}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="인증이 필요합니다"
        )

    return user


def get_admin_user(
    user_data: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    현재 사용자가 관리자인지 확인합니다.

    Args:
        user_data: 현재 사용자 정보

    Returns:
        dict: 사용자 정보

    Raises:
        HTTPException: 관리자가 아닌 경우 (403)
    """
    if user_data.get("user_role") != "ADMIN":
        logger.warning(f"관리자 권한 필요 접근 시도: user={user_data.get('user_id')}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="관리자 권한이 필요합니다"
        )

    return user_data
