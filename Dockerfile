FROM python:3.12-slim

WORKDIR /app

# 시스템 패키지 설치 (최소화) 및 타임존 설정
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    tzdata \
    && rm -rf /var/lib/apt/lists/* \
    && ln -fs /usr/share/zoneinfo/Asia/Seoul /etc/localtime \
    && echo "Asia/Seoul" > /etc/timezone \
    && dpkg-reconfigure -f noninteractive tzdata

# 환경 변수 파일 복사
COPY .env ./

# Python 종속성 설치
COPY main/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 백엔드 소스 코드 복사
COPY main/ ./main/

# 로그 디렉토리 생성
RUN mkdir -p ./main/logs

# 정적 파일 디렉토리 생성 및 권한 설정
RUN mkdir -p ./main/static/css ./main/static/js ./main/static/images
RUN chmod -R 755 ./main/static

# 템플릿 디렉토리 생성
RUN mkdir -p ./main/templates
RUN chmod -R 755 ./main/templates

# 작업 디렉토리 설정
WORKDIR /app

# Python 임포트 경로 설정을 위한 환경 변수 설정
ENV PYTHONPATH=/app

# 컨테이너가 시작될 때 실행할 명령
CMD ["python", "-m", "main.main"]
# 헬스체크용 포트 노출
EXPOSE 8080
