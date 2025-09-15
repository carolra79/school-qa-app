FROM public.ecr.aws/docker/library/python:3.11-slim

WORKDIR /app

RUN pip install streamlit boto3

COPY app_agentcore.py .
COPY config.py .
COPY st-marys-logo.png .

EXPOSE 8501

CMD ["streamlit", "run", "app_agentcore.py", "--server.port=8501", "--server.address=0.0.0.0"]
