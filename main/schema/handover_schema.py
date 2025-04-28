"""
인수인계 관련 스키마
"""

from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

class HandoverBase(BaseModel):
    """인수인계 기본 스키마"""
    title: str = Field(..., description="제목")
    content: str = Field(..., description="내용")
    is_notice: bool = Field(False, description="공지사항 여부")

class HandoverCreate(HandoverBase):
    """인수인계 생성 스키마"""
    pass

class HandoverUpdate(HandoverBase):
    """인수인계 수정 스키마"""
    pass

class HandoverResponse(HandoverBase):
    """인수인계 응답 스키마"""
    id: int = Field(..., description="인수인계 ID", alias="handover_id")
    writer_id: str = Field(..., description="작성자 ID", alias="update_by")
    created_at: datetime = Field(..., description="생성 일시", alias="create_at")
    updated_at: Optional[datetime] = Field(None, description="수정 일시", alias="update_at")

    class Config:
        from_attributes = True
        populate_by_name = True
        allow_population_by_field_name = True
        
class HandoverDeleteResponse(BaseModel):
    """인수인계 삭제 응답 스키마"""
    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="메시지")

class HandoverListResponse(BaseModel):
    """인수인계 목록 응답 스키마"""
    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="메시지")
    data: List[HandoverResponse] = Field(..., description="인수인계 목록")
    pagination: dict = Field(..., description="페이지네이션 정보")
