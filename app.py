from flask import Flask, request, jsonify, send_file, after_this_request
from flask_cors import CORS
from google import genai
import tempfile, os

app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)

# ---- CONFIG ----
# from dotenv import load_dotenv
# load_dotenv()
API_KEY = os.environ.get("GEMINI_API_KEY")

# Create the GenAI client
client = genai.Client(api_key=API_KEY)

# ---- HELPER FUNCTION ----
def get_prompt(feature, text):
    return {
        "chat":      f"Answer conversationally in max 100 words: {text}",
        "summarize": f"Summarize the following in exactly 5 bullet points:\n{text}",
        "notes":     f"Create structured notes for the following topic:\n{text}",
        "email":     f"Write a professional email for this context:\n{text}",
        "questions": f"Generate exactly 5 insightful questions about:\n{text}",
        "translate": f"Translate the following text (English ↔ Telugu):\n{text}",
        "prompt":    f"Rewrite the following as a clear, effective AI prompt:\n{text}",
    }.get(feature, text)

# ---- ROUTES ----
@app.route("/")
def index():
    return app.send_static_file("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json()
    feature = data.get("feature", "chat")
    message = data.get("message", "").strip()

    if not message:
        return jsonify({"error": "Message is empty"}), 400

    prompt = get_prompt(feature, message)

    try:
        # Call the Gemini API via the client
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return jsonify({"response": response.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/audio", methods=["POST"])
def audio():
    text = request.get_json().get("text", "").strip()
    if not text:
        return jsonify({"error": "No text provided"}), 400
    try:
        import pyttsx3
        engine = pyttsx3.init()
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp.close()
        engine.save_to_file(text, tmp.name)
        engine.runAndWait()

        @after_this_request
        def remove_file(response):
            os.unlink(tmp.name)
            return response

        return send_file(tmp.name, mimetype="audio/wav", as_attachment=True, download_name="output.wav")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---- MAIN ----
if __name__ == "__main__":
    app.run(debug=True, port=5000)
