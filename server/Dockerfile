# Dockerfile para RemotDesk Server
FROM python:3.11-slim

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Diretório de trabalho
WORKDIR /app

# Copiar requirements e instalar dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY app/ ./app/

# Expor porta
EXPOSE 8000

# Variáveis de ambiente
ENV HOST=0.0.0.0
ENV PORT=8000
ENV DEBUG=false

# Comando para iniciar
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
