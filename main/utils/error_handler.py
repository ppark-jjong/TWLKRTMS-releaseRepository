"""
오류 처리를 위한 공통 유틸리티 함수
"""

from typing import Dict, Any, Optional, List
from fastapi import status
from fastapi.responses import JSONResponse
import logging  # 표준 로깅 임포트

logger = logging.getLogger(__name__)  # 로거 인스턴스 생성


def create_error_response(
    message: str,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> JSONResponse:
    """
    표준화된 오류 응답 생성

    Args:
        message: 오류 메시지
        status_code: HTTP 상태 코드
        error_code: 내부 오류 코드 (선택)
        details: 상세 오류 정보 (선택)

    Returns:
        JSONResponse: 오류 응답
    """
    content = {"success": False, "message": message}

    if error_code:
        content["error_code"] = error_code

    if details:
        content["details"] = details

    # 오류 로깅
    logger.error(f"오류 응답: {message} (코드: {status_code}, 내부 코드: {error_code})")
    if details:
        # logger.debug(f"오류 상세 정보: {details}") # 프로덕션에서 불필요한 로그 제거
        pass  # debug 로그만 있었으므로 pass 추가

    return JSONResponse(status_code=status_code, content=content)


def create_success_response(
    data: Any = None,
    message: Optional[str] = None,
    status_code: int = status.HTTP_200_OK,
) -> Dict[str, Any]:
    """
    표준화된 성공 응답 생성

    Args:
        data: 응답 데이터
        message: 성공 메시지 (선택)
        status_code: HTTP 상태 코드

    Returns:
        Dict: 성공 응답 구조
    """
    response = {"success": True}

    if message:
        response["message"] = message

    if data is not None:
        response["data"] = data

    return response


def handle_exceptions(
    func_name: str,
    exception: Exception,
    error_message: str,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
) -> JSONResponse:
    """
    예외 처리 및 로깅 도우미 함수

    Args:
        func_name: 예외가 발생한 함수 이름
        exception: 발생한 예외
        error_message: 사용자에게 표시할 오류 메시지
        status_code: HTTP 상태 코드

    Returns:
        JSONResponse: 오류 응답
    """
    # 오류 로깅
    logger.error(f"{func_name} 함수에서 오류 발생: {str(exception)}", exc_info=True)

    return create_error_response(message=error_message, status_code=status_code)


def validate_batch_results(
    results: List[Dict[str, Any]], total_items: int
) -> Dict[str, Any]:
    """
    일괄 처리 결과 검증 및 요약

    Args:
        results: 일괄 처리 결과 목록
        total_items: 총 대상 항목 수

    Returns:
        Dict: 결과 요약
    """
    success_count = sum(1 for item in results if item.get("success", False))
    failed_count = sum(1 for item in results if not item.get("success", False))

    # 실패한 항목 중에서 락 때문에 실패한 항목 카운트
    lock_count = sum(
        1
        for item in results
        if not item.get("success", False) and "다른 사용자가" in item.get("message", "")
    )

    # 일반 실패 (락 제외)
    general_fail_count = failed_count - lock_count

    summary = {
        "success": success_count > 0,  # 하나라도 성공했으면 성공으로 간주
        "message": f"처리완료: {success_count}건 성공, {general_fail_count}건 실패, {lock_count}건 락 상태",
        "total": total_items,
        "processed": len(results),
        "success_count": success_count,
        "failed_count": failed_count,
        "lock_count": lock_count,
        "details": results,
    }

    return summary
