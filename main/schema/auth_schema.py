"""
인증 관련 스키마 정의
"""

from typing import Optional
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """
    로그인 요청 스키마
    """

    user_id: str = Field(..., description="사용자 ID")
    password: str = Field(..., description="비밀번호")

    class Config:
        """스키마 설정"""

        # 외부 표현(JSON)과 내부 모델 필드 간 1:1 매핑을 위한 설정
        by_alias = True
        # 필드 이름으로 직접 속성에 접근 가능하도록 설정
        populate_by_name = True
        # 스키마 예시
        json_schema_extra = {"example": {"user_id": "user1", "password": "password123"}}


class LoginResponse(BaseModel):
    """
    로그인 응답 스키마
    """

    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="메시지")
    user_id: Optional[str] = Field(None, description="사용자 ID", alias="userId")
    user_role: Optional[str] = Field(None, description="사용자 역할", alias="userRole")
    user_department: Optional[str] = Field(
        None, description="사용자 부서", alias="userDepartment"
    )

    class Config:
        """스키마 설정"""

        by_alias = True
        populate_by_name = True


class LogoutResponse(BaseModel):
    """
    로그아웃 응답 스키마
    """

    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="메시지")

    class Config:
        """스키마 설정"""

        by_alias = True
        populate_by_name = True


class UserResponse(BaseModel):
    """
    사용자 정보 응답 스키마
    """

    user_id: str = Field(..., description="사용자 ID", alias="userId")
    user_role: str = Field(..., description="사용자 역할", alias="userRole")
    user_department: str = Field(..., description="사용자 부서", alias="userDepartment")

    class Config:
        """스키마 설정"""

        by_alias = True
        populate_by_name = True
