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
from main.utils.lock import acquire_lock, release_lock, check_lock_status

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

        # 락 상태 확인 (utils에서 가져온 check_lock_status 사용)
        lock_info = check_lock_status(
            db, "handover", handover_id, current_user.get("user_id")
        )

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
            "lock_info": lock_info,
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
@db_transaction  # 락 획득/해제 위해 트랜잭션 필요
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
        # 인수인계 정보 로드 (락 전에 수행)
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

        # 먼저 현재 락 상태 확인
        lock_status = check_lock_status(db, "handover", handover_id, user_id)

        # 이미 내가 락을 가지고 있는 경우 새로 획득할 필요 없음
        if (
            lock_status.get("success")
            and lock_status.get("editable")
            and lock_status.get("locked")
        ):
            if lock_status.get("locked_by") == user_id:
                logger.info(
                    f"인수인계 수정 페이지: 이미 본인({user_id})의 락이 있어 재사용: id={handover_id}"
                )
                # 락 시간 갱신 (락 만료 방지)
                try:
                    from main.utils.lock import _update_lock

                    _update_lock(db, "handover", handover_id, user_id, True, True)
                except Exception as e:
                    logger.warning(f"락 시간 갱신 실패: {str(e)}")

                # 이미 락을 가지고 있으므로 그대로 진행
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
                }

                return templates.TemplateResponse("handover_form.html", context)

        # 다른 락이 있거나 락이 없는 경우 새로 획득 시도
        success, message = acquire_lock(db, "handover", handover_id, user_id)

        if not success:
            # 락 획득 실패 시 상세 페이지로 리다이렉트
            error_msg = message.get("message", "현재 다른 사용자가 수정 중입니다.")
            locked_by = message.get("locked_by", "다른 사용자")
            locked_at = message.get("locked_at")

            if locked_at:
                try:
                    locked_at_str = locked_at.strftime("%Y-%m-%d %H:%M")
                    error_msg = f"{locked_by}님이 {locked_at_str}부터 수정 중입니다."
                except:
                    # 시간 형식 변환 실패 시 기본 메시지 유지
                    pass

            logger.warning(f"인수인계 수정 페이지 락 획득 실패: {error_msg}")
            error_message = quote(error_msg)
            return RedirectResponse(
                f"{detail_url}?error={error_message}",
                status_code=status.HTTP_303_SEE_OTHER,
            )

        # 락 획득 성공 시 수정 페이지 렌더링
        logger.info(
            f"인수인계 수정 페이지 락 획득 성공: id={handover_id}, user={user_id}"
        )

        # 인수인계 데이터
        handover_data = _handover_to_dict(handover_model)

        # 공지사항 생성 권한
        can_make_notice = current_user.get("user_role") == "ADMIN"

        # 페이지 컨텍스트 설정
        context = {
            "request": request,
            "handover": handover_data,
            "current_user": current_user,
            "is_edit": True,
            "can_create_notice": can_make_notice,
            "error_message": request.query_params.get("error"),
            "success_message": request.query_params.get("success"),
        }

        # 락을 해제하지 않고 유지 - 실제 수정 API 호출 시까지 락 유지
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
        try:
            # 예외 발생 시 락 해제 시도
            release_lock(db, "handover", handover_id, user_id)
        except Exception as release_error:
            logger.error(f"예외 후 락 해제 실패: {str(release_error)}")

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
        None, description="부서 필터링 (CS, HES, LENOVO)"
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
      - department(str): 부서 (CS/HES/LENOVO)
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
        if department not in ["CS", "HES", "LENOVO"]:
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
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    인수인계 수정 API (락 점검 포함)

    - Path 파라미터:
      - handover_id(int): 인수인계 ID

    - Form 파라미터:
      - title(str): 제목
      - content(str): 내용
      - is_notice(str): 공지사항 여부 (문자열 "true"/"false")
      - department(str): 부서 (CS/HES/LENOVO)
    """
    user_id = current_user.get("user_id")
    user_role = current_user.get("user_role")
    logger.info(f"인수인계 수정 API 호출: id={handover_id}, user={user_id}")
    detail_url = f"/handover/{handover_id}"
    edit_url = f"/handover/{handover_id}/edit"

    try:
        # 수정 전 락 상태 확인
        lock_status = check_lock_status(db, "handover", handover_id, user_id)

        if not lock_status.get("success") or not lock_status.get("editable"):
            # 락 소유 검사 실패, 423 응답 또는 상세 페이지로 리다이렉트
            error_msg = lock_status.get(
                "message", "다른 사용자가 수정 중이거나 락이 만료되었습니다."
            )
            logger.warning(f"인수인계 수정 API 락 검증 실패: {error_msg}")

            # API 호출인 경우 JSON 응답, 일반 폼 제출인 경우 리다이렉트
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JSONResponse(
                    status_code=status.HTTP_423_LOCKED,
                    content={"success": False, "message": error_msg},
                )
            else:
                error_message = quote(error_msg)
                return RedirectResponse(
                    f"{detail_url}?error={error_message}",
                    status_code=status.HTTP_303_SEE_OTHER,
                )

        # 현재 인수인계 객체 조회 (권한 검증용)
        handover = get_handover_by_id(db, handover_id)
        if not handover:
            logger.warning(f"인수인계 수정 실패: ID {handover_id} 찾을 수 없음")
            error_message = quote("수정할 인수인계를 찾을 수 없습니다.")
            return RedirectResponse(
                f"/handover?error={error_message}",
                status_code=status.HTTP_303_SEE_OTHER,
            )

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
        if department not in ["CS", "HES", "LENOVO"]:
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

        # 서비스 함수 호출하여 인수인계 수정
        handover = update_handover(
            db=db,
            handover_id=handover_id,
            update_data=update_data,
            updated_by=user_id,
            user_role=user_role,
        )

        # 락 해제 (finally 블록에서도 수행하지만 명시적으로 성공 시에도 해제)
        try:
            release_lock(db, "handover", handover_id, user_id)
            logger.info(f"인수인계 수정 완료 후 락 해제 성공: ID {handover_id}")
        except Exception as release_err:
            logger.error(f"인수인계 수정 완료 후 락 해제 실패: {release_err}")

        # 성공 메시지 및 리다이렉트
        success_message = quote("인수인계가 성공적으로 수정되었습니다.")
        return RedirectResponse(
            f"{detail_url}?success={success_message}",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    except HTTPException as http_exc:
        logger.warning(
            f"인수인계 수정 API HTTP 오류: {http_exc.status_code}, {http_exc.detail}"
        )
        if http_exc.status_code == 423:  # Locked
            # 락 관련 오류
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JSONResponse(
                    status_code=http_exc.status_code,
                    content={"success": False, "message": http_exc.detail},
                )
            else:
                return RedirectResponse(
                    f"{detail_url}?error={quote(http_exc.detail)}",
                    status_code=status.HTTP_303_SEE_OTHER,
                )
        else:
            # 기타 HTTP 오류
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JSONResponse(
                    status_code=http_exc.status_code,
                    content={"success": False, "message": http_exc.detail},
                )
            else:
                return RedirectResponse(
                    f"{edit_url}?error={quote(http_exc.detail)}",
                    status_code=status.HTTP_303_SEE_OTHER,
                )
    except Exception as e:
        # 기타 예외
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
    finally:
        # 락 해제 시도 (작업 성공 여부와 관계없이)
        try:
            release_lock(db, "handover", handover_id, user_id)
            logger.info(
                f"인수인계 수정 finally 블록에서 락 해제 시도: ID {handover_id}"
            )
        except Exception as release_err:
            logger.error(f"finally 블록에서 락 해제 실패: {release_err}")


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
        # 락 상태 확인 (본인이 락을 가지고 있거나 획득 가능한지)
        lock_status = check_lock_status(db, "handover", handover_id, user_id)

        if not lock_status.get("success") or not lock_status.get("editable"):
            # 락 소유 검사 실패, 423 응답 또는 상세 페이지로 리다이렉트
            error_msg = lock_status.get(
                "message", "다른 사용자가 수정 중이거나 락이 만료되었습니다."
            )
            logger.warning(f"인수인계 삭제 API 락 검증 실패: {error_msg}")

            # API 호출인 경우 JSON 응답, 일반 폼 제출인 경우 리다이렉트
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JSONResponse(
                    status_code=status.HTTP_423_LOCKED,
                    content={"success": False, "message": error_msg},
                )
            else:
                error_message = quote(error_msg)
                return RedirectResponse(
                    f"{detail_url}?error={error_message}",
                    status_code=status.HTTP_303_SEE_OTHER,
                )

        # 락 획득 시도
        success, message = acquire_lock(db, "handover", handover_id, user_id)

        if not success:
            # 락 획득 실패 시 상세 페이지로 리다이렉트
            error_msg = message.get("message", "현재 다른 사용자가 수정 중입니다.")
            logger.warning(f"인수인계 삭제 락 획득 실패: {error_msg}")
            error_message = quote(error_msg)
            return RedirectResponse(
                f"{detail_url}?error={error_message}",
                status_code=status.HTTP_303_SEE_OTHER,
            )

        # 삭제 권한 확인 (작성자 또는 관리자)
        result = delete_handover(db, handover_id, user_id, user_role)

        if not result:
            logger.warning(f"인수인계 삭제 실패: ID {handover_id}")
            error_message = quote("인수인계 삭제 중 오류가 발생했습니다.")
            return RedirectResponse(
                f"{detail_url}?error={error_message}",
                status_code=status.HTTP_303_SEE_OTHER,
            )

        # 락 해제 (finally 블록에서도 수행하지만 명시적으로 성공 시에도 해제)
        try:
            release_lock(db, "handover", handover_id, user_id)
            logger.info(f"인수인계 삭제 완료 후 락 해제 성공: ID {handover_id}")
        except Exception as release_err:
            logger.error(f"인수인계 삭제 완료 후 락 해제 실패: {release_err}")

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
        # 락 오류(423)인 경우 특별 처리
        if http_exc.status_code == status.HTTP_423_LOCKED:
            error_message = quote(http_exc.detail)
            return RedirectResponse(
                f"{detail_url}?error={error_message}",
                status_code=status.HTTP_303_SEE_OTHER,
            )

        # 기타 HTTP 오류
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
    finally:
        # 락 해제 시도 (작업 성공 여부와 관계없이)
        try:
            release_lock(db, "handover", handover_id, user_id)
            logger.info(
                f"인수인계 삭제 finally 블록에서 락 해제 시도: ID {handover_id}"
            )
        except Exception as release_err:
            logger.error(f"finally 블록에서 락 해제 실패: {release_err}")


# 페이지 이탈 시 락 해제 API
@api_router.post("/{handover_id}/release-lock", status_code=status.HTTP_200_OK)
@db_transaction
async def release_handover_lock(
    request: Request,
    handover_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    user_id = current_user.get("user_id")
    logger.info(f"인수인계 락 해제 API 요청: id={handover_id}, user={user_id}")

    try:
        # 락 해제 시도
        success, message = release_lock(db, "handover", handover_id, user_id)

        if success:
            logger.info(f"인수인계 락 해제 성공: id={handover_id}, user={user_id}")
            return {"success": True, "message": "락이 성공적으로 해제되었습니다."}
        else:
            logger.warning(
                f"인수인계 락 해제 실패: id={handover_id}, 사유={message.get('message', '알 수 없음')}"
            )
            return {"success": False, "message": message.get("message", "락 해제 실패")}

    except Exception as e:
        logger.error(f"인수인계 락 해제 API 오류: {str(e)}")
        return {"success": False, "message": "락 해제 처리 중 오류가 발생했습니다"}
