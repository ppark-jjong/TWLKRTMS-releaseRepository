"""
권한 검사 유틸리티
"""

from typing import Dict, Any, List


def can_change_status(
    user: Dict[str, Any], current_status: str, new_status: str
) -> bool:
    """
    사용자의 상태 변경 권한 확인

    ADMIN: 모든 상태 간 자유롭게 변경 가능 (역행, 롤백 포함)
    USER: 제한된 상태 변경만 가능 (대기 -> 진행, 진행 -> 완료/이슈/취소)

    Args:
        user: 사용자 정보
        current_status: 현재 상태 코드
        new_status: 새 상태 코드

    Returns:
        bool: 상태 변경 가능 여부
    """
    user_role = user.get("user_role", "USER")

    # 관리자는 모든 상태 변경 가능
    if user_role == "ADMIN":
        return True

    # 일반 사용자는 제한된 상태 변경만 가능
    # 대기 -> 진행
    if current_status == "WAITING" and new_status == "IN_PROGRESS":
        return True

    # 진행 -> 완료/이슈/취소
    if current_status == "IN_PROGRESS" and new_status in [
        "COMPLETE",
        "ISSUE",
        "CANCEL",
    ]:
        return True

    # 그 외의 경우는 권한 없음
    return False


def can_edit_order(user: Dict[str, Any], order_data: Dict[str, Any]) -> bool:
    """
    주문 수정 권한 확인

    Args:
        user: 사용자 정보
        order_data: 주문 데이터

    Returns:
        bool: 수정 가능 여부
    """
    # 주문 데이터에 'editable' 플래그가 있고, 그 값이 True여야 수정 가능
    if not order_data.get("editable", False):
        return False

    # 여기에 추가적인 사용자 역할 기반 등의 수정 권한 로직이 필요하다면 추가할 수 있습니다.
    # 예를 들어, 특정 부서의 사용자만 수정 가능하다거나 하는 등의 조건입니다.
    # 현재는 'editable' 플래그에만 의존합니다.

    return True


def get_accessible_statuses(user: Dict[str, Any], current_status: str) -> List[str]:
    """
    사용자가 접근 가능한 상태 목록 반환

    Args:
        user: 사용자 정보
        current_status: 현재 상태 코드

    Returns:
        List[str]: 접근 가능한 상태 코드 목록
    """
    user_role = user.get("user_role", "USER")

    all_statuses = ["WAITING", "IN_PROGRESS", "COMPLETE", "ISSUE", "CANCEL"]

    # 관리자는 모든 상태 접근 가능
    if user_role == "ADMIN":
        return all_statuses

    # 일반 사용자는 상태에 따라 다른 상태 옵션
    if current_status == "WAITING":
        return ["WAITING", "IN_PROGRESS"]
    elif current_status == "IN_PROGRESS":
        return ["IN_PROGRESS", "COMPLETE", "ISSUE", "CANCEL"]
    else:
        # 그 외 상태는 변경 불가, 현재 상태만 표시
        return [current_status]


def get_status_options(
    user: Dict[str, Any], current_status: str
) -> List[Dict[str, str]]:
    """
    상태 변경 옵션 목록 반환 (템플릿용)

    Args:
        user: 사용자 정보
        current_status: 현재 상태 코드

    Returns:
        List[Dict[str, str]]: 상태 옵션 목록
    """
    # 상태 레이블 매핑
    status_labels = {
        "WAITING": "대기",
        "IN_PROGRESS": "진행",
        "COMPLETE": "완료",
        "ISSUE": "이슈",
        "CANCEL": "취소",
    }

    # 접근 가능한 상태 목록
    accessible_statuses = get_accessible_statuses(user, current_status)

    # 옵션 목록 생성
    options = []
    for status in ["WAITING", "IN_PROGRESS", "COMPLETE", "ISSUE", "CANCEL"]:
        options.append(
            {
                "value": status,
                "label": status_labels.get(status, status),
                "selected": status == current_status,
                "disabled": status not in accessible_statuses,
            }
        )

    return options
