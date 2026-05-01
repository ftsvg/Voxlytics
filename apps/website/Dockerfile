FROM python:3.13-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

ENV ENV=dev

CMD ["sh", "-c", "if [ \"$ENV\" = \"prod\" ]; then uvicorn apps.website.app:app --host 0.0.0.0 --port 5000 --workers 2; else python -m apps.website.app; fi"]