const MessageRecipient = {
    GENERATOR: 1,
    SUGGESTER: 2,
    SUMMARIZER: 3,
};
let Default_Suggestion_limit = 5;
let Default_Generation_limit = 10;
document.addEventListener("DOMContentLoaded", function () {
    let Suggestion_limit = Default_Suggestion_limit;
    let Generation_limit = Default_Generation_limit;

    const SummaryRequesterButton = document.getElementById(
        "SummaryRequesterButton"
    );
    const messageInput = document.getElementById("messageInput");
    const div = document.getElementById("suggest_box_div");
    const settings = document.getElementById("settings");

    function updateSettings() {
        Suggestion_limit = parseInt(
            document.getElementById("no_of_samples").value
        );
        Generation_limit = parseInt(
            document.getElementById("no_of_gen_toks").value
        );
    }

    document
        .getElementById("no_of_samples")
        .addEventListener("input", updateSettings);
    document
        .getElementById("no_of_gen_toks")
        .addEventListener("input", updateSettings);

    const socket = new WebSocket("ws://localhost:8000"); // WebSocket server address

    socket.onopen = function (event) {
        console.log("WebSocket connection opened:", event);
    };

    socket.onmessage = function (event) {
        data = JSON.parse(event.data);
        console.log("Received message:", data);
        if (data["from_generator"]) {
            document.getElementById("messageInput").value += data["message"];
        }
        if (data["from_suggester"]) {
            console.log("Suggested text:", data["message"]);
            show_suggestions(data["message"]);
        }
    };

    socket.onclose = function (event) {
        console.log("WebSocket connection closed:", event);
    };

    socket.onerror = function (e) {
        alert(e.msg);
    };

    function suggestText(
        message,
        no_of_samples,
        recipient,
        generation_count = 1
    ) {
        var data = JSON.stringify({
            message: message,
            no_of_samples: no_of_samples,
            recipient: recipient,
            generation_count: generation_count,
        });
        socket.send(data);
    }

    function add_suggestion_to_prompt(id) {
        let element = document.getElementById(id);
        messageInput.value += element.innerHTML + " ";
        console.log(element.innerHTML + " added to prompt");
        let recipient = MessageRecipient.SUGGESTER;
        suggestText(messageInput.value.slice(0, -1), Suggestion_limit, recipient);
    }

    // Handle button click to send a message
    SummaryRequesterButton.addEventListener("click", function () {
        const fileInput = document.getElementById("fileInput");
        const file = fileInput.files[0];

        if (!file) {
            return;
        }

        var reader = new FileReader();

        reader.loadend = function () {};

        reader.onload = function (e) {
            var rawData = e.target.result;

            var sendData = {
                recipient: MessageRecipient.SUMMARIZER,
                file: rawData,
            }
            console.log(
                "Sending message:\n",
                sendData,
                "\n\nStringified to:\n",
                JSON.stringify(sendData)
            );

            socket.send(JSON.stringify(sendData));

            console.log("the File has been transferred.");
        };

        reader.readAsArrayBuffer(file);
    });

    // Suggest text
    messageInput.addEventListener("keyup", function (event) {
        if (event.key === "\\") {
            //remove last Character
            var prompt = messageInput.value.slice(0, -1);
            messageInput.value = prompt;
            let recipient = MessageRecipient.GENERATOR;
            suggestText(prompt, 1, recipient, Generation_limit);
        }
        if (event.key === " ") {
            var prompt = messageInput.value.slice(0, -1);
            let recipient = MessageRecipient.SUGGESTER;
            suggestText(prompt, Suggestion_limit, recipient, 1);
            console.log("Suggested text:", prompt);
        }
    });

    document.addEventListener("pointermove", moveDiv);
    function moveDiv(event) {
        div.style.left = event.clientX + "px";
        div.style.top = event.clientY + "px";
    }

    function create_suggestion_card(id, element) {
        console.log(element);
        var sbg_test = document.createElement("button");
        sbg_test.setAttribute("class", "hover_card");
        sbg_test.setAttribute("id", "suggestion_card_" + id);
        sbg_test.onclick = function () {
            add_suggestion_to_prompt("suggestion_card_" + id);
        };
        sbg_test.innerHTML = element;
        div.appendChild(sbg_test);
    }
    function show_suggestions(suggestions) {
        //remove previous suggestions
        div.innerHTML = "";

        //display new suggestions
        console.log(suggestions);
        for (let i = 0; i < suggestions.length; i++) {
            const element = suggestions[i];
            create_suggestion_card(i, element.trim());
        }
    }
});
