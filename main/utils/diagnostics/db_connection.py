"""
데이터베이스 연결 진단 유틸리티
App Engine과 Cloud SQL 간 연결 문제를 진단하고 해결하기 위한 모듈
"""

import os
import socket
import logging
from datetime import datetime
import pymysql
from sqlalchemy import text
from functools import lru_cache

logger = logging.getLogger(__name__)

# 단 한 번만 실행되도록 캐싱
@lru_cache(maxsize=1)
def diagnose_db_connection():
    """
    데이터베이스 연결 진단 - 최초 1회만 실행
    TCP 소켓 연결 및 실제 MySQL 연결 테스트 수행
    """
    try:
        from main.utils.config import get_settings
        settings = get_settings()
        
        # 기본 환경 정보
        host = settings.MYSQL_HOST
        user = settings.MYSQL_USER
        password = settings.MYSQL_PASSWORD
        database = settings.MYSQL_DATABASE
        port = settings.MYSQL_PORT
        
        # 로그 접두어로 쉽게 필터링 가능하게 함
        logger.info(f"[DB진단] 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"[DB진단] GAE -> Cloud SQL 직접 연결 테스트")
        logger.info(f"[DB진단] 대상: {host}:{port}")
        
        # 1. 소켓 TCP 연결 테스트 (MySQL 서버 포트 접근 가능 여부)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)  # 3초 타임아웃
        result = sock.connect_ex((host, port))
        sock.close()
        
        tcp_conn_status = '성공' if result == 0 else f'실패(코드:{result})'
        logger.info(f"[DB진단] TCP 연결: {tcp_conn_status}")
        
        # 2. 실제 DB 연결 테스트 (TCP 연결 성공 시만)
        if result == 0:
            try:
                # 저수준 pymysql 직접 연결 시도
                logger.info(f"[DB진단] 저수준 pymysql 직접 연결 시도...")
                conn = pymysql.connect(
                    host=host,
                    user=user,
                    password=password,
                    database=database,
                    connect_timeout=5
                )
                
                with conn.cursor() as cursor:
                    cursor.execute("SELECT VERSION()")
                    version = cursor.fetchone()[0]
                
                logger.info(f"[DB진단] MySQL 연결 성공: 버전 {version}")
                conn.close()
                
                # 3. VPC 네트워크 정보 확인 (참고용)
                try:
                    # 현재 GAE 인스턴스의 내부 IP 확인
                    local_ip = socket.gethostbyname(socket.gethostname())
                    logger.info(f"[DB진단] 현재 GAE 인스턴스 IP: {local_ip}")
                    
                    # VPC 커넥터 설정 확인
                    vpc_connector = os.environ.get("VPC_CONNECTOR", "설정 없음")
                    logger.info(f"[DB진단] VPC 커넥터: {vpc_connector}")
                except Exception as e:
                    logger.warning(f"[DB진단] 네트워크 정보 수집 실패: {str(e)}")
                
                return True
            except Exception as db_err:
                logger.error(f"[DB진단] MySQL 연결 실패: {str(db_err)}")
                
                # 오류 원인 분석
                error_msg = str(db_err).lower()
                if "access denied" in error_msg:
                    logger.error(f"[DB진단] 원인: 사용자 권한 문제 (액세스 거부)")
                elif "timeout" in error_msg:
                    logger.error(f"[DB진단] 원인: 연결 타임아웃 (방화벽 또는 네트워크 문제)")
                elif "unknown host" in error_msg:
                    logger.error(f"[DB진단] 원인: 알 수 없는 호스트 (DNS 문제)")
                else:
                    logger.error(f"[DB진단] 원인: 기타 문제 - {error_msg}")
                
                return False
        else:
            # TCP 연결 실패 원인 분석
            if result == 111:  # Connection refused
                logger.error(f"[DB진단] 원인: 연결 거부 - DB 서버가 실행 중이 아니거나 포트가 열려있지 않음")
            elif result == 110:  # Connection timed out
                logger.error(f"[DB진단] 원인: 타임아웃 - 방화벽 규칙 또는 네트워크 문제")
            elif result == 113:  # No route to host
                logger.error(f"[DB진단] 원인: 호스트 경로 없음 - VPC 연결 문제")
            else:
                logger.error(f"[DB진단] 원인: 알 수 없는 오류 코드 {result}")
            
            return False
            
    except Exception as e:
        logger.error(f"[DB진단] 예상치 못한 오류 발생: {str(e)}")
        return False
    finally:
        logger.info(f"[DB진단] 완료")


# 직접 pymysql로 연결 시도 (대체 방법)
@lru_cache(maxsize=1)
def try_direct_mysql_connection():
    """
    SQLAlchemy를 우회하고 직접 pymysql로 연결 시도 (문제 해결용)
    """
    try:
        from main.utils.config import get_settings
        settings = get_settings()
        
        logger.info("[DB대체연결] 직접 pymysql 연결 시도 시작")
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
            cursor.execute("SELECT 1")  # 간단한 쿼리로 연결 확인
            result = cursor.fetchone()
            logger.info(f"[DB대체연결] 성공: {result}")
        
        conn.close()
        return True
    except Exception as e:
        logger.error(f"[DB대체연결] 실패: {str(e)}")
        return False
