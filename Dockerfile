FROM python:3

COPY app /app
COPY config.yaml /config.yaml
COPY entrypoint.sh /entrypoint.sh

RUN pip install --upgrade pip
RUN pip install -r /app/requirements.txt

CMD bash /entrypoint.sh
