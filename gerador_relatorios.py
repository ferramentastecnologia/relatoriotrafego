import pandas as pd
import os
from datetime import datetime
import glob
import sys
import io
from typing import List, Any

# Forçar UTF-8 no terminal se possível
try:
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

def analisar_campanha(row: pd.Series) -> str:
    nome = row['Nome da campanha']
    gasto = row['Valor usado (BRL)']
    impressoes = row['Impressões']
    alcance = row['Alcance']
    
    # KPIs comuns
    compras = row.get('Compras', 0)
    receita = row.get('Valor de conversão da compra', 0)
    cliques = row.get('Cliques', 0) # Se houver coluna de cliques, senao usar Resultados como proxy se for tráfego
    resultados = row.get('Resultados', 0)
    custo_por_resultado = row.get('Custo por resultados', 0)
    
    texto = []
    
    # Lógica de Classificação
    tipo = "Outros"
    if any(x in nome.lower() for x in ['tráfego', 'perfil', 'institucional', 'aquisição', 'topo']):
        tipo = "Aquisição"
    elif any(x in nome.lower() for x in ['vendas', 'conversão', 'fundo', 'cardápio']):
        tipo = "Vendas"

    if tipo == "Aquisição":
        visitas = int(resultados) # Assumindo que Resultado = Visita ao Perfil para campanhas de Tráfego
        custo_visita = custo_por_resultado
        
        texto.append(f"📊 Campanha de Aquisição (Topo de Funil – Marca e Público Novo)")
        texto.append(f"({nome})\n")
        texto.append(f"Essa campanha tem como objetivo principal fazer a marca aparecer para mais pessoas da região, gerar lembrança de marca e trazer público novo para o perfil.\n")
        texto.append(f"• Investimento: R$ {gasto:,.2f}")
        texto.append(f"• Pessoas alcançadas: {int(alcance):,}".replace(',', '.'))
        texto.append(f"• Impressões: {int(impressoes):,}".replace(',', '.'))
        texto.append(f"• Visitas ao perfil: {visitas}")
        texto.append(f"• Custo por visita: R$ {custo_visita:,.2f}")
        # Tentar achar compras rastreadas mesmo em campanha de tráfego
        if compras > 0:
            texto.append(f"• Compras rastreadas: {int(compras)}")
            texto.append(f"• Valor rastreado: R$ {receita:,.2f}")
        
        texto.append(f"\n📌 O ponto mais importante aqui:")
        texto.append(f"Mesmo não sendo uma campanha focada em venda direta, ela influencia fortemente os pedidos que acontecem depois.")
        texto.append(f"Na prática, ela faz com que o cliente veja a marca hoje e volte a comprar dias depois, algo muito comum no delivery.")

    elif tipo == "Vendas":
        roas = receita / gasto if gasto > 0 else 0
        cpa = gasto / compras if compras > 0 else 0
        
        # Métricas de Funil Detalhado
        visualizacoes = row.get('Visualizações do conteúdo', 0)
        add_carrinho = row.get('Adições ao carrinho', 0)
        valor_add_carrinho = row.get('Valor de conversão de adições ao carrinho', 0)
        checkout_iniciado = row.get('Finalizações de compra iniciadas', 0)
        
        ticket_medio = receita / compras if compras > 0 else 0
        
        texto.append(f"📊 Campanha de Vendas (Performance no Cardápio Próprio)")
        texto.append(f"({nome})\n")
        texto.append(f"Aqui está onde os números mostram a força da estratégia:\n")
        texto.append(f"• Investimento: R$ {gasto:,.2f}")
        texto.append(f"• Pessoas alcançadas: {int(alcance):,}".replace(',', '.'))
        texto.append(f"• Impressões: {int(impressoes):,}".replace(',', '.'))
        
        # FUNIL DE VENDAS
        if visualizacoes > 0:
            texto.append(f"• 👁️ Visualizações do cardápio: {int(visualizacoes)}")
            
        if add_carrinho > 0:
            texto.append(f"• 🛒 Adições ao carrinho: {int(add_carrinho)}")
        
        if checkout_iniciado > 0:
            texto.append(f"• 💳 Finalizações de compra iniciadas: {int(checkout_iniciado)}")
            
        texto.append(f"• ✅ Compras realizadas: {int(compras)}")
        
        if receita > 0:
            texto.append(f"• 💰 Faturamento rastreado: R$ {receita:,.2f}")
            
        if ticket_medio > 0:
            texto.append(f"• Ticket Médio: R$ {ticket_medio:,.2f}")
            
        texto.append(f"• Custo por compra (CPA): R$ {cpa:,.2f}")
        
        if roas > 0:
            texto.append(f"• ROAS: {roas:.2f}")

        # Narrativa
        if roas > 0:
            texto.append(f"\n📌 Traduzindo isso:")
            texto.append(f"Cada R$ 1 investido em anúncios retornou mais de R$ {int(roas)} em vendas.")
            if ticket_medio > 0:
                texto.append(f"O ticket médio das compras foi de R$ {ticket_medio:,.2f}.")
        else:
            texto.append(f"\n📌 Análise:")
            if cliques > 0:
                texto.append(f"A campanha gerou tráfego, mas ainda não contabilizou vendas diretas atribuídas neste período.")
            else:
                texto.append(f"A campanha ainda está em fase de aprendizado ou não houve atribuição direta de vendas neste período.")
    
    else:
        # Padrão genérico
        texto.append(f"📊 {nome}")
        texto.append(f"• Investimento: R$ {gasto:,.2f}")
        texto.append(f"• Resultados: {int(resultados)}")
        texto.append(f"• ROAS: {(receita / gasto if gasto > 0 else 0):.2f}")

    return "\n".join(texto)

def obter_nome_cliente(caminho_arquivo: str) -> str:
    nome_arquivo = os.path.basename(caminho_arquivo)
    # Tenta extrair o nome antes de "-Campanhas" ou pega as primeiras partes
    parts = nome_arquivo.replace('_', '-').split('-')
    
    # Heurística simples: pegar as primeiras palavras até "Campanhas" ou data
    nome_cliente = []
    for part in parts:
        if any(c.isdigit() for c in part) or part.lower() in ['campanhas', 'relatorio', 'de', 'ate', 'csv']:
            break
        nome_cliente.append(part)
    
    if nome_cliente:
        return " ".join(nome_cliente).strip()
    return "CLIENTE"

def gerar_texto_relatorio(df: pd.DataFrame, nome_cliente: str) -> str:
    # Verificar se é um arquivo válido de colunas esperadas
    if 'Nome da campanha' not in df.columns:
        return "Erro: O arquivo não parece ser um relatório de campanhas (Coluna 'Nome da campanha' ausente)."

    # Limpar colunas numéricas
    cols_to_numeric = ['Valor usado (BRL)', 'Valor de conversão da compra', 'Compras', 'Impressões', 'Alcance', 'Resultados', 'Custo por resultados', 'Visualizações do conteúdo', 'Adições ao carrinho', 'Valor de conversão de adições ao carrinho', 'Finalizações de compra iniciadas']
    for col in cols_to_numeric:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Obter datas do período
    data_inicio = df['Início dos relatórios'].iloc[0] if 'Início dos relatórios' in df.columns else "N/A"
    data_fim = df['Término dos relatórios'].iloc[0] if 'Término dos relatórios' in df.columns else "N/A"

    try:
        data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').strftime('%d/%m/%Y')
        data_fim = datetime.strptime(data_fim, '%Y-%m-%d').strftime('%d/%m/%Y')
    except ValueError:
        pass

    relatorio_final = []
    relatorio_final.append(f"RELATÓRIO DE PERFORMANCE - {nome_cliente}")
    relatorio_final.append(f"Período: {data_inicio} a {data_fim}")
    relatorio_final.append(f"Data de Geração: {datetime.now().strftime('%d/%m/%Y')}\n")
    
    # Agrupar por campanha
    cols_sum = [c for c in cols_to_numeric if c in df.columns]
    df_grouped = df.groupby('Nome da campanha')[cols_sum].sum().reset_index()
    
    for index, row in df_grouped.iterrows():
        bloco = analisar_campanha(row)
        relatorio_final.append(bloco)
        relatorio_final.append("\n" + "="*30 + "\n")
        
    return '\n'.join(relatorio_final)

def gerar_relatorio():
    # Caminhos
    downloads_path = r'c:\Users\Juan\Downloads'
    output_folder = r'c:\Users\Juan\Desktop\Antigravity\Relatorios'
    
    # Pega qualquer CSV recente que pareça relatório de ads (heurística por data ou padrão)
    list_of_files = glob.glob(os.path.join(downloads_path, '*.csv'))
    
    if not list_of_files:
        print("Nenhum arquivo CSV encontrado na pasta Downloads.")
        return

    latest_file = max(list_of_files, key=os.path.getctime)
    print(f"Arquivo mais recente encontrado: {os.path.basename(latest_file)}")
    
    nome_cliente = obter_nome_cliente(latest_file).upper()
    print(f"Cliente identificado: {nome_cliente}")

    try:
        df = pd.read_csv(latest_file)
        
        texto_relatorio = gerar_texto_relatorio(df, nome_cliente)
        
        if texto_relatorio.startswith("Erro:"):
            print(texto_relatorio)
            return

        # Salvar
        safe_cliente = nome_cliente.replace(' ', '_')
        output_filename = f"Relatorio_{safe_cliente}_{datetime.now().strftime('%Y-%m-%d')}.txt"
        output_path = os.path.join(output_folder, output_filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(texto_relatorio)
            
        print(f"Relatório gerado: {output_path}")
        print("\n--- PREVIEW (Início) ---\n")
        print(texto_relatorio[:1000]) # type: ignore # Preview menor

    except Exception as e:
        print(f"Erro: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    gerar_relatorio()
