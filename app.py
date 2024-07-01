import os
import pandas as pd
import requests
from flask import Flask, request, jsonify
from azure.storage.blob import BlobServiceClient

app = Flask(__name__)

# Initialize Blob Service Client
blob_service_client = BlobServiceClient.from_connection_string(os.getenv('AZURE_STORAGE_CONNECTION_STRING'))

# Azure OpenAI endpoint and key
openai_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
openai_key = os.getenv('AZURE_OPENAI_KEY')

def generate_faqs(df):
    faqs = []
    headers = {
        'Content-Type': 'application/json',
        'api-key': openai_key
    }
    for index, row in df.iterrows():
        prompt = f"Generate a FAQ for the following topic: {row['topic']}"
        data = {
            "prompt": prompt,
            "max_tokens": 150
        }
        response = requests.post(f"{openai_endpoint}/openai/deployments/text-davinci-003/completions", headers=headers, json=data)
        response_json = response.json()
        faqs.append(response_json['choices'][0]['text'].strip())
    return faqs

@app.route('/generate-faqs', methods=['POST'])
def generate_faqs_route():
    csv_file_name = request.json.get('csv_file_name')
    if not csv_file_name:
        return jsonify({"error": "Please provide the name of the CSV file in the request."}), 400

    # Download the CSV file from Blob Storage
    container_name = 'your-container-name'
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=csv_file_name)
    csv_data = blob_client.download_blob().readall()

    # Read the CSV file
    df = pd.read_csv(pd.compat.StringIO(str(csv_data, 'utf-8')))

    # Generate FAQs
    faqs = generate_faqs(df)

    return jsonify(faqs)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
