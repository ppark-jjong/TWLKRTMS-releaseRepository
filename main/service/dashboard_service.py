"""
대시보드(주문) 관련 서비스 로직
"""

from typing import Optional, List, Dict, Tuple, Any
from datetime import datetime, timedelta, date
from sqlalchemy import and_, or_, func, text, desc, case, extract
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from starlette import status

from main.models.dashboard_model import Dashboard
from main.models.postal_code_model import PostalCode
from main.models.user_model import User
from main.schema.dashboard_schema import DashboardCreate, DashboardUpdate
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

    # 관계(relationship)를 통해 로드된 사용자 이름 사용
    updater_name = order.updater.user_name if order.updater else None

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
        # ETA 필드 ISO 8601 형식으로 변환
        "eta": order.eta.isoformat() if order.eta else None,
        # 상태 및 유형 라벨 추가
        "status_label": status_labels.get(order.status, order.status),
        "type_label": type_labels.get(order.type, order.type),
        # update_by 필드 추가
        "update_by": order.update_by,  # ID는 유지 (내부 로직용)
        "updater_name": updater_name,  # 사용자 이름 추가
        # 누락된 필드 추가 - 우편번호 관련
        "city": order.city,
        "county": order.county,
        "district": order.district,
        "region": order.region,
        "distance": order.distance,
        "duration_time": order.duration_time,
        "delivery_company": order.delivery_company,  # 배송사 추가
        "version": order.version,  # 버전 추가
    }

    return data


def get_dashboard_list_item_data(order: Dashboard) -> Dict[str, Any]:
    """Dashboard 모델 객체를 목록 응답용 딕셔너리로 변환 (최종 요구사항 반영)"""
    if not order:
        return None

    # updater_name 조회 로직 제거

    data = {
        "dashboard_id": order.dashboard_id,
        "create_time": order.create_time.isoformat() if order.create_time else None,
        "order_no": order.order_no,  # 주문번호 추가
        "type": order.type,
        "department": order.department,
        "warehouse": order.warehouse,
        "sla": order.sla,
        "eta": order.eta.isoformat() if order.eta else None,
        "status": order.status,
        "region": order.region,
        "depart_time": order.depart_time.isoformat() if order.depart_time else None,
        "complete_time": (
            order.complete_time.isoformat() if order.complete_time else None
        ),
        "customer": order.customer,
        "delivery_company": order.delivery_company,
        "driver_name": order.driver_name,
        # version, updater_name, update_at 등 목록 표시 외 필드 제거
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
    """조건에 맞는 주문 목록 조회 (페이지네이션 없음) - User 정보 JOIN"""
    try:
        query = db.query(Dashboard).options(
            joinedload(Dashboard.updater)
        )  # User 정보 JOIN
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

    # delivery_company 필드 처리
    delivery_company = order_data.pop("delivery_company", None)

    order_data.update(
        {
            "status": "WAITING",  # 강제로 상태는 WAITING으로 설정
            "create_time": datetime.now(),
            "update_by": user_id,
            "update_at": datetime.now(),
            # 모델에 없는 필드는 제외됨 (예: DashboardCreate에만 있는 필드)
        }
    )

    try:
        order = Dashboard(**order_data)
        if delivery_company:  # 배송사 값이 있으면 설정
            order.delivery_company = delivery_company
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
    """주문 업데이트 상태 변경 시 시간 자동 업데이트"""
    # update_order_action API 에서 호출 시 data는 DashboardUpdate 모델의 dict 형태

    try:
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
            logger.info(
                f"DEBUG (update_dashboard entry): Order ID {dashboard_id}, Old Status: {old_status}, New Status: {new_status}, Current depart_time: {order.depart_time}, Current complete_time: {order.complete_time}"
            )

            # 시나리오 1: COMPLETE, ISSUE, CANCEL 상태들 간의 변경 (서로 다른 상태로 변경 시)
            if (
                old_status in ["COMPLETE", "ISSUE", "CANCEL"]
                and new_status in ["COMPLETE", "ISSUE", "CANCEL"]
                and old_status != new_status
            ):
                logger.info(
                    f"DEBUG (update_dashboard): SCENARIO 1 - ({old_status} -> {new_status}) for order ID {dashboard_id}. Updating complete_time."
                )
                order.complete_time = now

            # 시나리오 2: WAITING -> IN_PROGRESS
            elif old_status == "WAITING" and new_status == "IN_PROGRESS":
                logger.info(
                    f"DEBUG (update_dashboard): SCENARIO 2 - WAITING -> IN_PROGRESS for order ID {dashboard_id}."
                )
                order.depart_time = now

            # 시나리오 3: IN_PROGRESS -> COMPLETE
            elif old_status == "IN_PROGRESS" and new_status == "COMPLETE":
                logger.info(
                    f"DEBUG (update_dashboard): SCENARIO 3 - IN_PROGRESS -> COMPLETE for order ID {dashboard_id}."
                )
                if order.depart_time is None:
                    logger.info(
                        f"DEBUG (update_dashboard): Correcting missing depart_time for order ID {dashboard_id} during IN_PROGRESS -> COMPLETE."
                    )
                    order.depart_time = now
                order.complete_time = now

            # 시나리오 4: IN_PROGRESS -> ISSUE 또는 CANCEL
            elif old_status == "IN_PROGRESS" and new_status in ["ISSUE", "CANCEL"]:
                logger.info(
                    f"DEBUG (update_dashboard): SCENARIO 4 - IN_PROGRESS -> {new_status} for order ID {dashboard_id}."
                )
                if order.depart_time is None:
                    logger.info(
                        f"DEBUG (update_dashboard): Correcting missing depart_time for order ID {dashboard_id} during IN_PROGRESS -> {new_status}."
                    )
                    order.depart_time = now
                order.complete_time = now

            # 시나리오 5: COMPLETE -> IN_PROGRESS (역방향)
            elif old_status == "COMPLETE" and new_status == "IN_PROGRESS":
                logger.info(
                    f"DEBUG (update_dashboard): SCENARIO 5 - COMPLETE -> IN_PROGRESS for order ID {dashboard_id}."
                )
                order.complete_time = None

            # 시나리오 6: IN_PROGRESS -> WAITING (역방향)
            elif old_status == "IN_PROGRESS" and new_status == "WAITING":
                logger.info(
                    f"DEBUG (update_dashboard): SCENARIO 6 - IN_PROGRESS -> WAITING for order ID {dashboard_id}."
                )
                order.depart_time = None
                order.complete_time = None

            # 시나리오 7: ISSUE 또는 CANCEL 에서 WAITING 또는 IN_PROGRESS 로 변경
            elif old_status in ["ISSUE", "CANCEL"]:
                if new_status == "WAITING":
                    logger.info(
                        f"DEBUG (update_dashboard): SCENARIO 7a - {old_status} -> WAITING for order ID {dashboard_id}."
                    )
                    order.depart_time = None
                    order.complete_time = None
                elif new_status == "IN_PROGRESS":
                    logger.info(
                        f"DEBUG (update_dashboard): SCENARIO 7b - {old_status} -> IN_PROGRESS for order ID {dashboard_id}."
                    )
                    order.depart_time = now
                    order.complete_time = None

            else:
                logger.warning(
                    f"DEBUG (update_dashboard): UNHANDLED or FALLTHROUGH status transition for order ID {dashboard_id} from {old_status} to {new_status}."
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
        order.version += 1  # 버전 1 증가

        logger.info(
            f"주문 정보 업데이트 준비: ID={dashboard_id}, 변경 필드={list(update_fields.keys())}"
        )

        db.add(order)  # 세션에 변경사항 추가
        db.flush()  # DB에 반영 (아직 커밋 아님)
        logger.info(f"주문 업데이트 DB 반영 완료 (커밋 전): ID {dashboard_id}")

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
    """주문 상태 변경 (재정의된 규칙 및 시간 값 처리 적용)"""
    results = []
    now = datetime.now()

    # 재정의된 상태 전이 규칙 (백엔드용)
    status_transitions = {  # 일반 사용자
        "WAITING": ["IN_PROGRESS"],  # ISSUE, CANCEL 제거
        "IN_PROGRESS": ["COMPLETE", "ISSUE", "CANCEL"],
        "COMPLETE": ["ISSUE", "CANCEL"],
        "ISSUE": ["COMPLETE", "CANCEL"],
        "CANCEL": ["COMPLETE", "ISSUE"],
    }
    admin_status_transitions = {  # 관리자
        "WAITING": ["IN_PROGRESS"],  # ISSUE, CANCEL 제거
        "IN_PROGRESS": ["WAITING", "COMPLETE", "ISSUE", "CANCEL"],
        "COMPLETE": [
            "IN_PROGRESS",
            "ISSUE",
            "CANCEL",
        ],  # WAITING으로 바로 가는 것 제외 (규칙 기반)
        "ISSUE": ["IN_PROGRESS", "COMPLETE", "CANCEL"],  # WAITING 제외
        "CANCEL": ["IN_PROGRESS", "COMPLETE", "ISSUE"],  # WAITING 제외
    }

    for dashboard_id in dashboard_ids:
        try:
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

            # --- 상태 변경 유효성 검증 (재정의된 규칙) ---
            allowed_next_states = []
            if user_role == "ADMIN":
                allowed_next_states = admin_status_transitions.get(old_status, [])
            else:
                allowed_next_states = status_transitions.get(old_status, [])

            can_change = new_status in allowed_next_states

            if not can_change:
                logger.warning(
                    f"권한 없는 상태 변경 시도 (재정의 규칙): ID {dashboard_id}, {old_status} -> {new_status}, User {user_id}, Role {user_role}"
                )
                results.append(
                    {
                        "id": dashboard_id,
                        "success": False,
                        "message": f"현재 상태 '{status_labels.get(old_status, old_status)}'에서 '{status_labels.get(new_status, new_status)}'(으)로 변경할 수 없습니다.",
                    }
                )
                continue

            # 상태 변경 적용
            order.status = new_status

            # --- 시간 값 설정/초기화 로직 (재정의된 규칙) ---
            # 순방향 시간값 변경
            if old_status == "WAITING" and new_status == "IN_PROGRESS":
                order.depart_time = now
            elif old_status == "IN_PROGRESS" and new_status in [
                "COMPLETE",
                "ISSUE",
                "CANCEL",
            ]:
                if (
                    order.depart_time is None
                ):  # 안전 장치: IN_PROGRESS인데 depart_time 없으면 설정
                    order.depart_time = now
                order.complete_time = now

            # 역방향 시간값 초기화
            elif (
                old_status in ["COMPLETE", "ISSUE", "CANCEL"]
                and new_status == "IN_PROGRESS"
            ):  # COMPLETE, ISSUE, CANCEL -> IN_PROGRESS (주로 관리자)
                order.complete_time = None  # 완료시간만 초기화
            elif (
                old_status == "IN_PROGRESS" and new_status == "WAITING"
            ):  # IN_PROGRESS -> WAITING (주로 관리자)
                order.depart_time = None
                order.complete_time = None  # 출발시간, 완료시간 모두 초기화

            # COMPLETE, ISSUE, CANCEL 상태들 간의 변경 시 complete_time 업데이트 (사용자 요청)
            elif old_status in ["COMPLETE", "ISSUE", "CANCEL"] and new_status in [
                "COMPLETE",
                "ISSUE",
                "CANCEL",
            ]:
                logger.info(
                    f"DEBUG: Updating complete_time for order ID {order.dashboard_id} from {old_status} to {new_status}. Old complete_time: {order.complete_time}, New complete_time will be: {now}"
                )
                # 이 블록에 진입 시 old_status != new_status 는 함수 상단에서 보장됨
                order.complete_time = now

            # 공통 업데이트 정보
            order.update_by = user_id
            order.update_at = now
            order.version += 1

            db.flush()
            logger.info(
                f"주문 상태 변경 성공 (재정의 규칙): ID {dashboard_id}, {old_status} -> {new_status}, "
                f"depart: {order.depart_time}, complete: {order.complete_time}"
            )
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
                f"주문 상태 변경 중 DB 오류 (재정의 규칙): ID {dashboard_id}, {e}",
                exc_info=True,
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
    delivery_company: Optional[str],
    user_id: str,
) -> List[Dict[str, Any]]:
    """주문에 기사 및 배송사 배정"""
    results = []
    now = datetime.now()
    for dashboard_id in dashboard_ids:
        try:
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
            order.delivery_company = delivery_company
            order.update_by = user_id
            order.update_at = now
            order.version += 1

            db.flush()
            results.append(
                {
                    "id": dashboard_id,
                    "success": True,
                    "message": f"기사/배송사 배정 완료: {driver_name} ({delivery_company or '-'})",
                }
            )
            logger.info(
                f"주문 기사/배송사 배정 성공: ID {dashboard_id}, Driver {driver_name}, Company {delivery_company}"
            )

        except SQLAlchemyError as e:
            db.rollback()
            logger.error(
                f"기사/배송사 배정 중 DB 오류: ID {dashboard_id}, {str(e)}",
                exc_info=True,
            )
            results.append(
                {"id": dashboard_id, "success": False, "message": "데이터베이스 오류"}
            )

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
        try:
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
