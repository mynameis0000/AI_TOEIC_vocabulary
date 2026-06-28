SUPPORTED_PARTS_OF_SPEECH = [
    "noun",
    "verb",
    "adjective",
    "adverb",
    "other"
]

PRIMARY_PARTS_OF_SPEECH = [
    "noun",
    "verb",
    "adjective",
    "adverb"
]

BE_VERBS = {
    "be",
    "am",
    "is",
    "are",
    "was",
    "were",
    "been",
    "being"
}

OTHER_PART_OF_SPEECH_WORDS = {
    "a",
    "an",
    "the",
    "and",
    "or",
    "but",
    "because",
    "if",
    "for",
    "from",
    "of",
    "in",
    "on",
    "to",
    "with",
    "under",
    "over",
    "as"
}

COMMON_WORDS = [
    "ask", "as", "ash", "asp", "ass", "also", "after", "again", "age", "air",
    "all", "am", "an", "and", "any", "apple", "are", "area", "around", "art",
    "at", "away", "baby", "back", "bad", "bag", "ball", "banana", "be", "bed",
    "before", "begin", "best", "better", "big", "bird", "black", "blue", "book",
    "boy", "bring", "build", "bus", "but", "buy", "call", "can", "car", "cat",
    "change", "child", "city", "class", "clean", "close", "cold", "come", "cook",
    "country", "cut", "day", "different", "dog", "do", "door", "down", "draw",
    "drink", "ear", "early", "earth", "eat", "end", "enough", "environment",
    "eye", "face", "fall", "family",
    "far", "fast", "father", "feel", "few", "find", "fine", "fire", "fish",
    "food", "for", "free", "friend", "from", "fruit", "game", "get", "girl",
    "give", "go", "good", "great", "green", "group", "grow", "hand", "happy",
    "hard", "have", "he", "head", "hear", "help", "her", "here", "high", "him",
    "his", "home", "hot", "house", "how", "I", "idea", "important", "in", "is",
    "it", "job", "keep", "kind", "know", "large", "last", "late", "learn",
    "leave", "left", "life", "light", "like", "line", "little", "live", "long",
    "look", "love", "lovely", "make", "man", "many", "me", "meet", "money",
    "more", "morning", "mother", "move", "music", "my", "name", "near", "need",
    "new", "next", "night", "no", "not", "now", "number", "of", "off", "old",
    "on", "one", "open", "or", "orange", "other", "out", "over", "page",
    "paper", "part", "people", "place", "play", "point", "put", "quick",
    "quickly", "read", "red", "right", "room", "run", "same", "say", "school",
    "see", "sentence", "set", "she", "short", "show", "side", "sit", "small",
    "so", "some", "sound", "spell", "stand", "start", "stop", "story", "study",
    "take", "talk", "teach", "tell", "that", "the", "their", "them", "then",
    "there", "they", "thing", "think", "this", "time", "to", "tree", "try",
    "under", "up", "use", "very", "walk", "want", "water", "way", "we", "week",
    "well", "what", "when", "where", "white", "who", "why", "will", "with",
    "word", "work", "world", "write", "yellow", "yes", "you", "young", "your"
]

WORD_FREQUENCY_RANKS = {
    word.lower(): index
    for index, word in enumerate(COMMON_WORDS)
}