FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 APP_ENV=production PORT=8000
WORKDIR /app
RUN groupadd --system cuentaluz && useradd --system --gid cuentaluz --home /app cuentaluz
COPY requirements.lock ./
RUN pip install --no-cache-dir --upgrade pip setuptools && pip install --no-cache-dir -r requirements.lock
COPY --chown=cuentaluz:cuentaluz app app
COPY --chown=cuentaluz:cuentaluz config config
COPY --chown=cuentaluz:cuentaluz templates templates
COPY --chown=cuentaluz:cuentaluz static static
COPY --chown=cuentaluz:cuentaluz data/tarifas_historico.json data/tarifas_historico.json
COPY --chown=cuentaluz:cuentaluz main.py database.py ./
COPY --chown=cuentaluz:cuentaluz scripts/backup_sqlite.py scripts/monitor_health.py ops/
RUN chown cuentaluz:cuentaluz /app/data
USER cuentaluz
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s CMD python -c "import os,urllib.request; r=urllib.request.Request('http://127.0.0.1:'+os.getenv('PORT','8000')+'/health/ready',headers={'Host':os.environ['ALLOWED_HOSTS'].split(',')[0]}); urllib.request.urlopen(r, timeout=4)"
CMD ["sh", "-c", "exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --no-access-log --limit-concurrency 100 --timeout-keep-alive 5"]
