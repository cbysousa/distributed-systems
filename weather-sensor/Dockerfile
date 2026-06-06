FROM python:3.12-slim

WORKDIR /app

RUN pip install protobuf

COPY *.py ./

CMD ["python", "-u", "sensor.py"]
