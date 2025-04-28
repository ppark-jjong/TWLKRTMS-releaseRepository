"""
인수인계 관련 서비스 - 모델 필드명 일치하도록 수정
"""

from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_, or_
from fastapi import HTTPException, status

from main.utils.logger import logger
from main.models.handover_model import Handover  # 모델 임포트


def get_handover_list(
    db: Session, 
    page: int = 1, 
    page_size: int = 10,
    is_notice: bool = False,
    search_term: Optional[str] = None  # 파라미터는 유지하되 내부 로직에서 사용하지 않음
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    인수인계 목록 조회 (페이지네이션)
    
    Args:
        db: 데이터베이스 세션
        page: 페이지 번호
        page_size: 페이지 크기
        is_notice: 공지사항 여부
        search_term: 미사용 파라미터 (호환성 유지)
        
    Returns:
        인수인계 목록과 페이지네이션 정보
    """
    try:
        # 기본 쿼리 생성 
        query = db.query(Handover).filter(Handover.is_notice == is_notice)
            
        # 전체 건수 조회
        total = query.count()
        
        # 페이지네이션 계산
        total_pages = max(1, (total + page_size - 1) // page_size)  # 올림 나눗셈, 최소 1페이지
        offset = (page - 1) * page_size
        
        # 인수인계 목록 조회 (최신순)
        handovers = query\
            .order_by(desc(Handover.update_at))\
            .offset(offset)\
            .limit(page_size)\
            .all()
            
        # 응답 데이터 가공
        handover_list = []
        for handover in handovers:
            handover_list.append({
                "id": handover.handover_id,
                "title": handover.title,
                "content": handover.content,
                "is_notice": handover.is_notice,
                "writer_id": handover.update_by,
                "update_at": handover.update_at.strftime("%Y-%m-%d %H:%M") if handover.update_at else None,
            })
            
        # 페이지네이션 정보
        pagination = {
            "total": total,
            "total_pages": total_pages,
            "current": page,
            "page_size": page_size
        }
        
        return handover_list, pagination
        
    except Exception as e:
        logger.error(f"인수인계 목록 조회 중 오류 발생: {str(e)}", exc_info=True)
        raise e


def get_notice_list(
    db: Session, 
    page: int = 1, 
    page_size: int = 5
) -> List[Dict[str, Any]]:
    """
    공지사항 목록 조회 (is_notice=True)
    """
    try:
        # 공지사항 목록 조회 (최신순)
        handovers, _ = get_handover_list(db, page, page_size, is_notice=True)
        return handovers
    except Exception as e:
        logger.error(f"공지사항 목록 조회 중 오류 발생: {str(e)}", exc_info=True)
        raise e


def get_handover_by_id(db: Session, handover_id: int) -> Optional[Handover]:
    """
    인수인계 상세 조회
    """
    try:
        handover = db.query(Handover).filter(Handover.handover_id == handover_id).first()
        return handover
    except Exception as e:
        logger.error(f"인수인계 상세 조회 중 오류 발생: {str(e)}", exc_info=True)
        raise e


def create_handover(
    db: Session, 
    title: str, 
    content: str, 
    is_notice: bool,
    writer_id: str,
    writer_name: str = None  # 호환성을 위해 유지하되 사용하지 않음
) -> Handover:
    """
    인수인계 생성
    """
    try:
        # 새 인수인계 생성
        now = datetime.now()
        handover = Handover(
            title=title,
            content=content,
            is_notice=is_notice,
            update_by=writer_id,
            update_at=now  # create_at 제거
        )
        
        # DB에 저장
        db.add(handover)
        db.commit()
        db.refresh(handover)
        
        logger.info(f"인수인계 생성: ID {handover.handover_id}, 작성자 {writer_id}")
        
        return handover
    except Exception as e:
        db.rollback()
        logger.error(f"인수인계 생성 중 오류 발생: {str(e)}", exc_info=True)
        raise e


def update_handover(
    db: Session, 
    handover_id: int, 
    title: str, 
    content: str, 
    is_notice: bool,
    updated_by: str
) -> Handover:
    """
    인수인계 수정 (행 단위 락 확인 포함)
    """
    from main.utils.lock import acquire_lock, release_lock
    
    # 락 획득 시도
    lock_success, lock_info = acquire_lock(db, "handover", handover_id, updated_by)
    
    if not lock_success:
        logger.warning(
            f"인수인계 수정 실패 (락 획득 불가): ID {handover_id}, 사용자 {updated_by}"
        )
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="현재 다른 사용자가 이 인수인계를 편집 중입니다.",
        )
    
    try:
        # 인수인계 조회
        handover = get_handover_by_id(db, handover_id)
        
        if not handover:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="인수인계를 찾을 수 없습니다."
            )
            
        # 인수인계 정보 업데이트
        handover.title = title
        handover.content = content
        handover.is_notice = is_notice
        handover.update_at = datetime.now()
        handover.update_by = updated_by
        
        # DB에 저장
        db.commit()
        db.refresh(handover)
        
        # 락 해제
        release_lock(db, "handover", handover_id, updated_by)
        
        logger.info(f"인수인계 수정: ID {handover.handover_id}, 수정자 {updated_by}")
        
        return handover
    except HTTPException:
        # HTTP 예외는 그대로 전달
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"인수인계 수정 중 오류 발생: {str(e)}", exc_info=True)
        raise e


def delete_handover(db: Session, handover_id: int) -> bool:
    """
    인수인계 삭제
    """
    try:
        # 인수인계 조회
        handover = get_handover_by_id(db, handover_id)
        
        if not handover:
            return False
            
        # DB에서 삭제
        db.delete(handover)
        db.commit()
        
        logger.info(f"인수인계 삭제: ID {handover_id}")
        
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"인수인계 삭제 중 오류 발생: {str(e)}", exc_info=True)
        raise e
