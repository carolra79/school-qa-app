FROM public.ecr.aws/docker/library/python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app_agentcore.py .
COPY config.py .
COPY bedrock_config.json .
COPY fallback_links.json .
COPY st-marys-logo.png .

EXPOSE 8501

CMD ["streamlit", "run", "app_agentcore.py", "--server.port=8501", "--server.address=0.0.0.0"]
