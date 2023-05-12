import flask
from flask import Flask, request, jsonify, abort
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from waitress import serve
import requests
import json
import logging
import os

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO)

# Set up rate limiting
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per day", "50 per hour"])
limiter.init_app(app)

# Get API key from environment
api_key = os.getenv('sentiment_api_key')
if not api_key:
    logging.error("No API key found in environment")
    exit(1)

def analyze_sentiment(text, api_key):
    url = "https://language.googleapis.com/v1/documents:analyzeSentiment?key={}".format(api_key)

    headers = {"Content-Type": "application/json"}

    body = {
        "document": {
            "type": "PLAIN_TEXT",
            "content": text
        },
        "encodingType": "UTF8"
    }

    response = requests.post(url, headers=headers, data=json.dumps(body))

    if response.status_code != 200:
        logging.error("Google API returned error: %s", response.text)
        return None

    return response.json()

@app.route('/analyze', methods=['POST'])
@limiter.limit("10 per minute")
def analyze():
    data = request.get_json()

    if not data or 'text' not in data:
        abort(400)

    text = data.get('text', '')
    result = analyze_sentiment(text, api_key)

    if not result:
        abort(500)

    return jsonify(result)
@app.route('/.well-known/ai-plugin.json')
def serve_ai_plugin():
  return send_from_directory('.',
                             'ai-plugin.json',
                             mimetype='application/json')


@app.route('/.well-known/openapi.yaml')
def serve_openapi_yaml():
  return send_from_directory('.', 'openapi.yaml', mimetype='text/yaml')


if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=8080)
