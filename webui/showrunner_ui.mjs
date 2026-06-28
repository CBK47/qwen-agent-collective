export function createShowrunnerUI() {
    const style = document.createElement('style');
    style.textContent = `
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .showrunner-container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
        }
        .input-area {
            margin-bottom: 15px;
        }
        textarea {
            width: 100%;
            height: 100px;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        button {
            padding: 10px 15px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        button:hover {
            background: #0056b3;
        }
        .output-area {
            margin-top: 20px;
            padding: 15px;
            background: #f9f9f9;
            border: 1px solid #ddd;
            border-radius: 4px;
            white-space: pre-wrap;
        }
    `;
    document.head.appendChild(style);

    const container = document.createElement('div');
    container.className = 'showrunner-container';

    const header = document.createElement('h1');
    header.textContent = 'Showrunner Demo';
    container.appendChild(header);

    const inputArea = document.createElement('div');
    inputArea.className = 'input-area';
    const label = document.createElement('label');
    label.htmlFor = 'prompt';
    label.textContent = 'Enter your script idea:';
    const textarea = document.createElement('textarea');
    textarea.id = 'prompt';
    textarea.placeholder = 'Describe the scene, characters, or plot...';
    inputArea.appendChild(label);
    inputArea.appendChild(textarea);
    container.appendChild(inputArea);

    const button = document.createElement('button');
    button.id = 'generate-btn';
    button.textContent = 'Generate Script';
    container.appendChild(button);

    const outputArea = document.createElement('div');
    outputArea.className = 'output-area';
    outputArea.id = 'output';
    outputArea.textContent = 'Generated script will appear here...';
    container.appendChild(outputArea);

    document.body.appendChild(container);

    button.addEventListener('click', async () => {
        const prompt = textarea.value;
        if (!prompt) {
            alert('Please enter a prompt');
            return;
        }

        try {
            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt })
            });
            if (!response.ok) throw new Error('Network response was not ok');
            const data = await response.json();
            outputArea.textContent = data.script;
        } catch (error) {
            console.error('Error:', error);
            outputArea.textContent = 'Error generating script. Please try again.';
        }
    });
}
