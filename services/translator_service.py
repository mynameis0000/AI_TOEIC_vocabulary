import requests
import google.generativeai as genai
from googletrans import Translator
from difflib import SequenceMatcher

import os
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(GEMINI_MODEL)

translator = Translator()

SUPPORTED_PARTS_OF_SPEECH = [
    "noun",
    "verb",
    "adjective",
    "adverb"
]

COMMON_WORDS = [
    "ask", "as", "ash", "asp", "ass", "also", "after", "again", "age", "air",
    "all", "am", "an", "and", "any", "are", "art", "at", "away", "back",
    "bad", "bag", "ball", "be", "bed", "big", "book", "boy", "bring", "build",
    "bus", "but", "buy", "call", "can", "car", "cat", "come", "cook", "day",
    "dog", "do", "door", "down", "drink", "eat", "end", "eye", "face", "fall",
    "family", "feel", "find", "fine", "fish", "food", "for", "friend", "from",
    "get", "give", "go", "good", "great", "green", "hand", "have", "he", "help",
    "her", "here", "him", "his", "home", "hot", "house", "how", "I", "in",
    "is", "it", "job", "keep", "know", "learn", "left", "like", "line", "live",
    "look", "love", "make", "man", "many", "me", "meet", "more", "mother",
    "move", "my", "name", "need", "new", "no", "not", "now", "of", "off",
    "old", "on", "one", "open", "or", "out", "over", "play", "put", "read",
    "right", "run", "say", "school", "see", "she", "sit", "small", "so", "some",
    "stand", "start", "stop", "study", "take", "talk", "teach", "tell", "that",
    "the", "their", "them", "then", "there", "they", "thing", "think", "this",
    "time", "to", "try", "up", "use", "very", "walk", "want", "water", "way",
    "we", "what", "when", "where", "who", "why", "will", "with", "word", "work",
    "write", "you", "your"
]

def get_word_info(word):

    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"

    response = requests.get(url, timeout=5)

    if response.status_code != 200:
        return {
            "is_valid": False,
            "parts_of_speech": []
        }

    entries = response.json()
    part_of_speech_scores = {}

    for entry in entries:
        for meaning in entry.get("meanings", []):
            part_of_speech = meaning.get("partOfSpeech")

            if part_of_speech in SUPPORTED_PARTS_OF_SPEECH:
                definition_count = len(meaning.get("definitions", [])) or 1
                part_of_speech_scores[part_of_speech] = (
                    part_of_speech_scores.get(part_of_speech, 0)
                    + definition_count
                )

    parts_of_speech = []

    if part_of_speech_scores:
        primary_part_of_speech = max(
            part_of_speech_scores,
            key=part_of_speech_scores.get
        )

        parts_of_speech.append(primary_part_of_speech)

    return {
        "is_valid": True,
        "parts_of_speech": parts_of_speech
    }

def suggest_similar_words(word):

    prompt = f"""
    The user entered an invalid English word: "{word}"

    Suggest up to 3 real English words
    similar to the typo.

    Rules:
    - Only real English words
    - Maximum 3
    - One word per line
    - No numbering
    - No explanation
    """

    response = model.generate_content(prompt)

    suggestions = response.text.strip().split("\n")

    return clean_suggestions(suggestions)

def clean_suggestions(suggestions):

    cleaned = []

    for suggestion in suggestions:
        word = suggestion.strip().lower().strip("-•0123456789. )(")

        if word.isalpha() and word not in cleaned:
            cleaned.append(word)

    return cleaned[:3]

def suggest_similar_words_fallback(word):

    normalized_word = word.lower()

    ranked_words = sorted(
        COMMON_WORDS,
        key=lambda candidate: (
            abs(len(candidate) - len(normalized_word)),
            -SequenceMatcher(None, normalized_word, candidate.lower()).ratio(),
            COMMON_WORDS.index(candidate)
        )
    )

    return clean_suggestions(ranked_words[:3])

def build_invalid_word_message(suggestions):

    message = "❌ 존재하지 않는 영어 단어입니다."
    
    return message

def translate_word(word):

    try:
        word_info = get_word_info(word)

        if not word_info["is_valid"]:

            try:
                suggestions = suggest_similar_words(word)
            except Exception as error:
                print(error)
                suggestions = suggest_similar_words_fallback(word)

            return {
                "success": False,
                "word": word,
                "meaning": "",
                "result": build_invalid_word_message(suggestions),
                "suggestions": suggestions,
                "partsOfSpeech": []
            }

        translated = translator.translate(word, src="en", dest="ko")

        return {
            "success": True,
            "word": word,
            "meaning": translated.text,
            "result": f"{word} → {translated.text}",
            "suggestions": [],
            "partsOfSpeech": word_info["parts_of_speech"]
        }
    except Exception as error:
        print(error)

        return {
            "success": False,
            "word": word,
            "meaning": "",
            "result": "번역 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
            "suggestions": [],
            "partsOfSpeech": []
        }
