from flask import Flask, render_template
from flask import request, jsonify

from services.translator_service import translate_word

app = Flask(__name__)


@app.route("/")
def home():

    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():

    data = request.get_json() or {}

    word = data.get("word", "").strip()

    if not word:
        return jsonify({
            "success": False,
            "word": "",
            "meaning": "",
            "result": "단어를 입력해주세요."
        }), 400

    result = translate_word(word)

    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True)
