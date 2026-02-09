from flask import Flask, render_template, request, jsonify
import os
import re
import json
import base64
from datetime import datetime
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from gerador_relatorios import gerar_texto_relatorio, obter_nome_cliente

app = Flask(__name__)
if os.environ.get('VERCEL') == '1' or os.environ.get('VERCEL_ENV'):
    UPLOAD_FOLDER = os.path.join('/tmp', 'uploads')
    REPORTS_FOLDER = os.path.join('/tmp', 'relatorios')
else:
    UPLOAD_FOLDER = os.path.join(app.root_path, 'uploads')
    REPORTS_FOLDER = os.path.join(app.root_path, 'relatorios')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORTS_FOLDER, exist_ok=True)

def _load_service_account_info():
    raw = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON')
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        try:
            decoded = base64.b64decode(raw).decode('utf-8')
            return json.loads(decoded)
        except Exception:
            return None

def _upload_report_to_drive(file_path: str, filename: str):
    info = _load_service_account_info()
    if not info:
        raise ValueError('Google Drive não configurado. Defina GOOGLE_SERVICE_ACCOUNT_JSON.')
    folder_id = os.environ.get('DRIVE_FOLDER_ID')
    creds = service_account.Credentials.from_service_account_info(
        info,
        scopes=['https://www.googleapis.com/auth/drive.file']
    )
    service = build('drive', 'v3', credentials=creds)
    metadata = {'name': filename}
    if folder_id:
        metadata['parents'] = [folder_id]
    media = MediaFileUpload(file_path, mimetype='text/plain')
    result = service.files().create(body=metadata, media_body=media, fields='id, webViewLink').execute()
    return result

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/gerar', methods=['POST'])
def gerar():
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nome do arquivo vazio'}), 400

    if file:
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)
        
        try:
            df = pd.read_csv(filepath)
            nome_cliente = obter_nome_cliente(filepath).upper()
            texto_relatorio = gerar_texto_relatorio(df, nome_cliente)
            safe_cliente = re.sub(r'[^A-Za-z0-9_-]+', '_', nome_cliente).strip('_')
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            output_filename = f"Relatorio_{safe_cliente}_{timestamp}.txt" if safe_cliente else f"Relatorio_{timestamp}.txt"
            output_path = os.path.join(REPORTS_FOLDER, output_filename)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(texto_relatorio)
            drive_result = _upload_report_to_drive(output_path, output_filename)
            return jsonify({
                'success': True,
                'relatorio': texto_relatorio,
                'cliente': nome_cliente,
                'arquivo': output_filename,
                'drive': {
                    'id': drive_result.get('id'),
                    'link': drive_result.get('webViewLink')
                }
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)

if __name__ == '__main__':
    app.run(debug=True)
