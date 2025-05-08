"""
사용자 관리 관련 라우터 - 극도로 단순화
"""

from typing import Dict, Any, Optional
from fastapi import (
    APIRouter,
    Depends,
    Request,
    Query,
    Form,
    status,
    Path,
    HTTPException,
)
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
import logging

from main.core.templating import templates
from main.utils.database import get_db
from main.utils.security import get_admin_user, hash_password  # 관리자 전용 페이지
from main.service.user_service import (
    get_user_list,
    create_user,
    delete_user,
)

logger = logging.getLogger(__name__)

# 라우터 생성 (페이지 / API 분리 및 관리자 전용)
page_router = APIRouter(prefix="/admin/users", dependencies=[Depends(get_admin_user)])
api_router = APIRouter(
    prefix="/api/admin/users", dependencies=[Depends(get_admin_user)]
)


# === 페이지 렌더링 라우트 ===
@page_router.get("", include_in_schema=False)
async def users_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_admin_user),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    role: str = Query(None),
    search_type: str = Query(None),
    search_value: str = Query(None),
):
    """설명서 4.1: 사용자 관리 페이지 렌더링 (관리자 전용)"""
    logging.info(
        f"users_page 시작: user={current_user.get('user_id')}, 매개변수={{'page': {page}, 'limit': {limit}, 'role': {role}, 'search_type': {search_type}, 'search_value': {search_value}}}"
    )

    try:
        # 필터 정보 생성
        filter_data = {
            "role": role or "all",
            "search_type": search_type or "user_id",
            "search_value": search_value or "",
        }

        # 중간 포인트 로깅 - DB 쿼리 전
        # logging.debug(f"DB 쿼리 시작: 사용자 목록 조회 (필터: {filter_data})") # 프로덕션에서 불필요한 로그 제거

        # 사용자 목록 조회
        users, pagination = get_user_list(
            db=db,
            page=page,
            page_size=limit,
            role=role,
            search_type=search_type,
            search_value=search_value,
        )

        # 중간 포인트 로깅 - DB 쿼리 결과
        logging.info(f"사용자 관리 페이지 접근: 사용자 {len(users)}개 조회됨")

        # 함수 종료 로깅
        logging.info(f"users_page 완료: 결과=성공, 데이터={len(users)}건")

        # 템플릿 렌더링
        return templates.TemplateResponse(
            "users.html",
            {
                "request": request,
                "current_user": current_user,
                "users": users,
                "current_page": page,
                "total_pages": pagination["total_pages"],
                "filter": filter_data,
            },
        )
    except Exception as e:
        logging.error(
            f"사용자 관리 페이지 렌더링 중 오류 발생: {str(e)}", exc_info=True
        )

        # 함수 종료 로깅 (오류 발생)
        logging.info(f"users_page 완료: 결과=오류, 메시지={str(e)[:100]}")

        # 오류 발생 시 에러 페이지 렌더링
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error_message": "사용자 목록을 불러오는 중 오류가 발생했습니다.",
                "current_user": current_user,
            },
            status_code=500,
        )


# === API 엔드포인트 라우트 ===


@api_router.post("", status_code=status.HTTP_302_FOUND)
async def create_new_user(
    db: Session = Depends(get_db),
    current_admin: Dict[str, Any] = Depends(get_admin_user),
    user_id: str = Form(...),
    user_name: str = Form(...),
    user_password: str = Form(...),
    user_role: str = Form(...),
    user_department: Optional[str] = Form(None),
):
    """설명서 4.3: 사용자 생성 처리 (Form 방식)"""
    logging.info(
        f"사용자 생성 API 호출: userId={user_id}, role={user_role}, by={current_admin.get('user_id')}"
    )
    try:
        hashed_password = hash_password(user_password)
        create_user(
            db=db,
            user_id=user_id,
            user_name=user_name,
            user_password=hashed_password,
            user_role=user_role,
            user_department=user_department,
        )
        logging.info(f"사용자 생성 성공: userId={user_id}")
        return RedirectResponse(
            url="/admin/users", status_code=status.HTTP_303_SEE_OTHER
        )
    except Exception as e:
        logging.error(f"사용자 생성 중 오류 발생: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"사용자 생성 중 오류가 발생했습니다: {str(e)}"
        )


@api_router.post("/{user_id_to_delete}/delete", status_code=status.HTTP_302_FOUND)
async def delete_user_account(
    user_id_to_delete: str = Path(..., description="삭제할 사용자 ID"),
    db: Session = Depends(get_db),
    current_admin: Dict[str, Any] = Depends(get_admin_user),
):
    """설명서 4.4: 사용자 삭제 처리"""
    logging.info(
        f"사용자 삭제 API 호출: targetUserId={user_id_to_delete}, by={current_admin.get('user_id')}"
    )

    if user_id_to_delete == current_admin.get("user_id"):
        logging.warning(f"자기 자신 삭제 시도: user={user_id_to_delete}")
        return RedirectResponse(
            url="/admin/users?error=자기 자신은 삭제할 수 없습니다.",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    try:
        delete_user(db=db, user_id=user_id_to_delete)
        logging.info(f"사용자 삭제 성공: targetUserId={user_id_to_delete}")
        return RedirectResponse(
            url="/admin/users?success=사용자가 삭제되었습니다.",
            status_code=status.HTTP_303_SEE_OTHER,
        )
    except Exception as e:
        logging.error(f"사용자 삭제 중 오류 발생: {str(e)}", exc_info=True)
        return RedirectResponse(
            url=f"/admin/users?error=사용자 삭제 중 오류 발생: {str(e)}",
            status_code=status.HTTP_303_SEE_OTHER,
        )
