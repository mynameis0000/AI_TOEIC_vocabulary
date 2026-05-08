import os
import json
import logging
import requests

from flask import Flask, request, jsonify
import gspread
from google.oauth2.service_account import Credentials

# 로그 설정 (Render 대시보드에서 확인 가능)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def get_ai_response(word):
    try:
        api_key = os.environ.get("GEMINI_API_KEY")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"

        headers = {
            "Content-Type": "application/json"
        }

        data = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": f"{word} 뜻과 예문"
                        }
                    ]
                }
            ]
        }

        response = requests.post(
            url,
            headers=headers,
            json=data
        )

        logger.info(response.text)

        result = response.json()

        return result["candidates"][0]["content"]["parts"][0]["text"]

    except Exception as e:
        logger.error(f"AI Error: {str(e)}")
        return "AI 오류"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)