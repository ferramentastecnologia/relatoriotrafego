import pandas as pd
import os
from datetime import datetime
import glob
import sys
import io
import re
import unicodedata
from typing import List, Any

# Forçar UTF-8 no terminal se possível
try:
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

def analisar_campanha(row: pd.Series) -> str:
    nome = row.get('Nome da campanha', 'Campanha')
    gasto = row.get('Valor usado (BRL)', 0)
    impressoes = row.get('Impressões', 0)
    alcance = row.get('Alcance', 0)
    
    # KPIs comuns
    compras = row.get('Compras', 0)
    receita = row.get('Valor de conversão da compra', 0)
    cliques = row.get('Cliques', 0)
    resultados = row.get('Resultados', 0)
    custo_por_resultado = row.get('Custo por resultados', 0)
    visitas_perfil = row.get('Visitas ao perfil', 0)
    custo_visita = custo_por_resultado if (custo_por_resultado > 0 and visitas_perfil > 0) else (gasto / visitas_perfil if visitas_perfil > 0 else 0)
    
    texto = []
    
    # Lógica de Classificação
    tipo = "Outros"
    nome_lower = str(nome).lower()
    funil_sinais = [
        row.get('Visualizações do conteúdo', 0),
        row.get('Adições ao carrinho', 0),
        row.get('Finalizações de compra iniciadas', 0),
        row.get('Valor de conversão de adições ao carrinho', 0)
    ]
    if compras > 0 or receita > 0 or any(v > 0 for v in funil_sinais):
        tipo = "Vendas"
    elif any(x in nome_lower for x in ['tráfego', 'perfil', 'institucional', 'aquisição', 'topo']):
        tipo = "Aquisição"
    elif any(x in nome_lower for x in ['vendas', 'conversão', 'fundo', 'cardápio']):
        tipo = "Vendas"

    if tipo == "Aquisição":
        texto.append(f"📊 Campanha de Aquisição (Topo de Funil – Marca e Público Novo)")
        texto.append(f"({nome})\n")
        texto.append(f"Essa campanha tem como objetivo principal fazer a marca aparecer para mais pessoas da região, gerar lembrança de marca e trazer público novo para o perfil.\n")
        texto.append(f"• Investimento: R$ {gasto:,.2f}")
        texto.append(f"• Pessoas alcançadas: {int(alcance):,}".replace(',', '.'))
        texto.append(f"• Impressões: {int(impressoes):,}".replace(',', '.'))
        if visitas_perfil > 0:
            texto.append(f"• Visitas ao perfil: {int(visitas_perfil)}")
            texto.append(f"• Custo por visita: R$ {custo_visita:,.2f}")
        # Tentar achar compras rastreadas mesmo em campanha de tráfego
        if compras > 0:
            texto.append(f"• Compras rastreadas: {int(compras)}")
            texto.append(f"• Valor rastreado: R$ {receita:,.2f}")
        
        texto.append(f"\n📌 O ponto mais importante aqui:")
        texto.append(f"Essa campanha não tem objetivo principal de venda direta, e sim reconhecimento de marca e aquisição de público na região.")
        texto.append(f"Ela influencia pedidos que acontecem dias depois, algo muito comum no delivery.")
        if receita > 0:
            texto.append(f"Como houve venda atribuída, o resultado é lucro adicional para a marca.")
        elif roas := (receita / gasto if gasto > 0 else 0):
            texto.append(f"Mesmo sendo topo de funil, já trouxe ROAS de {roas:.2f}, o que é excelente para reconhecimento.")

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
        if visitas_perfil > 0:
            texto.append(f"• Visitas ao perfil: {int(visitas_perfil)}")
            texto.append(f"• Custo por visita: R$ {custo_visita:,.2f}")
        
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
            if 'trafego' in nome_lower or 'perfil' in nome_lower:
                texto.append(f"Campanha voltada para aquisição de público e reconhecimento de marca na região, além de novos seguidores para a página.")
                if compras > 0 or receita > 0:
                    texto.append(f"Obs: resultados em venda através dessa campanha são lucro na performance de tráfego.")
            else:
                if roas >= 6:
                    texto.append(f"ROAS acima de 6 é considerado um ótimo resultado para campanha de cardápio.")
                else:
                    texto.append(f"ROAS abaixo de 6 indica espaço para otimização em criativos, público e oferta.")
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
        texto.append(f"📊 {nome}")
        texto.append(f"• Investimento: R$ {gasto:,.2f}")
        if alcance > 0:
            texto.append(f"• Pessoas alcançadas: {int(alcance):,}".replace(',', '.'))
        if impressoes > 0:
            texto.append(f"• Impressões: {int(impressoes):,}".replace(',', '.'))
        if resultados > 0:
            texto.append(f"• Resultados: {int(resultados)}")
        if cliques > 0:
            texto.append(f"• Cliques: {int(cliques)}")
        if custo_por_resultado > 0:
            texto.append(f"• Custo por resultado: R$ {custo_por_resultado:,.2f}")
        if compras > 0:
            texto.append(f"• Compras: {int(compras)}")
        if receita > 0:
            texto.append(f"• Receita: R$ {receita:,.2f}")
        if gasto > 0 and receita > 0:
            texto.append(f"• ROAS: {(receita / gasto):.2f}")

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

def _normalize_text(value: str) -> str:
    value = value.strip().lower()
    value = unicodedata.normalize('NFKD', value)
    value = ''.join(c for c in value if not unicodedata.combining(c))
    value = value.replace('_', ' ').replace('-', ' ')
    value = re.sub(r'[^a-z0-9 ]+', ' ', value)
    value = re.sub(r'\s+', ' ', value).strip()
    return value

def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    normalized_to_original = {}
    for col in df.columns:
        key = _normalize_text(str(col))
        if key and key not in normalized_to_original:
            normalized_to_original[key] = col
    variants = {
        'Nome da campanha': ['nome da campanha', 'campanha', 'campaign name', 'nome campanha', 'ad name', 'campaign'],
        'Valor usado (BRL)': ['valor usado (brl)', 'valor gasto (brl)', 'amount spent (brl)', 'valor gasto', 'gasto', 'spent', 'amount spent'],
        'Impressões': ['impressões', 'impressoes', 'impressions'],
        'Alcance': ['alcance', 'reach', 'people reached'],
        'Compras': ['compras', 'purchases', 'website purchases', 'on facebook purchases', 'app purchases', 'purchases (all)'],
        'Valor de conversão da compra': ['valor de conversao da compra', 'purchase conversion value', 'valor de conversao da compra (brl)', 'purchase conversion value (brl)', 'website purchase conversion value', 'purchases conversion value'],
        'Cliques': ['cliques', 'link clicks', 'cliques no link', 'clicks', 'inline link clicks', 'clicks all', 'all clicks'],
        'Resultados': ['resultados', 'results', 'result'],
        'Visitas ao perfil': ['visitas ao perfil', 'profile visits', 'visitas do perfil', 'profile visit', 'visitas no perfil'],
        'Indicador de resultados': ['indicador de resultados', 'result indicator', 'results indicator'],
        'Custo por resultados': ['custo por resultados', 'cost per result', 'cost per results'],
        'Visualizações do conteúdo': ['visualizacoes do conteudo', 'visualizações do conteúdo', 'content views', 'landing page views', 'view content', 'content view'],
        'Adições ao carrinho': ['adicoes ao carrinho', 'adições ao carrinho', 'add to cart', 'adds to cart', 'add to cart (website)', 'adds to cart (website)'],
        'Valor de conversão de adições ao carrinho': ['valor de conversao de adicoes ao carrinho', 'add to cart conversion value', 'valor de conversao de adicoes ao carrinho (brl)', 'add to cart conversion value (brl)'],
        'Finalizações de compra iniciadas': ['finalizacoes de compra iniciadas', 'checkouts initiated', 'initiated checkouts', 'initiate checkout'],
        'Início dos relatórios': ['inicio dos relatorios', 'início dos relatórios', 'reporting starts', 'reporting start', 'inicio relatorios', 'reporting start date'],
        'Término dos relatórios': ['termino dos relatorios', 'término dos relatórios', 'reporting ends', 'reporting end', 'termino relatorios', 'reporting end date']
    }
    renames = {}
    for canonical, opts in variants.items():
        for opt in opts:
            key = _normalize_text(opt)
            if key in normalized_to_original:
                renames[normalized_to_original[key]] = canonical
                break
        if canonical not in renames.values():
            for col_key, original in normalized_to_original.items():
                for opt in opts:
                    opt_key = _normalize_text(opt)
                    if opt_key and opt_key in col_key:
                        renames[original] = canonical
                        break
                if original in renames:
                    break
    keyword_rules = {
        'Nome da campanha': [['campaign'], ['campanha'], ['ad name']],
        'Valor usado (BRL)': [['amount', 'spent'], ['valor', 'gasto'], ['spend'], ['spent']],
        'Impressões': [['impress'], ['impression']],
        'Alcance': [['reach'], ['alcance']],
        'Compras': [['purchase'], ['compra']],
        'Valor de conversão da compra': [['purchase', 'value'], ['conversion', 'value', 'purchase'], ['valor', 'conversao', 'compra']],
        'Cliques': [['click'], ['clique']],
        'Resultados': [['result'], ['resultado']],
        'Visitas ao perfil': [['profile', 'visit'], ['visita', 'perfil']],
        'Indicador de resultados': [['result', 'indicator'], ['indicador', 'resultado']],
        'Custo por resultados': [['cost', 'result'], ['custo', 'resultado']],
        'Visualizações do conteúdo': [['content', 'view'], ['landing', 'page', 'view'], ['visualizacao', 'conteudo']],
        'Adições ao carrinho': [['add', 'cart'], ['adicao', 'carrinho']],
        'Valor de conversão de adições ao carrinho': [['add', 'cart', 'value'], ['conversion', 'value', 'cart'], ['valor', 'conversao', 'adicao', 'carrinho']],
        'Finalizações de compra iniciadas': [['checkout'], ['finalizacao', 'compra']],
        'Início dos relatórios': [['reporting', 'start'], ['inicio', 'relatorio']],
        'Término dos relatórios': [['reporting', 'end'], ['termino', 'relatorio']]
    }
    for canonical, keyword_sets in keyword_rules.items():
        if canonical in renames.values():
            continue
        for col_key, original in normalized_to_original.items():
            for keywords in keyword_sets:
                if all(k in col_key for k in keywords):
                    renames[original] = canonical
                    break
            if original in renames:
                break
    if renames:
        df = df.rename(columns=renames)
    return df

def _safe_div(n: float, d: float) -> float:
    return n / d if d else 0

import json

def carregar_estrategia_cliente():
    caminho_estrategia = os.path.join(os.path.dirname(__file__), 'mdf_passo_fundo_strategy.json')
    if os.path.exists(caminho_estrategia):
        try:
            with open(caminho_estrategia, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return None
    return None

def gerar_inteligencia_gastronomia(df: pd.DataFrame) -> str:
    estrategia = carregar_estrategia_cliente()
    
    gasto = df['Valor usado (BRL)'].sum() if 'Valor usado (BRL)' in df.columns else 0
    receita = df['Valor de conversão da compra'].sum() if 'Valor de conversão da compra' in df.columns else 0
    compras = df['Compras'].sum() if 'Compras' in df.columns else 0
    impressoes = df['Impressões'].sum() if 'Impressões' in df.columns else 0
    alcance = df['Alcance'].sum() if 'Alcance' in df.columns else 0
    resultados = df['Resultados'].sum() if 'Resultados' in df.columns else 0
    visitas_perfil = df['Visitas ao perfil'].sum() if 'Visitas ao perfil' in df.columns else 0
    cliques = df['Cliques'].sum() if 'Cliques' in df.columns else 0
    visualizacoes = df['Visualizações do conteúdo'].sum() if 'Visualizações do conteúdo' in df.columns else 0
    add_carrinho = df['Adições ao carrinho'].sum() if 'Adições ao carrinho' in df.columns else 0
    checkout = df['Finalizações de compra iniciadas'].sum() if 'Finalizações de compra iniciadas' in df.columns else 0

    roas = _safe_div(receita, gasto)
    cpa = _safe_div(gasto, compras)
    cpr = _safe_div(gasto, resultados)
    cpm = _safe_div(gasto * 1000, impressoes)
    cpc = _safe_div(gasto, cliques)
    taxa_visita = _safe_div(visitas_perfil, alcance)
    freq = _safe_div(impressoes, alcance)
    ticket_medio = _safe_div(receita, compras)
    taxa_add_carrinho = _safe_div(add_carrinho, visualizacoes)
    taxa_checkout = _safe_div(checkout, add_carrinho)
    taxa_compra = _safe_div(compras, checkout)

    linhas = []
    linhas.append("INTELIGÊNCIA DE TRÁFEGO - GASTRONOMIA")
    linhas.append("Resumo executivo:")
    linhas.append(f"• Investimento total: R$ {gasto:,.2f}")
    if impressoes > 0:
        linhas.append(f"• Impressões: {int(impressoes):,}".replace(',', '.'))
    if alcance > 0:
        linhas.append(f"• Alcance: {int(alcance):,}".replace(',', '.'))
    if resultados > 0:
        linhas.append(f"• Resultados: {int(resultados):,}".replace(',', '.'))
    if visitas_perfil > 0:
        linhas.append(f"• Visitas ao perfil: {int(visitas_perfil):,}".replace(',', '.'))
        linhas.append(f"• Custo por visita: R$ {_safe_div(gasto, visitas_perfil):,.2f}")
    if compras > 0:
        linhas.append(f"• Compras: {int(compras):,}".replace(',', '.'))
        linhas.append(f"• CPA: R$ {cpa:,.2f}")
    if receita > 0:
        linhas.append(f"• Receita rastreada: R$ {receita:,.2f}")
    if ticket_medio > 0:
        linhas.append(f"• Ticket médio: R$ {ticket_medio:,.2f}")
    if roas > 0:
        linhas.append(f"• ROAS: {roas:.2f}")
        
        # Análise Don Chevico Style - Impacto Real do Tráfego
        # Estimativa: assumindo que 50% das vendas vêm de tráfego se não tivermos dados de orgânico
        # Se tivermos dados reais de faturamento total (imput manual ou config), usaríamos aqui.
        # Como só temos o CSV do Ads, vamos destacar o que É DO ADS.
        linhas.append(f"\n--- IMPACTO REAL DO TRÁFEGO (Don Chevico Analysis) ---")
        linhas.append(f"Faturamento rastreado via anúncios: R$ {receita:,.2f}")
        if receita > 0 and gasto > 0:
            lucro_bruto_ads = receita - gasto
            linhas.append(f"Lucro bruto sobre investimento (Ads): R$ {lucro_bruto_ads:,.2f}")
            if lucro_bruto_ads > 0:
                linhas.append(f"Prova matemática: O tráfego pagou a si mesmo e gerou caixa.")
            else:
                linhas.append(f"Atenção: O retorno direto ainda não cobriu o investimento. Foco em LTV e branding.")
        
        if compras > 0:
            linhas.append(f"Base de clientes ativos (vendas): {int(compras)} pedidos gerados.")
            linhas.append(f"Isso significa {int(compras)} experiências de marca entregues na casa do cliente.")
            
        if visitas_perfil > 0:
            linhas.append(f"Novos interessados (Visitas ao perfil): {int(visitas_perfil)}")
            linhas.append(f"Potencial de clientes futuros (Público Frio) que conheceram a marca.")

        if impressoes > 0:
            linhas.append(f"• CPM: R$ {cpm:,.2f}")
    if cliques > 0:
        linhas.append(f"• CPC: R$ {cpc:,.2f}")

    diagnosticos = []
    if gasto > 0 and compras <= 0:
        diagnosticos.append("Sem compras atribuídas no período; revisar oferta, criativos e público.")
    if visualizacoes > 0 and add_carrinho <= 0:
        diagnosticos.append("Visualizações sem adição ao carrinho; oferta e preço podem estar desalinhados.")
    if add_carrinho > 0 and checkout <= 0:
        diagnosticos.append("Adições ao carrinho sem checkout; revisar fricção do funil.")
    if checkout > 0 and compras <= 0:
        diagnosticos.append("Checkouts iniciados sem compra; revisar meios de pagamento e taxa de conversão.")
    if roas > 0 and roas < 2:
        diagnosticos.append("ROAS baixo para gastronomia; otimizar criativos, público e oferta.")
    if freq > 3.5:
        diagnosticos.append("Frequência alta; risco de fadiga criativa.")
    if alcance > 0 and taxa_visita < 0.003 and resultados > 0:
        diagnosticos.append("Baixa taxa de visita; mensagens e criativos podem não estar atraentes.")

    if diagnosticos:
        linhas.append("\nDiagnóstico:")
        for d in diagnosticos[:6]:
            linhas.append(f"• {d}")

    if estrategia:
        linhas.append("\n--- ESTRATÉGIA PERSONALIZADA (MDF - Passo Fundo) ---")
        linhas.append("Baseada em análise de concorrentes locais (Somare, Didio's, Honshu, etc.)")
        
        sugestao = estrategia.get('estrategia_sugerida', {})
        orcamento_meta = sugestao.get('orcamento_diario_total', 0)
        
        linhas.append(f"\nMeta de Investimento Diário: R$ {orcamento_meta:.2f}")
        if gasto > 0:
            dias_aprox = gasto / (gasto/len(df)) if len(df) > 0 else 1 # Estimativa grosseira se nao tiver dias
            media_diaria = gasto / 7 # Assumindo semanal ou ajustar conforme dados reais de dias
            # Melhor pegar datas
            try:
                dt_ini = pd.to_datetime(df['Início dos relatórios'].iloc[0])
                dt_fim = pd.to_datetime(df['Término dos relatórios'].iloc[0])
                dias = (dt_fim - dt_ini).days + 1
                if dias > 0:
                    media_diaria = gasto / dias
                    linhas.append(f"Investimento Atual Diário (Média): R$ {media_diaria:.2f}")
                    if media_diaria < orcamento_meta * 0.8:
                        linhas.append(f"⚠️ Atenção: Você está investindo abaixo do planejado (R$ {orcamento_meta}).")
                    elif media_diaria > orcamento_meta * 1.2:
                        linhas.append(f"⚠️ Atenção: O investimento está acima da meta de R$ {orcamento_meta}.")
            except:
                pass

        linhas.append("\nEstrutura Recomendada:")
        for camp in sugestao.get('campanhas', []):
            linhas.append(f"• {camp['nome']} (R$ {camp['orcamento_diario']:.2f}/dia)")
            linhas.append(f"  Objetivo: {camp['objetivo']}")
            linhas.append(f"  Criativos Sugeridos: {', '.join(camp['criativos'][:2])}")
            
    linhas.append("\n--- PRÓXIMOS PASSOS E CONCLUSÃO ESTRATÉGICA ---")
    linhas.append("1. Manter Campanhas de Venda Direta: São o motor de faturamento (sustentação).")
    linhas.append("2. Expandir Topo de Funil: Continuar trazendo gente nova (Visitas ao Perfil) para evitar saturação da base.")
    linhas.append("3. Testar Novos Canais (Google Ads): Captar quem já busca por 'pizzaria' ou 'delivery' na região.")
    linhas.append("4. Monitorar Recompra: O tráfego traz o cliente a primeira vez; o produto garante a volta.")
    
    linhas.append("\nAções recomendadas (Gerais):")
    linhas.append("• Criativos com produto campeão, preço e tempo de entrega em destaque.")
    linhas.append("• Ofertas com combo e frete grátis acima de um valor mínimo.")
    linhas.append("• Campanhas por horário de pico com orçamento concentrado.")
    linhas.append("• Remarketing de 7 a 14 dias com foco em quem visitou ou adicionou ao carrinho.")
    linhas.append("• Segmentação por raio com exclusão de áreas de baixa conversão.")
    if taxa_add_carrinho > 0 and taxa_add_carrinho < 0.03:
        linhas.append("• Ajustar descrição do cardápio e reforçar benefícios no criativo.")
    if taxa_checkout > 0 and taxa_checkout < 0.5:
        linhas.append("• Revisar UX do checkout e incentivos para finalizar pedido.")
    if taxa_compra > 0 and taxa_compra < 0.5:
        linhas.append("• Testar cupom de primeira compra e prova social.")

    return "\n".join(linhas)

def gerar_texto_relatorio(df: pd.DataFrame, nome_cliente: str) -> str:
    df = _normalize_columns(df.copy())
    if 'Nome da campanha' not in df.columns:
        df['Nome da campanha'] = 'Campanha'

    # Limpar colunas numéricas
    cols_to_numeric = ['Valor usado (BRL)', 'Valor de conversão da compra', 'Compras', 'Impressões', 'Alcance', 'Resultados', 'Visitas ao perfil', 'Custo por resultados', 'Visualizações do conteúdo', 'Adições ao carrinho', 'Valor de conversão de adições ao carrinho', 'Finalizações de compra iniciadas']
    for col in cols_to_numeric:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    if 'Visitas ao perfil' not in df.columns:
        df['Visitas ao perfil'] = 0
    if 'Indicador de resultados' in df.columns and 'Resultados' in df.columns:
        indicador = df['Indicador de resultados'].astype(str).str.lower()
        mask_visitas = indicador.str.contains('profile') | indicador.str.contains('perfil') | indicador.str.contains('visita')
        df.loc[mask_visitas & (df['Visitas ao perfil'] <= 0), 'Visitas ao perfil'] = df.loc[mask_visitas, 'Resultados']
    
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

    relatorio_final.append(gerar_inteligencia_gastronomia(df))
        
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
