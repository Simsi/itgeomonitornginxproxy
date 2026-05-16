FROM python:3.12-alpine

WORKDIR /app
COPY rewrite_proxy.py /app/rewrite_proxy.py

ENV PYTHONUNBUFFERED=1

CMD ["python", "/app/rewrite_proxy.py"]
