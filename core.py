import os
import re
import json
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# 1. 안전 설정 (기존 설정 유지)
safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

# 2. AI 인스트럭션 (기존 설정 유지)
instruction_save = """너는 영단어 DB 생성기야. 
입력된 단어가 실존하는 영단어인 경우에만 '뜻 | 품사 | 토익 빈출 예문' 형식으로 출력해.
만약 존재하지 않는 단어이거나 의미 없는 철자 조합이라면 무조건 'ERROR'라고만 출력해.
인사말 없이 결과만 출력해."""

def is_valid_input(word):
    """기본 문자열 검증 로직"""
    if not word or len(word.strip()) < 2: return False
    if re.search("[ㄱ-ㅎㅏ-ㅣ가-힣]", word): return False
    return True

async def get_gemini_word_data(word):
    """모드 1: 단어 정보 생성 엔진"""
    save_model = genai.GenerativeModel('models/gemini-flash-latest', system_instruction=instruction_save)
    response = save_model.generate_content(word, safety_settings=safety_settings)
    raw_res = response.text.strip()
    
    if "ERROR" in raw_res or "|" not in raw_res:
        return None
    
    parsed = [item.strip() for item in raw_res.split('|')]
    # [뜻, 품사, 예문] 반환
    return (parsed + ["-", "-", "-"])[:3]

async def get_quiz_feedback(q_ex, q_word, q_mean, u_ans):
    """모드 2: 퀴즈 해설 및 분석 엔진"""
    model = genai.GenerativeModel('models/gemini-flash-latest')
    prompt = f"영문: {q_ex}\n단어: {q_word}({q_mean})\n학생해석: {u_ans}\n\n[지침: 1.정확도(%), 2.본래뜻, 3.학습포인트(1문장)만 출력]"
    response = model.generate_content(prompt, safety_settings=safety_settings)
    return response.text.strip()