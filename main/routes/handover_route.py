"""
인수인계 관련 라우터 - 리팩토링 버전
"""

from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime
from urllib.parse import quote
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Query,
    Path,
    status,
    Form,
)
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
import logging
import json

from main.core.templating import templates
from main.utils.database import get_db, db_transaction
from main.utils.security import get_current_user, get_admin_user
from main.models.user_model import User

# 서비스 함수 이름 변경에 따른 임포트 조정
from main.service.handover_service import (
    get_handover_list_paginated,
    get_handover_list_all,
    get_notice_list,
    get_handover_by_id,
    create_handover,
    update_handover,
    delete_handover,
    _handover_to_dict,  # 내부 변환 함수 임포트
)
from main.utils.json_util import CustomJSONEncoder

# 스키마 임포트 추가
from main.schema.handover_schema import (
    HandoverListResponse,
    HandoverCreate,
    HandoverResponse,
)

logger = logging.getLogger(__name__)

# 라우터 생성 (페이지 / API 분리)
page_router = APIRouter(prefix="/handover", dependencies=[Depends(get_current_user)])
api_router = APIRouter(prefix="/api/handover", dependencies=[Depends(get_current_user)])


# === 유틸리티 함수 ===
def handle_redirect_error(
    error: Union[Exception, str],
    redirect_url: str,
    status_code: int = status.HTTP_303_SEE_OTHER,
) -> RedirectResponse:
    """오류를 처리하고 리다이렉션 응답을 생성하는 헬퍼 함수"""
    if isinstance(error, Exception):
        error_message = getattr(error, "detail", str(error))
    else:
        error_message = error

    # 메시지 인코딩 및 리다이렉션
    encoded_message = quote(error_message)
    return RedirectResponse(
        f"{redirect_url}?error={encoded_message}", status_code=status_code
    )


def handle_redirect_success(
    message: str, redirect_url: str, status_code: int = status.HTTP_303_SEE_OTHER
) -> RedirectResponse:
    """성공 메시지를 처리하고 리다이렉션 응답을 생성하는 헬퍼 함수"""
    encoded_message = quote(message)
    return RedirectResponse(
        f"{redirect_url}?success={encoded_message}", status_code=status_code
    )


# === 페이지 렌더링 라우트 ===


@page_router.get("/new", name="handover_create_page")
async def handover_create_page(
    request: Request, current_user: Dict[str, Any] = Depends(get_current_user)
):
    logger.info(f"인수인계 생성 페이지 로드: user={current_user.get('user_id')}")
    can_create_notice = current_user.get("user_role") == "ADMIN"
    context = {
        "request": request,
        "current_user": current_user,
        "can_create_notice": can_create_notice,
        "handover": None,
        "is_edit": False,
    }
    return templates.TemplateResponse("handover_form.html", context)


@page_router.get("/", name="handover_list_page")
async def handover_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    logger.info(f"인수인계 목록 페이지 로드: user={current_user.get('user_id')}")
    error_message = request.query_params.get("error")
    success_message = request.query_params.get("success")

    try:
        context = {
            "request": request,
            "current_user": current_user,
            "error_message": error_message,
            "success_message": success_message,
        }
        return templates.TemplateResponse("handover.html", context)

    except Exception as e:
        logger.error(f"인수인계 페이지 로드 오류: {e}", exc_info=True)
        context = {
            "request": request,
            "error_message": "페이지 로드 중 오류 발생",
            "current_user": current_user,
        }
        return templates.TemplateResponse("error.html", context, status_code=500)


@page_router.get("/{handover_id}", name="handover_detail_page")
async def get_handover_detail_page(
    request: Request,
    handover_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    logger.info(
        f"인수인계 상세 페이지 로드: id={handover_id}, user={current_user.get('user_id')}"
    )
    error_message = request.query_params.get("error")
    success_message = request.query_params.get("success")

    try:
        handover_model = get_handover_by_id(db, handover_id)
        if not handover_model:
            raise HTTPException(status_code=404, detail="인수인계를 찾을 수 없습니다.")

        handover_data = _handover_to_dict(handover_model)

        # 작성자 본인 또는 ADMIN만 수정 가능하도록 editable 속성 설정
        is_owner = handover_model.create_by == current_user.get("user_id")
        is_admin = current_user.get("user_role") == "ADMIN"
        handover_data["editable"] = is_owner or is_admin

        # 라벨 정보 추가
        type_labels = {"NOTICE": "공지", "HANDOVER": "인수인계"}
        handover_data["type_label"] = type_labels.get(
            "NOTICE" if handover_data["is_notice"] else "HANDOVER"
        )

        context = {
            "request": request,
            "handover": handover_data,
            "current_user": current_user,
            "error_message": error_message,
            "success_message": success_message,
        }
        return templates.TemplateResponse("handover_detail.html", context)

    except HTTPException as http_exc:
        logger.warning(
            f"인수인계 상세 로드 오류 (HTTP): {http_exc.status_code}, {http_exc.detail}"
        )
        error_message_redirect = quote(http_exc.detail)
        return RedirectResponse(
            f"/handover?error={error_message_redirect}",
            status_code=status.HTTP_303_SEE_OTHER,
        )
    except Exception as e:
        logger.error(f"인수인계 상세 페이지 로드 오류: {e}", exc_info=True)
        error_message_redirect = quote("상세 정보 로드 중 오류 발생")
        return RedirectResponse(
            f"/handover?error={error_message_redirect}",
            status_code=status.HTTP_303_SEE_OTHER,
        )


@page_router.get("/{handover_id}/edit", name="handover_edit_page")
async def handover_edit_page(
    request: Request,
    handover_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    user_id = current_user.get("user_id")
    logger.info(f"인수인계 수정 페이지 요청: id={handover_id}, user={user_id}")
    detail_url = f"/handover/{handover_id}"

    try:
        # 인수인계 정보 로드
        handover_model = get_handover_by_id(db, handover_id)
        if not handover_model:
            logger.warning(f"인수인계 수정 페이지 로드 실패: 인수인계를 찾을 수 없음")
            error_message = quote("수정할 인수인계를 찾을 수 없습니다.")
            return RedirectResponse(
                f"/handover?error={error_message}",
                status_code=status.HTTP_303_SEE_OTHER,
            )

        # 작성자 또는 관리자만 수정 가능
        if (handover_model.create_by != user_id) and (
            current_user.get("user_role") != "ADMIN"
        ):
            logger.warning(f"인수인계 수정 권한 없음: user={user_id}, id={handover_id}")
            error_message = quote("이 인수인계를 수정할 권한이 없습니다.")
            return RedirectResponse(
                f"{detail_url}?error={error_message}",
                status_code=status.HTTP_303_SEE_OTHER,
            )

        # 인수인계 데이터
        handover_data = _handover_to_dict(handover_model)
        can_make_notice = current_user.get("user_role") == "ADMIN"

        context = {
            "request": request,
            "handover": handover_data,
            "current_user": current_user,
            "is_edit": True,
            "can_create_notice": can_make_notice,
            "error_message": request.query_params.get("error"),
            "success_message": request.query_params.get("success"),
            "version": handover_model.version,
        }

        return templates.TemplateResponse("handover_form.html", context)

    except HTTPException as http_exc:
        logger.warning(
            f"인수인계 수정 페이지 HTTP 오류: {http_exc.status_code}, {http_exc.detail}"
        )
        error_message = quote(http_exc.detail)
        return RedirectResponse(
            f"{detail_url}?error={error_message}",
            status_code=status.HTTP_303_SEE_OTHER,
        )
    except Exception as e:
        logger.error(f"인수인계 수정 페이지 처리 중 예외 발생: {str(e)}", exc_info=True)
        error_message = quote("페이지 로드 중 오류가 발생했습니다")
        return RedirectResponse(
            f"{detail_url}?error={error_message}",
            status_code=status.HTTP_303_SEE_OTHER,
        )


# === API 엔드포인트 라우트 ===


@api_router.get("/list", response_model=HandoverListResponse)
async def get_handover_list_api(
    db: Session = Depends(get_db),
    is_notice: Optional[bool] = Query(
        None,
        description="null: 전체, True: 공지, False: 인수인계",
    ),
    department: Optional[str] = Query(
        None, description="부서 필터링 (CS, HES, LENOVO, ALL)"
    ),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    logger.info(
        f"인수인계 목록 API 호출: notice={is_notice}, department={department}, user={current_user.get('user_id')}"
    )
    try:
        all_items = get_handover_list_all(
            db=db, is_notice=is_notice, department=department
        )
        # HandoverListResponse 스키마에 맞게 반환
        return HandoverListResponse(
            success=True, message="목록 조회 성공", data=all_items
        )
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"인수인계 목록 API 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="목록 조회 중 오류 발생")


@api_router.post("/create", response_model=Dict[str, Any])
@db_transaction
async def create_handover_api(
    request: Request,
    title: str = Form(...),
    content: str = Form(...),
    is_notice: str = Form(default="false"),
    department: str = Form(default="CS"),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    인수인계 생성 API

    - Form 파라미터:
      - title(str): 제목
      - content(str): 내용
      - is_notice(str): 공지사항 여부 (문자열 "true"/"false")
      - department(str): 부서 (CS/HES/LENOVO/ALL)
    """
    user_id = current_user.get("user_id")
    user_role = current_user.get("user_role")
    logger.info(f"인수인계 생성 API 호출: user={user_id}, role={user_role}")

    try:
        # 공지사항 생성 권한 확인 (관리자만 가능)
        is_notice_bool = is_notice.lower() == "true"
        if is_notice_bool and user_role != "ADMIN":
            logger.warning(f"공지사항 생성 권한 없음: user={user_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="관리자만 공지사항을 생성할 수 있습니다.",
            )

        # 부서 유효성 검증
        if department not in ["CS", "HES", "LENOVO", "ALL"]:
            logger.warning(f"유효하지 않은 부서: {department}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="유효하지 않은 부서입니다.",
            )

        # 인수인계 생성
        new_handover = create_handover(
            db=db,
            title=title,
            content=content,
            is_notice=is_notice_bool,
            writer_id=user_id,
            department=department,
        )

        logger.info(
            f"인수인계 생성 성공: ID={new_handover.handover_id}, 공지사항={is_notice_bool}"
        )

        success_message = quote("인수인계가 성공적으로 생성되었습니다.")
        return RedirectResponse(
            f"/handover/{new_handover.handover_id}?success={success_message}",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    except HTTPException as http_exc:
        logger.warning(f"인수인계 생성 API 오류: {http_exc.detail}")
        error_message = quote(http_exc.detail)
        return RedirectResponse(
            f"/handover/new?error={error_message}",
            status_code=status.HTTP_303_SEE_OTHER,
        )
    except Exception as e:
        logger.error(f"인수인계 생성 중 예외 발생: {e}", exc_info=True)
        error_message = quote("인수인계 생성 중 오류가 발생했습니다.")
        return RedirectResponse(
            f"/handover/new?error={error_message}",
            status_code=status.HTTP_303_SEE_OTHER,
        )


@api_router.post("/{handover_id}/update", response_model=Dict[str, Any])
@db_transaction
async def update_handover_api(
    request: Request,
    handover_id: int = Path(..., ge=1),
    title: str = Form(...),
    content: str = Form(...),
    is_notice: str = Form(default="false"),
    department: str = Form(default="CS"),
    status_val: Optional[str] = Form(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
    version: int = Form(..., description="수정 대상의 현재 버전"),
):
    """
    인수인계 수정 API

    - Path 파라미터:
      - handover_id(int): 인수인계 ID

    - Form 파라미터:
      - title(str): 제목
      - content(str): 내용
      - is_notice(str): 공지사항 여부 (문자열 "true"/"false")
      - department(str): 부서 (CS/HES/LENOVO/ALL)
    """
    user_id = current_user.get("user_id")
    user_role = current_user.get("user_role")
    logger.info(f"인수인계 수정 API 호출: id={handover_id}, user={user_id}")
    detail_url = f"/handover/{handover_id}"
    edit_url = f"/handover/{handover_id}/edit"

    try:
        # 현재 DB 버전 확인
        current_handover = get_handover_by_id(db, handover_id)
        if not current_handover:
            raise HTTPException(
                status_code=404, detail="수정할 인수인계를 찾을 수 없습니다."
            )

        version_mismatch = current_handover.version != version
        if version_mismatch:
            logger.warning(
                f"인수인계 수정 버전 불일치: ID={handover_id}, Client Version={version}, DB Version={current_handover.version}"
            )
            # 경고 메시지에 필요한 정보 (동시 수정 발생 시) - 사용자 이름 조회
            updater_user = (
                db.query(User)
                .filter(User.user_id == current_handover.update_by)
                .first()
            )
            concurrent_modifier_name = (
                updater_user.user_name if updater_user else current_handover.update_by
            )  # 이름 없으면 ID 표시
            concurrent_update_at = (
                current_handover.update_at.strftime("%Y-%m-%d %H:%M")
                if current_handover.update_at
                else "알 수 없음"
            )
            warning_msg = f"다른 사용자({concurrent_modifier_name})가 {concurrent_update_at}에 먼저 수정했습니다."
        else:
            warning_msg = None

        # 현재 인수인계 객체 조회 (권한 검증용) - get_handover_by_id 호출 중복 제거
        handover = current_handover  # 위에서 이미 조회함

        # 수정 권한 확인 (작성자 또는 관리자)
        if handover.create_by != user_id and user_role != "ADMIN":
            logger.warning(f"인수인계 수정 권한 없음: user={user_id}, id={handover_id}")
            error_message = quote("이 인수인계를 수정할 권한이 없습니다.")
            return RedirectResponse(
                f"{detail_url}?error={error_message}",
                status_code=status.HTTP_303_SEE_OTHER,
            )

        # 문자열 "true"/"false"를 불리언으로 변환
        is_notice_bool = is_notice.lower() == "true"

        # 공지사항 여부 변경 시 관리자 권한 필요
        if is_notice_bool != handover.is_notice and user_role != "ADMIN":
            logger.warning(f"공지사항 변경 권한 없음: user={user_id}, id={handover_id}")
            error_message = quote("관리자만 공지사항 설정을 변경할 수 있습니다.")
            return RedirectResponse(
                f"{edit_url}?error={error_message}",
                status_code=status.HTTP_303_SEE_OTHER,
            )

        # 부서 유효성 검증
        if department not in ["CS", "HES", "LENOVO", "ALL"]:
            logger.warning(f"유효하지 않은 부서: {department}")
            error_message = quote("유효하지 않은 부서입니다.")
            return RedirectResponse(
                f"{edit_url}?error={error_message}",
                status_code=status.HTTP_303_SEE_OTHER,
            )

        # 수정 데이터 준비
        update_data = {
            "title": title,
            "content": content,
            "is_notice": is_notice_bool,
            "department": department,
        }
        if status_val:
            update_data["status"] = status_val

        # 서비스 함수 호출하여 인수인계 수정
        handover = update_handover(
            db=db,
            handover_id=handover_id,
            update_data=update_data,
            updated_by=user_id,
            user_role=user_role,
        )

        # 성공 메시지 및 리다이렉트
        success_message = quote("인수인계가 성공적으로 수정되었습니다.")

        redirect_url = f"{detail_url}?success={success_message}"
        if version_mismatch and warning_msg:  # 버전 불일치 시 경고 메시지 추가
            redirect_url += f"&warning={quote(warning_msg)}"

        return RedirectResponse(redirect_url, status_code=status.HTTP_303_SEE_OTHER)

    except HTTPException as http_exc:
        logger.warning(
            f"인수인계 수정 API HTTP 오류: {http_exc.status_code}, {http_exc.detail}"
        )
        error_message = quote(http_exc.detail)
        return RedirectResponse(
            f"{edit_url}?error={error_message}",
            status_code=status.HTTP_303_SEE_OTHER,
        )
    except Exception as e:
        logger.error(f"인수인계 수정 API 처리 중 예외 발생: {e}", exc_info=True)
        error_message = quote("인수인계 수정 중 서버 오류가 발생했습니다.")

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "success": False,
                    "message": "인수인계 수정 중 서버 오류가 발생했습니다.",
                },
            )
        else:
            return RedirectResponse(
                f"{edit_url}?error={error_message}",
                status_code=status.HTTP_303_SEE_OTHER,
            )


@api_router.post("/{handover_id}/delete", status_code=status.HTTP_302_FOUND)
@db_transaction
async def delete_handover_action(
    request: Request,
    handover_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    user_id = current_user.get("user_id")
    user_role = current_user.get("user_role")
    logger.info(f"인수인계 삭제 API 요청: id={handover_id}, user={user_id}")

    detail_url = f"/handover/{handover_id}"
    list_url = "/handover"

    try:
        # 삭제 권한 확인 (작성자 또는 관리자)
        result = delete_handover(db, handover_id, user_id, user_role)

        if not result:
            logger.warning(f"인수인계 삭제 실패: ID {handover_id}")
            error_message = quote("인수인계 삭제 중 오류가 발생했습니다.")
            return RedirectResponse(
                f"{detail_url}?error={error_message}",
                status_code=status.HTTP_303_SEE_OTHER,
            )

        # 성공 메시지 및 리다이렉트
        success_message = quote("인수인계가 성공적으로 삭제되었습니다.")
        logger.info(f"인수인계 삭제 성공: ID {handover_id}")
        return RedirectResponse(
            f"{list_url}?success={success_message}",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    except HTTPException as http_exc:
        logger.warning(
            f"인수인계 삭제 API HTTP 오류: {http_exc.status_code}, {http_exc.detail}"
        )
        error_message = quote(http_exc.detail)
        return RedirectResponse(
            f"{detail_url}?error={error_message}", status_code=status.HTTP_303_SEE_OTHER
        )
    except Exception as e:
        logger.error(f"인수인계 삭제 API 처리 중 예외 발생: {e}", exc_info=True)
        error_message = quote("인수인계 삭제 중 오류가 발생했습니다.")
        return RedirectResponse(
            f"{detail_url}?error={error_message}", status_code=status.HTTP_303_SEE_OTHER
        )
