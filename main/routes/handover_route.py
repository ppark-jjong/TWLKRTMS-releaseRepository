"""
인수인계 관련 라우터
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, Response, Query, Path, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from main.core.templating import templates
from main.utils.database import get_db
from main.utils.security import get_current_user, get_admin_user
from main.utils.lock import check_lock_status
from main.utils.logger import logger
from main.schema.handover_schema import (
    HandoverCreate,
    HandoverUpdate,
    HandoverResponse
)
from main.service.handover_service import (
    get_handover_list,
    get_notice_list,
    get_handover_by_id,
    create_handover,
    update_handover,
    delete_handover
)

# 라우터 생성
router = APIRouter()

@router.get("")
async def handover_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100)
):
    """
    인수인계 페이지 렌더링
    """
    try:
        # 공지사항 목록 조회 (is_notice=True)
        notices = get_notice_list(
            db=db,
            page=1,  # 공지사항은 1페이지만 표시
            page_size=5  # 최근 5개만 표시
        )
        
        # 인수인계 목록 조회 (is_notice=False)
        handovers, pagination = get_handover_list(
            db=db,
            page=page,
            page_size=limit,
            search_term=None  # 검색 기능 제거
        )
        
        logger.info(f"인수인계 페이지 접근: 공지사항 {len(notices)}개, 인수인계 {len(handovers)}개")
        
        # 템플릿 렌더링
        return templates.TemplateResponse(
            "handover.html",
            {
                "request": request,
                "user": current_user,
                "notices": notices,
                "handovers": handovers,
                "current_page": page,
                "total_pages": pagination["total_pages"]
            }
        )
    except Exception as e:
        logger.error(f"인수인계 페이지 렌더링 중 오류 발생: {str(e)}", exc_info=True)
        # 오류 발생 시 에러 페이지 렌더링
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error_message": "인수인계 목록을 불러오는 중 오류가 발생했습니다.",
                "error_detail": str(e) if current_user.get("user_role") == "ADMIN" else "",
            },
            status_code=500
        )

@router.get("/handovers/{handover_id}")
async def get_handover_detail(
    request: Request,
    handover_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    인수인계 상세 조회 API
    """
    try:
        handover = get_handover_by_id(db, handover_id)
        
        if not handover:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"success": False, "message": "인수인계를 찾을 수 없습니다."}
            )
            
        # 응답 데이터 구성
        handover_data = {
            "id": handover.handover_id,
            "title": handover.title,
            "content": handover.content,
            "is_notice": handover.is_notice,
            "writer_id": handover.update_by,
            "updated_at": handover.update_at.strftime("%Y-%m-%d %H:%M") if handover.update_at else None,
            # 편집 권한 확인 (작성자 또는 관리자만 가능)
            "can_edit": current_user.get("user_id") == handover.update_by or current_user.get("user_role") == "ADMIN",
            # 삭제 권한 확인 (관리자만 가능)
            "can_delete": current_user.get("user_role") == "ADMIN"
        }
        
        return {"success": True, "data": handover_data}
    except Exception as e:
        logger.error(f"인수인계 상세 조회 중 오류 발생: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "인수인계 상세 조회 중 오류가 발생했습니다."}
        )

@router.post("/handovers")
async def create_handover_item(
    request: Request,
    handover_data: HandoverCreate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    인수인계 생성 API
    """
    try:
        # 공지사항 등록 시 관리자 권한 확인
        if handover_data.is_notice and current_user.get("user_role") != "ADMIN":
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"success": False, "message": "공지사항 등록 권한이 없습니다."}
            )
            
        # 인수인계 생성
        new_handover = create_handover(
            db=db, 
            title=handover_data.title,
            content=handover_data.content,
            is_notice=handover_data.is_notice,
            writer_id=current_user.get("user_id"),
            writer_name=current_user.get("user_name", current_user.get("user_id"))
        )
        
        return {
            "success": True, 
            "message": "인수인계가 성공적으로 등록되었습니다.",
            "id": new_handover.handover_id
        }
    except Exception as e:
        logger.error(f"인수인계 생성 중 오류 발생: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "인수인계 등록 중 오류가 발생했습니다."}
        )

@router.put("/handovers/{handover_id}")
async def update_handover_item(
    request: Request,
    handover_id: int = Path(..., ge=1),
    handover_data: HandoverUpdate = None,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    인수인계 수정 API
    """
    try:
        # 기존 인수인계 조회
        handover = get_handover_by_id(db, handover_id)
        
        if not handover:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"success": False, "message": "인수인계를 찾을 수 없습니다."}
            )
            
        # 수정 권한 확인 (작성자 또는 관리자만 가능)
        if current_user.get("user_id") != handover.update_by and current_user.get("user_role") != "ADMIN":
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"success": False, "message": "인수인계 수정 권한이 없습니다."}
            )
            
        # 공지사항 설정 시 관리자 권한 확인
        if handover_data.is_notice and current_user.get("user_role") != "ADMIN":
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"success": False, "message": "공지사항 설정 권한이 없습니다."}
            )
            
        # 인수인계 수정
        updated_handover = update_handover(
            db=db,
            handover_id=handover_id,
            title=handover_data.title,
            content=handover_data.content,
            is_notice=handover_data.is_notice,
            updated_by=current_user.get("user_id")
        )
        
        return {
            "success": True, 
            "message": "인수인계가 성공적으로 수정되었습니다.",
            "id": updated_handover.handover_id
        }
    except Exception as e:
        logger.error(f"인수인계 수정 중 오류 발생: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "인수인계 수정 중 오류가 발생했습니다."}
        )

@router.get("/lock/{handover_id}")
async def check_handover_lock(
    request: Request,
    handover_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    인수인계 락 상태 확인 API
    """
    try:
        # 락 상태 확인
        lock_status = check_lock_status(
            db, "handover", handover_id, current_user.get("user_id")
        )
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

@router.delete("/handovers/{handover_id}")
async def delete_handover_item(
    request: Request,
    handover_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),  # 일반 사용자도 삭제 가능
):
    """
    인수인계 삭제 API (본인 작성 또는 관리자)
    """
    try:
        # 기존 인수인계 조회
        handover = get_handover_by_id(db, handover_id)
        
        if not handover:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"success": False, "message": "인수인계를 찾을 수 없습니다."}
            )
            
        # 삭제 권한 확인 (작성자 또는 관리자만 가능)
        if current_user.get("user_id") != handover.update_by and current_user.get("user_role") != "ADMIN":
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"success": False, "message": "인수인계 삭제 권한이 없습니다."}
            )
        
        # 인수인계 삭제
        success = delete_handover(db, handover_id)
        
        if not success:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"success": False, "message": "인수인계 삭제 중 오류가 발생했습니다."}
            )
            
        return {"success": True, "message": "인수인계가 성공적으로 삭제되었습니다."}
    except Exception as e:
        logger.error(f"인수인계 삭제 중 오류 발생: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "message": "인수인계 삭제 중 오류가 발생했습니다."}
        )
