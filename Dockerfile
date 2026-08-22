FROM python:3.10.19-slim-bookworm
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PORT=8000
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/* \
    && groupadd --system --gid 10001 mexingsof \
    && useradd --system --uid 10001 --gid mexingsof --home /nonexistent --shell /usr/sbin/nologin mexingsof
COPY requirements.txt ./
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt "uvicorn>=0.23,<1" \
    && python -m pip check
COPY . .
RUN chmod 0555 /app/docker-entrypoint.sh && chown -R 10001:10001 /app
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=45s --retries=5 \
  CMD ["python", "-c", "import os,socket;s=socket.create_connection(('127.0.0.1',int(os.getenv('PORT','8000'))),5);s.close()"]
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["serve"]
