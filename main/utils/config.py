"""
설정 파일 - 간소화된 환경 변수 및 애플리케이션 설정 관리
"""

import os
import time
from typing import List, Dict, Any
from functools import lru_cache
import logging

# 시스템 전체 타임존을 Asia/Seoul로 설정
os.environ['TZ'] = 'Asia/Seoul'
try:
    time.tzset()  # 타임존 적용
except AttributeError:
    # Windows 환경에서는 tzset()이 지원되지 않음
    pass

try:
    from dotenv import load_dotenv

    # 환경 변수 로드 - Docker와 로컬 환경 모두 확인
    env_paths = [
        "/app/.env",  # Docker 컨테이너 내부 경로
        os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),  # 프로젝트 루트
        os.path.join(os.path.dirname(__file__), ".env"),  # backend 폴더
    ]
    
    env_loaded = False
    for env_path in env_paths:
        if os.path.exists(env_path):
            load_dotenv(env_path)
            logging.info(f".env 파일을 로드했습니다: {env_path}")
            env_loaded = True
            break
            
    if not env_loaded:
        logging.warning("어떤 .env 파일도 찾을 수 없습니다. 기본 환경 변수를 사용합니다.")
        
except ImportError:
    logging.warning(
        "python-dotenv 패키지가 설치되지 않았습니다. 기본 환경 변수를 사용합니다."
    )


def parse_comma_separated_list(value: str) -> List[str]:
    """콤마로 구분된 문자열을 리스트로 변환"""
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


class Settings:
    """애플리케이션 설정 - pydantic을 사용하지 않는 간소화된 설정 클래스"""

    def __init__(self):
        # 서버 설정
        self.DEBUG = os.getenv("DEBUG", "False").lower() == "true"
        self.PORT = int(os.getenv("PORT", "8080"))

        # 콤마로 구분된 문자열을 리스트로 변환
        origins_env = os.getenv("ALLOWED_ORIGINS", "http://localhost:8080")
        self.ALLOWED_ORIGINS = parse_comma_separated_list(origins_env)

        # 데이터베이스 설정
        self.MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
        self.MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
        self.MYSQL_USER = os.getenv("MYSQL_USER", "root")
        self.MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "1234")
        self.MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "delivery_system")
        self.MYSQL_CHARSET = os.getenv("MYSQL_CHARSET", "utf8mb4")

        # 인증 설정
        self.SESSION_SECRET = os.getenv(
            "SESSION_SECRET",
            "4a24ff058be1925b52a62b9d594b367a600dde8730e647d2d29c9b2f7c7f6fff",
        )
        self.SESSION_EXPIRE_HOURS = int(os.getenv("SESSION_EXPIRE_HOURS", "24"))

        # 락 관련 설정 (5분 = 300초)
        self.LOCK_TIMEOUT_SECONDS = int(os.getenv("LOCK_TIMEOUT_SECONDS", "300"))
        self.LOCK_CLEANUP_INTERVAL_MINUTES = int(
            os.getenv("LOCK_CLEANUP_INTERVAL_MINUTES", "10")
        )

        # 설정 로드 로그
        logging.debug("애플리케이션 설정이 로드되었습니다")
        logging.debug(f"DEBUG: {self.DEBUG}")
        logging.debug(f"ALLOWED_ORIGINS: {self.ALLOWED_ORIGINS}")

    # 로그 경로 설정 - Docker와 로컬 환경 모두 고려
    @property
    def LOG_DIR(self) -> str:
        if os.path.exists("/app"):
            return "/app/backend/logs"
        return os.path.join(os.path.dirname(__file__), "logs")

    # DB 연결 문자열
    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}?charset={self.MYSQL_CHARSET}"


@lru_cache()
def get_settings() -> Settings:
    """
    설정 객체 싱글톤 반환 (캐싱 적용)
    """
    return Settings()
