FROM python:3

COPY app /app
COPY config.yson /config.yson
COPY entrypoint.sh /entrypoint.sh

RUN pip install -r /app/requirements.txt

CMD bash /entrypoint.sh
