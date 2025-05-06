"""
페이지네이션 유틸리티 모듈
"""

from typing import Dict, Any, Tuple, List, TypeVar, Generic, Optional, Callable
from sqlalchemy.orm import Query
from sqlalchemy import func

T = TypeVar("T")


def paginate_query(
    query: Query, page: int = 1, page_size: int = 10
) -> Tuple[List[Any], Dict[str, Any]]:
    """
    SQLAlchemy 쿼리에 페이지네이션을 적용하고 결과와 메타데이터를 반환합니다.

    Args:
        query: 페이지네이션을 적용할 SQLAlchemy 쿼리
        page: 페이지 번호 (1부터 시작)
        page_size: 페이지당 항목 수

    Returns:
        Tuple[List[Any], Dict[str, Any]]: (페이지 항목 목록, 페이지네이션 메타데이터)
    """
    try:
        # 전체 항목 수 조회
        total_items = query.count()

        # 전체 페이지 수 계산 (최소 1페이지)
        total_pages = max(1, (total_items + page_size - 1) // page_size)

        # 페이지 범위 검증 및 조정
        if page < 1:
            page = 1
        elif page > total_pages and total_pages > 0:
            page = total_pages

        # 오프셋 계산
        offset = (page - 1) * page_size

        # 쿼리에 페이지네이션 적용하여 결과 가져오기
        items = query.offset(offset).limit(page_size).all() if total_items > 0 else []

        # 페이지네이션 메타데이터 구성 (라우터와 키 이름 통일)
        pagination = {
            "total_items": total_items,
            "page_size": page_size,
            "current_page": page,
            "total_pages": total_pages,
            "start_index": offset + 1 if total_items > 0 else 0,
            "end_index": min(offset + page_size, total_items) if total_items > 0 else 0,
        }

        return items, pagination
    except Exception as e:
        import logging

        logging.getLogger("pagination").error(
            f"페이지네이션 처리 중 오류 발생: {str(e)}"
        )

        # 오류 발생 시 안전한 기본값 반환 (키 이름 통일)
        fallback_pagination = {
            "total_items": 0,
            "page_size": page_size,
            "current_page": 1,
            "total_pages": 1,
            "start_index": 0,
            "end_index": 0,
        }
        return [], fallback_pagination


def calculate_dashboard_stats(query: Query) -> Dict[str, int]:
    """
    대시보드 통계 정보를 계산합니다.

    Args:
        query: 통계를 계산할 SQLAlchemy 쿼리

    Returns:
        Dict[str, int]: 상태별 통계 정보
    """
    try:
        from sqlalchemy import case
        from main.models.dashboard_model import Dashboard

        # 통계 쿼리 실행
        stats_result = query.with_entities(
            func.count().label("total"),
            func.sum(case((Dashboard.status == "WAITING", 1), else_=0)).label(
                "waiting"
            ),
            func.sum(case((Dashboard.status == "IN_PROGRESS", 1), else_=0)).label(
                "in_progress"
            ),
            func.sum(case((Dashboard.status == "COMPLETE", 1), else_=0)).label(
                "complete"
            ),
            func.sum(case((Dashboard.status == "ISSUE", 1), else_=0)).label("issue"),
            func.sum(case((Dashboard.status == "CANCEL", 1), else_=0)).label("cancel"),
        ).first()

        # 통계 결과를 딕셔너리로 변환
        if stats_result and hasattr(stats_result, "total"):
            return {
                "total": stats_result.total or 0,
                "waiting": stats_result.waiting or 0,
                "in_progress": stats_result.in_progress or 0,
                "complete": stats_result.complete or 0,
                "issue": stats_result.issue or 0,
                "cancel": stats_result.cancel or 0,
            }
        else:
            # 결과가 없는 경우 기본값 반환
            return {
                "total": 0,
                "waiting": 0,
                "in_progress": 0,
                "complete": 0,
                "issue": 0,
                "cancel": 0,
            }
    except Exception as e:
        import logging

        logging.getLogger("pagination").error(
            f"대시보드 통계 계산 중 오류 발생: {str(e)}"
        )
        # 오류 발생 시 안전한 기본값 반환
        return {
            "total": 0,
            "waiting": 0,
            "in_progress": 0,
            "complete": 0,
            "issue": 0,
            "cancel": 0,
        }
