"""
사용자 관리 관련 라우터 - 극도로 단순화
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, Request, Query, Form, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from main.core.templating import templates
from main.utils.database import get_db
from main.utils.security import get_admin_user, hash_password  # 관리자 전용 페이지
from main.utils.logger import logger
from main.service.user_service import (
    get_user_list,
    create_user,
    update_user_role,
    delete_user
)

# 라우터 생성 (관리자 전용)
router = APIRouter()

@router.get("")
async def users_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_admin_user),  # 관리자만 접근 가능
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    role: str = Query(None),
    search_type: str = Query(None),
    search_value: str = Query(None)
):
    """
    사용자 관리 페이지 렌더링 (관리자 전용)
    """
    try:
        # 필터 정보 생성
        filter_data = {
            "role": role or "all",
            "search_type": search_type or "user_id",
            "search_value": search_value or ""
        }
        
        # 사용자 목록 조회
        users, pagination = get_user_list(
            db=db,
            page=page,
            page_size=limit,
            role=role,
            search_type=search_type,
            search_value=search_value
        )
        
        logger.info(f"사용자 관리 페이지 접근: 사용자 {len(users)}개 조회됨")
        
        # 템플릿 렌더링
        return templates.TemplateResponse(
            "users.html",
            {
                "request": request,
                "user": current_user,
                "users": users,
                "current_page": page,
                "total_pages": pagination["total_pages"],
                "filter": filter_data  # 필터 정보 추가
            }
        )
    except Exception as e:
        logger.error(f"사용자 관리 페이지 렌더링 중 오류 발생: {str(e)}", exc_info=True)
        # 오류 발생 시 에러 페이지 렌더링
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error_message": "사용자 목록을 불러오는 중 오류가 발생했습니다."
            },
            status_code=500
        )

@router.post("/create")
async def create_new_user(
    user_id: str = Form(...),
    user_password: str = Form(...),
    user_role: str = Form(...),
    user_department: str = Form(...),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_admin_user)  # 관리자만 접근 가능
):
    """
    사용자 생성 API (관리자 전용)
    """
    try:
        # 비밀번호 해싱
        hashed_password = hash_password(user_password)
        
        # 사용자 생성
        create_user(
            db=db,
            user_id=user_id,
            user_password=hashed_password,
            user_role=user_role,
            user_department=user_department
        )
        
        return {"success": True, "message": "사용자가 성공적으로 생성되었습니다."}
    except Exception as e:
        logger.error(f"사용자 생성 중 오류 발생: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "사용자 생성 중 오류가 발생했습니다."}
        )

@router.post("/role")
async def change_user_role(
    user_id: str = Form(...),
    user_role: str = Form(...),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_admin_user)  # 관리자만 접근 가능
):
    """
    사용자 권한 변경 API (관리자 전용)
    """
    try:
        # 사용자 권한 변경
        update_user_role(
            db=db,
            user_id=user_id,
            user_role=user_role
        )
        
        return {"success": True, "message": "사용자 권한이 성공적으로 변경되었습니다."}
    except Exception as e:
        logger.error(f"사용자 권한 변경 중 오류 발생: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "사용자 권한 변경 중 오류가 발생했습니다."}
        )

@router.post("/delete")
async def delete_user_account(
    user_id: str = Form(...),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_admin_user)  # 관리자만 접근 가능
):
    """
    사용자 삭제 API (관리자 전용)
    """
    try:
        # 사용자 삭제
        delete_user(
            db=db,
            user_id=user_id
        )
        
        return {"success": True, "message": "사용자가 성공적으로 삭제되었습니다."}
    except Exception as e:
        logger.error(f"사용자 삭제 중 오류 발생: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "사용자 삭제 중 오류가 발생했습니다."}
        )
