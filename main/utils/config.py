"""
설정 파일 - GAE 프로덕션 환경용 환경 변수 및 애플리케이션 설정 관리
"""

import os
import time
from typing import List, Dict, Any
from functools import lru_cache
import logging
import urllib.parse  # URL 인코딩을 위해 추가

# 로깅 설정
logger = logging.getLogger(__name__)

# 시스템 전체 타임존을 Asia/Seoul로 설정
os.environ["TZ"] = "Asia/Seoul"
try:
    time.tzset()  # 타임존 적용
except AttributeError:
    # Windows 환경에서는 tzset()이 지원되지 않음
    pass


def parse_comma_separated_list(value: str) -> List[str]:
    """콤마로 구분된 문자열을 리스트로 변환"""
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


class Settings:
    """애플리케이션 설정 - GAE 프로덕션 환경 전용"""

    def __init__(self):
        # 서버 설정
        self.DEBUG = False  # 프로덕션 환경에서는 항상 False
        self.PORT = int(os.getenv("PORT", "8080"))
        self.LOG_LEVEL = "INFO"  # 프로덕션 환경에서 기본 로그 레벨

        # CORS 설정
        origins_env = os.getenv("ALLOWED_ORIGINS", "https://twlkr-tms.du.r.appspot.com")
        self.ALLOWED_ORIGINS = parse_comma_separated_list(origins_env)

        # 데이터베이스 설정
        self.MYSQL_HOST = os.getenv("MYSQL_HOST", "10.113.80.3")
        self.MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
        self.MYSQL_USER = os.getenv("MYSQL_USER", "teckwahkr-user")
        self.MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "teckwah0206")
        self.MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "delivery_system")
        self.MYSQL_CHARSET = os.getenv("MYSQL_CHARSET", "utf8mb4")

        # 인증 설정
        self.SESSION_SECRET = os.getenv(
            "SESSION_SECRET",
            "bbdcf8bf3de489b385cc6307ce420ad563ba4848c201fa9d003cdb4efdab42da",
        )
        self.SESSION_EXPIRE_HOURS = int(os.getenv("SESSION_EXPIRE_HOURS", "24"))

        # 설정 로드 로그
        logger.info("=== GAE 프로덕션 애플리케이션 설정 로드 ===")
        logger.info(f"DEBUG: {self.DEBUG}")
        logger.info(f"PORT: {self.PORT}")
        logger.info(f"ALLOWED_ORIGINS: {self.ALLOWED_ORIGINS}")
        logger.info(f"MYSQL_HOST: {self.MYSQL_HOST}")
        logger.info(f"MYSQL_DATABASE: {self.MYSQL_DATABASE}")
        logger.info(f"MYSQL_USER: {self.MYSQL_USER}")
        logger.info(
            f"MYSQL_PASSWORD 설정 여부: {'YES' if self.MYSQL_PASSWORD else 'NO'}"
        )
        logger.info("=============================")

    # DB 연결 문자열 - GAE 프로덕션 환경 전용
    # 로깅 중복 방지용 플래그
    _db_url_logged = False

    @property
    def DATABASE_URL(self) -> str:
        """
        데이터베이스 연결 URL 생성
        명시적인 IP 주소를 사용하여 DNS 관련 문제 방지
        """
        # 사용자 이름과 비밀번호 URL 인코딩
        try:
            # 기본 연결 방식 사용 (URL 인코딩 없이 시도)
            user = self.MYSQL_USER
            password = self.MYSQL_PASSWORD
            # 명시적 IP 주소 사용 (DNS 대신)
            host = self.MYSQL_HOST  # 현재 10.54.192.10

            # 로깅은 최초 1회만 수행
            if not Settings._db_url_logged:
                # 디버깅을 위한 로깅 추가
                logger.info(f"DB 연결 정보 - MYSQL_USER: '{user}'")
                logger.info(
                    f"DB 연결 정보 - MYSQL_PASSWORD 설정 여부: {'YES' if password else 'NO'}"
                )
                logger.info(f"DB 연결 정보 - MYSQL_HOST: '{host}' (명시적 IP 사용)")

                # 마스킹된 URL 로깅
                masked_url = f"mysql+pymysql://{user}:{'*****'}@{host}/{self.MYSQL_DATABASE}?charset={self.MYSQL_CHARSET}"
                logger.info(f"생성된 DB 연결 URL(마스킹됨): {masked_url}")
                Settings._db_url_logged = True

            # 단순화된 연결 문자열
            return f"mysql+pymysql://{user}:{password}@{host}/{self.MYSQL_DATABASE}?charset={self.MYSQL_CHARSET}"
        except Exception as e:
            # 예외 발생시 상세 로깅
            logger.error(f"DB 연결 URL 생성 중 오류 발생: {str(e)}")
            # 환경 변수 직접 로깅
            logger.error(
                f"환경변수 직접 확인 - MYSQL_USER: '{os.getenv('MYSQL_USER', '')}'"
            )
            logger.error(
                f"환경변수 직접 확인 - MYSQL_HOST: '{os.getenv('MYSQL_HOST', '')}'"
            )
            # 기본값으로 재시도
            return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}/{self.MYSQL_DATABASE}?charset={self.MYSQL_CHARSET}"


@lru_cache()
def get_settings() -> Settings:
    """
    설정 객체 싱글톤 반환 (캐싱 적용)
    """
    return Settings()
