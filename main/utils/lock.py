"""
행 단위 락(Row-Level Lock) 관리 유틸리티 (locked_by, locked_at 사용)
"""

from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Tuple, Dict, Any, Optional
import logging
from main.utils.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# 허용된 테이블 목록
ALLOWED_TABLES = ["dashboard", "handover"]


def acquire_lock(
    db: Session, table_name: str, row_id: int, user_id: str
) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    특정 테이블의 특정 행에 대한 락을 획득합니다. (트랜잭션 내에서 실행되어야 함)
    트랜잭션 commit/rollback은 호출하는 쪽에서 관리합니다.

    Args:
        db: 데이터베이스 세션
        table_name: 락을 획득할 테이블 이름
        row_id: 락을 획득할 행 ID
        user_id: 락을 획득하려는 사용자 ID

    Returns:
        Tuple[bool, Optional[Dict[str, Any]]]: (락 획득 성공 여부, 락 정보 메시지)
    """
    if table_name not in ALLOWED_TABLES:
        logger.error(f"유효하지 않은 테이블 이름: {table_name}")
        return False, {"message": "유효하지 않은 테이블 이름입니다"}

    try:
        # 락 정보 조회 쿼리 (locked_by, locked_at 포함)
        query = text(
            f"""
            SELECT is_locked, locked_by, locked_at
            FROM {table_name}
            WHERE {table_name}_id = :row_id FOR UPDATE
            """
        )
        result = db.execute(query, {"row_id": row_id}).fetchone()

        if not result:
            logger.warning(
                f"락 획득 실패: {table_name} 테이블에서 ID {row_id}인 행을 찾을 수 없음"
            )
            return False, {"message": "지정된 항목을 찾을 수 없습니다"}

        is_locked, locked_by, locked_at = result

        # 락이 이미 설정되어 있는 경우
        if is_locked:
            lock_timeout_time = datetime.now() - timedelta(
                seconds=settings.LOCK_TIMEOUT_SECONDS
            )

            # 타임아웃 확인
            if locked_at and locked_at < lock_timeout_time:
                logger.info(f"만료된 락 발견 및 해제 시도: {table_name} ID {row_id}")
                # 만료된 락은 해제 후 획득 시도
                return _update_lock(db, table_name, row_id, user_id, True)

            # 타임아웃되지 않았고 다른 사용자가 락 소유
            if locked_by != user_id:
                locked_at_str = (
                    locked_at.strftime("%Y-%m-%d %H:%M") if locked_at else "알 수 없음"
                )
                message = (
                    f"현재 다른 사용자({locked_by})가 {locked_at_str}부터 수정 중입니다"
                )
                logger.warning(f"락 획득 실패: {message}")
                return False, {
                    "message": message,
                    "locked_by": locked_by,
                    "locked_at": locked_at,
                }

            # 타임아웃되지 않았고 본인이 락 소유 (재진입)
            logger.info(f"본인이 이미 락 소유 중: {table_name} ID {row_id}")
            # 이미 락을 가지고 있으므로 성공으로 처리, 락 시간 갱신은 선택 사항
            return _update_lock(
                db, table_name, row_id, user_id, True, update_time=True
            )  # 락 시간 갱신

        # 락이 없는 경우 획득
        return _update_lock(db, table_name, row_id, user_id, True)

    except SQLAlchemyError as e:
        # db.rollback() # 외부에서 처리
        logger.error(f"락 획득 중 데이터베이스 오류: {str(e)}", exc_info=True)
        # 예외를 다시 발생시켜 외부 트랜잭션이 롤백되도록 함
        raise e
    except Exception as e:
        # db.rollback() # 외부에서 처리
        logger.error(f"락 획득 중 예외 발생: {str(e)}", exc_info=True)
        raise e


def release_lock(
    db: Session, table_name: str, row_id: int, user_id: str, force: bool = False
) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    특정 테이블의 특정 행에 대한 락을 해제합니다. (트랜잭션 내에서 실행되어야 함)
    트랜잭션 commit/rollback은 호출하는 쪽에서 관리합니다.

    Args:
        db: 데이터베이스 세션
        table_name: 락을 해제할 테이블 이름
        row_id: 락을 해제할 행 ID
        user_id: 락을 해제하려는 사용자 ID
        force: 관리자 등이 강제로 해제할 경우 True (현재 미구현)

    Returns:
        Tuple[bool, Optional[Dict[str, Any]]]: (락 해제 성공 여부, 메시지 정보)
    """
    if table_name not in ALLOWED_TABLES:
        logger.error(f"유효하지 않은 테이블 이름: {table_name}")
        return False, {"success": False, "message": "유효하지 않은 테이블 이름입니다"}

    try:
        # 락 정보 조회
        query = text(
            f"""
            SELECT is_locked, locked_by
            FROM {table_name}
            WHERE {table_name}_id = :row_id FOR UPDATE
            """
        )
        result = db.execute(query, {"row_id": row_id}).fetchone()

        if not result:
            logger.warning(
                f"락 해제 실패: {table_name} 테이블에서 ID {row_id}인 행을 찾을 수 없음"
            )
            return False, {
                "success": False,
                "message": "지정된 항목을 찾을 수 없습니다",
            }

        is_locked, current_locked_by = result

        if not is_locked:
            logger.info(f"락 해제 불필요: {table_name} ID {row_id}에 락이 없음")
            return True, {"success": True, "message": "락이 이미 해제되어 있습니다"}

        # 본인의 락이거나 강제 해제가 아닌 경우 소유권 확인
        if not force and current_locked_by != user_id:
            logger.warning(
                f"락 해제 실패: {table_name} ID {row_id}의 락은 {current_locked_by} 소유"
            )
            return False, {
                "success": False,
                "message": f"다른 사용자({current_locked_by})의 락은 해제할 수 없습니다",
                "locked_by": current_locked_by,
            }

        # 락 해제 실행
        success, message_info = _update_lock(db, table_name, row_id, user_id, False)

        if not success:
            # _update_lock에서 오류 발생 시 예외가 발생하므로 이 경로는 실제로는 도달하기 어려움
            logger.error(
                f"락 해제 실패 (_update_lock 반환 오류): {table_name} ID {row_id}"
            )
            return False, {"success": False, "message": "락 해제 중 오류 발생"}

        logger.info(f"락 해제 성공: {table_name} ID {row_id}")
        return True, {"success": True, "message": "락이 성공적으로 해제되었습니다."}

    except SQLAlchemyError as e:
        # db.rollback() # 외부에서 처리
        logger.error(f"락 해제 중 데이터베이스 오류: {str(e)}", exc_info=True)
        raise e
    except Exception as e:
        # db.rollback() # 외부에서 처리
        logger.error(f"락 해제 중 예외 발생: {str(e)}", exc_info=True)
        raise e


def check_lock_status(
    db: Session, table_name: str, row_id: int, user_id: str
) -> Dict[str, Any]:
    """
    특정 테이블의 특정 행에 대한 락 상태를 확인합니다. (트랜잭션 내에서 실행 가능)
    만료된 락은 이 함수에서 자동으로 해제하지 않습니다. acquire_lock을 사용하세요.

    Args:
        db: 데이터베이스 세션
        table_name: 락을 확인할 테이블 이름
        row_id: 락을 확인할 행 ID
        user_id: 확인하는 사용자 ID

    Returns:
        Dict[str, Any]: 락 상태 정보 (editable 포함)
                         {'success': bool, 'editable': bool, 'message': str,
                          'locked': bool, 'locked_by': Optional[str], 'locked_at': Optional[datetime]}
    """
    if table_name not in ALLOWED_TABLES:
        logger.error(f"유효하지 않은 테이블 이름: {table_name}")
        return {
            "success": False,
            "editable": False,
            "message": "유효하지 않은 테이블 이름입니다",
            "locked": False,
            "locked_by": None,
            "locked_at": None,
        }

    try:
        # 락 정보 조회 (FOR UPDATE 불필요, 단순 조회)
        query = text(
            f"""
            SELECT is_locked, locked_by, locked_at
            FROM {table_name}
            WHERE {table_name}_id = :row_id
            """
        )
        result = db.execute(query, {"row_id": row_id}).fetchone()

        if not result:
            logger.warning(
                f"락 상태 확인 실패: {table_name} 테이블에서 ID {row_id}인 행을 찾을 수 없음"
            )
            return {
                "success": False,
                "editable": False,
                "message": "지정된 항목을 찾을 수 없습니다",
                "locked": False,
                "locked_by": None,
                "locked_at": None,
            }

        is_locked, locked_by, locked_at = result

        # 락 만료 시간 계산
        is_expired = False
        if is_locked and locked_at:
            lock_timeout_time = datetime.now() - timedelta(
                seconds=settings.LOCK_TIMEOUT_SECONDS
            )
            if locked_at < lock_timeout_time:
                is_expired = True
                logger.info(
                    f"만료된 락 확인됨: {table_name} ID {row_id}, 만료 시간: {locked_at}"
                )

        # 락이 설정되어 있고 만료된 경우
        if is_locked and is_expired:
            return {
                "success": True,
                "editable": True,  # 만료된 락은 획득 가능
                "message": f"이전에 {locked_by}가 잠갔으나 만료되었습니다.",
                "locked": False,  # 만료되었으므로 사실상 락 없음
                "locked_by": locked_by,
                "locked_at": locked_at,
                "is_expired": True,
            }

        # 락이 설정되어 있고 만료되지 않은 경우
        if is_locked and not is_expired:
            is_own_lock = locked_by == user_id
            locked_at_str = (
                locked_at.strftime("%Y-%m-%d %H:%M") if locked_at else "알 수 없음"
            )
            message = (
                "현재 편집 중입니다"
                if is_own_lock
                else f"다른 사용자({locked_by})가 {locked_at_str}부터 편집 중입니다"
            )
            return {
                "success": True,
                "editable": is_own_lock,
                "message": message,
                "locked": True,
                "locked_by": locked_by,
                "locked_at": locked_at,
                "is_expired": False,
            }

        # 락이 없는 경우
        return {
            "success": True,
            "editable": True,
            "message": "편집 가능합니다",
            "locked": False,
            "locked_by": None,
            "locked_at": None,
            "is_expired": False,
        }

    except SQLAlchemyError as e:
        logger.error(f"락 상태 확인 중 데이터베이스 오류: {str(e)}", exc_info=True)
        # 예외 발생 시 편집 불가능으로 간주
        return {
            "success": False,
            "editable": False,
            "message": "데이터베이스 오류로 락 상태 확인 실패",
            "locked": False,
            "locked_by": None,
            "locked_at": None,
        }
    except Exception as e:
        logger.error(f"락 상태 확인 중 예외 발생: {str(e)}", exc_info=True)
        return {
            "success": False,
            "editable": False,
            "message": "락 상태 확인 중 오류 발생",
            "locked": False,
            "locked_by": None,
            "locked_at": None,
        }


def release_expired_locks(db: Session) -> int:
    """
    만료된 모든 락을 해제합니다. 서버 시작 시 또는 주기적으로 호출될 수 있습니다.
    (트랜잭션 내에서 실행되어야 함)

    Args:
        db: 데이터베이스 세션

    Returns:
        int: 해제된 락의 수
    """
    lock_timeout_time = datetime.now() - timedelta(
        seconds=settings.LOCK_TIMEOUT_SECONDS
    )
    total_released = 0

    try:
        for table in ALLOWED_TABLES:
            query = text(
                f"""
                UPDATE {table}
                SET is_locked = False, locked_by = NULL, locked_at = NULL
                WHERE is_locked = True AND locked_at < :lock_timeout_time
                """
            )
            result = db.execute(query, {"lock_timeout_time": lock_timeout_time})
            released_count = result.rowcount
            total_released += released_count

            if released_count > 0:
                logger.info(f"{table} 테이블에서 만료된 락 {released_count}개 해제")

        # db.commit() # 외부에서 처리
        return total_released

    except SQLAlchemyError as e:
        # db.rollback() # 외부에서 처리
        logger.error(f"만료된 락 해제 중 데이터베이스 오류: {str(e)}", exc_info=True)
        raise e  # 외부 트랜잭션 롤백 유도
    except Exception as e:
        # db.rollback() # 외부에서 처리
        logger.error(f"만료된 락 해제 중 예외 발생: {str(e)}", exc_info=True)
        raise e


def _update_lock(
    db: Session,
    table_name: str,
    row_id: int,
    user_id: str,
    lock_status: bool,
    update_time: bool = True,
) -> Tuple[bool, Dict[str, Any]]:
    """
    내부 함수: 특정 테이블의 특정 행에 대한 락 상태를 DB에 업데이트합니다.
    (트랜잭션 내에서 실행되어야 함)

    Args:
        db: 데이터베이스 세션
        table_name: 테이블 이름
        row_id: 행 ID
        user_id: 사용자 ID
        lock_status: True=락 설정, False=락 해제
        update_time: 락 설정 시 locked_at 시간을 갱신할지 여부

    Returns:
        Tuple[bool, Dict[str, Any]]: (성공 여부, 결과 메시지)
    """
    try:
        now = datetime.now()
        if lock_status:
            # 락 설정 쿼리
            query = text(
                f"""
                UPDATE {table_name}
                SET is_locked = :is_locked, locked_by = :locked_by, locked_at = :locked_at
                WHERE {table_name}_id = :row_id
                """
            )
            params = {
                "is_locked": True,
                "locked_by": user_id,
                "locked_at": (
                    now if update_time else text("locked_at")
                ),  # 시간 갱신 여부
                "row_id": row_id,
            }
        else:
            # 락 해제 쿼리
            query = text(
                f"""
                UPDATE {table_name}
                SET is_locked = :is_locked, locked_by = NULL, locked_at = NULL
                WHERE {table_name}_id = :row_id AND (locked_by = :locked_by OR locked_by IS NULL)
                """  # 본인 락만 해제하거나 이미 풀린 경우 대비
            )
            params = {
                "is_locked": False,
                "row_id": row_id,
                "locked_by": user_id,  # 본인 락인지 확인용
            }

        result = db.execute(query, params)
        # db.commit() # 외부에서 처리

        if result.rowcount == 0 and not lock_status:
            # 락 해제 시도 시 이미 다른 사용자의 락이거나 해제된 경우 (경쟁 상태 등)
            # release_lock 함수에서 소유권 체크를 하므로 여기서는 로깅만
            logger.warning(
                f"락 해제 시 영향받은 행 없음: {table_name} ID {row_id}. 이미 해제되었거나 다른 사용자의 락일 수 있음."
            )
            # 실패로 간주하지는 않음, release_lock에서 최종 판단

        action = "획득" if lock_status else "해제"
        logger.info(
            f"락 {action} DB 업데이트 시도: {table_name} ID {row_id}, 사용자: {user_id}"
        )

        return True, {"message": f"락 {action} 성공"}

    except SQLAlchemyError as e:
        # db.rollback() # 외부에서 처리
        logger.error(f"락 업데이트 DB 작업 중 오류: {str(e)}", exc_info=True)
        raise e  # 외부 트랜잭션 롤백 유도
    except Exception as e:
        # db.rollback() # 외부에서 처리
        logger.error(f"락 업데이트 중 예외 발생: {str(e)}", exc_info=True)
        raise e
