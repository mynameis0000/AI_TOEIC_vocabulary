<div align="center">

# AI Vocabulary

### AI 기반 TOEIC 영어 단어 학습 웹앱

영어 단어를 입력하면
AI 기반 추천 검색어, 번역, 품사 분류 기능을 제공하는
모바일 중심 영어 학습 서비스입니다.

<br>

<img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white">
<img src="https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white">
<img src="https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black">

</div>

---

# 📌 Overview

AI Vocabulary는 TOEIC 학습을 위한 AI 기반 영어 단어 학습 웹앱입니다.

사용자가 영어 단어를 입력하면:

* 실제 영어 단어 여부 검증
* 영어 → 한국어 번역
* AI 기반 추천 검색어 제공
* 품사 기반 단어 분류
* 단어 카드 저장

기능을 제공합니다.

또한 모바일 환경에서는 Bottom Sheet 기반 단어장을 제공하여 실제 모바일 앱과 유사한 사용자 경험을 목표로 개발했습니다.

---

# ✨ Features

## 🔍 AI 기반 추천 검색어

존재하지 않는 영어 단어 입력 시:

* Damerau-Levenshtein 거리 기반 오타 보정
* Prefix similarity 기반 추천
* Gemini API 보조 추천

기능을 제공합니다.

### Example

```plaintext id="j3b2r7"
bananan → banana
hte → the
quie → quit
```

---

## 🌐 영어 단어 검증

dictionaryapi.dev를 사용하여 실제 영어 단어 여부를 검증합니다.

존재하지 않는 단어는 추천 검색어와 함께 안내합니다.

---

## 🇰🇷 영어 → 한국어 번역

googletrans 기반 번역 기능 제공.

### Example

```plaintext id="d2m8f4"
government → 정부
improve → 향상시키다
```

---

## 🗂 품사 기반 카테고리 시스템

저장된 단어를 품사별로 분류합니다.

### Categories

* 명사
* 동사
* 형용사
* 부사
* 기타

---

## 📱 반응형 모바일 UI

### PC

* 좌측 채팅 영역
* 우측 단어 카드 영역

### Mobile

* Bottom Sheet 기반 단어장
* 모바일 앱 스타일 인터랙션
* 1열 카드 레이아웃

---

## 📄 PDF / XLSX 다운로드

저장된 단어를:

* PDF
* XLSX

형태로 다운로드할 수 있습니다.

### PDF 특징

* Flask 서버 기반 생성
* 한글 폰트 지원
* 브라우저 print 방식 제거
* 즉시 다운로드 지원

---

# 🛠 Tech Stack

## Frontend

* HTML
* CSS
* JavaScript

## Backend

* Python
* Flask

## AI / API

* Gemini API
* dictionaryapi.dev
* googletrans

## Deployment

* Render.com

---

# 📂 Project Structure

```plaintext id="z6m4q2"
ai-vocab-app/
│
├── main.py
│
├── services/
│   └── translator_service.py
│
├── templates/
│   └── index.html
│
├── static/
│   ├── style.css
│   └── script.js
│
├── requirements.txt
├── README.md
└── .gitignore
```

---

# ⚡ Technical Challenges

## 1. 오타 추천 정확도 개선

초기에는 Gemini 기반 추천만 사용했지만:

* 추천 정확도 부족
* quota 낭비
* 짧은 단어 추천 실패

문제가 발생했습니다.

이를 해결하기 위해:

* Damerau-Levenshtein 거리
* Prefix similarity
* Frequency rank

기반 추천 시스템으로 개선했습니다.

---

## 2. 모바일 UX 최적화

모바일 환경에서:

```plaintext id="s7q2m8"
100vh + fixed layout
```

구조 충돌 문제가 발생했습니다.

이를 해결하기 위해:

* Bottom Sheet 구조 개선
* overflow 구조 수정
* 모바일 viewport 대응

작업을 진행했습니다.

---

## 3. 한글 PDF 다운로드 문제 해결

ReportLab 기본 폰트는 한글을 지원하지 않아 PDF에서 한글이 깨지는 문제가 발생했습니다.

이를 해결하기 위해:

* UnicodeCIDFont 적용
* Flask 서버 기반 PDF 생성

방식으로 개선했습니다.

---

# 🚀 Future Plans

* SQLite 저장 기능
* 로그인 기능
* 오답노트
* 예문 생성
* 발음 기능
* 학습 통계 Dashboard
* TOEIC 단어 세트 제공

---

# 👨‍💻 Author

### AI Vocabulary Project

Developed with Flask + JavaScript + Gemini API
