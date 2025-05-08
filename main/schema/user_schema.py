"""
사용자 관리 관련 스키마 - 필요한 경우를 위한 최소한의 구조체
"""

from pydantic import BaseModel, Field
from typing import Optional


class UserCreateForm(BaseModel):
    """폼 데이터 유효성 검사용 스키마"""

    user_id: str = Field(..., description="사용자 ID", alias="userId")
    user_name: str = Field(..., description="사용자 이름", alias="userName")
    user_password: str = Field(..., description="비밀번호", alias="userPassword")
    user_role: str = Field(
        ..., description="권한", example="ADMIN 또는 USER", alias="userRole"
    )
    user_department: str = Field(..., description="부서", alias="userDepartment")

    class Config:
        """스키마 설정"""

        by_alias = True
        populate_by_name = True


class UserResponse(BaseModel):
    """사용자 정보 응답 스키마"""

    user_id: str = Field(..., description="사용자 ID", alias="userId")
    user_name: str = Field(..., description="사용자 이름", alias="userName")
    user_role: str = Field(..., description="사용자 역할", alias="userRole")
    user_department: str = Field(..., description="사용자 부서", alias="userDepartment")

    class Config:
        """스키마 설정"""

        by_alias = True
        populate_by_name = True
        from_attributes = True
