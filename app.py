from flask import Flask, render_template, request, jsonify
import os
import pandas as pd
from gerador_relatorios import gerar_texto_relatorio, obter_nome_cliente

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
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
            # Processar
            df = pd.read_csv(filepath)
            nome_cliente = obter_nome_cliente(filepath).upper()
            
            # Gerar relatório usando a função refatorada
            texto_relatorio = gerar_texto_relatorio(df, nome_cliente)
            
            return jsonify({
                'success': True,
                'relatorio': texto_relatorio,
                'cliente': nome_cliente
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
