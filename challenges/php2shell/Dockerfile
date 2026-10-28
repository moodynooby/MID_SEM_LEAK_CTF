# Pinned by digest so the challenge image is reproducible offline.
FROM python:3.11-alpine@sha256:79440cc1dfa86a5f98d67efcd219726a8e9d8083cc0aafd27c7bef5976c38868

RUN adduser -D -H -u 10001 app

WORKDIR /app

COPY app.py /app/app.py

# Uploads live inside the container; create them owned by the unprivileged user.
RUN mkdir -p /app/uploads && chown -R app:app /app

USER app

EXPOSE 5003

CMD ["python", "app.py"]
