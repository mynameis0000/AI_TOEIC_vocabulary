from flask import Flask, render_template
from flask import request, jsonify

from services.translator_service import translate_word

app = Flask(__name__)


@app.route("/")
def home():

    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():

    data = request.get_json()

    word = data.get("word")

    result = translate_word(word)

    success = not result.startswith("❌")

    return jsonify({
        "success": success,
        "word": word,
        "meaning": result,
        "result": result
    })


if __name__ == "__main__":
    app.run(debug=True)