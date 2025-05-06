"""
대시보드(주문) 관련 서비스 로직
"""

from typing import Optional, List, Dict, Tuple, Any
from datetime import datetime, timedelta, date
from sqlalchemy import and_, or_, func, text, desc, case, extract
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from starlette import status

from main.models.dashboard_model import Dashboard
from main.models.postal_code_model import PostalCode
from main.schema.dashboard_schema import DashboardCreate, DashboardUpdate
from main.utils.lock import acquire_lock, release_lock, check_lock_status
from main.utils.pagination import calculate_dashboard_stats, paginate_query
import logging

logger = logging.getLogger(__name__)

# 전역 변수로 status_labels, type_labels 정의 (get_dashboard_response_data 와 공유)
status_labels = {
    "WAITING": "대기",
    "IN_PROGRESS": "진행",
    "COMPLETE": "완료",
    "ISSUE": "이슈",
    "CANCEL": "취소",
}
type_labels = {"DELIVERY": "배송", "RETURN": "회수"}


def get_dashboard_by_id(db: Session, dashboard_id: int) -> Optional[Dashboard]:
    """ID로 주문 조회"""
    try:
        return (
            db.query(Dashboard).filter(Dashboard.dashboard_id == dashboard_id).first()
        )
    except SQLAlchemyError as e:
        logger.error(
            f"주문 조회 중 오류 발생 (ID: {dashboard_id}): {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="데이터베이스 오류가 발생했습니다.",
        )


def get_dashboard_response_data(order: Dashboard) -> Dict[str, Any]:
    """Dashboard 모델 객체를 API 응답용 딕셔너리로 변환 (ISO 8601 형식 사용)"""
    if not order:
        return None

    # NULL 값 처리를 개선하여 'None' 문자열이 아닌 null로 반환하도록 변경
    # None 값을 빈 문자열('')이나 문자열 'None'으로 변환하지 않고 그대로 null로 전달
    data = {
        "dashboard_id": order.dashboard_id,
        "order_no": order.order_no,
        "type": order.type,
        "department": order.department,
        "warehouse": order.warehouse,
        "sla": order.sla,
        "postal_code": order.postal_code,
        "address": order.address,
        "customer": order.customer,
        "contact": order.contact,  # None 값을 그대로 전달
        "status": order.status,
        "driver_name": order.driver_name,  # None 값을 그대로 전달
        "driver_contact": order.driver_contact,  # None 값을 그대로 전달
        "remark": order.remark,  # None 값을 그대로 전달
        "update_at": order.update_at.isoformat() if order.update_at else None,
        "is_locked": order.is_locked,
        "locked_by": order.locked_by,
        "locked_at": order.locked_at.isoformat() if order.locked_at else None,
        # ETA 필드 ISO 8601 형식으로 변환
        "eta": order.eta.isoformat() if order.eta else None,
        # 상태 및 유형 라벨 추가
        "status_label": status_labels.get(order.status, order.status),
        "type_label": type_labels.get(order.type, order.type),
        # update_by 필드 추가
        "update_by": order.update_by,
        # 누락된 필드 추가 - 우편번호 관련
        "city": order.city,
        "county": order.county,
        "district": order.district,
        "region": order.region,
        "distance": order.distance,
        "duration_time": order.duration_time,
    }

    return data


def get_dashboard_list_item_data(order: Dashboard) -> Dict[str, Any]:
    """Dashboard 모델 객체를 목록 응답용 딕셔너리로 변환 (ISO 8601 형식 사용)"""
    if not order:
        return None

    # 목록 화면에서 실제로 필요한 필드만 선택하여 응답 최적화
    data = {
        "dashboard_id": order.dashboard_id,  # 주문 상세로 이동하기 위한 ID
        "order_no": order.order_no,  # 주문번호
        "type": order.type,  # 배송/회수 구분
        "department": order.department,  # 부서
        "warehouse": order.warehouse,  # 창고
        "sla": order.sla,  # SLA
        "customer": order.customer,  # 고객명
        "status": order.status,  # 상태
        "driver_name": order.driver_name,  # 배송기사명
        "eta": order.eta.isoformat() if order.eta else None,  # 예상 도착 시간
        # 상태 및 유형 라벨 추가
        "status_label": status_labels.get(order.status, order.status),
        "type_label": type_labels.get(order.type, order.type),
        # 목록에 표시되는 지역 정보
        "region": order.region,  # 지역 정보
        # 목록에 표시되는 거리 정보
        "distance": order.distance,  # 거리
        # 마지막 업데이트 정보 (정렬 등에 필요)
        "update_at": order.update_at.isoformat() if order.update_at else None,
    }

    return data


def get_dashboard_by_order_no(db: Session, order_no: str) -> Optional[Dashboard]:
    """주문번호로 주문 조회"""
    try:
        return db.query(Dashboard).filter(Dashboard.order_no == order_no).first()
    except SQLAlchemyError as e:
        logger.error(
            f"주문번호로 조회 중 오류 발생 ({order_no}): {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="데이터베이스 오류가 발생했습니다.",
        )


def get_dashboard_list(
    db: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> List[Dashboard]:
    """조건에 맞는 주문 목록 조회 (페이지네이션 없음)"""
    try:
        query = db.query(Dashboard)
        if start_date:
            start_datetime = datetime.combine(start_date, datetime.min.time())
            query = query.filter(Dashboard.eta >= start_datetime)
        if end_date:
            end_datetime = datetime.combine(end_date, datetime.max.time())
            query = query.filter(Dashboard.eta <= end_datetime)
        return query.order_by(desc(Dashboard.eta)).all()
    except SQLAlchemyError as e:
        logger.error(f"주문 목록 조회 중 DB 오류: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="데이터베이스 오류가 발생했습니다.",
        )


def search_dashboard_by_order_no(db: Session, order_no: str) -> Optional[Dashboard]:
    """주문번호로 정확히 일치하는 단일 주문 검색"""
    # get_dashboard_by_order_no 와 동일하므로 하나로 통일 가능 (여기서는 유지)
    return get_dashboard_by_order_no(db, order_no)


def _ensure_postal_code_exists(db: Session, postal_code: str):
    """PostalCode 테이블에 해당 우편번호가 없으면 생성"""
    postal_exists = (
        db.query(PostalCode).filter(PostalCode.postal_code == postal_code).first()
    )
    if not postal_exists:
        try:
            new_postal = PostalCode(
                postal_code=postal_code, city=None, county=None, district=None
            )
            db.add(new_postal)
            db.flush()  # ID 등 필요 시
            logger.info(f"존재하지 않는 우편번호 {postal_code} 레코드 생성")
        except SQLAlchemyError as e:
            db.rollback()  # 생성 실패 시 롤백
            logger.warning(f"우편번호 {postal_code} 레코드 생성 실패: {str(e)}")
            # 주문 생성/수정은 계속 진행될 수 있으나, 관련 정보는 누락될 수 있음


def create_dashboard(db: Session, data: DashboardCreate, user_id: str) -> Dashboard:
    """주문 생성"""
    postal_code = data.postal_code  # 검증은 스키마에서 완료
    _ensure_postal_code_exists(db, postal_code)

    # region은 DB에서 생성되므로 모델 데이터에서 제외
    order_data = data.model_dump(exclude={"region"})

    # 주문 생성 시 상태는 항상 'WAITING'으로 강제 설정 (클라이언트에서 어떤 값이 전달되어도 무시)
    if "status" in order_data:
        logger.info(
            f"주문 생성 시 상태 강제 설정: {order_data.get('status')} -> WAITING"
        )

    order_data.update(
        {
            "status": "WAITING",  # 강제로 상태는 WAITING으로 설정
            "create_time": datetime.now(),
            "update_by": user_id,
            "update_at": datetime.now(),
            "is_locked": False,
            # 모델에 없는 필드는 제외됨 (예: DashboardCreate에만 있는 필드)
        }
    )

    try:
        order = Dashboard(**order_data)
        db.add(order)
        db.flush()  # ID 등 생성 값 확인
        logger.info(f"주문 생성 완료: ID {order.dashboard_id}")
        return order
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"주문 생성 DB 오류: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="주문 생성 중 데이터베이스 오류가 발생했습니다.",
        )


def update_dashboard(
    db: Session, dashboard_id: int, data: Dict[str, Any], user_id: str
) -> Dashboard:
    """주문 업데이트 및 락 관리, 상태 변경 시 시간 자동 업데이트"""
    # update_order_action API 에서 호출 시 data는 DashboardUpdate 모델의 dict 형태

    try:
        # 1. 락 상태 확인 (서비스 함수 진입 시)
        lock_status = check_lock_status(db, "dashboard", dashboard_id, user_id)

        # 락 상태 확인이 실패했거나 락이 있으면서 내 락이 아닌 경우
        if not lock_status.get("success") or (
            lock_status.get("locked") and not lock_status.get("editable")
        ):
            error_msg = lock_status.get(
                "message", "다른 사용자가 편집 중이거나 락이 만료되었습니다."
            )
            logger.warning(f"주문 업데이트 락 확인 실패: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=error_msg,
            )

        order = (
            db.query(Dashboard).filter(Dashboard.dashboard_id == dashboard_id).first()
        )
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="수정할 주문을 찾을 수 없습니다.",
            )

        # update_data 준비
        update_fields = data.copy()

        # region 필드는 DB에서 자동 생성되므로 제거
        if "region" in update_fields:
            del update_fields["region"]

        if not update_fields:
            logger.info(f"주문 업데이트 내용 없음: ID {dashboard_id}")
            return order

        # 상태 변경 시 시간 업데이트 로직
        if "status" in update_fields and order.status != update_fields["status"]:
            old_status = order.status
            new_status = update_fields["status"]
            now = datetime.now()

            # 1. WAITING -> IN_PROGRESS
            if (
                old_status == "WAITING"
                and new_status == "IN_PROGRESS"
                and order.depart_time is None
            ):
                order.depart_time = now
                logger.info(
                    f"주문 ID {dashboard_id}: 상태 변경(IN_PROGRESS), depart_time 설정: {now}"
                )

            # 2. IN_PROGRESS -> COMPLETE/ISSUE/CANCEL
            elif (
                old_status == "IN_PROGRESS"
                and new_status in ["COMPLETE", "ISSUE", "CANCEL"]
                and order.complete_time is None
            ):
                order.complete_time = now
                logger.info(
                    f"주문 ID {dashboard_id}: 상태 변경({new_status}), complete_time 설정: {now}"
                )

            # 3. 롤백: COMPLETE/ISSUE/CANCEL -> IN_PROGRESS/WAITING
            elif old_status in ["COMPLETE", "ISSUE", "CANCEL"] and new_status in [
                "IN_PROGRESS",
                "WAITING",
            ]:
                if order.complete_time is not None:
                    order.complete_time = None
                    logger.info(
                        f"주문 ID {dashboard_id}: 상태 롤백({new_status}), complete_time 초기화"
                    )
                # 추가: IN_PROGRESS로 롤백 시 depart_time은 유지되어야 함
                # WAITNG으로 롤백 시 depart_time도 초기화 (아래 4번 조건에서 처리)

            # 4. 롤백: IN_PROGRESS -> WAITING
            elif old_status == "IN_PROGRESS" and new_status == "WAITING":
                if order.depart_time is not None:
                    order.depart_time = None
                    logger.info(
                        f"주문 ID {dashboard_id}: 상태 롤백(WAITING), depart_time 초기화"
                    )

        # 우편번호 변경 시 처리
        if (
            "postal_code" in update_fields
            and order.postal_code != update_fields["postal_code"]
        ):
            _ensure_postal_code_exists(db, update_fields["postal_code"])

        # 필드 업데이트 적용
        for key, value in update_fields.items():
            setattr(order, key, value)

        # 공통 업데이트 정보 설정
        order.update_by = user_id
        order.update_at = datetime.now()

        logger.info(
            f"주문 정보 업데이트 준비: ID={dashboard_id}, 변경 필드={list(update_fields.keys())}"
        )

        db.add(order)  # 세션에 변경사항 추가
        db.flush()  # DB에 반영 (아직 커밋 아님)
        logger.info(f"주문 업데이트 DB 반영 완료 (커밋 전): ID {dashboard_id}")

        # 수정 완료 후 락 해제
        try:
            release_lock(db, "dashboard", dashboard_id, user_id)
            logger.info(f"주문 업데이트 완료 후 락 해제: ID {dashboard_id}")
        except Exception as lock_release_err:
            logger.error(
                f"주문 업데이트 후 락 해제 실패: ID {dashboard_id}, 오류: {lock_release_err}"
            )
            # 락 해제 실패는 오류 처리하지 않고 계속 진행

        return order

    except HTTPException as http_exc:
        # 락 점검 실패(423) 또는 유효성 검사 오류(400 등)는 그대로 전달
        raise http_exc
    except SQLAlchemyError as e:
        logger.error(f"주문 업데이트 DB 오류: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="주문 업데이트 중 데이터베이스 오류 발생",
        )
    except Exception as e:
        logger.error(f"주문 업데이트 중 예외 발생: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="주문 업데이트 처리 중 오류 발생",
        )


def change_status(
    db: Session, dashboard_ids: List[int], new_status: str, user_id: str, user_role: str
) -> List[Dict[str, Any]]:
    """주문 상태 변경 (최종 규칙 시간 처리, 프론트엔드 검증 신뢰)"""
    results = []

    for dashboard_id in dashboard_ids:
        try:
            # 1. 락 상태 확인
            lock_status = check_lock_status(db, "dashboard", dashboard_id, user_id)
            if not lock_status.get("success") or not lock_status.get("editable"):
                results.append(
                    {
                        "id": dashboard_id,
                        "success": False,
                        "message": lock_status.get("message", "락 오류 또는 편집 불가"),
                    }
                )
                continue

            order = (
                db.query(Dashboard)
                .filter(Dashboard.dashboard_id == dashboard_id)
                .first()
            )
            if not order:
                results.append(
                    {
                        "id": dashboard_id,
                        "success": False,
                        "message": "주문을 찾을 수 없습니다.",
                    }
                )
                continue

            old_status = order.status
            if old_status == new_status:
                results.append(
                    {
                        "id": dashboard_id,
                        "success": True,
                        "message": "이미 해당 상태입니다.",
                    }
                )
                continue

            # --- 최종 규칙: ISSUE 또는 CANCEL 상태에서는 변경 불가 ---
            if old_status in ["ISSUE", "CANCEL"]:
                logger.warning(
                    f"최종 상태 변경 시도: ID {dashboard_id}, {old_status} -> {new_status}, User {user_id}"
                )
                results.append(
                    {
                        "id": dashboard_id,
                        "success": False,
                        "message": f"{status_labels.get(old_status, old_status)} 상태는 변경할 수 없습니다.",
                    }
                )
                continue

            # --- 백엔드 단계 유효성 검증 제거 ---
            # (프론트엔드에서 선택 자체를 제한하므로 불필요)

            # 2. 상태 변경 및 시간 기록 (최종 규칙 적용)
            order.status = new_status
            now = datetime.now()
            depart_time = order.depart_time
            complete_time = order.complete_time

            # --- 시간 값 설정/초기화 (최종 규칙) ---
            if new_status == "WAITING":  # 역행: IN_PROGRESS -> WAITING (Admin Only)
                if user_role == "ADMIN" and old_status == "IN_PROGRESS":
                    depart_time = None
                    complete_time = None
            elif new_status == "IN_PROGRESS":
                if old_status == "WAITING":  # 순방향: WAITING -> IN_PROGRESS
                    depart_time = now
                    complete_time = None
                elif (
                    user_role == "ADMIN" and old_status == "COMPLETE"
                ):  # 관리자 역행: COMPLETE -> IN_PROGRESS
                    complete_time = None  # 완료 시간만 제거
            elif new_status == "COMPLETE":
                if old_status == "IN_PROGRESS":  # 순방향: IN_PROGRESS -> COMPLETE
                    if depart_time is None:
                        depart_time = now  # 방어 코드
                    complete_time = now
            elif new_status == "ISSUE":
                # -> ISSUE는 시간 값 유지 (규칙 수정)
                pass
            elif new_status == "CANCEL":
                # -> CANCEL은 시간 값 유지 (규칙 수정)
                pass

            # 계산된 시간 값 적용
            order.depart_time = depart_time
            order.complete_time = complete_time

            # 공통 업데이트 정보
            order.update_by = user_id
            order.update_at = now

            db.flush()
            results.append(
                {
                    "id": dashboard_id,
                    "success": True,
                    "message": f"상태 변경: {status_labels.get(old_status)} → {status_labels.get(new_status)}",
                    "old_status": old_status,
                    "new_status": new_status,
                }
            )

        except SQLAlchemyError as e:
            db.rollback()
            logger.error(
                f"주문 상태 변경 중 DB 오류: ID {dashboard_id}, {str(e)}", exc_info=True
            )
            results.append(
                {"id": dashboard_id, "success": False, "message": "데이터베이스 오류"}
            )

    return results


def assign_driver(
    db: Session,
    dashboard_ids: List[int],
    driver_name: str,
    driver_contact: Optional[str],
    user_id: str,
) -> List[Dict[str, Any]]:
    """주문에 기사 배정"""
    results = []
    for dashboard_id in dashboard_ids:
        lock_held = False
        try:
            # 1. 락 상태 확인
            lock_status = check_lock_status(db, "dashboard", dashboard_id, user_id)
            if not lock_status.get("success") or not lock_status.get("editable"):
                results.append(
                    {
                        "id": dashboard_id,
                        "success": False,
                        "message": lock_status.get("message", "락 오류"),
                    }
                )
                continue
            lock_held = True

            order = (
                db.query(Dashboard)
                .filter(Dashboard.dashboard_id == dashboard_id)
                .first()
            )
            if not order:
                results.append(
                    {
                        "id": dashboard_id,
                        "success": False,
                        "message": "주문을 찾을 수 없습니다.",
                    }
                )
                continue

            order.driver_name = driver_name
            order.driver_contact = driver_contact
            order.update_by = user_id
            order.update_at = datetime.now()
            order.is_locked = False  # 기사 배정 시 락 해제

            db.flush()
            results.append(
                {
                    "id": dashboard_id,
                    "success": True,
                    "message": f"기사 배정 완료: {driver_name}",
                }
            )

        except SQLAlchemyError as e:
            db.rollback()
            logger.error(
                f"기사 배정 중 DB 오류: ID {dashboard_id}, {str(e)}", exc_info=True
            )
            results.append(
                {"id": dashboard_id, "success": False, "message": "데이터베이스 오류"}
            )
        finally:
            if lock_held:
                try:
                    release_lock(db, "dashboard", dashboard_id, user_id)
                except Exception as release_err:
                    logger.error(
                        f"기사 배정 락 해제 실패: ID {dashboard_id}, {release_err}"
                    )

    # db.commit()
    return results


def delete_dashboard(
    db: Session, dashboard_ids: List[int], user_id: str, user_role: str
) -> List[Dict[str, Any]]:
    """주문 삭제 (ADMIN 전용, 락 점검 포함)"""
    results = []
    if user_role != "ADMIN":
        logger.warning(f"주문 삭제 권한 없음: 사용자 {user_id}")
        return [{"success": False, "message": "삭제 권한이 없습니다."}]

    for dashboard_id in dashboard_ids:
        lock_held = False
        try:
            # 1. 락 상태 확인 (삭제 전)
            lock_status = check_lock_status(db, "dashboard", dashboard_id, user_id)
            if not lock_status.get("success") or not lock_status.get("editable"):
                # 다른 사용자가 락을 잡고 있으면 실패 처리
                results.append(
                    {
                        "id": dashboard_id,
                        "success": False,
                        "message": lock_status.get(
                            "message", "다른 사용자가 편집 중이거나 락 오류"
                        ),
                    }
                )
                continue  # 다음 ID 처리
            lock_held = True  # 락 소유 확인

            order = (
                db.query(Dashboard)
                .filter(Dashboard.dashboard_id == dashboard_id)
                .first()
            )
            if not order:
                results.append(
                    {
                        "id": dashboard_id,
                        "success": False,
                        "message": "주문을 찾을 수 없습니다.",
                    }
                )
                continue

            order_no = order.order_no
            db.delete(order)
            db.flush()
            results.append(
                {
                    "id": dashboard_id,
                    "success": True,
                    "message": f"주문 삭제 완료: {order_no}",
                }
            )
            logger.info(f"주문 삭제 완료: ID {dashboard_id}, OrderNo {order_no}")

        except SQLAlchemyError as e:
            logger.error(
                f"주문 삭제 중 DB 오류: ID {dashboard_id}, {str(e)}", exc_info=True
            )
            results.append(
                {"id": dashboard_id, "success": False, "message": "데이터베이스 오류"}
            )
            # 롤백은 트랜잭션 데코레이터가 처리
        except Exception as e:
            logger.error(
                f"주문 삭제 중 오류: ID {dashboard_id}, {str(e)}", exc_info=True
            )
            results.append(
                {
                    "id": dashboard_id,
                    "success": False,
                    "message": f"삭제 중 오류 발생: {e}",
                }
            )
        finally:
            # 락을 획득(소유 확인)했다면 삭제 후 해제 시도
            if lock_held:
                try:
                    # release_lock은 삭제된 행에 대해선 실패할 수 있으나 시도는 함
                    release_lock(db, "dashboard", dashboard_id, user_id)
                    logger.info(f"주문 삭제 후 락 해제 시도: ID {dashboard_id}")
                except Exception as lock_release_err:
                    # 삭제 후 락 해제 실패는 로깅만
                    logger.warning(
                        f"삭제된 주문 락 해제 실패 (예상 가능): ID {dashboard_id}, 오류: {lock_release_err}"
                    )

    return results


def get_dashboard_list_paginated(
    db: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    page: int = 1,
    page_size: int = 30,
) -> Tuple[List[Dashboard], Dict[str, Any]]:
    """조건에 맞는 주문 목록 조회 (페이지네이션 적용)"""
    try:
        query = db.query(Dashboard)
        if start_date:
            start_datetime = datetime.combine(start_date, datetime.min.time())
            query = query.filter(Dashboard.eta >= start_datetime)
        if end_date:
            end_datetime = datetime.combine(end_date, datetime.max.time())
            query = query.filter(Dashboard.eta <= end_datetime)

        query = query.order_by(desc(Dashboard.eta))
        orders, pagination_info = paginate_query(query, page, page_size)
        return orders, pagination_info

    except SQLAlchemyError as e:
        logger.error(f"페이지네이션 주문 목록 조회 중 DB 오류: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="주문 목록 조회 중 데이터베이스 오류가 발생했습니다.",
        )
    except Exception as e:
        logger.error(
            f"페이지네이션 주문 목록 조회 중 일반 오류: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="주문 목록 조회 중 오류가 발생했습니다.",
        )
