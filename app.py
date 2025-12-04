import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
import time
import unicodedata 
from sklearn.feature_extraction.text import CountVectorizer

# --- CONFIGURAÇÕES ---
NOME_PLANILHA = "Respostas Conecta Sede"
NOME_ARQUIVO_LOGO = "VERSÃO VERTICAL Colorida negativa (2).png" # <--- O arquivo deve estar no GitHub com esse nome exato

# LISTA com os nomes exatos das 3 colunas (Cabeçalhos)
COLUNAS_PERGUNTAS = [
    "De quais projetos/resultados da minha equipe tenho orgulho?",
    "O quê de bom aconteceu na Sede/Desenvolvimento Econômico que eu me orgulho?",
    "Do quê eu me orgulho em mim como profissional em 2025?"
]

# Títulos curtos para aparecer em cima de cada nuvem
TITULOS_VISUAIS = [
    "Projetos do time",
    "Sucessos da Sede",
    "Eu Profissional"
]

TEMPO_REFRESH = 10

# --- FUNÇÃO HELPER PARA REMOVER ACENTOS ---
def remover_acentos(texto):
    """
    Remove acentos e coloca em minúsculas.
    Ex: 'Ações' -> 'acoes', 'Relatório' -> 'relatorio'
    """
    if not isinstance(texto, str):
        return str(texto)
    nfkd_form = unicodedata.normalize('NFKD', texto)
    # Filtra caracteres que não são marcas de acentuação ('Mn')
    return "".join([c for c in nfkd_form if not unicodedata.category(c) == 'Mn']).lower()

# --- CONFIGURAÇÃO DE STOPWORDS ---
stopwords_pt = set(STOPWORDS)
lista_extra = [
    "de", "a", "o", "que", "e", "do", "da", "em", "um", "para", "é", "com", "não", "uma", "os", "no", 
    "se", "na", "por", "mais", "as", "dos", "como", "mas", "ao", "ele", "das", "tem", "à", "seu", "sua", 
    "ou", "ser", "quando", "muito", "nos", "já", "está", "eu", "também", "só", "pelo", "pela", "até", 
    "isso", "ela", "entre", "depois", "sem", "mesmo", "aos", "ter", "seus", "quem", "nas", "me", "esse", 
    "eles", "estão", "você", "tinha", "foram", "essa", "num", "nem", "suas", "meu", "às", "minha", "têm", 
    "numa", "pelos", "elas", "havia", "seja", "qual", "será", "nós", "tenho", "lhe", "deles", "essas", 
    "esses", "pelas", "este", "fosse", "dele", "tu", "te", "vocês", "vos", "lhes", "meus", "minhas", 
    "teu", "tua", "teus", "tuas", "nosso", "nossa", "nossos", "nossas", "ok", "foi"
]
stopwords_pt.update(lista_extra)

# Cria versão normalizada das stopwords (sem acento) para bater com o texto limpo
stopwords_normalizadas = set([remover_acentos(w) for w in stopwords_pt])


# --- CORES PERSONALIZADAS ---
COLOR_NAVY = "#1F3C73"
COLOR_GOLD = "#F2C94C"
COLOR_WHITE = "#FFFFFF"

def criar_colormap_personalizado(nome, lista_cores):
    return LinearSegmentedColormap.from_list(nome, lista_cores, N=256)

cmap_navy_gold = criar_colormap_personalizado("NavyGold", [COLOR_NAVY, "#4a6fa5", COLOR_GOLD])
cmap_navy_only = criar_colormap_personalizado("NavyOnly", ["#0d1a33", COLOR_NAVY, "#4a6fa5"])
cmap_gold_only = criar_colormap_personalizado("GoldOnly", ["#997a00", COLOR_GOLD, "#ffe082"])

NOVAS_CORES = [cmap_navy_gold, cmap_navy_only, cmap_gold_only]


# --- LAYOUT E ESTILO ---
st.set_page_config(page_title="Dashboard Ao Vivo", layout="wide")

hide_st_style = f"""
            <style>
            #MainMenu {{visibility: hidden;}}
            footer {{visibility: hidden;}}
            header {{visibility: hidden;}}
            .stApp {{
                background-color: {COLOR_WHITE};
            }}
            h1, h2, h3 {{
                color: {COLOR_NAVY} !important;
            }}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# --- LAYOUT DE TOPO CORRIGIDO (PARA NÃO CORTAR LOGO) ---
# Usamos [1.5, 4.5] para dar um espaço generoso à esquerda
col_logo, col_titulo = st.columns([1.5, 4.5]) 

with col_logo:
    try:
        # use_container_width=True faz a imagem ocupar 100% da coluna sem cortar
        st.image(NOME_ARQUIVO_LOGO, use_container_width=True) 
    except:
        st.write("") 

with col_titulo:
    # Espaços para alinhar o texto verticalmente com a imagem
    st.write("") 
    st.write("") 
    st.title("🚀 Orgulho de fazer parte | Nosso Legado em 2025")

st.markdown(f"---") 

# --- FUNÇÕES ---
def conectar_gsheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client

def buscar_dados():
    try:
        client = conectar_gsheets()
        sheet = client.open(NOME_PLANILHA).sheet1
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.warning("Conectando à planilha...") 
        return pd.DataFrame()

# --- CÁLCULO DE FREQUÊNCIAS (LÓGICA NOVA) ---
def calcular_frequencias(lista_textos):
    """
    1. Remove acentos.
    2. Conta unigramas e bigramas.
    3. Subtrai contagem: Se 'novos aprendizados' existe, tira ponto de 'novos'.
    """
    
    # 1. Normaliza todo o texto (sem acento)
    textos_limpos = [remover_acentos(t) for t in lista_textos]
    
    # Usa stopwords normalizadas
    cv = CountVectorizer(ngram_range=(1, 2), stop_words=list(stopwords_normalizadas))
    
    try:
        # Cria a matriz
        X = cv.fit_transform(textos_limpos)
        sum_words = X.sum(axis=0) 
        
        # Dicionário Geral (Frases + Palavras)
        freqs_geral = {word: sum_words[0, idx] for word, idx in cv.vocabulary_.items()}
        
        # Separa Frases (tem espaço) de Palavras (não tem espaço)
        bigramas = {k: v for k, v in freqs_geral.items() if " " in k}
        unigramas = {k: v for k, v in freqs_geral.items() if " " not in k}
        
        # A Lógica de Subtração
        for frase, count in bigramas.items():
            palavras = frase.split(" ") 
            for p in palavras:
                # Se a palavra existe sozinha, subtrai a contagem da frase
                if p in unigramas:
                    unigramas[p] -= count
        
        # Reconstrói o dicionário final
        dicionario_final = bigramas.copy() # Prioridade para as frases
        
        for palavra, count in unigramas.items():
            if count > 0: # Só entra se sobrou contagem
                dicionario_final[palavra] = count
                
        return dicionario_final
    
    except ValueError:
        return {}

def gerar_figura_nuvem_com_borda(frequencias_dict, cor_mapa, cor_borda):
    # Gera nuvem a partir do dicionário já limpo
    wordcloud = WordCloud(
        width=800,
        height=600,
        background_color='white', 
        colormap=cor_mapa,        
        min_font_size=12,
        max_words=50,             
        random_state=42,          
        collocations=False # False pois já calculamos manualmente
    ).generate_from_frequencies(frequencias_dict) 

    # Plotagem
    fig, ax = plt.subplots(figsize=(8, 6), facecolor='none')
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis("off")

    # Borda Arredondada
    fancy_box = mpatches.FancyBboxPatch(
        (0, 0), 1, 1,                                      
        boxstyle="round,pad=0.05,rounding_size=0.3", 
        linewidth=4,                                       
        edgecolor=cor_borda,                               
        facecolor='none',                                  
        transform=ax.transAxes,                            
        clip_on=False                                      
    )
    ax.add_patch(fancy_box)
    plt.tight_layout(pad=1.5) 
    return fig

# --- CONTAINER PRINCIPAL ---
placeholder = st.empty()

while True:
    with placeholder.container():
        df = buscar_dados()

        if not df.empty:
            col1, col2, col3 = st.columns(3)
            colunas_streamlit = [col1, col2, col3]

            for i, nome_coluna_sheet in enumerate(COLUNAS_PERGUNTAS):
                if i < len(colunas_streamlit):
                    with colunas_streamlit[i]:
                        st.subheader(TITULOS_VISUAIS[i])
                        
                        if nome_coluna_sheet in df.columns:
                            # Pega os textos da coluna
                            textos_lista = df[nome_coluna_sheet].dropna().astype(str).tolist()
                            
                            if len(textos_lista) > 0:
                                try:
                                    # 1. Calcula Frequências com lógica inteligente
                                    freq_dict = calcular_frequencias(textos_lista)
                                    
                                    if freq_dict:
                                        # 2. Gera Nuvem
                                        fig = gerar_figura_nuvem_com_borda(
                                            freq_dict, 
                                            NOVAS_CORES[i], 
                                            COLOR_NAVY
                                        )
                                        st.pyplot(fig, use_container_width=True)
                                        plt.close(fig)
                                        st.markdown(f"<p style='color:gray; font-size:0.8em;'>{len(textos_lista)} respostas</p>", unsafe_allow_html=True)
                                    else:
                                         st.info("Insira palavras significativas.")
                                except Exception as e:
                                     st.error(f"Erro ao gerar: {e}")
                            else:
                                st.info("Aguardando primeiras respostas...")
                        else:
                            st.warning(f"Coluna '{TITULOS_VISUAIS[i]}' pendente.")
        else:
            st.info("Aguardando conexão com a planilha ou a planilha está vazia...")

    time.sleep(TEMPO_REFRESH)
