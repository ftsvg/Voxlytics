FROM python:3.13-slim

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt \
    && pip install gunicorn

ENV ENV=dev

CMD ["sh", "-c", "if [ \"$ENV\" = \"prod\" ]; then gunicorn apps.website.app:app --bind 0.0.0.0:5000; else python -m apps.website.app; fi"]