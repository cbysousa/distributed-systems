
FROM python:3.12-slim

WORKDIR /app

RUN pip install protobuf grpcio-tools

COPY contracts/ /contracts/
COPY client/client.py .

RUN python -m grpc_tools.protoc \
    -I /contracts \
    --python_out=/app \
    /contracts/cam.proto \
    /contracts/lamppost.proto \
    /contracts/semaphore.proto \
    /contracts/client.proto

CMD ["python", "client.py"]