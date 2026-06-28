export function createShowrunnerUI() {
    const style = document.createElement('style');
    style.textContent = `
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        }
        .showrunner-container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .logo {
            font-size: 28px;
            font-weight: bold;
            background: linear-gradient(45deg, #6a11cb, #2575fc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-align: center;
            margin-bottom: 5px;
        }
        .subtitle {
            text-align: center;
            color: #555;
            font-size: 14px;
            margin-bottom: 20px;
        }
        .input-area {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            color: #333;
        }
        textarea {
            width: 100%;
            height: 100px;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            transition: border-color 0.3s;
        }
        textarea:focus {
            border-color: #6a11cb;
            outline: none;
        }
        .button-container {
            display: flex;
            gap: 10px;
            margin-top: 10px;
        }
        button {
            padding: 10px 15px;
            background: linear-gradient(45deg, #6a11cb, #2575fc);
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            transition: transform 0.2s;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        button:active {
            transform: translateY(1px);
        }
        .clear-btn {
            background: #e0e0e0;
            color: #333;
        }
        .output-area {
            margin-top: 20px;
            padding: 15px;
            background: #f9f9f9;
            border: 1px solid #ddd;
            border-radius: 4px;
            white-space: pre-wrap;
            font-family: monospace;
            line-height: 1.5;
        }
    `;
    document.head.appendChild(style);

    const container = document.createElement('div');
    container.className = 'showrunner-container';

    const logo = document.createElement('div');
    logo.className = 'logo';
    logo.textContent = 'ScriptGen AI';
    container.appendChild(logo);

    const subtitle = document.createElement('p');
    subtitle.className = 'subtitle';
    subtitle.textContent = 'AI-Powered Scriptwriting Assistant';
    container.appendChild(subtitle);

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

    const buttonContainer = document.createElement('div');
    buttonContainer.className = 'button-container';

    const generateButton = document.createElement('button');
    generateButton.id = 'generate-btn';
    generateButton.textContent = 'Generate Script';

    const clearButton = document.createElement('button');
    clearButton.id = 'clear-btn';
    clearButton.className = 'clear-btn';
    clearButton.textContent = 'Clear';

    buttonContainer.appendChild(generateButton);
    buttonContainer.appendChild(clearButton);
    container.appendChild(buttonContainer);

    const outputArea = document.createElement('div');
    outputArea.className = 'output-area';
    outputArea.id = 'output';
    outputArea.textContent = 'Generated script will appear here...';
    container.appendChild(outputArea);

    document.body.appendChild(container);

    generateButton.addEventListener('click', async () => {
        const prompt = textarea.value;
        if (!prompt) {
            alert('Please enter a prompt');
            return;
        }

        generateButton.disabled = true;
        generateButton.textContent = 'Generating...';

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
        } finally {
            generateButton.disabled = false;
            generateButton.textContent = 'Generate Script';
        }
    });

    clearButton.addEventListener('click', () => {
        textarea.value = '';
        outputArea.textContent = 'Generated script will appear here...';
    });
}
