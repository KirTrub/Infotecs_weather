FROM python:3.14.6-slim

WORKDIR /app


COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY . .

RUN chmod +x docker-entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
