const sendButton = document.getElementById("sendButton");

const wordInput = document.getElementById("wordInput");

const chatArea = document.getElementById("chatArea");


function addUserMessage(message) {

    const messageDiv = document.createElement("div");

    messageDiv.classList.add("user-message");

    messageDiv.innerHTML = message.replace(/\n/g, "<br>");

    chatArea.appendChild(messageDiv);

    chatArea.scrollTop = chatArea.scrollHeight;
}


function addBotMessage(message) {

    const messageDiv = document.createElement("div");

    messageDiv.classList.add("bot-message");

    messageDiv.innerHTML = message.replace(/\n/g, "<br>");

    chatArea.appendChild(messageDiv);

    chatArea.scrollTop = chatArea.scrollHeight;
}


sendButton.addEventListener("click", async () => {

    const message = wordInput.value.trim();

    if (message === "") {
        return;
    }

    addUserMessage(message);

    wordInput.value = "";

    const response = await fetch("/generate", {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({
            word: message
        })
    });

    const data = await response.json();

    addBotMessage(data.result);

});


wordInput.addEventListener("keydown", (event) => {

    if (event.key === "Enter" && !event.shiftKey) {

        event.preventDefault();

        sendButton.click();
    }

});