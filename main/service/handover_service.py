"""
인수인계 관련 서비스 - 리팩토링 버전
"""

from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from fastapi import HTTPException, status
import logging
from main.models.handover_model import Handover
from main.models.user_model import User
from main.utils.pagination import paginate_query

logger = logging.getLogger(__name__)


def _handover_to_dict(handover: Handover) -> Dict[str, Any]:
    """Handover 모델 객체를 API 응답용 딕셔너리로 변환 (ISO 8601 형식 사용)"""

    # 관계(relationship)를 통해 로드된 사용자 이름 사용
    creator_name = handover.creator.user_name if handover.creator else None
    updater_name = handover.updater.user_name if handover.updater else None

    return {
        "handover_id": handover.handover_id,
        "title": handover.title,
        "content": handover.content,
        "is_notice": handover.is_notice,
        "department": handover.department,
        "create_by": handover.create_by,
        "creator_name": creator_name,
        "create_time": (
            handover.create_time.isoformat() if handover.create_time else None
        ),
        "update_by": handover.update_by,
        "update_at": handover.update_at.isoformat() if handover.update_at else None,
        "status": handover.status,
        "version": handover.version,
    }


def get_handover_list_paginated(
    db: Session,
    page: int = 1,
    page_size: int = 30,
    is_notice: bool = False,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """페이지네이션된 인수인계/공지 목록 조회"""
    try:
        query = db.query(Handover).filter(Handover.is_notice == is_notice)
        handovers_raw, pagination_info = paginate_query(
            query.order_by(desc(Handover.update_at)), page, page_size
        )
        # 모델 객체 리스트를 딕셔너리 리스트로 변환
        handover_list = [_handover_to_dict(h) for h in handovers_raw]
        return handover_list, pagination_info
    except Exception as e:
        logger.error(f"페이지네이션 목록 조회 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="목록 조회 중 오류 발생")


def get_handover_list_all(
    db: Session, is_notice: Optional[bool] = None, department: Optional[str] = None
) -> List[Dict[str, Any]]:
    """전체 인수인계/공지 목록 조회 (is_notice가 None이면 전체) - User 정보 JOIN"""
    try:
        query = db.query(Handover).options(
            joinedload(Handover.creator), joinedload(Handover.updater)
        )
        if is_notice is not None:
            # is_notice 값이 True 또는 False로 명시된 경우 필터링
            query = query.filter(Handover.is_notice == is_notice)
        if department is not None:
            # department 값이 지정된 경우 필터링
            query = query.filter(Handover.department == department)
        # is_notice가 None이면 필터링 없이 전체 조회
        all_handovers = query.order_by(desc(Handover.update_at)).all()
        return [_handover_to_dict(h) for h in all_handovers]
    except Exception as e:
        logger.error(f"전체 목록 조회 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="목록 조회 중 오류 발생")


def get_notice_list(
    db: Session, page: int = 1, page_size: int = 5
) -> List[Dict[str, Any]]:
    """공지사항 목록 조회 (페이지네이션 적용)"""
    notices, _ = get_handover_list_paginated(db, page, page_size, is_notice=True)
    return notices


def get_handover_by_id(db: Session, handover_id: int) -> Optional[Handover]:
    """ID로 인수인계 상세 조회 (모델 객체 반환)"""
    try:
        return db.query(Handover).filter(Handover.handover_id == handover_id).first()
    except Exception as e:
        logger.error(f"ID로 상세 조회 오류 ({handover_id}): {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="데이터 조회 중 오류 발생")


def create_handover(
    db: Session,
    title: str,
    content: str,
    is_notice: bool,
    writer_id: str,
    department: str = "ALL",
) -> Handover:
    """인수인계 생성"""
    logger.info(f"인수인계 생성 요청: 작성자={writer_id}, 제목='{title}'")
    try:
        # Handover 객체 생성 시 필수 필드 명시적 설정
        handover = Handover(
            title=title,
            content=content,
            is_notice=is_notice,
            create_by=writer_id,
            update_by=writer_id,
            update_at=datetime.now(),  # 명시적으로 현재 시간 설정
            department=department,
        )
        db.add(handover)
        db.flush()
        logger.info(f"인수인계 생성 완료: ID={handover.handover_id}")
        return handover
    except Exception as e:
        logger.error(f"인수인계 생성 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="인수인계 생성 중 오류 발생")


def update_handover(
    db: Session,
    handover_id: int,
    update_data: Dict[str, Any],  # 수정할 데이터 딕셔너리
    updated_by: str,
    user_role: str,  # 권한 확인용
) -> Handover:
    """인수인계 수정 (락 점검 및 권한 확인 포함)"""
    try:
        handover = get_handover_by_id(db, handover_id)
        if not handover:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="수정할 인수인계를 찾을 수 없습니다.",
            )

        # 2. 수정 권한 확인 (작성자 또는 ADMIN)
        if handover.create_by != updated_by and user_role != "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="이 인수인계를 수정할 권한이 없습니다.",
            )

        # 3. 공지사항 변경 권한 확인 (ADMIN만 가능)
        is_notice_new = update_data.get("is_notice")
        if (
            is_notice_new is not None
            and is_notice_new != handover.is_notice
            and user_role != "ADMIN"
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="관리자만 공지사항 여부를 변경할 수 있습니다.",
            )

        # status 필드 처리 및 권한 확인 (작성자 또는 ADMIN만 변경 가능)
        new_status = update_data.get("status")
        if new_status is not None and new_status != handover.status:
            if handover.create_by != updated_by and user_role != "ADMIN":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="인수인계 상태는 작성자 또는 관리자만 변경할 수 있습니다.",
                )
            # 유효한 상태 값인지 확인 (선택적)
            if new_status not in ["OPEN", "CLOSE"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="유효하지 않은 상태 값입니다 (OPEN 또는 CLOSE).",
                )

        # 4. 필드 업데이트 적용
        for key, value in update_data.items():
            setattr(handover, key, value)

        # 공통 업데이트 정보
        handover.update_at = datetime.now()
        handover.update_by = updated_by
        handover.version += 1  # 버전 1 증가

        db.flush()  # 변경사항 반영
        logger.info(f"인수인계 수정 완료 (커밋 전): ID {handover.handover_id}")
        return handover

    except Exception as e:
        logger.error(f"인수인계 수정 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="인수인계 수정 중 오류 발생")


def delete_handover(
    db: Session, handover_id: int, user_id: str, user_role: str
) -> bool:
    """인수인계 삭제 (락 점검 및 권한 확인 포함)"""
    try:
        handover = get_handover_by_id(db, handover_id)
        if not handover:
            # 락 확인 후 객체가 사라진 경우 (매우 드묾)
            logger.warning(f"삭제할 인수인계({handover_id}) 찾을 수 없음 (락 확인 후)")
            # 실패로 처리하거나, 이미 삭제된 것으로 간주하고 성공 처리 가능
            return False  # 실패로 처리

        # 2. 삭제 권한 확인 (작성자 또는 ADMIN)
        if handover.create_by != user_id and user_role != "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="이 인수인계를 삭제할 권한이 없습니다.",
            )

        db.delete(handover)
        db.flush()
        logger.info(f"인수인계 삭제 완료 (커밋 전): ID {handover_id}")
        return True
    except Exception as e:
        logger.error(f"인수인계 삭제 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="인수인계 삭제 중 오류 발생")


# check_handover_lock_status 함수 제거 (common 사용)
# 이전 라우터 호환성을 위한 함수 제거
