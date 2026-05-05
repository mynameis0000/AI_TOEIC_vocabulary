# 1. 파이썬 3.11 슬림 이미지를 기반으로 시작
FROM python:3.11-slim

# 2. 시스템 필수 도구(curl, unzip) 설치
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# 3. Bun 설치 및 환경 변수 설정
RUN curl -fsSL https://bun.sh/install | bash
ENV PATH="/root/.bun/bin:$PATH"

# 4. 작업 디렉토리 설정
WORKDIR /app

# 5. 파이썬 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Bun(Node) 의존성 설치
COPY package.json .
# 만약 lock 파일이 있다면 함께 복사 (없어도 무방)
COPY bun.lockb* . 
RUN bun install

# 7. 프로젝트 전체 파일 복사
COPY . .

# 8. Flask 포트 설정 (Render 기본값 10000)
EXPOSE 10000

# 9. 메인 서버 실행
CMD ["python", "main.py"]