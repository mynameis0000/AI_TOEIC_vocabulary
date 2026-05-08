import os
import json
import logging
from flask import Flask, request, jsonify
import google.generativeai as genai
import gspread
from google.oauth2.service_account import Credentials

# 로그 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

import google.generativeai as genai
from google.generativeai import types

import google.generativeai as genai

def get_ai_response(word):
    try:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return "ERROR: API KEY MISSING"
            
        genai.configure(api_key=api_key)
        
        # 1.5 flash 모델의 가장 정확한 풀 네임을 사용합니다.
        # 만약 이것도 404가 뜨면 'gemini-1.5-flash-latest'로 바꿔보세요.
        model = genai.GenerativeModel('models/gemini-1.5-flash')
        
        prompt = f"영어 단어 '{word}'의 뜻과 예문을 한국어로 아주 짧게 알려줘. 형식: 뜻 / 예문"
        
        # 안전한 생성을 위해 약간의 설정을 추가합니다.
        response = model.generate_content(prompt)
        
        if response and response.text:
            return response.text
        else:
            return "AI 응답 없음"
            
    except Exception as e:
        logger.error(f"AI Error: {str(e)}")
        # 에러 메시지가 너무 길면 시트가 지저분해지므로 핵심만 리턴
        if "429" in str(e):
            return "할당량 초과 (잠시 후 시도)"
        return f"에러: {str(e)[:15]}"

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        # 데이터 수신
        data = request.get_json()
        word = data.get('word')
        spreadsheet_id = data.get('spreadsheetId')
        row_index = data.get('rowIndex')

        logger.info(f"데이터 수신: {word}, ID: {spreadsheet_id}, Row: {row_index}")

        if not all([word, spreadsheet_id, row_index]):
            return jsonify({"error": "Missing data"}), 400

        # 구글 인증
        creds_raw = os.environ.get('GOOGLE_SHEETS_CREDENTIALS')
        if not creds_raw:
            logger.error("GOOGLE_SHEETS_CREDENTIALS Env Var missing")
            return jsonify({"error": "Auth config missing"}), 500
            
        creds_info = json.loads(creds_raw)
        scopes = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
        client = gspread.authorize(creds)
        
        # 시트 열기 및 업데이트
        sh = client.open_by_key(spreadsheet_id)
        try:
            worksheet = sh.worksheet("시트1")
        except gspread.exceptions.WorksheetNotFound:
            logger.warning("'시트1'을 찾지 못해 첫 번째 시트를 사용합니다.")
            worksheet = sh.get_worksheet(0)
        
        # AI 결과 생성
        result = get_ai_response(word)
        
        # B열(2번) 업데이트
        worksheet.update_cell(row_index, 2, result)
        
        logger.info(f"업데이트 성공: {word} -> {result}")
        return jsonify({"status": "success", "result": result}), 200

    except Exception as e:
        logger.error(f"Server Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)