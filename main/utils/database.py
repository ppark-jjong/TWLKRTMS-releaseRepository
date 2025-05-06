"""
데이터베이스 연결 설정
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import logging
from functools import wraps
from fastapi import Depends
import os

from main.utils.config import get_settings

settings = get_settings()

logger = logging.getLogger(__name__)

# 환경에 따른 데이터베이스 연결 정보 로깅
logger.info("=== 데이터베이스 설정 확인 ===")
logger.info(f"MYSQL_HOST: {settings.MYSQL_HOST}")
logger.info(f"MYSQL_PORT: {settings.MYSQL_PORT}")
logger.info(f"MYSQL_DATABASE: {settings.MYSQL_DATABASE}")
logger.info(f"GAE_ENV: {os.getenv('GAE_ENV', '없음')}")
logger.info(
    f"연결 URL 패턴: mysql+pymysql://[user]@{settings.MYSQL_HOST}{'/' if os.getenv('GAE_ENV', '').startswith('standard') else ':' + str(settings.MYSQL_PORT) + '/'}{settings.MYSQL_DATABASE}"
)
logger.info("===========================")

# SQLAlchemy 엔진 생성
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # 연결 유효성 검사
    pool_recycle=3600,  # 1시간마다 연결 재활용
    pool_size=5,  # 연결 풀 크기
    max_overflow=10,  # 최대 초과 연결 수
)

# 세션 팩토리 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 베이스 모델 생성
Base = declarative_base()


# 데이터베이스 연결 테스트
def test_db_connection():
    """
    데이터베이스 연결을 간단히 테스트하고 결과 로그를 남깁니다.
    프로젝트 규칙에 따라 최초 한 번만 시도합니다.
    """
    from sqlalchemy import text
    import socket

    try:
        logger.info("=====================================================")
        logger.info("데이터베이스 연결 테스트 시작...")

        # 환경 정보 로깅
        is_gae = os.getenv("GAE_ENV", "").startswith("standard")
        logger.info(f"환경: {'GAE 프로덕션' if is_gae else '로컬/개발'}")
        logger.info(f"호스트 IP: {socket.gethostbyname(socket.gethostname())}")

        # 상세 연결 정보 로깅
        logger.info(f"연결 대상: {settings.MYSQL_HOST}:{settings.MYSQL_PORT}")
        logger.info(f"데이터베이스: {settings.MYSQL_DATABASE}")
        logger.info(f"사용자: {settings.MYSQL_USER}")
        logger.info(
            f"비밀번호 길이: {len(settings.MYSQL_PASSWORD) if settings.MYSQL_PASSWORD else 0}"
        )

        # 연결 URL 로깅 (비밀번호 마스킹)
        safe_url = settings.DATABASE_URL.replace(settings.MYSQL_PASSWORD, "******")
        logger.info(f"생성된 연결 URL: {safe_url}")

        # 먼저 IP 주소로 연결 가능한지 소켓으로 확인 (MySQL 서버까지 네트워크 연결 가능성 확인)
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)  # 5초 타임아웃
            result = sock.connect_ex((settings.MYSQL_HOST, settings.MYSQL_PORT))
            sock.close()

            if result == 0:
                logger.info(
                    f"소켓 테스트: {settings.MYSQL_HOST}:{settings.MYSQL_PORT}에 연결 가능"
                )
            else:
                logger.warning(
                    f"소켓 테스트: {settings.MYSQL_HOST}:{settings.MYSQL_PORT}에 연결 불가 (오류코드: {result})"
                )
        except Exception as sock_err:
            logger.warning(f"소켓 연결 테스트 실패: {str(sock_err)}")

        # 실제 데이터베이스 연결 시도
        logger.info("SQLAlchemy로 데이터베이스 연결 시도...")
        with engine.connect() as conn:
            # MySQL 버전 확인
            result = conn.execute(text("SELECT VERSION()"))
            version = result.fetchone()[0]

            # 현재 사용자 확인
            result = conn.execute(text("SELECT CURRENT_USER()"))
            current_user = result.fetchone()[0]

            logger.info(f"데이터베이스 연결 성공!")
            logger.info(f"MySQL 버전: {version}")
            logger.info(f"연결된 사용자: {current_user}")
            logger.info("=====================================================")

            return True
    except Exception as e:
        logger.error("=====================================================")
        logger.error(f"데이터베이스 연결 실패: {str(e)}")

        # 오류 메시지에서 'Access denied' 문자열 확인
        error_msg = str(e).lower()
        if "access denied" in error_msg:
            logger.error("원인: MySQL 사용자 접근 권한 문제")
            logger.error("해결 방법:")
            logger.error("1. Cloud SQL에서 다음 SQL 명령어로 사용자 권한 설정:")
            logger.error(
                "   CREATE USER 'teckwahkr-db'@'%' IDENTIFIED BY 'teckwah0206';"
            )
            logger.error(
                "   GRANT ALL PRIVILEGES ON delivery_system.* TO 'teckwahkr-db'@'%';"
            )
            logger.error("   FLUSH PRIVILEGES;")

            # 오류 메시지에서 실제 IP 주소 추출 시도
            import re

            ip_match = re.search(r"'([^']*)'@'([^']*)'", error_msg)
            if ip_match:
                connecting_ip = ip_match.group(2)
                logger.error(
                    f"2. 연결 시도 IP: {connecting_ip} - 이 IP에 대한 권한이 필요합니다."
                )

        # 연결 URL 부분 마스킹 (비밀번호 제외)
        parts = settings.DATABASE_URL.split("@")
        if len(parts) > 1:
            masked_url = f"...@{parts[1]}"
            logger.error(f"사용된 연결 URL: {masked_url}")

        logger.error(f"설정된 DB 호스트: {settings.MYSQL_HOST}:{settings.MYSQL_PORT}")
        logger.error(f"설정된 DB 이름: {settings.MYSQL_DATABASE}")
        logger.error("=====================================================")

        return False


# 주의: 초기 DB 연결 테스트는 main.py에서 한 번만 수행합니다.
# 여기서는 별도로 초기화하지 않고 함수만 제공합니다.


# FastAPI의 Depends와 함께 사용하기 위한 의존성 함수
def get_db() -> Generator[Session, None, None]:
    """
    데이터베이스 세션 의존성 함수
    세션을 자동으로 닫고 예외 발생 시 롤백 처리
    """
    import uuid

    # 각 세션 요청에 고유 ID 부여하여 추적
    session_id = str(uuid.uuid4())[:8]
    logger.info(f"DB 세션 시작 [세션ID: {session_id}]")

    db = SessionLocal()
    try:
        logger.info(f"DB 세션 생성 완료 [세션ID: {session_id}]")
        yield db
        db.commit()
        logger.info(f"DB 트랜잭션 커밋 완료 [세션ID: {session_id}]")
    except Exception as e:
        db.rollback()
        logger.error(f"DB 트랜잭션 롤백: {str(e)} [세션ID: {session_id}]")
        # 오류 세부 정보 기록
        import traceback

        logger.error(
            f"DB 오류 상세 내용: {traceback.format_exc()} [세션ID: {session_id}]"
        )
        raise
    finally:
        db.close()
        logger.info(f"DB 세션 종료 [세션ID: {session_id}]")


# 트랜잭션 관리 데코레이터
def db_transaction(func):
    """
    API 엔드포인트 함수에 적용하여 DB 트랜잭션을 자동으로 관리하는 데코레이터.
    함수 실행 성공 시 커밋, 예외 발생 시 롤백.
    `db: Session = Depends(get_db)` 파라미터를 함수 시그니처에 포함해야 함.
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        # 함수 인자에서 db 세션 찾기
        db = kwargs.get("db")
        if not db:
            # Depends로 주입되지 않은 경우 예외 발생
            raise ValueError(
                "db_transaction 데코레이터는 'db: Session = Depends(get_db)' 인자가 필요합니다."
            )

        try:
            result = await func(*args, **kwargs)
            db.commit()  # 명시적 커밋
            return result
        except Exception as e:
            db.rollback()  # 명시적 롤백
            logger.error(
                f"DB 트랜잭션 롤백 (데코레이터): 함수 {func.__name__}, 오류: {str(e)}",
                exc_info=True,
            )
            # 원래 예외를 다시 발생시켜 FastAPI 에러 핸들러가 처리하도록 함
            raise e
        # finally 블록은 get_db() 에서 세션 close를 처리하므로 여기서는 불필요

    return wrapper
