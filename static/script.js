document.getElementById('send-button').addEventListener('click', async function() {
    const userInput = document.getElementById('user-input').value;
    if (!userInput) return;

    // Display the user's query in the chat box
    const chatBox = document.getElementById('chat-box');
    chatBox.innerHTML += `<p><strong>You:</strong> ${userInput}</p>`;
    
    // Send the query to the chatbot backend
    const response = await fetch('http://localhost:8000/query', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            query: userInput,
            thread_id: "1" // if you're managing threads/sessions
        })
    });

    const data = await response.json();
    const botResponse = data.response;

    // Display the chatbot's response in the chat box
    chatBox.innerHTML += `<p><strong>Bot:</strong> ${botResponse}</p>`;

    // Clear the input box
    document.getElementById('user-input').value = '';

    // Scroll to the bottom of the chat box
    chatBox.scrollTop = chatBox.scrollHeight;
});
