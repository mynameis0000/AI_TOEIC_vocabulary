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

# (상단 import 및 get_ai_response 함수는 이전과 동일)

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        word = data.get('word')
        spreadsheet_id = data.get('spreadsheetId')
        row_index = data.get('rowIndex')

        # 데이터 검증
        if not all([word, spreadsheet_id, row_index]):
            return jsonify({"error": "Data missing"}), 400

        # 1. 환경 변수명 확인 (Render에 등록한 이름과 일치해야 함)
        # 만약 Render에 'MY_GCP_KEY'라고 저장했다면 아래 이름을 수정하세요.
        creds_raw = os.environ.get('GOOGLE_SHEETS_CREDENTIALS') 
        
        if not creds_raw:
            logger.error("환경 변수가 설정되지 않았습니다.")
            return jsonify({"error": "Environment variable missing"}), 500
            
        creds_info = json.loads(creds_raw)
        scopes = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
        client = gspread.authorize(creds)
        
        # 2. 시트 열기 ('시트1' 이름 명시)
        sh = client.open_by_key(spreadsheet_id)
        try:
            worksheet = sh.worksheet("시트1") 
        except gspread.exceptions.WorksheetNotFound:
            # 혹시나 '시트1'이 없을 경우를 대비해 첫 번째 시트라도 가져오도록 예외 처리
            worksheet = sh.get_worksheet(0)
            logger.warning("'시트1'을 찾지 못해 첫 번째 워크시트를 선택했습니다.")
        
        # 3. AI 결과 생성 및 업데이트
        result = get_ai_response(word)
        
        # 업데이트 (2열: B열)
        worksheet.update_cell(row_index, 2, result)
        
        logger.info(f"성공: {word} 업데이트 완료")
        return jsonify({"status": "success"}), 200

    except Exception as e:
        logger.error(f"상세 에러: {str(e)}")
        return jsonify({"error": "Internal Server Error"}), 500
    
if __name__ == "__main__":
    # Render 환경에서 포트 설정 필수
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)