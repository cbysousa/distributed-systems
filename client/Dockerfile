FROM python:3.12-slim

WORKDIR /app

RUN pip install protobuf flask

COPY . .

CMD ["python", "-u", "web_client.py"]
