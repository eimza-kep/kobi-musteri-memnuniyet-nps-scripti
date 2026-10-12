FROM python:3.12-alpine

WORKDIR /app

COPY . /app

RUN chmod -R 755 /app

ENV PORT=8091
EXPOSE 8091

CMD ["python", "server.py"]
