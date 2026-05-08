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
 def get_ai_response(word):
    try:
        api_key = os.environ.get("GEMINI_API_KEY")
        genai.configure(api_key=api_key)
        
        # 'models/'를 빼고 이름만 전달해 봅니다.
        # 터미널 목록에 있던 이름 그대로입니다.
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"영어 단어 '{word}'의 뜻과 예문을 한국어로 아주 짧게 알려줘. 형식: 뜻 / 예문"
        
        # 혹시 모를 타임아웃을 방지하기 위해 생성 시도
        response = model.generate_content(prompt)
        
        if response.text:
            return response.text
        return "AI 분석 결과가 비어 있습니다."
        
    except Exception as e:
        logger.error(f"AI Error Detail: {str(e)}")
        # 에러가 나면 시트에서 바로 확인할 수 있게 핵심 내용 리턴
        if "404" in str(e):
            return "모델명 오류: 다른 이름 시도 필요"
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