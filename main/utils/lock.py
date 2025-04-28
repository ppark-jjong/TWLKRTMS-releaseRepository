"""
행 단위 락(Row-Level Lock) 관리 유틸리티
"""

from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Tuple, Dict, Any, Optional, Union, List
import json

from main.utils.logger import logger
from main.utils.config import get_settings

settings = get_settings()


def acquire_lock(
    db: Session, table_name: str, row_id: int, user_id: str
) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    특정 테이블의 특정 행에 대한 락을 획득합니다.

    Args:
        db: 데이터베이스 세션
        table_name: 락을 획득할 테이블 이름
        row_id: 락을 획득할 행 ID
        user_id: 락을 획득하려는 사용자 ID

    Returns:
        bool: 락 획득 성공 여부
        dict: 현재 락 정보 (실패 시 현재 락 보유자 정보 포함)
    """
    try:
        # 락 정보 조회 쿼리 생성
        query = text(
            f"""
        SELECT is_locked, update_by, update_at 
        FROM {table_name} 
        WHERE {table_name}_id = :row_id
        """
        )

        # 쿼리 실행 및 결과 가져오기
        result = db.execute(query, {"row_id": row_id}).fetchone()

        if not result:
            logger.warning(
                f"락 획득 실패: {table_name} 테이블에서 ID {row_id}인 행을 찾을 수 없음"
            )
            return False, {"message": "지정된 항목을 찾을 수 없습니다"}

        is_locked, locked_by, locked_at = result

        # 이미 락이 있고 다른 사용자가 점유 중인 경우
        if is_locked and locked_by != user_id:
            # 락 타임아웃 확인 (5분 이상 경과한 락은 만료로 간주)
            lock_timeout = datetime.now() - timedelta(
                seconds=settings.LOCK_TIMEOUT_SECONDS
            )

            if locked_at and locked_at < lock_timeout:
                # 락 타임아웃 발생 - 락 해제 후 재획득 시도
                logger.info(
                    f"만료된 락 해제: {table_name} ID {row_id}, 이전 사용자: {locked_by}"
                )
                return _update_lock(db, table_name, row_id, user_id, True)

            # 락 획득 실패, 현재 락 보유자 정보 반환
            logger.warning(
                f"락 획득 실패: {table_name} ID {row_id}는 현재 {locked_by}가 락 보유 중"
            )
            return False, {
                "message": f"현재 다른 사용자가 편집 중입니다",
                "locked_by": locked_by,
                "locked_at": locked_at,
                "editable": False,
            }

        # 락이 없거나, 본인이 락 보유 중인 경우 획득/갱신
        return _update_lock(db, table_name, row_id, user_id, True)

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"락 획득 중 데이터베이스 오류: {str(e)}")
        return False, {"message": "데이터베이스 오류로 락 획득 실패"}
    except Exception as e:
        db.rollback()
        logger.error(f"락 획득 중 예외 발생: {str(e)}")
        return False, {"message": "락 획득 중 오류 발생"}


def release_lock(
    db: Session, table_name: str, row_id: int, user_id: str
) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    특정 테이블의 특정 행에 대한 락을 해제합니다.

    Args:
        db: 데이터베이스 세션
        table_name: 락을 해제할 테이블 이름
        row_id: 락을 해제할 행 ID
        user_id: 락을 해제하려는 사용자 ID

    Returns:
        bool: 락 해제 성공 여부
        dict: 메시지 정보
    """
    try:
        # 락 정보 조회 쿼리 생성
        query = text(
            f"""
        SELECT is_locked, update_by 
        FROM {table_name} 
        WHERE {table_name}_id = :row_id
        """
        )

        # 쿼리 실행 및 결과 가져오기
        result = db.execute(query, {"row_id": row_id}).fetchone()

        if not result:
            logger.warning(
                f"락 해제 실패: {table_name} 테이블에서 ID {row_id}인 행을 찾을 수 없음"
            )
            return False, {"message": "지정된 항목을 찾을 수 없습니다"}

        is_locked, locked_by = result

        # 락이 없는 경우
        if not is_locked:
            logger.info(f"락 해제 불필요: {table_name} ID {row_id}에 락이 없음")
            return True, {"message": "락이 이미 해제되어 있습니다"}

        # 다른 사용자의 락인 경우 (관리자가 아니면 해제 불가)
        if locked_by != user_id:
            logger.warning(
                f"락 해제 실패: {table_name} ID {row_id}의 락은 {locked_by}의 소유"
            )
            return False, {
                "message": "다른 사용자의 락은 해제할 수 없습니다",
                "locked_by": locked_by,
            }

        # 락 해제 실행
        return _update_lock(db, table_name, row_id, user_id, False)

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"락 해제 중 데이터베이스 오류: {str(e)}")
        return False, {"message": "데이터베이스 오류로 락 해제 실패"}
    except Exception as e:
        db.rollback()
        logger.error(f"락 해제 중 예외 발생: {str(e)}")
        return False, {"message": "락 해제 중 오류 발생"}


def check_lock_status(
    db: Session, table_name: str, row_id: int, user_id: str
) -> Dict[str, Any]:
    """
    특정 테이블의 특정 행에 대한 락 상태를 확인합니다.

    Args:
        db: 데이터베이스 세션
        table_name: 락을 확인할 테이블 이름
        row_id: 락을 확인할 행 ID
        user_id: 확인하는 사용자 ID

    Returns:
        dict: 락 상태 정보
    """
    try:
        # 락 정보 조회 쿼리 생성
        query = text(
            f"""
        SELECT is_locked, update_by, update_at 
        FROM {table_name} 
        WHERE {table_name}_id = :row_id
        """
        )

        # 쿼리 실행 및 결과 가져오기
        result = db.execute(query, {"row_id": row_id}).fetchone()

        if not result:
            logger.warning(
                f"락 상태 확인 실패: {table_name} 테이블에서 ID {row_id}인 행을 찾을 수 없음"
            )
            return {"editable": False, "message": "지정된 항목을 찾을 수 없습니다"}

        is_locked, locked_by, locked_at = result

        # 락이 없는 경우
        if not is_locked:
            return {"editable": True, "message": "락이 없습니다. 편집 가능합니다."}

        # 본인이 락을 보유한 경우
        if locked_by == user_id:
            return {
                "editable": True,
                "locked_by": locked_by,
                "locked_at": locked_at,
                "message": "본인이 락을 보유 중입니다. 편집 가능합니다.",
            }

        # 다른 사용자가 락을 보유한 경우
        return {
            "editable": False,
            "locked_by": locked_by,
            "locked_at": locked_at,
            "message": f"다른 사용자({locked_by})가 편집 중입니다.",
        }

    except SQLAlchemyError as e:
        logger.error(f"락 상태 확인 중 데이터베이스 오류: {str(e)}")
        return {"editable": False, "message": "데이터베이스 오류로 락 상태 확인 실패"}
    except Exception as e:
        logger.error(f"락 상태 확인 중 예외 발생: {str(e)}")
        return {"editable": False, "message": "락 상태 확인 중 오류 발생"}


def release_expired_locks(db: Session) -> int:
    """
    만료된 모든 락을 해제합니다. 서버 시작 시 호출됩니다.

    Args:
        db: 데이터베이스 세션

    Returns:
        int: 해제된 락의 수
    """
    tables_with_locks = ["dashboard", "handover"]
    lock_timeout = datetime.now() - timedelta(seconds=settings.LOCK_TIMEOUT_SECONDS) # 5분 타임아웃
    total_released = 0

    try:
        for table in tables_with_locks:
            # 만료된 락 해제 쿼리 생성
            query = text(
                f"""
            UPDATE {table}
            SET is_locked = False
            WHERE is_locked = True
            AND update_at < :lock_timeout
            """
            )

            # 쿼리 실행 및 영향 받은 행 수 가져오기
            result = db.execute(query, {"lock_timeout": lock_timeout})
            released_count = result.rowcount
            total_released += released_count

            if released_count > 0:
                logger.info(f"{table} 테이블에서 만료된 락 {released_count}개 해제")

        db.commit()
        return total_released

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"만료된 락 해제 중 데이터베이스 오류: {str(e)}")
        return 0
    except Exception as e:
        db.rollback()
        logger.error(f"만료된 락 해제 중 예외 발생: {str(e)}")
        return 0


def _update_lock(
    db: Session, table_name: str, row_id: int, user_id: str, lock_status: bool
) -> Tuple[bool, Dict[str, Any]]:
    """
    특정 테이블의 특정 행에 대한 락 상태를 업데이트합니다.

    Args:
        db: 데이터베이스 세션
        table_name: 락을 업데이트할 테이블 이름
        row_id: 락을 업데이트할 행 ID
        user_id: 락을 업데이트하는 사용자 ID
        lock_status: True=락 설정, False=락 해제

    Returns:
        bool: 락 업데이트 성공 여부
        dict: 결과 메시지
    """
    try:
        update_data = {
            "is_locked": lock_status,
            "update_by": user_id if lock_status else None,
            "update_at": datetime.now() if lock_status else None,
        }

        # 락 업데이트 쿼리 생성
        column_sets = []
        params = {"row_id": row_id}

        for key, value in update_data.items():
            if value is None:
                column_sets.append(f"{key} = NULL")
            else:
                params[key] = value
                column_sets.append(f"{key} = :{key}")

        column_set_str = ", ".join(column_sets)
        query = text(
            f"""
        UPDATE {table_name}
        SET {column_set_str}
        WHERE {table_name}_id = :row_id
        """
        )

        # 쿼리 실행
        db.execute(query, params)
        db.commit()

        action = "획득" if lock_status else "해제"
        logger.info(f"락 {action} 성공: {table_name} ID {row_id}, 사용자: {user_id}")

        result = {"message": f"락 {action} 성공", "editable": lock_status}

        if lock_status:
            result.update(
                {"locked_by": user_id, "locked_at": update_data["update_at"]}
            )

        return True, result

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"락 업데이트 중 데이터베이스 오류: {str(e)}")
        return False, {"message": "데이터베이스 오류로 락 업데이트 실패"}
    except Exception as e:
        db.rollback()
        logger.error(f"락 업데이트 중 예외 발생: {str(e)}")
        return False, {"message": "락 업데이트 중 오류 발생"}
