from flask import Flask, render_template, request, jsonify, send_file
from services.translator_service import translate_word
from services.excel_service import build_xlsx
from services.pdf_service import build_pdf


#Flack 서버 설정
# 서버 객체를 생성
app = Flask(__name__)

#영어 품사 받으면 한글로 바꾸기
PART_OF_SPEECH_LABELS = {
    "noun": "명사",
    "verb": "동사",
    "adjective": "형용사",
    "adverb": "부사",
    "other": "기타"
}

# 경로 설정
@app.route("/")
def home():
    return render_template("index.html")

#데이터 처리 및 통신
#검색 버튼 눌러 데이터를 서버로 보낼 때
@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json() or {}
    word = data.get("word", "").strip() #word찾기, 공백 제거
    if not word:
        return jsonify({
            "success": False,
            "word": "",
            "meaning": "",
            "result": "단어를 입력해주세요."
        }), 400

    result = translate_word(word)
    return jsonify(result) #SON 형식으로 변환하여 다시 전송


# 다운로드는 별도의 경로에서 처리
@app.route("/export/xlsx", methods=["POST"])
def export_xlsx():
    data = request.get_json() or {}
    words = data.get("words", [])
    xlsx_buffer = build_xlsx(words) 
    
    return send_file(
        xlsx_buffer, 
        download_name="words.xlsx", 
    )

@app.route("/export/pdf", methods=["POST"])
def export_pdf():
    data = request.get_json() or {}
    words = data.get("words", [])
    pdf_buffer = build_pdf(words)
    
    return send_file(
        pdf_buffer, 
        download_name="words.pdf", 
    )

if __name__ == "__main__":
    app.run(debug=True)
