"""
로깅 유틸리티 - 중복 로그 문제 해결 버전
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
import traceback
import platform
from main.utils.config import get_settings

# 현재 운영체제에 따라 로그 경로 설정
if platform.system() == "Windows":
    LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
else:
    # Docker 환경이나 Linux 서버 환경
    LOG_DIR = "/app/main/logs"

# 로그 디렉토리가 없다면 생성
os.makedirs(LOG_DIR, exist_ok=True)

# 로거 생성 (이미 존재하는 핸들러 제거 후 초기화)
logger = logging.getLogger("delivery_tms")
logger.setLevel(logging.INFO)

# 기존 핸들러 제거 (중복 로그 방지)
if logger.handlers:
    logger.handlers.clear()

# 로그 포맷 설정
log_format = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)

# 콘솔 핸들러 추가
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(log_format)
logger.addHandler(console_handler)

# 파일 핸들러 추가 (일별 로테이션)
file_handler = RotatingFileHandler(
    os.path.join(LOG_DIR, "delivery_tms.log"),
    maxBytes=10 * 1024 * 1024,  # 10MB
    backupCount=10,
    encoding="utf-8",
)
file_handler.setFormatter(log_format)
logger.addHandler(file_handler)

# 루트 로거 전파 방지 (중복 로깅 방지)
logger.propagate = False

try:
    if get_settings().DEBUG:
        logger.setLevel(logging.DEBUG)
        logger.debug("디버그 모드 활성화됨")
except Exception as e:
    logger.warning(f"설정 로드 중 오류: {str(e)}")


# 서비스 로그 함수
def service(service_name, method_name, data=None):
    """서비스 로그"""
    message = f"[서비스] {service_name}.{method_name}()"
    if data:
        message += f" - 파라미터: {str(data)}"
    logger.debug(message)


# API 요청 로그 함수
def api(method, url, data=None):
    """API 요청 로그"""
    message = f"[API] {method} {url}"
    if data:
        message += f" - 데이터: {str(data)}"
    logger.debug(message)


# API 응답 로그 함수
def response(url, success, data=None):
    """API 응답 로그"""
    status = "성공" if success else "실패"
    message = f"[응답] {url} - {status}"
    if data and not success:
        message += f" - 데이터: {str(data)}"
    logger.debug(message)


# 에러 로그 함수 (간소화)
def error(message, exception=None):
    """에러 로그"""
    if exception:
        logger.error(f"{message}: {str(exception)}")
        logger.error(traceback.format_exc())
    else:
        logger.error(message)


# 정보 로그 함수
def info(message):
    """정보 로그"""
    logger.info(message)


# 경고 로그 함수
def warn(message):
    """경고 로그"""
    logger.warning(message)


# 디버그 로그 함수
def debug(message):
    """디버그 로그"""
    logger.debug(message)
