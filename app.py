from flask import Flask, render_template, request, jsonify
import os
import re
from datetime import datetime
import pandas as pd
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
            return jsonify({
                'success': True,
                'relatorio': texto_relatorio,
                'cliente': nome_cliente,
                'arquivo': output_filename
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)

if __name__ == '__main__':
    app.run(debug=True)
