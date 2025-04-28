"""
사용자 관리 관련 스키마 - 필요한 경우를 위한 최소한의 구조체
"""

from pydantic import BaseModel, Field

class UserCreateForm(BaseModel):
    """폼 데이터 유효성 검사용 스키마"""
    user_id: str = Field(..., description="사용자 ID")
    user_password: str = Field(..., description="비밀번호")
    user_role: str = Field(..., description="권한", example="ADMIN 또는 USER")
    user_department: str = Field(..., description="부서")
