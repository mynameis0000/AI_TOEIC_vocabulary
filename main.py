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

def get_ai_response(word):
    """Gemini API를 사용하여 단어 뜻 분석"""
    try:
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
        model = genai.GenerativeModel('gemini-pro')
        # prompt를 간결하게 수정
        prompt = f"영어 단어 '{word}'의 뜻과 예문을 한국어로 아주 짧게 알려줘. 형식: 뜻 / 예문"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"AI 분석 에러: {str(e)}")
        return "AI 분석 실패"

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        word = data.get('word')
        spreadsheet_id = data.get('spreadsheetId')
        row_index = data.get('rowIndex')

        if not word or not spreadsheet_id:
            return jsonify({"error": "데이터 누락"}), 400

        # 환경 변수에서 구글 인증 정보 가져오기
        creds_raw = os.environ.get('GOOGLE_SHEETS_CREDENTIALS')
        if not creds_raw:
            logger.error("환경 변수 GOOGLE_SHEETS_CREDENTIALS가 설정되지 않았습니다.")
            return jsonify({"error": "Env Var Missing"}), 500
            
        creds_info = json.loads(creds_raw)
        
        # 구글 시트 인증 및 연결
        scopes = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
        client = gspread.authorize(creds)
        
        # 시트 열기 (반드시 '시트1' 이름 확인!)
        sh = client.open_by_key(spreadsheet_id)
        worksheet = sh.worksheet("시트1") 
        
        # AI 결과 생성
        result = get_ai_response(word)
        
        # B열(2번째 칸)에 결과 업데이트
        worksheet.update_cell(row_index, 2, result)
        
        logger.info(f"성공: {word} -> {result}")
        return jsonify({"status": "success"}), 200

    except Exception as e:
        logger.error(f"서버 에러: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Render 환경에서 포트 설정 필수
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)