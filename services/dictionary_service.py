from PyDictionary import PyDictionary

dictionary = PyDictionary()


def get_word_meaning(word):

    try:

        meaning = dictionary.meaning(word)

        if not meaning:
            return "뜻을 찾을 수 없습니다."

        first_part = list(meaning.keys())[0]

        first_meaning = meaning[first_part][0]

        return f"{first_part}: {first_meaning}"

    except Exception as e:

        print(e)

        return "사전 검색 중 오류가 발생했습니다."