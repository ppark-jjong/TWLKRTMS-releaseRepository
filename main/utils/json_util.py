"""
JSON 관련 유틸리티
"""

import json
from datetime import datetime, date
from decimal import Decimal
from typing import Any
import logging
from sqlalchemy import Column

logger = logging.getLogger(__name__)


class CustomJSONEncoder(json.JSONEncoder):
    """
    커스텀 JSON 인코더
    FastAPI의 응답과 템플릿에서 사용할 수 있는 확장 JSON 직렬화 지원
    """

    def default(self, obj: Any) -> Any:
        # SQLAlchemy Column 타입 처리
        if isinstance(obj, Column):
            return str(obj)

        # Decimal 타입 처리
        if isinstance(obj, Decimal):
            return float(obj)

        # datetime 타입 처리
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%dT%H:%M")

        # date 타입 처리
        if isinstance(obj, date):
            return obj.strftime("%Y-%m-%d")

        # 나머지는 기본 인코더에 위임
        return super().default(obj)


def custom_json_dumps(obj: Any) -> str:
    """
    안전한 JSON 직렬화 함수

    Args:
        obj: 직렬화할 객체

    Returns:
        str: JSON 문자열
    """
    try:
        return json.dumps(obj, cls=CustomJSONEncoder, ensure_ascii=False)
    except TypeError as e:
        # 직렬화 불가능한 객체 처리
        logger.error(f"JSON 직렬화 오류: {str(e)}")

        # 객체 타입 로깅
        if hasattr(obj, "__dict__"):
            # logger.debug( # 프로덕션에서 불필요한 로그 제거
            #     f"객체 타입: {type(obj).__name__}, 속성: {list(obj.__dict__.keys())}"
            # )
            pass  # debug 로그만 있었으므로 pass 추가

        # 딕셔너리인 경우 문제 필드 찾기
        if isinstance(obj, dict):
            for key, value in obj.items():
                try:
                    json.dumps({key: value}, cls=CustomJSONEncoder)
                except TypeError:
                    logger.error(
                        f"직렬화 불가능한 필드: {key}={value}, 타입={type(value).__name__}"
                    )
                    # 재귀적으로 객체 처리
                    obj[key] = str(value)

        # 다시 시도
        try:
            return json.dumps(obj, cls=CustomJSONEncoder, ensure_ascii=False)
        except:
            # 마지막 시도 - 문자열 변환
            return json.dumps(str(obj), ensure_ascii=False)
