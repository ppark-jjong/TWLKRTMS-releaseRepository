"""
비밀번호 검증 함수 패치 - 로깅 기능 추가
보안 유틸리티의 함수를 대체하세요.
"""

import bcrypt
import logging

logger = logging.getLogger(__name__)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """해시화된 비밀번호와 일반 텍스트 비밀번호를 비교합니다."""
    # 함수 진입 로깅
    # logger.debug("비밀번호 해시 검증 시작") # 프로덕션에서 불필요한 로그 제거

    try:
        # 문자열을 바이트로 변환
        plain_password_bytes = plain_password.encode("utf-8")
        # logger.debug("일반 비밀번호 바이트 변환 완료") # 프로덕션에서 불필요한 로그 제거

        hashed_password_bytes = hashed_password.encode("utf-8")
        # logger.debug("해시 비밀번호 바이트 변환 완료") # 프로덕션에서 불필요한 로그 제거

        # bcrypt로 비밀번호 검증
        result = bcrypt.checkpw(plain_password_bytes, hashed_password_bytes)

        # 검증 결과 로깅 (비밀번호 내용 자체는 로깅하지 않음)
        if result:
            # logger.debug("비밀번호 검증 결과: 일치") # 프로덕션에서 불필요한 로그 제거
            pass  # debug 로그만 있었으므로 pass 추가
        else:
            # logger.debug("비밀번호 검증 결과: 불일치") # 프로덕션에서 불필요한 로그 제거
            pass  # debug 로그만 있었으므로 pass 추가

        return result

    except Exception as e:
        # 상세 오류 로깅
        logger.error(f"비밀번호 검증 중 오류 발생: {str(e)}", exc_info=True)
        return False
