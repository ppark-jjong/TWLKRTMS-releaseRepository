"""
대시보드(주문) 관련 라우터
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
    Query,
    status,
    Path,
)
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
import os

# main.py 에서 설정된 전역 templates 객체 임포트 -> 제거
# from main.main import templates -> 제거
from main.core.templating import templates  # 수정된 경로에서 임포트

from main.utils.database import get_db
from main.utils.security import get_current_user, get_admin_user
from main.utils.logger import logger
from main.schema.dashboard_schema import (
    DashboardCreate,
    DashboardUpdate,
    DashboardResponse,
    DashboardListResponse,
    StatusChangeRequest,
    DriverAssignRequest,
    DashboardDeleteRequest,
)
from main.service.dashboard_service import (
    get_dashboard_by_id,
    get_dashboard_list,
    search_dashboard_by_order_no,
    create_dashboard,
    update_dashboard,
    change_status,
    assign_driver,
    delete_dashboard,
    get_lock_status,
)

# 라우터 생성
router = APIRouter()


@router.get("")
async def dashboard_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
    startDate: Optional[str] = None,
    endDate: Optional[str] = None,
    orderNo: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=100),
):
    """
    대시보드 페이지 렌더링
    """
    # 날짜 기본값은 오늘
    today = datetime.now().date()
    start_date = today
    end_date = today

    logger.info(
        f"대시보드 페이지 접근: URL 파라미터 - startDate={startDate}, endDate={endDate}, orderNo={orderNo}"
    )

    # URL 파라미터에서 날짜 가져오기
    if startDate:
        try:
            # 'YYYY-MM-DD' 또는 'YYYY-MM-DD HH:MM:SS' 형식 처리
            start_date = datetime.strptime(startDate.split(" ")[0], "%Y-%m-%d").date()
            logger.info(f"시작 날짜 설정: {start_date}")
        except ValueError:
            logger.warning(
                f"잘못된 시작 날짜 형식: {startDate}. 오늘 날짜로 대체합니다."
            )
    else:
        logger.info(f"시작 날짜 파라미터 없음. 오늘 날짜({today})로 설정")

    if endDate:
        try:
            # 'YYYY-MM-DD' 또는 'YYYY-MM-DD HH:MM:SS' 형식 처리
            end_date = datetime.strptime(endDate.split(" ")[0], "%Y-%m-%d").date()
            logger.info(f"종료 날짜 설정: {end_date}")
        except ValueError:
            logger.warning(f"잘못된 종료 날짜 형식: {endDate}. 오늘 날짜로 대체합니다.")
    else:
        logger.info(f"종료 날짜 파라미터 없음. 오늘 날짜({today})로 설정")

    # 주문번호로 검색
    if orderNo:
        try:
            orders, pagination, stats = search_dashboard_by_order_no(
                db=db,
                order_no=orderNo,
                page=page,
                page_size=limit,
            )
        except Exception as e:
            logger.error(f"주문번호 검색 중 오류 발생: {e}", exc_info=True)
            orders, pagination, stats = (
                [],
                {
                    "total": 0,
                    "total_pages": 0,
                    "current": 1,
                    "page_size": limit,
                    "start": 0,
                    "end": 0,
                },
                {},
            )
    else:
        # 기본 데이터 조회 (선택된 날짜 기준 - 나머지 필터링은 클라이언트에서 처리)
        try:
            orders, pagination, stats = get_dashboard_list(
                db=db,
                start_date=start_date,
                end_date=end_date,
                page=page,
                page_size=limit,
            )
        except Exception as e:
            logger.error(f"대시보드 데이터 조회 중 오류 발생: {e}", exc_info=True)
            # 오류 발생 시 빈 데이터와 함께 오류 페이지 렌더링 또는 오류 메시지 표시
            # 여기서는 간단히 빈 리스트 반환 처리
            orders, pagination, stats = (
                [],
                {
                    "total": 0,
                    "total_pages": 0,
                    "current": 1,
                    "page_size": limit,
                    "start": 0,
                    "end": 0,
                },
                {},
            )

    # 주문 데이터 가공 (템플릿 표시용)
    orders_data = []
    for order in orders:
        # 상태, 유형 레이블 설정
        status_labels = {
            "WAITING": "대기",
            "IN_PROGRESS": "진행",
            "COMPLETE": "완료",
            "ISSUE": "이슈",
            "CANCEL": "취소",
        }
        type_labels = {"DELIVERY": "배송", "RETURN": "반품"}

        # 날짜 포맷팅
        eta_formatted = order.eta.strftime("%Y-%m-%d %H:%M") if order.eta else ""
        create_time_formatted = (
            order.create_time.strftime("%Y-%m-%d %H:%M") if order.create_time else ""
        )

        orders_data.append(
            {
                "dashboardId": order.dashboard_id,
                "orderNo": order.order_no,
                "type": order.type,
                "type_label": type_labels.get(order.type, order.type),
                "status": order.status,
                "status_label": status_labels.get(order.status, order.status),
                "department": order.department,
                "warehouse": order.warehouse,
                "sla": order.sla,
                "eta": eta_formatted,
                "createTime": create_time_formatted,
                "departTime": (
                    order.depart_time.strftime("%Y-%m-%d %H:%M")
                    if order.depart_time
                    else ""
                ),
                "completeTime": (
                    order.complete_time.strftime("%Y-%m-%d %H:%M")
                    if order.complete_time
                    else ""
                ),
                "postalCode": order.postal_code,
                "address": order.address,
                "region": getattr(order, "region", "") or "",
                "city": getattr(order, "city", "") or "",
                "county": getattr(order, "county", "") or "",
                "district": getattr(order, "district", "") or "",
                "distance": getattr(order, "distance", 0),
                "durationTime": getattr(order, "duration_time", 0),
                "customer": order.customer,
                "contact": order.contact,
                "driverName": order.driver_name,
                "driverContact": order.driver_contact,
                "remark": getattr(order, "remark", ""),
                "isLocked": getattr(order, "is_locked", False),
                "updatedBy": getattr(order, "update_by", None),
                "updateAt": (
                    getattr(order, "update_at", None).strftime("%Y-%m-%d %H:%M")
                    if getattr(order, "update_at", None)
                    else ""
                ),
            }
        )

    # 드롭다운 선택 옵션
    statuses = [
        {"value": "WAITING", "label": "대기"},
        {"value": "IN_PROGRESS", "label": "진행"},
        {"value": "COMPLETE", "label": "완료"},
        {"value": "ISSUE", "label": "이슈"},
        {"value": "CANCEL", "label": "취소"},
    ]

    departments = [
        {"value": "CS", "label": "CS"},
        {"value": "HES", "label": "HES"},
        {"value": "LENOVO", "label": "LENOVO"},
    ]

    warehouses = [
        {"value": "SEOUL", "label": "서울"},
        {"value": "BUSAN", "label": "부산"},
        {"value": "GWANGJU", "label": "광주"},
        {"value": "DAEJEON", "label": "대전"},
    ]

    types = [
        {"value": "DELIVERY", "label": "배송"},
        {"value": "RETURN", "label": "회수"},
    ]

    # 템플릿 렌더링
    return templates.TemplateResponse(  # 전역 templates 사용
        "dashboard.html",
        {
            "request": request,
            "user": current_user,
            "orders": orders_data,
            "pagination": pagination,
            "stats": stats if stats else {},  # stats가 None일 경우 빈 dict 전달
            "statuses": statuses,
            "departments": departments,
            "warehouses": warehouses,
            "types": types,
            "selected_date": start_date.strftime(
                "%Y-%m-%d"
            ),  # date_filter 대신 start_date 사용
        },
    )


@router.get("/orders", response_model=DashboardListResponse)
async def get_orders(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    status: Optional[str] = None,
    department: Optional[str] = None,
    warehouse: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    """
    주문 목록 조회 API
    """
    # 주문 목록 조회
    orders, pagination, stats = get_dashboard_list(
        db=db,
        start_date=start_date,
        end_date=end_date,
        status=status,
        department=department,
        warehouse=warehouse,
        page=page,
        page_size=page_size,
    )

    # 응답 데이터 가공
    status_labels = {
        "WAITING": "대기",
        "IN_PROGRESS": "진행",
        "COMPLETE": "완료",
        "ISSUE": "이슈",
        "CANCEL": "취소",
    }
    type_labels = {"DELIVERY": "배송", "RETURN": "회수"}

    orders_data = []
    for order in orders:
        order_dict = {
            "dashboardId": order.dashboard_id,
            "orderNo": order.order_no,
            "type": order.type,
            "status": order.status,
            "department": order.department,
            "warehouse": order.warehouse,
            "sla": order.sla,
            "eta": order.eta,
            "postalCode": order.postal_code,
            "customer": order.customer,
            "region": order.region,
            "driverName": order.driver_name,
            "statusLabel": status_labels.get(order.status, order.status),
            "typeLabel": type_labels.get(order.type, order.type),
        }
        orders_data.append(order_dict)

    # 응답 반환
    return {
        "success": True,
        "message": "주문 목록 조회 성공",
        "data": orders_data,
        "pagination": pagination,
        "stats": stats,
    }


@router.get("/search", response_model=DashboardListResponse)
async def search_order(
    request: Request,
    order_no: str,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
):
    """
    주문번호로 주문 검색 API
    """
    # 주문 검색
    orders, pagination, stats = search_dashboard_by_order_no(
        db=db, order_no=order_no, page=page, page_size=page_size
    )

    # 응답 데이터 가공
    status_labels = {
        "WAITING": "대기",
        "IN_PROGRESS": "진행",
        "COMPLETE": "완료",
        "ISSUE": "이슈",
        "CANCEL": "취소",
    }
    type_labels = {"DELIVERY": "배송", "RETURN": "회수"}

    orders_data = []
    for order in orders:
        order_dict = {
            "dashboardId": order.dashboard_id,
            "orderNo": order.order_no,
            "type": order.type,
            "status": order.status,
            "department": order.department,
            "warehouse": order.warehouse,
            "sla": order.sla,
            "eta": order.eta,
            "postalCode": order.postal_code,
            "customer": order.customer,
            "region": order.region,
            "driverName": order.driver_name,
            "statusLabel": status_labels.get(order.status, order.status),
            "typeLabel": type_labels.get(order.type, order.type),
        }
        orders_data.append(order_dict)

    # 응답 반환
    return {
        "success": True,
        "message": f"주문번호 '{order_no}' 검색 결과",
        "data": orders_data,
        "pagination": pagination,
        "stats": stats,
    }


@router.get("/orders/{dashboard_id}", response_model=DashboardResponse)
async def get_order_detail(
    request: Request,
    dashboard_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    주문 상세 조회 API
    """
    order = get_dashboard_by_id(db, dashboard_id)

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="주문을 찾을 수 없습니다."
        )

    # 락 상태 확인
    lock_status = get_lock_status(db, dashboard_id, current_user.get("user_id"))

    # 응답 데이터 가공
    status_labels = {
        "WAITING": "대기",
        "IN_PROGRESS": "진행",
        "COMPLETE": "완료",
        "ISSUE": "이슈",
        "CANCEL": "취소",
    }
    type_labels = {"DELIVERY": "배송", "RETURN": "회수"}

    order_data = {
        "dashboardId": order.dashboard_id,
        "orderNo": order.order_no,
        "type": order.type,
        "status": order.status,
        "department": order.department,
        "warehouse": order.warehouse,
        "sla": order.sla,
        "eta": order.eta,
        "createTime": order.create_time,
        "departTime": order.depart_time,
        "completeTime": order.complete_time,
        "postalCode": order.postal_code,
        "city": getattr(order, "city", "") or "",
        "county": getattr(order, "county", "") or "",
        "district": getattr(order, "district", "") or "",
        "region": getattr(order, "region", "") or "",
        "distance": getattr(order, "distance", None),
        "durationTime": getattr(order, "duration_time", None),
        "address": order.address,
        "customer": order.customer,
        "contact": order.contact,
        "driverName": order.driver_name,
        "driverContact": order.driver_contact,
        "updatedBy": order.update_by,
        "remark": order.remark,
        "updateAt": order.update_at,
        "isLocked": order.is_locked,
        "statusLabel": status_labels.get(order.status, order.status),
        "typeLabel": type_labels.get(order.type, order.type),
        "editable": lock_status.get("editable", False),
    }

    return order_data


@router.post("/orders", status_code=status.HTTP_201_CREATED)
async def create_order(
    request: Request,
    order_data: DashboardCreate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    주문 생성 API
    """
    try:
        # 주문 생성
        new_order = create_dashboard(
            db=db, data=order_data, user_id=current_user.get("user_id")
        )

        return {
            "success": True,
            "message": "주문이 성공적으로 생성되었습니다.",
            "id": new_order.dashboard_id,
        }
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code, content={"success": False, "message": e.detail}
        )
    except Exception as e:
        logger.error(f"주문 생성 중 오류 발생: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "주문 생성 중 오류가 발생했습니다."},
        )


@router.put("/orders/{dashboard_id}")
async def update_order(
    request: Request,
    dashboard_id: int = Path(..., ge=1),
    order_data: DashboardUpdate = None,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    주문 업데이트 API
    """
    try:
        # 주문 업데이트
        updated_order = update_dashboard(
            db=db,
            dashboard_id=dashboard_id,
            data=order_data,
            user_id=current_user.get("user_id"),
        )

        return {
            "success": True,
            "message": "주문이 성공적으로 업데이트되었습니다.",
            "id": updated_order.dashboard_id,
        }
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code, content={"success": False, "message": e.detail}
        )
    except Exception as e:
        logger.error(f"주문 업데이트 중 오류 발생: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "주문 업데이트 중 오류가 발생했습니다.",
            },
        )


@router.post("/status")
async def change_order_status(
    request: Request,
    status_data: StatusChangeRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    주문 상태 변경 API
    """
    try:
        # 상태 변경
        results = change_status(
            db=db,
            dashboard_ids=status_data.ids,
            new_status=status_data.status,
            user_id=current_user.get("user_id"),
            user_role=current_user.get("user_role"),
        )

        # 성공/실패 건수 계산
        success_count = sum(1 for r in results if r.get("success", False))
        fail_count = len(results) - success_count

        return {
            "success": True,
            "message": f"상태 변경 완료: {success_count}건 성공, {fail_count}건 실패",
            "results": results,
        }
    except Exception as e:
        logger.error(f"상태 변경 중 오류 발생: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "상태 변경 중 오류가 발생했습니다."},
        )


@router.post("/driver")
async def assign_order_driver(
    request: Request,
    driver_data: DriverAssignRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    주문 기사 배정 API
    """
    try:
        # 기사 배정
        results = assign_driver(
            db=db,
            dashboard_ids=driver_data.ids,
            driver_name=driver_data.driver_name,
            driver_contact=driver_data.driver_contact,
            user_id=current_user.get("user_id"),
        )

        # 성공/실패 건수 계산
        success_count = sum(1 for r in results if r.get("success", False))
        fail_count = len(results) - success_count

        return {
            "success": True,
            "message": f"기사 배정 완료: {success_count}건 성공, {fail_count}건 실패",
            "results": results,
        }
    except Exception as e:
        logger.error(f"기사 배정 중 오류 발생: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "기사 배정 중 오류가 발생했습니다."},
        )


@router.post("/delete")
async def delete_order(
    request: Request,
    delete_data: DashboardDeleteRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    주문 삭제 API
    """
    try:
        # 관리자 권한 확인
        if current_user.get("user_role") != "ADMIN":
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"success": False, "message": "삭제 권한이 없습니다."},
            )

        # 주문 삭제
        results = delete_dashboard(
            db=db,
            dashboard_ids=delete_data.ids,
            user_id=current_user.get("user_id"),
            user_role=current_user.get("user_role"),
        )

        # 성공/실패 건수 계산
        success_count = sum(1 for r in results if r.get("success", False))
        fail_count = len(results) - success_count

        return {
            "success": True,
            "message": f"주문 삭제 완료: {success_count}건 성공, {fail_count}건 실패",
            "results": results,
        }
    except Exception as e:
        logger.error(f"주문 삭제 중 오류 발생: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "주문 삭제 중 오류가 발생했습니다."},
        )


@router.get("/lock/{dashboard_id}")
async def check_order_lock(
    request: Request,
    dashboard_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    주문 락 상태 확인 API
    """
    try:
        # 락 상태 확인
        lock_status = get_lock_status(db, dashboard_id, current_user.get("user_id"))
        return lock_status
    except Exception as e:
        logger.error(f"락 상태 확인 중 오류 발생: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "락 상태 확인 중 오류가 발생했습니다.",
            },
        )
