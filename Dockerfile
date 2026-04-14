FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
COPY src /app/src
COPY frontend /app/frontend
COPY config.example.yaml /app/config.example.yaml
COPY data /app/data
ENV PYTHONPATH=/app/src
EXPOSE 8000
CMD ["uvicorn", "traceable_ai_compliance_agent.api:app", "--host", "0.0.0.0", "--port", "8000"]
