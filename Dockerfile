FROM python:3.12-slim
WORKDIR /app
COPY requirements-lock.txt ./
RUN pip install --no-cache-dir -r requirements-lock.txt
COPY starter-kit ./starter-kit
COPY pyproject.toml README.md UPSTREAM_REVISION ./
COPY aegis ./aegis
COPY tests ./tests
RUN pip install --no-cache-dir --no-deps -e ./starter-kit -e . && useradd --create-home aegis && mkdir artifacts && chown -R aegis:aegis /app
USER aegis
CMD ["python", "-m", "aegis.cli", "evaluate", "--variants", "aegis"]
