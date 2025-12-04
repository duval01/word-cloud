import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from wordcloud import WordCloud, STOPWORDS
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
import time

# --- CONFIGURAÇÕES ---
NOME_PLANILHA = "Formulário sem título (respostas)"

# LISTA com os nomes exatos das 3 colunas (Cabeçalhos)
COLUNAS_PERGUNTAS = [
    "De quais projetos/resultados da minha equipe tenho orgulho?",   # Coluna 1
    "O quê de bom aconteceu na Sede/Desenvolvimento Econômico que eu me orgulho?",      # Coluna 2
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
# Isso impede que palavras como "de", "que", "para" fiquem gigantes na nuvem
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


# --- CORES PERSONALIZADAS (Baseadas no print CONECTA SEDE) ---
# Azul Marinho do cabeçalho e Dourado do logo
COLOR_NAVY = "#1F3C73"
COLOR_GOLD = "#F2C94C"
COLOR_WHITE = "#FFFFFF"

# Função para criar mapas de cores (colormaps) personalizados
def criar_colormap_personalizado(nome, lista_cores):
    return LinearSegmentedColormap.from_list(nome, lista_cores, N=256)

# Criando 3 variações de paletas dentro do tema
cmap_navy_gold = criar_colormap_personalizado("NavyGold", [COLOR_NAVY, "#4a6fa5", COLOR_GOLD])
cmap_navy_only = criar_colormap_personalizado("NavyOnly", ["#0d1a33", COLOR_NAVY, "#4a6fa5"])
cmap_gold_only = criar_colormap_personalizado("GoldOnly", ["#997a00", COLOR_GOLD, "#ffe082"])

# Lista com as novas paletas
NOVAS_CORES = [cmap_navy_gold, cmap_navy_only, cmap_gold_only]


# --- LAYOUT E ESTILO ---
st.set_page_config(page_title="Dashboard Ao Vivo", layout="wide")

# CSS para esconder menu, rodapé e ajustar fundo se necessário
hide_st_style = f"""
            <style>
            #MainMenu {{visibility: hidden;}}
            footer {{visibility: hidden;}}
            header {{visibility: hidden;}}
            /* Ajuste opcional para o fundo geral da página combinar com o slide */
            .stApp {{
                background-color: {COLOR_WHITE};
            }}
            /* Ajuste da cor dos títulos para o azul marinho */
            h1, h2, h3 {{
                color: {COLOR_NAVY} !important;
            }}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

st.title("🚀 Orgulho de fazer parte | Nosso Legado em 2025")
st.markdown(f"---") # Linha separadora

# --- FUNÇÕES ---
def conectar_gsheets():
    # Define o escopo de autorização
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # EM VEZ DE LER O ARQUIVO, LEMOS OS SEGREDOS DO STREAMLIT
    # st.secrets funciona como um dicionário seguro
    creds_dict = st.secrets["gcp_service_account"]
    
    # Usamos o método from_json_keyfile_dict (note o _dict no final)
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
        # st.error(f"Erro de conexão: {e}") # Escondendo erro para não sujar a tela de apresentação
        st.warning("Conectando à planilha...") # Mensagem mais suave
        return pd.DataFrame()

def gerar_figura_nuvem_com_borda(texto, cor_mapa, cor_borda):
    # 1. Gera a nuvem de palavras
    wordcloud = WordCloud(
        width=800,
        height=600,
        background_color='white', # Fundo branco dentro da nuvem
        colormap=cor_mapa,        # Usa a nossa paleta personalizada
        min_font_size=12,
        max_words=50,             # CORREÇÃO: Reduzido de 150 para 50 para aumentar o tamanho das palavras
        stopwords=stopwords_pt,   # CORREÇÃO: Adicionada lista de stopwords
        random_state=42,          # Garante consistência das cores
        collocations=False        # Evita duplicar frases (opcional, mas ajuda na limpeza)
    ).generate(texto)

    # 2. Configura a figura do Matplotlib
    # facecolor='none' deixa o fundo da figura transparente para não criar uma caixa branca extra
    fig, ax = plt.subplots(figsize=(8, 6), facecolor='none')
    
    # Mostra a imagem da nuvem
    ax.imshow(wordcloud, interpolation='bilinear')

    # Desliga os eixos padrões (linhas retas e números)
    ax.axis("off")

    # 3. ADICIONA A BORDA ARREDONDADA (Formato de "Nuvem"/Balão)
    # Usamos um FancyBboxPatch para criar uma borda muito arredondada
    fancy_box = mpatches.FancyBboxPatch(
        (0, 0), 1, 1,                                  # Coordenadas relativas (cobre todo o ax)
        boxstyle="round,pad=0.05,rounding_size=0.3", # Estilo arredondado
        linewidth=4,                                   # Espessura da borda (mais grossa)
        edgecolor=cor_borda,                           # Cor da borda (Azul Marinho)
        facecolor='none',                              # Sem preenchimento para ver as palavras
        transform=ax.transAxes,                        # Importante para alinhar ao tamanho do gráfico
        clip_on=False                                  # Permite que a borda grossa saia um pouco da área
    )
    ax.add_patch(fancy_box)

    plt.tight_layout(pad=1.5) # Garante espaço para a borda grossa não cortar
    return fig

# --- CONTAINER PRINCIPAL (LOOP) ---
placeholder = st.empty()

while True:
    with placeholder.container():
        # Tenta buscar dados. Se falhar, df virá vazio.
        df = buscar_dados()

        if not df.empty:
            # Cria 3 colunas no Streamlit
            col1, col2, col3 = st.columns(3)
            colunas_streamlit = [col1, col2, col3]

            # Loop para gerar as 3 nuvens
            for i, nome_coluna_sheet in enumerate(COLUNAS_PERGUNTAS):
                # Garante que não vamos tentar acessar uma coluna que não existe no layout
                if i < len(colunas_streamlit):
                    with colunas_streamlit[i]:
                        # Títulos com a cor azul marinho (definido no CSS lá em cima)
                        st.subheader(TITULOS_VISUAIS[i])

                        if nome_coluna_sheet in df.columns:
                            # Pega o texto, remove vazios e converte para string
                            textos = df[nome_coluna_sheet].dropna().astype(str).tolist()
                            
                            # CORREÇÃO: Adicionado .lower() para normalizar (Teste == teste)
                            texto_completo = " ".join(textos).lower()

                            # Verifica se tem texto suficiente (pelo menos algumas letras)
                            if len(texto_completo.strip()) > 5:
                                try:
                                    # Chama a função de gerar figura
                                    fig = gerar_figura_nuvem_com_borda(
                                        texto_completo,
                                        NOVAS_CORES[i], # Usa as novas paletas
                                        COLOR_NAVY      # Usa o azul marinho para a borda
                                    )
                                    # use_container_width=True ajuda a ajustar a imagem à coluna
                                    st.pyplot(fig, use_container_width=True)
                                    plt.close(fig)
                                    # Caption com cor mais discreta
                                    st.markdown(f"<p style='color:gray; font-size:0.8em;'>{len(textos)} respostas</p>", unsafe_allow_html=True)
                                except ValueError:
                                    st.info("Poucas palavras para gerar nuvem.")
                                except Exception as e:
                                     st.error(f"Erro ao gerar nuvem: {e}")

                            else:
                                st.info("Aguardando primeiras respostas...")
                        else:
                            # Mensagem de erro mais discreta em produção
                            st.warning(f"Coluna '{TITULOS_VISUAIS[i]}' pendente.")

        else:
            # Se não conseguiu dados, mostra uma mensagem de espera.
            # O loop vai tentar de novo em breve.
            st.info("Aguardando conexão com a planilha ou a planilha está vazia...")

    # Pausa antes do próximo refresh
    time.sleep(TEMPO_REFRESH)
