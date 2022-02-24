FROM python:3 

WORKDIR /app
COPY . /app
USER root

RUN mkdir -p /shared /playlists /config
RUN pip install -r /app/requirements.txt

USER root 
ENTRYPOINT ["python3", "-u", "/app/entrypoint.py"]