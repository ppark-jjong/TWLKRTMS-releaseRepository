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

# 최초 1회만 디버깅을 위한 정보 로깅 (로깅 중복 감소)
_connection_logged = False

def log_db_connection_info():
    global _connection_logged
    if not _connection_logged:
        logger.info("=== 데이터베이스 설정 확인 ===")
        logger.info(f"MYSQL_HOST: {settings.MYSQL_HOST}")
        logger.info(f"MYSQL_PORT: {settings.MYSQL_PORT}")
        logger.info(f"MYSQL_DATABASE: {settings.MYSQL_DATABASE}")
        logger.info(f"GAE_ENV: {os.getenv('GAE_ENV', '없음')}")
        logger.info(
            f"연결 URL 패턴: mysql+pymysql://[user]@{settings.MYSQL_HOST}{'/' if os.getenv('GAE_ENV', '').startswith('standard') else ':' + str(settings.MYSQL_PORT) + '/'}{settings.MYSQL_DATABASE}"
        )
        logger.info("===========================")
        _connection_logged = True

# 최초 1회 로깅
log_db_connection_info()

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


# 데이터베이스 연결 테스트 (최초 1회만 실행되도록)
_db_connection_tested = False

def test_db_connection():
    """
    데이터베이스 연결을 간단히 테스트하고 결과 로그를 남깁니다.
    프로젝트 규칙에 따라 최초 한 번만 시도합니다.
    """
    global _db_connection_tested
    if _db_connection_tested:
        logger.debug("데이터베이스 연결 테스트 이미 수행됨. 중복 실행 방지.")
        return True
    
    from sqlalchemy import text
    import socket

    try:
        logger.info("=====================================================")
        logger.info("데이터베이스 연결 테스트 시작...")

        # 환경 정보 로깅
        is_gae = os.getenv("GAE_ENV", "").startswith("standard")
        logger.info(f"환경: {'GAE 프로덕션' if is_gae else '로컬/개발'}")
        
        # 상세 연결 정보 로깅 (축소)
        logger.info(f"연결 대상: {settings.MYSQL_HOST}:{settings.MYSQL_PORT}")
        logger.info(f"데이터베이스: {settings.MYSQL_DATABASE}")

        # 실제 데이터베이스 연결 시도 (간소화된 로직)
        logger.info("데이터베이스 연결 시도...")
        try:
            # 직접 pymysql로 연결 시도 (저수준)
            import pymysql
            conn = pymysql.connect(
                host=settings.MYSQL_HOST,
                user=settings.MYSQL_USER,
                password=settings.MYSQL_PASSWORD,
                database=settings.MYSQL_DATABASE,
                port=settings.MYSQL_PORT,
                connect_timeout=5,
                charset='utf8mb4'
            )
            
            with conn.cursor() as cursor:
                cursor.execute("SELECT VERSION()")
                version = cursor.fetchone()[0]
                cursor.execute("SELECT CURRENT_USER()")
                current_user = cursor.fetchone()[0]
            
            logger.info(f"데이터베이스 직접 연결 성공!")
            logger.info(f"MySQL 버전: {version}")
            logger.info(f"연결된 사용자: {current_user}")
            conn.close()
            
            # SQLAlchemy 연결도 확인
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                sqlalchemy_result = result.fetchone()[0]
                
            logger.info(f"SQLAlchemy 연결 성공: {sqlalchemy_result}")
            logger.info("=====================================================")
            
            _db_connection_tested = True
            return True
        except Exception as direct_err:
            logger.error(f"직접 연결 실패: {str(direct_err)}")
            raise
            
    except Exception as e:
        logger.error("=====================================================")
        logger.error(f"데이터베이스 연결 실패: {str(e)}")

        # 간단한 오류 메시지 (축소됨)
        error_msg = str(e).lower()
        if "access denied" in error_msg:
            logger.error("원인: MySQL 사용자 접근 권한 문제")
        elif "connect" in error_msg and "timeout" in error_msg:
            logger.error("원인: 연결 타임아웃 - 방화벽 또는 VPC 설정 확인 필요")
        elif "unknown host" in error_msg:
            logger.error("원인: 알 수 없는 호스트 - IP 주소가 올바른지 확인하세요")
        
        logger.error("=====================================================")

        _db_connection_tested = True  # 실패해도 중복 실행 방지를 위해 플래그 설정
        return False


# 주의: 초기 DB 연결 테스트는 main.py에서 한 번만 수행합니다.
# 여기서는 별도로 초기화하지 않고 함수만 제공합니다.


# 세션 로깅 레벨을 DEBUG로 변경하여 일반 로그에서는 표시되지 않도록 함
# FastAPI의 Depends와 함께 사용하기 위한 의존성 함수
def get_db() -> Generator[Session, None, None]:
    """
    데이터베이스 세션 의존성 함수
    세션을 자동으로 닫고 예외 발생 시 롤백 처리
    """
    import uuid

    # 각 세션 요청에 고유 ID 부여하여 추적
    session_id = str(uuid.uuid4())[:8]
    # DEBUG 레벨로 변경하여 일반 INFO 로그에서는 표시되지 않게 함
    logger.debug(f"DB 세션 시작 [세션ID: {session_id}]")

    db = SessionLocal()
    try:
        logger.debug(f"DB 세션 생성 완료 [세션ID: {session_id}]") 
        yield db
        db.commit()
        logger.debug(f"DB 트랜잭션 커밋 완료 [세션ID: {session_id}]")
    except Exception as e:
        db.rollback()
        # 오류는 여전히 ERROR 레벨로 로깅
        logger.error(f"DB 트랜잭션 롤백: {str(e)} [세션ID: {session_id}]")
        # 오류 세부 정보 기록
        import traceback

        logger.error(
            f"DB 오류 상세 내용: {traceback.format_exc()} [세션ID: {session_id}]"
        )
        raise
    finally:
        db.close()
        logger.debug(f"DB 세션 종료 [세션ID: {session_id}]")


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
