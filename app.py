import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
import time

# --- NOVO IMPORT NECESSÁRIO PARA A LÓGICA DE BIGRAMAS ---
from sklearn.feature_extraction.text import CountVectorizer

# --- CONFIGURAÇÕES ---
NOME_PLANILHA = "Respostas Conecta Sede"

# LISTA com os nomes exatos das 3 colunas (Cabeçalhos)
COLUNAS_PERGUNTAS = [
    "De quais projetos/resultados da minha equipe tenho orgulho?",   # Coluna 1
    "O quê de bom aconteceu na Sede/Desenvolvimento Econômico que eu me orgulho?",       # Coluna 2
    "Do quê eu me orgulho em mim como profissional em 2025?"          # Coluna 3
]

# Títulos curtos para aparecer em cima de cada nuvem (Opcional)
TITULOS_VISUAIS = [
    "Projetos do time",
    "Sucessos da Sede",
    "Eu Profissional"
]

TEMPO_REFRESH = 10

# --- CONFIGURAÇÃO DE STOPWORDS (CONECTIVOS A IGNORAR) ---
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

# --- NOVA LÓGICA: GERAR DICIONÁRIO DE FREQUÊNCIA ---
def calcular_frequencias(lista_textos):
    """
    Recebe uma lista de frases e retorna um dicionário {palavra: contagem},
    considerando unigramas e bigramas (ex: 'novos aprendizados').
    """
    # ngram_range=(1, 2) -> Pega palavras sozinhas E pares de palavras
    cv = CountVectorizer(ngram_range=(1, 2), stop_words=list(stopwords_pt))
    
    try:
        # Cria a matriz de contagem (Fit e Transform)
        X = cv.fit_transform(lista_textos)
        
        # Soma as colunas da matriz (total de vezes que cada termo apareceu)
        sum_words = X.sum(axis=0) 
        
        # Cria lista de tuplas [(palavra, freq), ...]
        words_freq = [(word, sum_words[0, idx]) for word, idx in cv.vocabulary_.items()]
        
        # Ordena e transforma em dicionário
        words_freq = sorted(words_freq, key = lambda x: x[1], reverse=True)
        return dict(words_freq)
    
    except ValueError:
        # Acontece se o vocabulário ficar vazio (só tem stopwords)
        return {}

def gerar_figura_nuvem_com_borda(frequencias_dict, cor_mapa, cor_borda):
    """
    Agora recebe um Dicionário de Frequências em vez de texto cru.
    """
    # 1. Gera a nuvem de palavras A PARTIR DAS FREQUÊNCIAS
    wordcloud = WordCloud(
        width=800,
        height=600,
        background_color='white', 
        colormap=cor_mapa,        
        min_font_size=12,
        max_words=50,             
        # stopwords não precisa aqui, pois já limpamos no CountVectorizer, mas mal não faz
        random_state=42,          
        collocations=False        # Importante: False porque nós já calculamos as collocations (bigramas) manualmente
    ).generate_from_frequencies(frequencias_dict) # <--- MUDANÇA CRUCIAL AQUI

    # 2. Configura a figura do Matplotlib
    fig, ax = plt.subplots(figsize=(8, 6), facecolor='none')
    
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis("off")

    # 3. Borda
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

# --- CONTAINER PRINCIPAL (LOOP) ---
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
                            # Pega a lista de textos crua (sem dar join ainda)
                            textos_lista = df[nome_coluna_sheet].dropna().astype(str).tolist()
                            
                            # Verifica se tem conteúdo
                            if len(textos_lista) > 0:
                                try:
                                    # 1. CALCULA FREQUÊNCIAS (COM BIGRAMAS)
                                    freq_dict = calcular_frequencias(textos_lista)
                                    
                                    if freq_dict:
                                        # 2. GERA NUVEM COM BASE NO DICIONÁRIO
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
