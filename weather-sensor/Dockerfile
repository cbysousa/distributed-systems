FROM python:3.12-slim

WORKDIR /app

RUN pip install protobuf

COPY sensor.py .
COPY temperature_pb2.py .

CMD ["python", "-u", "sensor.py"]