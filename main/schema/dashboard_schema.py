"""
대시보드(주문) 관련 스키마 정의
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator


class DashboardCreate(BaseModel):
    """주문 생성 요청 스키마"""

    order_no: str = Field(..., description="주문번호", alias="orderNo")
    type: str = Field(..., description="유형(DELIVERY/RETURN)")
    department: str = Field(..., description="부서(CS/HES/LENOVO)")
    warehouse: str = Field(..., description="창고(SEOUL/BUSAN/GWANGJU/DAEJEON)")
    sla: str = Field(..., description="SLA")
    eta: datetime = Field(..., description="ETA(도착 예정 시간)")
    postal_code: str = Field(..., description="우편번호", alias="postalCode")
    address: str = Field(..., description="주소")
    customer: str = Field(..., description="고객명")
    contact: Optional[str] = Field(None, description="연락처")
    remark: Optional[str] = Field(None, description="비고")

    @validator("postal_code")
    def validate_postal_code(cls, v):
        """우편번호 검증 및 자동 보완 (4자리 → 5자리)"""
        if v and len(v) == 4:
            v = "0" + v
        if v and len(v) != 5:
            raise ValueError("우편번호는 5자리여야 합니다.")
        return v

    class Config:
        """스키마 설정"""

        by_alias = True
        populate_by_field_name = True
        json_encoders = {datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S")}


class DashboardUpdate(BaseModel):
    """주문 업데이트 요청 스키마"""

    order_no: Optional[str] = Field(None, description="주문번호", alias="orderNo")
    type: Optional[str] = Field(None, description="유형(DELIVERY/RETURN)")
    department: Optional[str] = Field(None, description="부서(CS/HES/LENOVO)")
    warehouse: Optional[str] = Field(
        None, description="창고(SEOUL/BUSAN/GWANGJU/DAEJEON)"
    )
    sla: Optional[str] = Field(None, description="SLA")
    eta: Optional[datetime] = Field(None, description="ETA(도착 예정 시간)")
    postal_code: Optional[str] = Field(None, description="우편번호", alias="postalCode")
    address: Optional[str] = Field(None, description="주소")
    customer: Optional[str] = Field(None, description="고객명")
    contact: Optional[str] = Field(None, description="연락처")
    remark: Optional[str] = Field(None, description="비고")
    driver_name: Optional[str] = Field(None, description="기사 이름", alias="driverName")
    driver_contact: Optional[str] = Field(None, description="기사 연락처", alias="driverContact")

    @validator("postal_code")
    def validate_postal_code(cls, v):
        """우편번호 검증 및 자동 보완 (4자리 → 5자리)"""
        if v and len(v) == 4:
            v = "0" + v
        if v and len(v) != 5:
            raise ValueError("우편번호는 5자리여야 합니다.")
        return v

    class Config:
        """스키마 설정"""

        by_alias = True
        populate_by_field_name = True
        json_encoders = {datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S")}


class DashboardResponse(BaseModel):
    """주문 상세 응답 스키마"""

    dashboard_id: int = Field(..., description="대시보드 ID", alias="dashboardId")
    order_no: str = Field(..., description="주문번호", alias="orderNo")
    type: str = Field(..., description="유형(DELIVERY/RETURN)")
    department: str = Field(..., description="부서(CS/HES/LENOVO)")
    warehouse: str = Field(..., description="창고(SEOUL/BUSAN/GWANGJU/DAEJEON)")
    sla: str = Field(..., description="SLA")
    region: Optional[str] = Field(None, description="지역(시 구 동)")
    eta: datetime = Field(..., description="ETA(도착 예정 시간)")
    postal_code: str = Field(..., description="우편번호", alias="postalCode")
    customer: str = Field(..., description="고객명")
    status: str = Field(
        ..., description="상태(WAITING/IN_PROGRESS/COMPLETE/ISSUE/CANCEL)"
    )
    create_time: datetime = Field(..., description="생성 시간", alias="createTime")
    depart_time: Optional[datetime] = Field(
        None, description="출발 시간", alias="departTime"
    )
    complete_time: Optional[datetime] = Field(
        None, description="완료 시간", alias="completeTime"
    )
    city: Optional[str] = Field(None, description="시")
    county: Optional[str] = Field(None, description="구")
    district: Optional[str] = Field(None, description="동")
    distance: Optional[int] = Field(None, description="거리(km)")
    duration_time: Optional[int] = Field(
        None, description="소요 시간(분)", alias="durationTime"
    )
    driver_name: Optional[str] = Field(
        None, description="기사 이름", alias="driverName"
    )
    driver_contact: Optional[str] = Field(
        None, description="기사 연락처", alias="driverContact"
    )
    updated_by: Optional[str] = Field(
        None, description="마지막 업데이트 사용자", alias="updatedBy"
    )
    remark: Optional[str] = Field(None, description="비고")
    update_at: Optional[datetime] = Field(
        None, description="마지막 업데이트 시간", alias="updateAt"
    )
    is_locked: bool = Field(False, description="락 여부", alias="isLocked")

    class Config:
        """스키마 설정"""

        by_alias = True
        populate_by_field_name = True
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S") if v else None
        }


class DashboardListItem(BaseModel):
    """주문 목록 항목 스키마"""

    dashboard_id: int = Field(..., description="대시보드 ID", alias="dashboardId")
    order_no: str = Field(..., description="주문번호", alias="orderNo")
    type: str = Field(..., description="유형(DELIVERY/RETURN)")
    department: str = Field(..., description="부서(CS/HES/LENOVO)")
    warehouse: str = Field(..., description="창고(SEOUL/BUSAN/GWANGJU/DAEJEON)")
    sla: str = Field(..., description="SLA")
    region: Optional[str] = Field(None, description="지역(시 구 동)")
    eta: datetime = Field(..., description="ETA(도착 예정 시간)")
    postal_code: str = Field(..., description="우편번호", alias="postalCode")
    customer: str = Field(..., description="고객명")
    status: str = Field(
        ..., description="상태(WAITING/IN_PROGRESS/COMPLETE/ISSUE/CANCEL)"
    )
    driver_name: Optional[str] = Field(
        None, description="기사 이름", alias="driverName"
    )

    class Config:
        """스키마 설정"""

        by_alias = True
        populate_by_field_name = True
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S") if v else None
        }


class DashboardListResponse(BaseModel):
    """주문 목록 응답 스키마"""

    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="메시지")
    data: List[DashboardListItem] = Field(..., description="주문 목록")
    pagination: Dict[str, Any] = Field(..., description="페이지네이션 정보")
    stats: Dict[str, int] = Field(..., description="통계 정보")

    class Config:
        """스키마 설정"""

        by_alias = True
        populate_by_field_name = True


class StatusChangeRequest(BaseModel):
    """상태 변경 요청 스키마"""

    ids: List[int] = Field(..., description="변경할 주문 ID 목록", alias="orderIds")
    status: str = Field(
        ..., description="변경할 상태(WAITING/IN_PROGRESS/COMPLETE/ISSUE/CANCEL)"
    )

    class Config:
        """스키마 설정"""

        by_alias = True
        populate_by_field_name = True


class DriverAssignRequest(BaseModel):
    """기사 배정 요청 스키마"""

    ids: List[int] = Field(..., description="배정할 주문 ID 목록", alias="orderIds")
    driver_name: str = Field(..., description="기사 이름", alias="driverName")
    driver_contact: Optional[str] = Field(
        None, description="기사 연락처", alias="driverContact"
    )

    class Config:
        """스키마 설정"""

        by_alias = True
        populate_by_field_name = True


class DashboardDeleteRequest(BaseModel):
    """주문 삭제 요청 스키마"""

    ids: List[int] = Field(..., description="삭제할 주문 ID 목록", alias="orderIds")

    class Config:
        """스키마 설정"""

        by_alias = True
        populate_by_field_name = True


class LockStatusResponse(BaseModel):
    """락 상태 응답 스키마"""

    editable: bool = Field(..., description="편집 가능 여부")
    message: str = Field(..., description="메시지")
    locked_by: Optional[str] = Field(None, description="락 보유자", alias="lockedBy")
    locked_at: Optional[datetime] = Field(
        None, description="락 획득 시간", alias="lockedAt"
    )

    class Config:
        """스키마 설정"""

        by_alias = True
        populate_by_field_name = True
        json_encoders = {
            datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S") if v else None
        }
