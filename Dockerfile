FROM python:3.11-slim-bullseye

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt clean && apt update && apt install curl netcat vim gettext -y

WORKDIR /telegram_app
COPY . /telegram_app/

RUN pip install --no-cache-dir -r requirements.txt

COPY .deploy/entrypoint.sh /
RUN chmod +x /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["sh", "/entrypoint.sh"]
