"""
인증 및 세션 관리 유틸리티
"""

import uuid
import time
import bcrypt
import threading
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List
from fastapi import Depends, HTTPException, Request, status
from main.utils.config import get_settings
from main.utils.logger import logger

settings = get_settings()

# 메모리 기반 세션 저장소 (운영 환경에서는 Redis 등으로 교체 고려)
sessions: Dict[str, Any] = {}

# 세션 정리 관련
cleanup_interval = 60 * 30  # 30분마다 세션 정리
cleanup_timer = None


def cleanup_expired_sessions():
    """만료된 세션을 주기적으로 정리"""
    global cleanup_timer

    # 현재 시간보다 만료 시간이 이전인 세션 찾기
    current_time = int(time.time())
    expired_sessions = [
        session_id
        for session_id, session_data in sessions.items()
        if session_data.get("expires_at", 0) < current_time
    ]

    # 만료된 세션 제거
    for session_id in expired_sessions:
        if session_id in sessions:
            del sessions[session_id]

    if expired_sessions:
        logger.info(f"만료된 세션 {len(expired_sessions)}개 정리 완료")

    # 다음 정리 예약
    cleanup_timer = threading.Timer(cleanup_interval, cleanup_expired_sessions)
    cleanup_timer.daemon = True
    cleanup_timer.start()


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


def create_session(user_data: Dict[str, Any]) -> str:
    """
    새로운 세션을 생성하고 세션 ID를 반환합니다.

    Args:
        user_data: 세션에 저장할 사용자 데이터

    Returns:
        str: 생성된 세션 ID
    """
    # 세션 ID 생성
    session_id = str(uuid.uuid4())

    # 만료 시간 계산 (현재 시간 + 설정된 시간)
    expires_at = int(time.time()) + (settings.SESSION_EXPIRE_HOURS * 3600)

    # 세션 데이터 구성
    session_data = {
        "user_id": user_data.get("user_id"),
        "user_role": user_data.get("user_role"),
        "user_department": user_data.get("user_department"),
        "created_at": int(time.time()),
        "expires_at": expires_at,
    }

    # 세션 저장
    sessions[session_id] = session_data

    # 첫 번째 세션이라면 정리 타이머 시작
    if len(sessions) == 1 and not cleanup_timer:
        cleanup_expired_sessions()

    logger.info(f"세션 생성: {session_id[:8]}... (사용자: {user_data.get('user_id')})")
    return session_id


def get_session(session_id: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    세션 ID로 세션 데이터를 조회합니다.

    Args:
        session_id: 세션 ID

    Returns:
        dict: 세션 데이터 또는 None (세션이 없거나 만료된 경우)
    """
    if not session_id or session_id not in sessions:
        return None

    # 세션 데이터 조회
    session_data = sessions.get(session_id)

    # 세션 만료 확인
    current_time = int(time.time())
    if session_data and session_data.get("expires_at", 0) < current_time:
        # 만료된 세션 제거
        del sessions[session_id]
        logger.info(f"만료된 세션 삭제: {session_id[:8]}...")
        return None

    # 세션 갱신 (만료 시간 연장)
    if session_data:
        session_data["expires_at"] = current_time + (
            settings.SESSION_EXPIRE_HOURS * 3600
        )

    return session_data


def delete_session(session_id: str) -> bool:
    """
    세션을 삭제합니다.

    Args:
        session_id: 세션 ID

    Returns:
        bool: 삭제 성공 여부
    """
    if session_id in sessions:
        user_id = sessions[session_id].get("user_id")
        del sessions[session_id]
        logger.info(f"세션 삭제: {session_id[:8]}... (사용자: {user_id})")
        return True
    return False


def get_current_user(request: Request) -> Dict[str, Any]:
    """
    현재 요청의 세션에서 사용자 정보를 가져옵니다.

    Args:
        request: FastAPI 요청 객체

    Returns:
        dict: 사용자 정보

    Raises:
        HTTPException: 인증되지 않은 경우
    """
    session_id = request.cookies.get("session_id")
    session_data = get_session(session_id)

    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="인증이 필요합니다"
        )

    return session_data


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
        HTTPException: 관리자가 아닌 경우
    """
    if user_data.get("user_role") != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="관리자 권한이 필요합니다"
        )

    return user_data
