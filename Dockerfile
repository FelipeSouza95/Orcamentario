# Imagem base leve com Python
FROM python:3.10-slim

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia os arquivos do projeto
COPY . .

# Instala dependências
RUN pip install --no-cache-dir -r requirements.txt

# Exponha a porta usada pelo Streamlit
EXPOSE 3103

# Comando para iniciar o Streamlit
CMD ["streamlit", "run", "app/main.py", "--server.port=3104", "--server.address=0.0.0.0"]
