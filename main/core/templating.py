from fastapi.templating import Jinja2Templates
import os
from datetime import datetime

# 템플릿 디렉토리 경로 설정 (main 폴더 기준)
# Docker 환경(/app/main/templates)과 로컬 환경 모두 고려
# __file__은 현재 파일(templating.py)의 경로
# os.path.dirname(__file__) -> /app/main/core
# os.path.dirname(os.path.dirname(__file__)) -> /app/main
TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")

# 디렉토리 존재 확인 (디버깅용)
try:
    if not os.path.isdir(TEMPLATE_DIR):
        print(f"[Templating] Warning: Template directory not found at {TEMPLATE_DIR}")
        # 대체 경로 시도 (로컬 실행 시)
        alt_template_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "templates")
        )
        if os.path.isdir(alt_template_dir):
            print(
                f"[Templating] Using alternative template directory: {alt_template_dir}"
            )
            TEMPLATE_DIR = alt_template_dir
        else:
            print(f"[Templating] Error: Cannot find templates directory.")
except Exception as e:
    print(f"[Templating] Error checking template directory: {e}")

# Jinja2Templates 인스턴스 생성
templates = Jinja2Templates(directory=TEMPLATE_DIR)

# 커스텀 템플릿 필터 추가
def datetime_format(value, format="%Y-%m-%d %H:%M"):
    """날짜/시간 포맷팅 필터"""
    if value is None:
        return ""
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            return value
    return value.strftime(format)

# 템플릿에 필터 등록
templates.env.filters["datetime"] = datetime_format

# 템플릿에 전역 함수 및 변수 추가
templates.env.globals["get_user"] = lambda request: getattr(request.state, "user", {"user_role": "USER"})

# 템플릿 렌더링 도우미 함수
def render_template(template_name, context):
    """
    템플릿 렌더링 도우미 함수
    request 객체가 있으면 user 정보를 확인하여 컨텍스트에 추가
    """
    if 'request' in context and 'user' not in context:
        request = context['request']
        user = getattr(request.state, 'user', {'user_role': 'USER'}) if hasattr(request, 'state') else {'user_role': 'USER'}
        context['user'] = user
    
    return templates.TemplateResponse(template_name, context)

# 디버깅용 메시지
print(f"[Templating] 템플릿 필터 등록 완료: {list(templates.env.filters.keys())}")
print(f"[Templating] 템플릿 전역 함수/변수 등록 완료: {list(templates.env.globals.keys())}")