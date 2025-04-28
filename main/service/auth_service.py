"""
인증 관련 서비스 로직
"""

from typing import Dict, Optional, Tuple, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from main.models.user_model import User
from main.utils.security import verify_password, create_session
from main.utils.logger import logger


def authenticate_user(
    db: Session, user_id: str, password: str
) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    사용자 인증을 수행하는 서비스 함수

    Args:
        db: 데이터베이스 세션
        user_id: 사용자 ID
        password: 사용자 비밀번호

    Returns:
        Tuple[bool, Optional[Dict]]: 인증 성공 여부와 사용자 정보
    """
    # 사용자 ID로 사용자 검색
    user = db.query(User).filter(User.user_id == user_id).first()

    # 사용자가 없는 경우
    if not user:
        logger.warning(f"로그인 실패: 사용자 ID '{user_id}'를 찾을 수 없음")
        return False, None

    # 비밀번호 검증
    if not verify_password(password, user.user_password):
        logger.warning(f"로그인 실패: 사용자 '{user_id}'의 비밀번호가 일치하지 않음")
        return False, None

    # 인증 성공: 사용자 정보 반환
    user_data = {
        "user_id": user.user_id,
        "user_role": user.user_role,
        "user_department": user.user_department,
    }

    logger.info(f"로그인 성공: 사용자 '{user_id}'")
    return True, user_data


def create_user_session(user_data: Dict[str, Any]) -> str:
    """
    사용자 세션을 생성하는 서비스 함수

    Args:
        user_data: 세션에 저장할 사용자 데이터

    Returns:
        str: 생성된 세션 ID
    """
    try:
        # 세션 생성 (security.py의 create_session 함수 사용)
        session_id = create_session(user_data)
        logger.info(f"세션 생성 성공: 사용자 '{user_data.get('user_id')}'")
        return session_id
    except Exception as e:
        # 세션 생성 실패
        logger.error(f"세션 생성 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="세션 생성 중 오류가 발생했습니다",
        )
