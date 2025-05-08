"""
대시보드(주문) 관련 스키마 정의 - snake_case 사용
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator


class DashboardCreate(BaseModel):
    """주문 생성 요청 스키마"""

    order_no: str = Field(..., description="주문번호")
    type: str = Field(..., description="유형(DELIVERY/RETURN)")
    department: str = Field(..., description="부서(CS/HES/LENOVO)")
    warehouse: str = Field(..., description="창고(SEOUL/BUSAN/GWANGJU/DAEJEON)")
    sla: str = Field(..., description="SLA")
    eta: datetime = Field(..., description="ETA(도착 예정 시간)")
    postal_code: str = Field(..., description="우편번호")
    address: str = Field(..., description="주소")
    customer: str = Field(..., description="고객명")
    contact: Optional[str] = Field(None, description="연락처")
    remark: Optional[str] = Field(None, description="비고")
    driver_name: Optional[str] = Field(None, description="기사 이름")
    driver_contact: Optional[str] = Field(None, description="기사 연락처")
    delivery_company: Optional[str] = Field(None, description="배송사")

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

        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.strftime("%Y-%m-%dT%H:%M") if v else None
        }


class DashboardUpdate(BaseModel):
    """주문 수정 요청 스키마 (모든 필드 선택적)"""

    order_no: Optional[str] = Field(None, description="주문번호")
    type: Optional[str] = Field(None, description="유형(DELIVERY/RETURN)")
    department: Optional[str] = Field(None, description="부서(CS/HES/LENOVO)")
    warehouse: Optional[str] = Field(
        None, description="창고(SEOUL/BUSAN/GWANGJU/DAEJEON)"
    )
    sla: Optional[str] = Field(None, description="SLA")
    eta: Optional[datetime] = Field(None, description="ETA(도착 예정 시간)")
    postal_code: Optional[str] = Field(None, description="우편번호")
    address: Optional[str] = Field(None, description="주소")
    customer: Optional[str] = Field(None, description="고객명")
    contact: Optional[str] = Field(None, description="연락처")
    remark: Optional[str] = Field(None, description="비고")
    status: Optional[str] = Field(
        None, description="상태(WAITING/IN_PROGRESS/COMPLETE/ISSUE/CANCEL)"
    )
    driver_name: Optional[str] = Field(None, description="기사 이름")
    driver_contact: Optional[str] = Field(None, description="기사 연락처")
    delivery_company: Optional[str] = Field(None, description="배송사")

    @validator("postal_code")
    def validate_postal_code(cls, v):
        """우편번호 검증 (수정 시에도 동일 적용)"""
        if v:
            if len(v) == 4:
                v = "0" + v
            if len(v) != 5:
                raise ValueError("우편번호는 5자리여야 합니다.")
        return v

    class Config:
        """스키마 설정"""

        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.strftime("%Y-%m-%dT%H:%M") if v else None
        }


class DashboardResponse(BaseModel):
    """주문 상세 응답 스키마"""

    dashboard_id: int = Field(..., description="대시보드 ID")
    order_no: str = Field(..., description="주문번호")
    type: str = Field(..., description="유형(DELIVERY/RETURN)")
    department: str = Field(..., description="부서(CS/HES/LENOVO)")
    warehouse: str = Field(..., description="창고(SEOUL/BUSAN/GWANGJU/DAEJEON)")
    sla: str = Field(..., description="SLA")
    region: Optional[str] = Field(None, description="지역(시 구 동) - DB 생성")
    eta: datetime = Field(..., description="ETA(도착 예정 시간)")
    postal_code: str = Field(..., description="우편번호")
    customer: str = Field(..., description="고객명")
    status: str = Field(
        ..., description="상태(WAITING/IN_PROGRESS/COMPLETE/ISSUE/CANCEL)"
    )
    create_time: datetime = Field(..., description="생성 시간")
    depart_time: Optional[datetime] = Field(None, description="출발 시간")
    complete_time: Optional[datetime] = Field(None, description="완료 시간")
    city: Optional[str] = Field(None, description="시")
    county: Optional[str] = Field(None, description="구")
    district: Optional[str] = Field(None, description="동")
    distance: Optional[int] = Field(None, description="거리(km)")
    duration_time: Optional[int] = Field(None, description="소요 시간(분)")
    driver_name: Optional[str] = Field(None, description="기사 이름")
    driver_contact: Optional[str] = Field(None, description="기사 연락처")
    delivery_company: Optional[str] = Field(None, description="배송사")
    update_by: Optional[str] = Field(None, description="마지막 업데이트 사용자")
    remark: Optional[str] = Field(None, description="비고")
    update_at: Optional[datetime] = Field(None, description="마지막 업데이트 시간")
    version: int = Field(..., description="데이터 버전")

    class Config:
        """스키마 설정"""

        populate_by_name = True
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.strftime("%Y-%m-%dT%H:%M") if v else None
        }


class DashboardListItem(BaseModel):
    """주문 목록 항목 스키마 (최종 요구사항 반영)"""

    dashboard_id: int
    create_time: Optional[datetime]
    order_no: str
    type: str
    department: str
    warehouse: str
    sla: str
    eta: Optional[datetime]
    status: str
    region: Optional[str]
    depart_time: Optional[datetime]
    complete_time: Optional[datetime]
    customer: str
    delivery_company: Optional[str]
    driver_name: Optional[str]

    class Config:
        """스키마 설정"""

        populate_by_name = True
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.strftime("%Y-%m-%dT%H:%M") if v else None
        }


class DashboardListResponse(BaseModel):
    """주문 목록 응답 스키마"""

    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="메시지")
    data: List[Dict[str, Any]] = Field(..., description="주문 목록")

    class Config:
        """스키마 설정"""

        populate_by_name = True


class DashboardDeleteRequest(BaseModel):
    """주문 삭제 요청 스키마"""

    dashboard_ids: List[int] = Field(
        ..., description="삭제할 주문 ID 목록", alias="ids"
    )

    class Config:
        """스키마 설정"""

        populate_by_name = True
