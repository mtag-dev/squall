FROM python:3.9-slim

RUN /usr/local/bin/pip install --no-cache-dir gunicorn uvicorn[standard] python-squall
RUN mkdir /app

COPY app.py /app
COPY sprint-response.json /app

EXPOSE 8080
WORKDIR /app

CMD /usr/local/bin/gunicorn -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8080 app:app --log-level debug
