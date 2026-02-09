from flask import Flask, render_template, request, jsonify
import os
import pandas as pd
from gerador_relatorios import gerar_texto_relatorio, obter_nome_cliente

app = Flask(__name__)
if os.environ.get('VERCEL') == '1' or os.environ.get('VERCEL_ENV'):
    UPLOAD_FOLDER = os.path.join('/tmp', 'uploads')
else:
    UPLOAD_FOLDER = os.path.join(app.root_path, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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
            return jsonify({
                'success': True,
                'relatorio': texto_relatorio,
                'cliente': nome_cliente
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)

if __name__ == '__main__':
    app.run(debug=True)
