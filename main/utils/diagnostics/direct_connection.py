"""
직접 연결 모듈
Cloud SQL 연결 문제 해결을 위한 직접 연결 메커니즘 제공
"""

import logging
import pymysql
from functools import lru_cache

logger = logging.getLogger(__name__)

class DirectMySQLConnection:
    """
    SQLAlchemy를 우회하고 직접 pymysql로 데이터베이스에 연결하는 클래스
    연결 실패 시 폴백 메커니즘으로 사용
    """
    
    def __init__(self, host, user, password, database, port=3306):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.port = port
        self.connection = None
        
    def connect(self):
        """데이터베이스에 연결"""
        if self.connection is not None:
            return
            
        logger.info(f"[직접연결] {self.host}:{self.port}에 직접 연결 시도")
        self.connection = pymysql.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.database,
            port=self.port,
            charset='utf8mb4',
            connect_timeout=5
        )
        logger.info(f"[직접연결] 성공")
        
    def disconnect(self):
        """연결 종료"""
        if self.connection is not None:
            self.connection.close()
            self.connection = None
            logger.info(f"[직접연결] 연결 종료")
            
    def execute_query(self, query, params=None):
        """
        쿼리 실행 및 결과 반환
        SELECT 쿼리의 경우 결과를 딕셔너리 리스트로 반환
        """
        if self.connection is None:
            self.connect()
            
        try:
            with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute(query, params)
                if query.strip().upper().startswith('SELECT'):
                    result = cursor.fetchall()
                    return result
                else:
                    self.connection.commit()
                    return {'affected_rows': cursor.rowcount}
        except Exception as e:
            logger.error(f"[직접연결] 쿼리 실행 오류: {str(e)}")
            if self.connection:
                self.connection.rollback()
            raise
            
    def __enter__(self):
        """컨텍스트 매니저 진입"""
        self.connect()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료"""
        self.disconnect()


# 싱글톤 인스턴스를 제공하는 함수
@lru_cache(maxsize=1)
def get_direct_connection():
    """
    직접 연결 인스턴스 제공 (싱글톤)
    데이터베이스 설정은 settings에서 가져옴
    """
    from main.utils.config import get_settings
    settings = get_settings()
    
    return DirectMySQLConnection(
        host=settings.MYSQL_HOST,
        user=settings.MYSQL_USER,
        password=settings.MYSQL_PASSWORD,
        database=settings.MYSQL_DATABASE,
        port=settings.MYSQL_PORT
    )


# 예제: 직접 연결로 간단한 쿼리 실행
def test_direct_connection():
    """직접 연결 테스트"""
    try:
        with get_direct_connection() as conn:
            result = conn.execute_query("SELECT VERSION() as version")
            if result:
                logger.info(f"[직접연결] MySQL 버전: {result[0]['version']}")
                return True
            return False
    except Exception as e:
        logger.error(f"[직접연결] 테스트 실패: {str(e)}")
        return False
