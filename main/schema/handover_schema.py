"""
인수인계 관련 스키마 - snake_case 사용
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class HandoverBase(BaseModel):
    """인수인계 기본 스키마"""

    title: str = Field(..., description="제목")
    content: str = Field(..., description="내용")
    is_notice: bool = Field(False, description="공지사항 여부")
    department: str = Field("ALL", description="부서(CS/HES/LENOVO/ALL)")

    class Config:
        populate_by_name = True


class HandoverCreate(HandoverBase):
    """인수인계 생성 스키마"""

    status: Optional[str] = Field("OPEN", description="상태(OPEN/CLOSE)")

    pass


class HandoverUpdate(HandoverBase):
    """인수인계 수정 스키마"""

    title: Optional[str] = Field(None, description="제목")
    content: Optional[str] = Field(None, description="내용")
    is_notice: Optional[bool] = Field(None, description="공지사항 여부")
    department: Optional[str] = Field(None, description="부서(CS/HES/LENOVO/ALL)")
    status: Optional[str] = Field(None, description="상태(OPEN/CLOSE)")

    class Config:
        populate_by_name = True


class HandoverResponse(HandoverBase):
    """인수인계 응답 스키마"""

    handover_id: int = Field(..., description="인수인계 ID")
    create_by: str = Field(..., description="작성자 ID")
    update_by: str = Field(..., description="수정자 ID")
    update_at: datetime = Field(..., description="수정 일시")
    create_time: datetime = Field(..., description="생성 일시")
    status: str = Field(..., description="상태(OPEN/CLOSE)")
    version: int = Field(..., description="데이터 버전")

    class Config:
        from_attributes = True
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.strftime("%Y-%m-%dT%H:%M") if v else None
        }


class HandoverDeleteResponse(BaseModel):
    """인수인계 삭제 응답 스키마"""

    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="메시지")


class HandoverListItem(BaseModel):
    """인수인계 목록 항목 스키마 (필요 최소 필드)"""

    handover_id: int
    title: str
    update_at: datetime
    update_by: str
    is_notice: bool
    department: str
    create_time: datetime
    status: str
    version: int

    class Config:
        from_attributes = True
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.strftime("%Y-%m-%dT%H:%M") if v else None
        }


class HandoverListResponse(BaseModel):
    """인수인계 목록 응답 스키마"""

    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="메시지")
    data: List[Dict[str, Any]]

    class Config:
        populate_by_name = True
