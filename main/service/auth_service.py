"""
인증 관련 서비스 로직
"""

from typing import Dict, Optional, Tuple, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import logging

from main.models.user_model import User
from main.utils.security import verify_password


def authenticate_user(
    db: Session, user_id: str, user_password: str
) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    사용자 인증을 수행하는 서비스 함수

    Args:
        db: 데이터베이스 세션
        user_id: 사용자 ID
        user_password: 사용자 비밀번호

    Returns:
        Tuple[bool, Optional[Dict]]: 인증 성공 여부와 사용자 정보
    """
    # 함수 진입 로깅
    logging.info(f"인증 프로세스 시작: 사용자 ID '{user_id}'")

    try:
        # 쿼리 실행 전 로깅
        # logging.debug(f"DB 쿼리 시작: User.user_id='{user_id}' 검색") # 프로덕션에서 불필요한 로그 제거

        # 사용자 ID로 사용자 검색
        user = db.query(User).filter(User.user_id == user_id).first()

        # 쿼리 결과 로깅
        if user:
            # logging.debug(f"DB 쿼리 성공: 사용자 '{user_id}' 정보 로드 완료") # 프로덕션에서 불필요한 로그 제거
            pass  # user가 있을 때 debug 로그만 있었으므로 pass 추가
        else:
            logging.warning(f"로그인 실패: 사용자 ID '{user_id}'를 찾을 수 없음")
            return False, None

        # 비밀번호 검증 시작 로깅
        # logging.debug(f"비밀번호 검증 시작: 사용자 '{user_id}'") # 프로덕션에서 불필요한 로그 제거

        # 비밀번호 검증
        is_valid_password = verify_password(user_password, user.user_password)

        # 비밀번호 검증 결과 로깅
        if not is_valid_password:
            logging.warning(
                f"로그인 실패: 사용자 '{user_id}'의 비밀번호가 일치하지 않음"
            )
            return False, None

        # 인증 성공 시 사용자 정보 구성
        user_data = {
            "user_id": user.user_id,
            "user_name": user.user_name,
            "user_role": user.user_role,
            "user_department": user.user_department,
        }

        # 성공 로깅
        logging.info(
            f"로그인 성공: 사용자 '{user_id}', 권한='{user.user_role}', 부서='{user.user_department}'"
        )
        return True, user_data

    except Exception as e:
        # 예외 발생 시 상세 로깅
        logging.error(f"인증 프로세스 중 오류 발생: {str(e)}", exc_info=True)
        return False, None
