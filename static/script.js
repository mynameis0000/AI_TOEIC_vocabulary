const sendButton = document.getElementById("sendButton");

const wordInput = document.getElementById("wordInput");

const chatArea = document.getElementById("chatArea");

const wordList = document.getElementById("wordList");

const categoryTabs = document.querySelectorAll(".category-tab");

const pdfDownloadButton = document.getElementById("pdfDownloadButton");

const xlsxDownloadButton = document.getElementById("xlsxDownloadButton");

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

    const messageDiv = document.createElement("div");

    messageDiv.classList.add("user-message");

    messageDiv.innerHTML = message.replace(/\n/g, "<br>");

    chatArea.appendChild(messageDiv);

    chatArea.scrollTop = chatArea.scrollHeight;
}


function addBotMessage(message, suggestions = []) {

    const messageDiv = document.createElement("div");

    messageDiv.classList.add("bot-message");

    message.split("\n").forEach((line, index) => {
        if (index > 0) {
            messageDiv.appendChild(document.createElement("br"));
        }

        messageDiv.appendChild(document.createTextNode(line));
    });

    if (suggestions.length > 0) {
        const suggestionLabel = document.createElement("div");

        suggestionLabel.classList.add("suggestion-label");
        suggestionLabel.textContent = "추천 검색어";

        const suggestionList = document.createElement("div");

        suggestionList.classList.add("suggestion-list");

        suggestions.forEach((suggestion) => {
            const suggestionButton = document.createElement("button");

            suggestionButton.classList.add("suggestion-chip");
            suggestionButton.type = "button";
            suggestionButton.textContent = suggestion;

            suggestionButton.addEventListener("click", () => {
                submitWords(suggestion);
            });

            suggestionList.appendChild(suggestionButton);
        });

        messageDiv.appendChild(suggestionLabel);
        messageDiv.appendChild(suggestionList);
    }

    chatArea.appendChild(messageDiv);

    chatArea.scrollTop = chatArea.scrollHeight;
}

function addSavedWord(word, meaning, partsOfSpeech = []) {

    savedWords.push({
        word: word,
        meaning: meaning,
        partsOfSpeech: partsOfSpeech
    });

    renderSavedWords();
}

function shouldShowWord(wordData) {

    return (
        activeCategory === "all" ||
        wordData.partsOfSpeech.includes(activeCategory)
    );
}

function createSavedWordCard(wordData) {

    const wordDiv = document.createElement("div");

    wordDiv.classList.add("saved-word");
    wordDiv.dataset.partsOfSpeech = wordData.partsOfSpeech.join(",");

    wordDiv.innerHTML = `
    
        <div class="english">
            ${wordData.word}
        </div>

        <div class="korean">
            ${wordData.meaning}
        </div>
    
    `;

    return wordDiv;
}

function renderSavedWords() {

    wordList.innerHTML = "";

    savedWords
        .filter(shouldShowWord)
        .forEach((wordData) => {
            wordList.appendChild(createSavedWordCard(wordData));
        });
}

function getExportRows() {

    return savedWords.map((wordData) => ({
        word: wordData.word,
        meaning: wordData.meaning,
        partsOfSpeech: wordData.partsOfSpeech
    }));
}

function getPartOfSpeechText(partsOfSpeech) {

    return partsOfSpeech
        .map((partOfSpeech) => partOfSpeechLabels[partOfSpeech] || partOfSpeech)
        .join(", ");
}

function escapeHtml(value) {

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function downloadBlob(blob, filename) {

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");

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

        addBotMessage("다운로드할 단어가 없습니다.");

        return;
    }

    try {

        const response = await fetch("/export/pdf", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                words: rows
            })
        });

        const blob = await response.blob();

        downloadBlob(blob, "ai-vocabulary.pdf");

    } catch (error) {

        addBotMessage("PDF 파일을 만드는 중 오류가 발생했습니다.");

        console.error(error);
    }
}

async function downloadXlsx() {

    const rows = getExportRows();

    if (rows.length === 0) {
        addBotMessage("다운로드할 단어가 없습니다.");
        return;
    }

    try {
        const response = await fetch("/export/xlsx", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                words: rows
            })
        });

        const blob = await response.blob();

        downloadBlob(blob, "ai-vocabulary.xlsx");
    } catch (error) {
        addBotMessage("XLSX 파일을 만드는 중 오류가 발생했습니다.");
        console.error(error);
    }
}

function parseWords(input) {

    return input
        .split(/[,\n]+/)
        .map((word) => word.trim())
        .filter((word) => word !== "");
}

async function fetchWord(word) {

    const response = await fetch("/generate", {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({
            word: word
        })
    });

    return response.json();
}

function formatBatchResult(word, data) {

    if (data.success) {
        return data.result;
    }

    return `${word}: ${data.result.replace(/\n+/g, " ")}`;
}

async function submitWords(input) {

    const rawMessage = input
    .trim()
    .toLowerCase();

    if (rawMessage === "") {
        return;
    }

    const words = parseWords(rawMessage);

    if (words.length === 0) {
        return;
    }

    addUserMessage(rawMessage);

    wordInput.value = "";

    const resultLines = [];
    const suggestions = [];

    try {
        for (const word of words) {
            const data = await fetchWord(word);

            resultLines.push(formatBatchResult(word, data));

            if (data.success) {
                addSavedWord(data.word, data.meaning, data.partsOfSpeech || []);
            }

            (data.suggestions || []).forEach((suggestion) => {
                if (!suggestions.includes(suggestion)) {
                    suggestions.push(suggestion);
                }
            });
        }

        addBotMessage(resultLines.join("\n"), suggestions);
    } catch (error) {
        addBotMessage("서버와 통신하는 중 오류가 발생했습니다.");
        console.error(error);
    }

}

sendButton.addEventListener("click", async () => {

    await submitWords(wordInput.value);

});


wordInput.addEventListener("keydown", (event) => {

    if (event.key === "Enter" && !event.shiftKey) {

        event.preventDefault();

        sendButton.click();
    }

});

const swapButton = document.getElementById("swapButton");

const content = document.querySelector(".content");

categoryTabs.forEach((tab) => {
    tab.addEventListener("click", () => {
        activeCategory = tab.dataset.category;

        categoryTabs.forEach((categoryTab) => {
            categoryTab.classList.toggle("active", categoryTab === tab);
        });

        renderSavedWords();
    });
});

pdfDownloadButton.addEventListener("click", downloadPdf);

xlsxDownloadButton.addEventListener("click", downloadXlsx);

swapButton.addEventListener("click", () => {

    content.classList.toggle("active");

});
