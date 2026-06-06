FROM python:3.12-slim

WORKDIR /app

RUN pip install protobuf grpcio-tools

COPY contracts/ /contracts/
COPY traffic-sensor/sensor.py .

RUN python -m grpc_tools.protoc \
    -I /contracts \
    --python_out=/app \
    /contracts/discovery.proto \
    /contracts/readings.proto \
    /contracts/temperature.proto \
    /contracts/air_quality.proto \
    /contracts/traffic.proto

CMD ["python", "-u", "sensor.py"]