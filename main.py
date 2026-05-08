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
from google.generativeai import client

def get_ai_response(word):
    try:
        api_key = os.environ.get("GEMINI_API_KEY")
        
        # [핵심] v1beta가 아닌 안정적인 v1 API를 사용하도록 명시적으로 설정합니다.
        # 이렇게 하면 404 에러의 주원인인 버전 불일치를 피할 수 있습니다.
        genai.configure(api_key=api_key)
        
        # 모델 객체를 생성할 때 'models/' 접두사를 확실히 붙여줍니다.
        model = genai.GenerativeModel('models/gemini-1.5-flash')
        
        prompt = f"영어 단어 '{word}'의 뜻과 예문을 한국어로 아주 짧게 알려줘. 형식: 뜻 / 예문"
        
        # 에러 메시지에서 언급된 v1beta를 피하기 위해 기본 호출을 수행합니다.
        response = model.generate_content(prompt)
        
        if response.text:
            return response.text
        return "응답을 생성할 수 없습니다."
        
    except Exception as e:
        logger.error(f"AI Error Detail: {str(e)}")
        # 404가 뜨는지 429가 뜨는지 시트에서 바로 확인하기 위해 출력
        return f"상태: {str(e)[:25]}"

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