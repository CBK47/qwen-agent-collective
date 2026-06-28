from flask import Flask, request

app = Flask(__name__)

@app.route('/')
def home():
    return '''
    <h1>Open Translate</h1>
    <form id="translationForm">
        <textarea name="text" rows="4" cols="50"></textarea><br>
        <button type="submit">Translate</button>
    </form>
    <div id="result"></div>
    <script>
        document.getElementById('translationForm').addEventListener('submit', function(e) {
            e.preventDefault();
            const text = this.elements['text'].value;
            fetch('/translate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({text: text})
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('result').innerText = data.translated;
            });
        });
    </script>
    '''

@app.route('/translate', methods=['POST'])
def translate():
    data = request.get_json()
    translated = data['text'][::-1]  # Simple reverse for demo
    return {'translated': translated}

if __name__ == '__main__':
    app.run(debug=True)
