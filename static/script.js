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


sendButton.addEventListener("click", () => {

    const message = wordInput.value.trim();

    if (message === "") {
        return;
    }

    addUserMessage(message);

    wordInput.value = "";
});

wordInput.addEventListener("keydown", (event) => {

    if (event.key === "Enter" && !event.shiftKey) {

        event.preventDefault();

        sendButton.click();
    }

});