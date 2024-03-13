const MessageRecipient = {
    GENERATOR: 1,
    SUGGESTER: 2,
    SUMMARIZER: 3,
    AGENT_SELECTOR: 4
};
let Default_Suggestion_limit = 5;
let Default_Generation_limit = 10;
document.addEventListener("DOMContentLoaded", function () {
    var socket = io("http://localhost:5000");

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

    document.getElementById("LoadModelButton").onclick = function loadModel(){
        data = {
            model_repo: document.getElementById("Model_repo").value,
            model_name: document.getElementById("Model_name").value,
            recipient: MessageRecipient.AGENT_SELECTOR

        }
        socket.emit("message", data);
    }

    document
        .getElementById("no_of_samples")
        .addEventListener("input", updateSettings);
    document
        .getElementById("no_of_gen_toks")
        .addEventListener("input", updateSettings);

    socket.on("connect", () => {
        console.log("WebSocket connection opened:", socket.connected);
    });

    socket.on("message", (data) => {
        data = JSON.parse(data);
        console.log("Received message:", data);
        if (data["from_generator"]) {
            document.getElementById("messageInput").value += data["message"];
        }
        if (data["from_suggester"]) {
            console.log("Suggested text:", data["message"]);
            show_suggestions(data["message"]);
        }
        if (data["from_agent_change"]) {
            var dat = document.getElementById("Model_repo").value+"/"+ document.getElementById("Model_name").value
            alert(dat+"chamge"+data['status']);
        }
    });

    socket.onclose = function (event) {
        console.log("WebSocket connection closed:", event);
    };

    socket.onerror = function (e) {
        alert(e.msg);
    };

    socket.on("connection_error", (err) => {
        console.log(err);
    });

    function ModelRequest(
        message,
        no_of_samples,
        recipient,
        generation_count = 1
    ) {
        var data = {
            message: message,
            no_of_samples: no_of_samples,
            recipient: recipient,
            generation_count: generation_count,
        };
        socket.emit("message", data);
    }

    function add_suggestion_to_prompt(id) {
        let element = document.getElementById(id);
        messageInput.value += element.innerHTML + " ";
        console.log(element.innerHTML + " added to prompt");
        let recipient = MessageRecipient.SUGGESTER;
        ModelRequest(messageInput.value.slice(0, -1), Suggestion_limit, recipient);
    }

    // Handle button click to send a message
    SummaryRequesterButton.addEventListener("click", function () {
        const fileInput = document.getElementById("fileInput");
        const file = fileInput.files[0];

        if (!file) {
            return;
        }
        
        var sendData = {
            recipient: MessageRecipient.SUMMARIZER,
            file: file,
            type: file.type
        }

        console.log("Sending message:\n", sendData);

        socket.emit("message", sendData);
    });

    // Suggest text
    messageInput.addEventListener("keyup", function (event) {
        if (event.key === "\\") {
            //remove last Character
            var prompt = messageInput.value.slice(0, -1);
            messageInput.value = prompt;
            let recipient = MessageRecipient.GENERATOR;
            ModelRequest(prompt, 1, recipient, Generation_limit);
        }
        if (event.key === " ") {
            var prompt = messageInput.value.slice(0, -1);
            let recipient = MessageRecipient.SUGGESTER;
            ModelRequest(prompt, Suggestion_limit, recipient, 1);
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
