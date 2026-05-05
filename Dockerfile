# 1. 파이썬과 노드(Bun)가 모두 포함된 이미지 사용
FROM oven/bun:1.1-slim AS bun-base
FROM python:3.10-slim

# 2. 필요한 시스템 도구 설치
RUN apt-get update && apt-get install -y curl unzip && rm -rf /var/lib/apt/lists/*

# 3. Bun 설치 (이미지에서 복사)
COPY --from=bun-base /usr/local/bin/bun /usr/local/bin/bun

# 4. 작업 디렉토리 설정
WORKDIR /app

# 5. 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY mcp-google-sheets/package.json ./mcp-google-sheets/
RUN cd mcp-google-sheets && bun install

# 6. 나머지 코드 복사
COPY . .

# 7. 실행
CMD ["python", "main.py"]