"""
사용자 관리 관련 서비스 - 기본 기능만 유지
"""

from typing import Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import logging  # 표준 로깅 임포트

logger = logging.getLogger(__name__)  # 로거 인스턴스 생성

from main.models.user_model import User


def get_user_list(
    db: Session,
    page: int = 1,
    page_size: int = 10,
    role: str = None,
    search_type: str = None,
    search_value: str = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    사용자 목록 조회 (페이지네이션)
    """
    try:
        # 기본 쿼리
        query = db.query(User)

        # 필터 적용
        if role and role.lower() != "all":
            query = query.filter(User.user_role == role)

        if search_type and search_value:
            if search_type == "user_id":
                query = query.filter(User.user_id.like(f"%{search_value}%"))
            elif search_type == "user_department":
                query = query.filter(User.user_department.like(f"%{search_value}%"))

        # 전체 건수 조회
        total = query.count()

        # 페이지네이션 계산
        total_pages = (total + page_size - 1) // page_size
        offset = (page - 1) * page_size

        # 사용자 목록 조회 (오름차순)
        users = query.order_by(User.user_id).offset(offset).limit(page_size).all()

        # 응답 데이터 가공 (테이블에 필요한 필드만)
        user_list = []
        for user in users:
            user_list.append(
                {
                    "user_id": user.user_id,
                    "user_name": user.user_name,
                    "user_role": user.user_role,
                    "user_department": user.user_department,
                }
            )

        # 페이지네이션 정보
        pagination = {
            "total": total,
            "total_pages": total_pages,
            "current": page,
            "page_size": page_size,
        }

        return user_list, pagination

    except Exception as e:
        logger.error(f"사용자 목록 조회 중 오류 발생: {str(e)}", exc_info=True)
        raise e


def create_user(
    db: Session,
    user_id: str,
    user_name: str,
    user_password: str,
    user_role: str,
    user_department: str,
) -> User:
    """
    사용자 생성
    """
    try:
        # 아이디 중복 확인
        existing_user = db.query(User).filter(User.user_id == user_id).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 존재하는 사용자 ID입니다.",
            )

        # 새 사용자 생성
        user = User(
            user_id=user_id,
            user_name=user_name,
            user_password=user_password,
            user_role=user_role,
            user_department=user_department,
        )

        # DB에 저장
        db.add(user)
        db.commit()
        db.refresh(user)

        logger.info(
            f"사용자 생성: ID {user_id}, 권한 {user_role}, 부서 {user_department}"
        )

        return user
    except HTTPException:
        # HTTP 예외는 그대로 전달
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"사용자 생성 중 오류 발생: {str(e)}", exc_info=True)
        raise e


def delete_user(db: Session, user_id: str) -> bool:
    """
    사용자 삭제
    """
    try:
        # 사용자 조회
        user = db.query(User).filter(User.user_id == user_id).first()

        if not user:
            return False

        # DB에서 삭제
        db.delete(user)
        db.commit()

        logger.info(f"사용자 삭제: ID {user_id}")

        return True
    except Exception as e:
        db.rollback()
        logger.error(f"사용자 삭제 중 오류 발생: {str(e)}", exc_info=True)
        raise e


def update_user_role(db: Session, user_id: str, user_role: str) -> bool:
    """
    사용자 권한 변경
    """
    try:
        # 사용자 조회
        user = db.query(User).filter(User.user_id == user_id).first()

        if not user:
            return False

        # 권한 변경
        user.user_role = user_role
        db.commit()

        logger.info(f"사용자 권한 변경: ID {user_id}, 새 권한 {user_role}")

        return True
    except Exception as e:
        db.rollback()
        logger.error(f"사용자 권한 변경 중 오류 발생: {str(e)}", exc_info=True)
        raise e
