

// // main.js
// import { fetchWord, exportData } from "./api.js";
// import { 
//     createSavedWordCard, 
//     renderSavedWords, 
//     addUserMessage, 
//     addBotMessage 
// } from "./ui.js";

// // 1. 상태 관리 및 DOM 요소
// let savedWords = JSON.parse(localStorage.getItem("savedWords") || "[]");
// let activeCategory = "all";
// let editingIndex = null;

// const wordInput = document.getElementById("wordInput");
// const sendButton = document.getElementById("sendButton");
// const chatArea = document.getElementById("chatArea");
// const wordList = document.getElementById("wordList");
// const categoryTabs = document.querySelectorAll(".category-tab");
// const editModal = document.getElementById("editModal");
// const editWordInput = document.getElementById("editWordInput");
// const editMeaningInput = document.getElementById("editMeaningInput");
// const saveEditButton = document.getElementById("saveEditButton");
// const cancelEditButton = document.getElementById("cancelEditButton");
// const pdfDownloadButton = document.getElementById("pdfDownloadButton");
// const xlsxDownloadButton = document.getElementById("xlsxDownloadButton");
// const clearWordsButton = document.getElementById("clearWordsButton");
// const swapButton = document.getElementById("swapButton");
// const content = document.querySelector(".content");

// // 2. 핵심 유틸리티 함수
// function saveWordsToStorage() { localStorage.setItem("savedWords", JSON.stringify(savedWords)); }
// function getExportRows() { return savedWords.map(w => ({ word: w.word, meaning: w.meaning, partsOfSpeech: w.partsOfSpeech || [] })); }

// function downloadBlob(blob, filename) {
//     const url = URL.createObjectURL(blob);
//     const a = document.createElement("a");
//     a.href = url; a.download = filename;
//     document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
// }

// // 3. UI 업데이트
// function updateUI() {
//     renderSavedWords(wordList, savedWords, activeCategory, 
//         (index) => { // onEdit
//             editingIndex = index;
//             editWordInput.value = savedWords[index].word;
//             editMeaningInput.value = savedWords[index].meaning;
//             // 체크박스 복구 로직
//             document.querySelectorAll('.edit-part-list input[type="checkbox"]').forEach(cb => {
//                 cb.checked = savedWords[index].partsOfSpeech.includes(cb.value);
//             });
//             editModal.classList.add("active");
//         },
//         (index) => { // onDelete
//             if(confirm(`"${savedWords[index].word}"을 삭제할까요?`)) {
//                 savedWords.splice(index, 1);
//                 saveWordsToStorage();
//                 updateUI();
//             }
//         }
//     );
// }

// // 4. 로직 및 이벤트

// export function parseWords(input) {

//     return input
//         .split(/[,\n]+/)
//         .map((word) => word.trim())
//         .filter((word) => word !== "");
// }

// function formatBatchResult(
//     word,
//     data
// ) {

//     if (data.success) {
//         return data.result;
//     }

//     return `${word}: ${data.result.replace(
//         /\n+/g,
//         " "
//     )}`;
// }

// function addSavedWord(
//     word,
//     meaning,
//     partsOfSpeech = []
// ) {

//     const alreadyExists =
//         savedWords.some(
//             (savedWord) =>

//                 savedWord.word
//                     .trim()
//                     .toLowerCase()

//                 ===

//                 word
//                     .trim()
//                     .toLowerCase()
//         );

//     if (alreadyExists) {

//         return false;
//     }

//     savedWords.push({

//         word: word,

//         meaning: meaning,

//         partsOfSpeech: partsOfSpeech
//     });

//     renderSavedWords();

//     saveWordsToStorage();

//     return true;
// }

// async function submitWords(input) {

//     const rawMessage = input
//         .trim()
//         .toLowerCase();

//     if (rawMessage === "") {
//         return;
//     }

//     const words = parseWords(rawMessage);

//     if (words.length === 0) {
//         return;
//     }

//     addUserMessage(rawMessage);

//     wordInput.value = "";

//     const resultLines = [];
//     const suggestions = [];

//     try {

//         for (const word of words) {

//             const data = await fetchWord(word);

//             if (data.success) {

//                 const wasAdded = addSavedWord(
//                     data.word,
//                     data.meaning,
//                     data.partsOfSpeech || []
//                 );

//                 // 이미 저장된 단어인 경우
//                 if (!wasAdded) {
//                     resultLines.push(
//                         `"${data.word}" 단어는 이미 저장되어 있습니다.`
//                     );
//                     continue;
//                 }
//             }

//             // 새로 저장된 단어 또는 조회 결과만 출력
//             resultLines.push(
//                 formatBatchResult(
//                     word,
//                     data
//                 )
//             );

//             (data.suggestions || []).forEach((suggestion) => {

//                 if (!suggestions.includes(suggestion)) {
//                     suggestions.push(suggestion);
//                 }

//             });
//         }

//         if (resultLines.length > 0) {
//             addBotMessage(
//                 resultLines.join("\n"),
//                 suggestions
//             );
//         }

//     } catch (error) {

//         addBotMessage(
//             "서버와 통신하는 중 오류가 발생했습니다."
//         );

//         console.error(error);
//     }
// }


// // 이벤트 리스너들
// sendButton.addEventListener("click", () => submitWords(wordInput.value));
// wordInput.addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendButton.click(); } });

// categoryTabs.forEach(tab => tab.addEventListener("click", () => {
//     activeCategory = tab.dataset.category;
//     categoryTabs.forEach(t => t.classList.toggle("active", t === tab));
//     updateUI();
// }));

// saveEditButton.addEventListener("click", () => {
//     if (editingIndex === null) return;
//     const checked = Array.from(document.querySelectorAll('.edit-part-list input:checked')).map(cb => cb.value);
//     savedWords[editingIndex] = { word: editWordInput.value.trim().toLowerCase(), meaning: editMeaningInput.value.trim(), partsOfSpeech: checked };
//     saveWordsToStorage();
//     updateUI();
//     editModal.classList.remove("active");
// });

// cancelEditButton.addEventListener("click", () => editModal.classList.remove("active"));
// pdfDownloadButton.addEventListener("click", async () => {
//     const blob = await exportData("pdf", getExportRows());
//     downloadBlob(blob, "ai-vocabulary.pdf");
// });
// xlsxDownloadButton.addEventListener("click", async () => {
//     const blob = await exportData("xlsx", getExportRows());
//     downloadBlob(blob, "ai-vocabulary.xlsx");
// });
// swapButton.addEventListener("click", () => content.classList.toggle("active"));
// clearWordsButton.addEventListener("click", () => {
//     if(confirm("모두 삭제할까요?")) { savedWords = []; saveWordsToStorage(); updateUI(); }
// });

// // 시작
// updateUI();


// main.js
import { fetchWord, exportData } from "./api.js";
import {
  renderSavedWords,
  addUserMessage,
  addBotMessage,
} from "./ui.js";

// 1. 상태 관리 및 DOM 요소
let savedWords = JSON.parse(localStorage.getItem("savedWords") || "[]");
let activeCategory = "all";
let editingIndex = null;

const wordInput = document.getElementById("wordInput");
const sendButton = document.getElementById("sendButton");
const chatArea = document.getElementById("chatArea");
const wordList = document.getElementById("wordList");
const categoryTabs = document.querySelectorAll(".category-tab");
const editModal = document.getElementById("editModal");
const editWordInput = document.getElementById("editWordInput");
const editMeaningInput = document.getElementById("editMeaningInput");
const saveEditButton = document.getElementById("saveEditButton");
const cancelEditButton = document.getElementById("cancelEditButton");
const pdfDownloadButton = document.getElementById("pdfDownloadButton");
const xlsxDownloadButton = document.getElementById("xlsxDownloadButton");
const clearWordsButton = document.getElementById("clearWordsButton");
const swapButton = document.getElementById("swapButton");
const content = document.querySelector(".content");

// 2. 핵심 유틸리티 함수
function saveWordsToStorage() {
  localStorage.setItem("savedWords", JSON.stringify(savedWords));
}

export function parseWords(input) {
  return input
    .split(/[,\n]+/)
    .map((word) => word.trim())
    .filter((word) => word !== "");
}

function formatBatchResult(word, data) {
  if (data.success) {
    return data.result;
  }
  return `${word}: ${data.result.replace(/\n+/g, " ")}`;
}

function getExportRows() {
  return savedWords.map((w) => ({
    word: w.word,
    meaning: w.meaning,
    partsOfSpeech: w.partsOfSpeech || [],
  }));
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

// 3. UI 업데이트
function updateUI() {
  renderSavedWords(
    wordList,
    savedWords,
    activeCategory,
    (index) => {
      // onEdit
      editingIndex = index;
      editWordInput.value = savedWords[index].word;
      editMeaningInput.value = savedWords[index].meaning;

      // 체크박스 복구 로직
      document
        .querySelectorAll('.edit-part-list input[type="checkbox"]')
        .forEach((cb) => {
          cb.checked = savedWords[index].partsOfSpeech.includes(cb.value);
        });
      editModal.classList.add("active");
    },
    (index) => {
      // onDelete
      if (confirm(`"${savedWords[index].word}"을 삭제할까요?`)) {
        savedWords.splice(index, 1);
        saveWordsToStorage();
        updateUI();
      }
    }
  );
}

// 4. 로직 및 이벤트
function addSavedWord(word, meaning, partsOfSpeech = []) {
  const alreadyExists = savedWords.some(
    (savedWord) =>
      savedWord.word.trim().toLowerCase() === word.trim().toLowerCase()
  );

  if (alreadyExists) {
    return false;
  }

  savedWords.push({
    word,
    meaning,
    partsOfSpeech,
  });

  saveWordsToStorage();
  updateUI();

  return true;
}

async function submitWords(input) {
  const rawMessage = input.trim().toLowerCase();

  if (rawMessage === "") {
    return;
  }

  const words = parseWords(rawMessage);

  if (words.length === 0) {
    return;
  }

  addUserMessage(rawMessage, chatArea);
  wordInput.value = "";

  const resultLines = [];
  const suggestions = [];

  try {
    for (const word of words) {
      const data = await fetchWord(word);

      if (data.success) {
        const wasAdded = addSavedWord(
          data.word,
          data.meaning,
          data.partsOfSpeech || []
        );

        if (!wasAdded) {
          resultLines.push(`"${data.word}" 단어는 이미 저장되어 있습니다.`);
          continue;
        }
      }

      resultLines.push(formatBatchResult(word, data));

      (data.suggestions || []).forEach((suggestion) => {
        if (!suggestions.includes(suggestion)) {
          suggestions.push(suggestion);
        }
      });
    }

    if (resultLines.length > 0) {
      // 세 번째 인자로 chatArea, 네 번째 인자로 클릭 핸들러인 submitWords를 전달합니다.
      addBotMessage(resultLines.join("\n"), chatArea, suggestions, submitWords);
    }
  } catch (error) {
    addBotMessage("서버와 통신하는 중 오류가 발생했습니다.", chatArea);
    console.error(error);
  }
}

// 이벤트 리스너들
sendButton.addEventListener("click", () => submitWords(wordInput.value));

wordInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendButton.click();
  }
});

categoryTabs.forEach((tab) =>
  tab.addEventListener("click", () => {
    activeCategory = tab.dataset.category;
    categoryTabs.forEach((t) => t.classList.toggle("active", t === tab));
    updateUI();
  })
);

saveEditButton.addEventListener("click", () => {
  if (editingIndex === null) return;

  const checked = Array.from(
    document.querySelectorAll(".edit-part-list input:checked")
  ).map((cb) => cb.value);

  savedWords[editingIndex] = {
    word: editWordInput.value.trim().toLowerCase(),
    meaning: editMeaningInput.value.trim(),
    partsOfSpeech: checked,
  };

  saveWordsToStorage();
  updateUI();
  editModal.classList.remove("active");
});

cancelEditButton.addEventListener("click", () =>
  editModal.classList.remove("active")
);

pdfDownloadButton.addEventListener("click", async () => {
  const rows = getExportRows();
  if (rows.length === 0) {
    addBotMessage("다운로드할 단어가 없습니다.", chatArea);
    return;
  }
  try {
    const blob = await exportData("pdf", rows);
    downloadBlob(blob, "ai-vocabulary.pdf");
  } catch (error) {
    addBotMessage("PDF 생성 중 오류가 발생했습니다.", chatArea);
  }
});

xlsxDownloadButton.addEventListener("click", async () => {
  const rows = getExportRows();
  if (rows.length === 0) {
    addBotMessage("다운로드할 단어가 없습니다.", chatArea);
    return;
  }
  try {
    const blob = await exportData("xlsx", rows);
    downloadBlob(blob, "ai-vocabulary.xlsx");
  } catch (error) {
    addBotMessage("XLSX 생성 중 오류가 발생했습니다.", chatArea);
  }
});

swapButton.addEventListener("click", () => content.classList.toggle("active"));

clearWordsButton.addEventListener("click", () => {
  if (confirm("저장된 단어를 모두 삭제할까요?")) {
    savedWords = [];
    saveWordsToStorage();
    updateUI();
    addBotMessage("모든 단어가 삭제되었습니다.", chatArea);
  }
});

// 시작 (초기 UI 렌더링)
updateUI();