# Word Cloud Dashboard

Dashboard interativo em tempo real para visualização de nuvens de palavras a partir de respostas de formulários do Google Sheets.

## Funcionalidades

- Conexão automática com Google Sheets
- Geração de 3 nuvens de palavras simultâneas
- Atualização automática a cada 10 segundos
- Paleta de cores personalizada (Azul Marinho e Dourado)
- Interface limpa e profissional

## Instalação

1. Instale as dependências:
```bash
pip install -r requirements.txt
```

2. Configure as credenciais do Google Sheets:
   - Crie um arquivo `credentials.json` com as credenciais de serviço do Google Cloud
   - Coloque o arquivo na raiz do projeto

## Uso

Execute o aplicativo Streamlit:
```bash
streamlit run app.py
```

## Configuração

Edite as variáveis no início do arquivo `app.py`:
- `NOME_PLANILHA`: Nome da planilha do Google Sheets
- `COLUNAS_PERGUNTAS`: Lista com os nomes exatos das colunas
- `TEMPO_REFRESH`: Intervalo de atualização em segundos

