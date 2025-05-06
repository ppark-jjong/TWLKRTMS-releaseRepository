from fastapi.templating import Jinja2Templates
import os
from datetime import datetime, date
import json
from decimal import Decimal

# 템플릿 디렉토리 경로 설정 (main 폴더 기준)
# Docker 환경(/app/main/templates)과 로컬 환경 모두 고려
# __file__은 현재 파일(templating.py)의 경로
# os.path.dirname(__file__) -> /app/main/core
# os.path.dirname(os.path.dirname(__file__)) -> /app/main
TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")

# 디렉토리 존재 확인
try:
    if not os.path.isdir(TEMPLATE_DIR):
        # 대체 경로 시도 (로컬 실행 시)
        alt_template_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "templates")
        )
        if os.path.isdir(alt_template_dir):
            TEMPLATE_DIR = alt_template_dir
except Exception:
    pass

# Jinja2Templates 인스턴스 생성
templates = Jinja2Templates(directory=TEMPLATE_DIR)


# 커스텀 템플릿 필터 추가
def datetime_format(value, format="%Y-%m-%dT%H:%M"):
    """날짜/시간 포맷팅 필터 - ISO 8601 형식으로 통일"""
    if value is None:
        return ""
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return value
    return value.strftime(format)


# JSON 변환을 위한 커스텀 필터 추가
class TemplateJSONEncoder(json.JSONEncoder):
    """템플릿에서 안전한 JSON 직렬화를 위한 커스텀 인코더"""

    def default(self, obj):
        # Decimal 타입 처리 (데이터베이스에서 가져온 숫자형)
        if isinstance(obj, Decimal):
            return float(obj)

        # datetime 타입 처리
        if isinstance(obj, datetime):
            return obj.strftime("%Y-%m-%dT%H:%M")

        # date 타입 처리
        if isinstance(obj, date):
            return obj.strftime("%Y-%m-%d")

        # SQLAlchemy 모델 객체 처리
        if hasattr(obj, "__dict__") and hasattr(obj, "__tablename__"):
            return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}

        # 기타 객체 처리
        try:
            return super().default(obj)
        except TypeError:
            # 직렬화할 수 없는 객체는 문자열로 변환
            return str(obj)


def custom_tojson(value):
    """안전한 JSON 변환 필터"""
    try:
        # 커스텀 인코더 사용하여 변환
        result = json.dumps(value, cls=TemplateJSONEncoder, ensure_ascii=False)
        return result
    except Exception as e:
        # 오류 상세 로깅
        if isinstance(value, dict):
            # logging.debug(f"JSON 직렬화 실패한 객체 키: {list(value.keys())}") # 프로덕션에서 불필요한 로그 제거
            pass  # debug 로그만 있었으므로 pass 추가

            # 문제의 키 식별
            for k, v in value.items():
                try:
                    json.dumps({k: v}, cls=TemplateJSONEncoder)
                except Exception as e2:
                    logging.error(
                        f"JSON 직렬화 문제 필드: {k}, 값 타입: {type(v).__name__}, 오류: {str(e2)}"
                    )

        # 마지막 시도 - 문자열 변환
        try:
            return json.dumps(str(value))
        except:
            return "{}"  # 모든 시도 실패 시 빈 객체 반환


# 템플릿에 필터 등록
templates.env.filters["datetime"] = datetime_format
templates.env.filters["safe_json"] = custom_tojson
templates.env.filters["tojson"] = custom_tojson  # 기본 tojson 필터 덮어쓰기

# 템플릿에 전역 함수 및 변수 추가
templates.env.globals["get_user"] = lambda request: getattr(
    request.state, "user", {"user_role": "USER"}
)


# 템플릿 렌더링 도우미 함수
def render_template(template_name, context):
    """
    템플릿 렌더링 도우미 함수
    request 객체가 있으면 user 정보를 확인하여 컨텍스트에 추가
    """
    if "request" in context and "user" not in context:
        request = context["request"]
        user = (
            getattr(request.state, "user", {"user_role": "USER"})
            if hasattr(request, "state")
            else {"user_role": "USER"}
        )
        context["user"] = user

    return templates.TemplateResponse(template_name, context)
