import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(GEMINI_MODEL)


def translate_word_with_gemini(word):

    print(
        f"[Gemini 분석] '{word}' 처리 중"
    )

    prompt = f"""
        Translate this English word or phrase into Korean.

        Input:
        "{word}"

        Return ONLY JSON.

        {{
        "meaning": "한국어 뜻"
        }}
        """

    try:

        response = model.generate_content(
            prompt,
            request_options={
                "timeout": 30
            }
        )

        clean_text = response.text.strip()

        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]

        elif clean_text.startswith("```"):
            clean_text = clean_text[3:]

        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]

        clean_text = clean_text.strip()

        result_json = json.loads(
            clean_text
        )

        result_json = json.loads(clean_text)

        meaning = result_json.get(
            "meaning",
            "뜻을 찾을 수 없음"
        )

        return {
            "success": True,
            "word": word,
            "meaning": meaning,
            "result": f"{word} → {meaning}",
            "suggestions": [],
            "partsOfSpeech": ["other"]
        }

    except Exception as error:

        print(
            f"[Gemini 실패] {str(error)}"
        )

        return {

            "success": False,

            "word": word,

            "meaning":
                "뜻을 찾을 수 없음",

            "result":
                "AI 서버가 일시적으로 응답하지 않습니다.",

            "suggestions": [],

            "partsOfSpeech": ["other"]
        }
