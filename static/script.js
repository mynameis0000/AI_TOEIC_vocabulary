const sendButton = document.getElementById("sendButton");

const wordInput = document.getElementById("wordInput");

const chatArea = document.getElementById("chatArea");

const wordList = document.getElementById("wordList");

const categoryTabs =
    document.querySelectorAll(".category-tab");

const pdfDownloadButton =
    document.getElementById("pdfDownloadButton");

const xlsxDownloadButton =
    document.getElementById("xlsxDownloadButton");

const clearWordsButton =
    document.getElementById("clearWordsButton");

const swapButton =
    document.getElementById("swapButton");

const content =
    document.querySelector(".content");

const editModal =
    document.getElementById("editModal");

const editWordInput =
    document.getElementById("editWordInput");

const editMeaningInput =
    document.getElementById("editMeaningInput");

const saveEditButton =
    document.getElementById("saveEditButton");

const cancelEditButton =
    document.getElementById("cancelEditButton");

let editingIndex = null;

const savedWords = [];

let activeCategory = "all";

const partOfSpeechLabels = {

    noun: "명사",

    verb: "동사",

    adjective: "형용사",

    adverb: "부사",

    other: "기타"
};


function addUserMessage(message) {

    const messageDiv =
        document.createElement("div");

    messageDiv.classList.add("user-message");

    messageDiv.innerHTML =
        message.replace(/\n/g, "<br>");

    chatArea.appendChild(messageDiv);

    chatArea.scrollTop =
        chatArea.scrollHeight;
}


function addBotMessage(
    message,
    suggestions = []
) {

    const messageDiv =
        document.createElement("div");

    messageDiv.classList.add("bot-message");

    message.split("\n").forEach(
        (line, index) => {

            if (index > 0) {

                messageDiv.appendChild(
                    document.createElement("br")
                );
            }

            messageDiv.appendChild(
                document.createTextNode(line)
            );
        }
    );

    if (suggestions.length > 0) {

        const suggestionLabel =
            document.createElement("div");

        suggestionLabel.classList.add(
            "suggestion-label"
        );

        suggestionLabel.textContent =
            "추천 검색어";

        const suggestionList =
            document.createElement("div");

        suggestionList.classList.add(
            "suggestion-list"
        );

        suggestions.forEach((suggestion) => {

            const suggestionButton =
                document.createElement("button");

            suggestionButton.classList.add(
                "suggestion-chip"
            );

            suggestionButton.type = "button";

            suggestionButton.textContent =
                suggestion;

            suggestionButton.addEventListener(
                "click",
                () => {

                    submitWords(suggestion);
                }
            );

            suggestionList.appendChild(
                suggestionButton
            );
        });

        messageDiv.appendChild(
            suggestionLabel
        );

        messageDiv.appendChild(
            suggestionList
        );
    }

    chatArea.appendChild(messageDiv);

    chatArea.scrollTop =
        chatArea.scrollHeight;
}


function addSavedWord(
    word,
    meaning,
    partsOfSpeech = []
) {

    const alreadyExists =
        savedWords.some(
            (savedWord) =>

                savedWord.word
                    .trim()
                    .toLowerCase()

                ===

                word
                    .trim()
                    .toLowerCase()
        );

    if (alreadyExists) {

        return false;
    }

    savedWords.push({

        word: word,

        meaning: meaning,

        partsOfSpeech: partsOfSpeech
    });

    renderSavedWords();

    saveWordsToStorage();

    return true;
}


function shouldShowWord(wordData) {

    return (

        activeCategory === "all" ||

        wordData.partsOfSpeech.includes(
            activeCategory
        )
    );
}


function createSavedWordCard(
    wordData,
    index
) {

    const wordDiv =
        document.createElement("div");

    wordDiv.classList.add("saved-word");

    wordDiv.dataset.partsOfSpeech =
        wordData.partsOfSpeech.join(",");

    wordDiv.innerHTML = `

        <div class="card-menu-wrapper">

            <button class="card-menu-button">
                ⋮
            </button>

            <div class="card-menu-dropdown">

                <button class="edit-word-button">
                    수정
                </button>

                <button class="delete-word-button">
                    삭제
                </button>

            </div>

        </div>

        <div class="english">
            ${wordData.word}
        </div>

        <div class="korean">
            ${wordData.meaning}
        </div>

        <div class="speak-button">
            🔊
        </div>

    `;

    const menuButton =
        wordDiv.querySelector(
            ".card-menu-button"
        );

    const dropdown =
        wordDiv.querySelector(
            ".card-menu-dropdown"
        );

    const editButton =
        wordDiv.querySelector(
            ".edit-word-button"
        );

    const deleteButton =
        wordDiv.querySelector(
            ".delete-word-button"
        );

    const speakButton =
        wordDiv.querySelector(
            ".speak-button"
        );

    menuButton.addEventListener(
        "click",
        (event) => {

            event.stopPropagation();

            document
                .querySelectorAll(
                    ".card-menu-dropdown"
                )
                .forEach((menu) => {

                    if (menu !== dropdown) {

                        menu.classList.remove(
                            "active"
                        );
                    }
                });

            dropdown.classList.toggle(
                "active"
            );
        }
    );

    editButton.addEventListener(
        "click",
        () => {

            editingIndex = index;

            editWordInput.value =
                wordData.word;

            editMeaningInput.value =
                wordData.meaning;

            document
                .querySelectorAll(
                    '.edit-part-list input[type="checkbox"]'
                )
                .forEach((checkbox) => {

                    checkbox.checked =
                        wordData.partsOfSpeech.includes(
                            checkbox.value
                        );
                });

            editModal.classList.add(
                "active"
            );

            dropdown.classList.remove(
                "active"
            );
        }
    );

    deleteButton.addEventListener(
        "click",
        () => {

            const confirmed = confirm(
                `"${wordData.word}" 단어를 삭제할까요?`
            );

            if (!confirmed) {
                return;
            }

            savedWords.splice(index, 1);

            saveWordsToStorage();

            renderSavedWords();
        }
    );

    speakButton.addEventListener(
        "click",
        (event) => {

            event.stopPropagation();

            const utterance =
                new SpeechSynthesisUtterance(
                    wordData.word
                );

            utterance.lang = "en-US";

            utterance.rate = 0.9;

            speechSynthesis.speak(
                utterance
            );
        }
    );

    document.addEventListener(
        "click",
        () => {

            dropdown.classList.remove(
                "active"
            );
        }
    );

    return wordDiv;
}


function renderSavedWords() {

    wordList.innerHTML = "";

    savedWords.forEach(
        (wordData, index) => {

            if (!shouldShowWord(wordData)) {
                return;
            }

            wordList.appendChild(
                createSavedWordCard(
                    wordData,
                    index
                )
            );
        }
    );
}


function saveWordsToStorage() {

    localStorage.setItem(
        "savedWords",
        JSON.stringify(savedWords)
    );
}


function loadWordsFromStorage() {

    const storedWords =
        localStorage.getItem(
            "savedWords"
        );

    if (!storedWords) {
        return;
    }

    const parsedWords =
        JSON.parse(storedWords);

    savedWords.push(...parsedWords);

    renderSavedWords();
}


saveEditButton.addEventListener(
    "click",
    () => {

        if (editingIndex === null) {
            return;
        }

        const checkedParts = [];

        document
            .querySelectorAll(
                '.edit-part-list input[type="checkbox"]'
            )
            .forEach((checkbox) => {

                if (checkbox.checked) {

                    checkedParts.push(
                        checkbox.value
                    );
                }
            });

        savedWords[editingIndex] = {

            word:
                editWordInput.value
                    .trim()
                    .toLowerCase(),

            meaning:
                editMeaningInput.value
                    .trim(),

            partsOfSpeech:
                checkedParts
        };

        saveWordsToStorage();

        renderSavedWords();

        editModal.classList.remove(
            "active"
        );

        editingIndex = null;
    }
);


cancelEditButton.addEventListener(
    "click",
    () => {

        editModal.classList.remove(
            "active"
        );

        editingIndex = null;
    }
);


function parseWords(input) {

    return input
        .split(/[,\n]+/)
        .map((word) => word.trim())
        .filter((word) => word !== "");
}


async function fetchWord(word) {

    const response = await fetch(
        "/generate",
        {

            method: "POST",

            headers: {
                "Content-Type":
                    "application/json"
            },

            body: JSON.stringify({
                word: word
            })
        }
    );

    return response.json();
}

function formatBatchResult(
    word,
    data
) {

    if (data.success) {
        return data.result;
    }

    return `${word}: ${data.result.replace(
        /\n+/g,
        " "
    )}`;
}

function getExportRows() {

    return savedWords.map((wordData) => ({

        word: wordData.word,

        meaning: wordData.meaning,

        partsOfSpeech:
            wordData.partsOfSpeech || []
    }));
}


function downloadBlob(blob, filename) {

    const url =
        URL.createObjectURL(blob);

    const link =
        document.createElement("a");

    link.href = url;

    link.download = filename;

    document.body.appendChild(link);

    link.click();

    link.remove();

    URL.revokeObjectURL(url);
}


async function downloadPdf() {

    const rows = getExportRows();

    if (rows.length === 0) {

        addBotMessage(
            "다운로드할 단어가 없습니다."
        );

        return;
    }

    try {

        const response =
            await fetch("/export/pdf", {

                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({
                    words: rows
                })
            });

        const blob =
            await response.blob();

        downloadBlob(
            blob,
            "ai-vocabulary.pdf"
        );

    } catch (error) {

        addBotMessage(
            "PDF 생성 중 오류가 발생했습니다."
        );

        console.error(error);
    }
}


async function downloadXlsx() {

    const rows = getExportRows();

    if (rows.length === 0) {

        addBotMessage(
            "다운로드할 단어가 없습니다."
        );

        return;
    }

    try {

        const response =
            await fetch("/export/xlsx", {

                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({
                    words: rows
                })
            });

        const blob =
            await response.blob();

        downloadBlob(
            blob,
            "ai-vocabulary.xlsx"
        );

    } catch (error) {

        addBotMessage(
            "XLSX 생성 중 오류가 발생했습니다."
        );

        console.error(error);
    }
}

async function submitWords(input) {

    const rawMessage = input
        .trim()
        .toLowerCase();

    if (rawMessage === "") {
        return;
    }

    const words =
        parseWords(rawMessage);

    if (words.length === 0) {
        return;
    }

    addUserMessage(rawMessage);

    wordInput.value = "";

    const resultLines = [];

    const suggestions = [];

    try {

        for (const word of words) {

            const data =
                await fetchWord(word);

            resultLines.push(
                formatBatchResult(
                    word,
                    data
                )
            );

            if (data.success) {

                const wasAdded =
                    addSavedWord(
                        data.word,
                        data.meaning,
                        data.partsOfSpeech || []
                    );

                if (!wasAdded) {

                    addBotMessage(
                        `"${data.word}" 단어는 이미 저장되어 있습니다.`
                    );

                    continue;
                }

            }

            (data.suggestions || [])
                .forEach((suggestion) => {

                    if (
                        !suggestions.includes(
                            suggestion
                        )
                    ) {

                        suggestions.push(
                            suggestion
                        );
                    }
                });
        }

        addBotMessage(
            resultLines.join("\n"),
            suggestions
        );

    } catch (error) {

        addBotMessage(
            "서버와 통신하는 중 오류가 발생했습니다."
        );

        console.error(error);
    }
}


sendButton.addEventListener(
    "click",
    async () => {

        await submitWords(
            wordInput.value
        );
    }
);


wordInput.addEventListener(
    "keydown",
    (event) => {

        if (
            event.key === "Enter" &&
            !event.shiftKey
        ) {

            event.preventDefault();

            sendButton.click();
        }
    }
);


categoryTabs.forEach((tab) => {

    tab.addEventListener(
        "click",
        () => {

            activeCategory =
                tab.dataset.category;

            categoryTabs.forEach(
                (categoryTab) => {

                    categoryTab.classList.toggle(
                        "active",
                        categoryTab === tab
                    );
                }
            );

            renderSavedWords();
        }
    );
});


pdfDownloadButton.addEventListener(
    "click",
    downloadPdf
);

xlsxDownloadButton.addEventListener(
    "click",
    downloadXlsx
);


swapButton.addEventListener(
    "click",
    () => {

        content.classList.toggle(
            "active"
        );
    }
);

clearWordsButton.addEventListener(
    "click",
    () => {
        const confirmed = confirm(
            "저장된 단어를 모두 삭제할까요?"
        );

        if (!confirmed) {
            return;
        }
        savedWords.length = 0;
        saveWordsToStorage();
        renderSavedWords();
        addBotMessage(
            "모든 단어가 삭제되었습니다."
        );
    }
);

loadWordsFromStorage();