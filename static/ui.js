// // ui.js

// /**
//  * 1. 단어 카드 생성 함수
//  * 로직을 직접 수행하지 않고, 전달받은 콜백 함수(onEdit, onDelete)를 호출합니다.
//  */
// export function createSavedWordCard(wordData, index, { onEdit, onDelete }) {
//     const wordDiv = document.createElement("div");
//     wordDiv.classList.add("saved-word");
//     wordDiv.innerHTML = `
//         <div class="card-menu-wrapper">
//             <button class="card-menu-button">⋮</button>
//             <div class="card-menu-dropdown">
//                 <button class="edit-word-button">수정</button>
//                 <button class="delete-word-button">삭제</button>
//             </div>
//         </div>
//         <div class="english">${wordData.word}</div>
//         <div class="korean">${wordData.meaning}</div>
//         <div class="speak-button">🔊</div>
//     `;

//     // 이벤트 리스너 연결
//     const menuButton = wordDiv.querySelector(".card-menu-button");
//     const dropdown = wordDiv.querySelector(".card-menu-dropdown");

//     menuButton.addEventListener("click", (e) => {
//         e.stopPropagation();
//         // 다른 메뉴 닫기 (UI 로직)
//         document.querySelectorAll(".card-menu-dropdown").forEach(m => {
//             if (m !== dropdown) m.classList.remove("active");
//         });
//         dropdown.classList.toggle("active");
//     });

//     wordDiv.querySelector(".edit-word-button").addEventListener("click", () => {
//         onEdit(index);
//         dropdown.classList.remove("active");
//     });

//     wordDiv.querySelector(".delete-word-button").addEventListener("click", () => {
//         onDelete(index);
//     });

//     wordDiv.querySelector(".speak-button").addEventListener("click", (e) => {
//         e.stopPropagation();
//         const utterance = new SpeechSynthesisUtterance(wordData.word);
//         utterance.lang = "en-US";
//         utterance.rate = 0.9;
//         speechSynthesis.speak(utterance);
//     });

//     // 외부 클릭 시 메뉴 닫기
//     document.addEventListener("click", () => dropdown.classList.remove("active"));

//     return wordDiv;
// }

// /**
//  * 2. 전체 단어 리스트 렌더링 함수
//  */
// export function renderSavedWords(container, savedWords, activeCategory, onEdit, onDelete) {
//     container.innerHTML = "";
    
//     // 카테고리 필터링 로직
//     const filteredWords = savedWords.filter(word => 
//         activeCategory === "all" || word.partsOfSpeech.includes(activeCategory)
//     );

//     filteredWords.forEach((wordData, index) => {
//         const card = createSavedWordCard(wordData, index, { onEdit, onDelete });
//         container.appendChild(card);
//     });
// }

// /**
//  * 3. 사용자 메시지 추가
//  */
// export function addUserMessage(message, chatArea) {
//     const messageDiv = document.createElement("div");
//     messageDiv.classList.add("user-message");
//     messageDiv.innerHTML = message.replace(/\n/g, "<br>");
//     chatArea.appendChild(messageDiv);
//     chatArea.scrollTop = chatArea.scrollHeight;
// }

// /**
//  * 4. 봇 메시지 및 추천 검색어 추가
//  */
// export function addBotMessage(message, chatArea, suggestions = [], onSuggestionClick) {
//     const messageDiv = document.createElement("div");
//     messageDiv.classList.add("bot-message");

//     // 메시지 줄바꿈 처리
//     message.split("\n").forEach((line, index) => {
//         if (index > 0) messageDiv.appendChild(document.createElement("br"));
//         messageDiv.appendChild(document.createTextNode(line));
//     });

//     // 추천 검색어 버튼 추가
//     if (suggestions.length > 0) {
//         const wrapper = document.createElement("div");
//         wrapper.innerHTML = '<div class="suggestion-label">추천 검색어</div>';
        
//         const list = document.createElement("div");
//         list.classList.add("suggestion-list");

//         suggestions.forEach(text => {
//             const btn = document.createElement("button");
//             btn.className = "suggestion-chip";
//             btn.textContent = text;
//             btn.addEventListener("click", () => onSuggestionClick(text));
//             list.appendChild(btn);
//         });

//         wrapper.appendChild(list);
//         messageDiv.appendChild(wrapper);
//     }

//     chatArea.appendChild(messageDiv);
//     chatArea.scrollTop = chatArea.scrollHeight;
// }


// ui.js

/**
 * 1. 단어 카드 생성 함수
 */
export function createSavedWordCard(wordData, index, { onEdit, onDelete }) {
  const wordDiv = document.createElement("div");
  wordDiv.classList.add("saved-word");
  
  wordDiv.innerHTML = `
    <div class="card-menu-wrapper">
        <button class="card-menu-button">⋮</button>
        <div class="card-menu-dropdown">
            <button class="edit-word-button">수정</button>
            <button class="delete-word-button">삭제</button>
        </div>
    </div>
    <div class="english">${wordData.word}</div>
    <div class="korean">${wordData.meaning}</div>
    <div class="speak-button">🔊</div>
  `;

  const menuButton = wordDiv.querySelector(".card-menu-button");
  const dropdown = wordDiv.querySelector(".card-menu-dropdown");

  menuButton.addEventListener("click", (e) => {
    e.stopPropagation();
    document.querySelectorAll(".card-menu-dropdown").forEach((m) => {
      if (m !== dropdown) m.classList.remove("active");
    });
    dropdown.classList.toggle("active");
  });

  wordDiv.querySelector(".edit-word-button").addEventListener("click", () => {
    onEdit(index);
    dropdown.classList.remove("active");
  });

  wordDiv.querySelector(".delete-word-button").addEventListener("click", () => {
    onDelete(index);
  });

  wordDiv.querySelector(".speak-button").addEventListener("click", (e) => {
    e.stopPropagation();
    const utterance = new SpeechSynthesisUtterance(wordData.word);
    utterance.lang = "en-US";
    utterance.rate = 0.9;
    window.speechSynthesis.speak(utterance);
  });

  document.addEventListener("click", () => dropdown.classList.remove("active"));

  return wordDiv;
}

/**
 * 2. 전체 단어 리스트 렌더링 함수
 */
export function renderSavedWords(container, savedWords, activeCategory, onEdit, onDelete) {
  if (!container) return;
  container.innerHTML = "";

  const filteredWords = savedWords.filter(
    (word) => activeCategory === "all" || (word.partsOfSpeech && word.partsOfSpeech.includes(activeCategory))
  );

  filteredWords.forEach((wordData, index) => {
    const card = createSavedWordCard(wordData, index, { onEdit, onDelete });
    container.appendChild(card);
  });
}

/**
 * 3. 사용자 메시지 추가
 */
export function addUserMessage(message, chatArea) {
  if (!chatArea) return;
  
  const messageDiv = document.createElement("div");
  messageDiv.classList.add("user-message");
  messageDiv.innerHTML = message.replace(/\n/g, "<br>"); 
  
  chatArea.appendChild(messageDiv);
  chatArea.scrollTop = chatArea.scrollHeight;
}

/**
 * 4. 봇 메시지 및 추천 검색어 추가
 */
export function addBotMessage(message, chatArea, suggestions = [], onSuggestionClick) {
  if (!chatArea) return;

  const messageDiv = document.createElement("div");
  messageDiv.classList.add("bot-message");

  // 메시지 줄바꿈 처리
  message.split("\n").forEach((line, index) => {
    if (index > 0) messageDiv.appendChild(document.createElement("br"));
    messageDiv.appendChild(document.createTextNode(line));
  });

  // 추천 검색어 버튼 추가
  if (suggestions && suggestions.length > 0) {
    const wrapper = document.createElement("div");
    wrapper.innerHTML = '<div class="suggestion-label">추천 검색어</div>';

    const list = document.createElement("div");
    list.classList.add("suggestion-list");

    suggestions.forEach((text) => {
      const btn = document.createElement("button");
      btn.className = "suggestion-chip";
      btn.type = "button";
      btn.textContent = text;
      
      if (onSuggestionClick) {
        btn.addEventListener("click", () => onSuggestionClick(text));
      }
      list.appendChild(btn);
    });

    wrapper.appendChild(list);
    messageDiv.appendChild(wrapper);
  }

  chatArea.appendChild(messageDiv);
  chatArea.scrollTop = chatArea.scrollHeight;
}