FROM python:3.12-slim-bookworm@sha256:e697c81897302a4c4333bade000d98038fbb21eb064f8ee1fd42d02ebcd9d337
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DT_CONTAINER_HEADLESS=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglfw3 && rm -rf /var/lib/apt/lists/*
COPY docker/requirements.lock /app/requirements.txt
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY mujoco /app/mujoco
COPY research_scope.json /app/research_scope.json
RUN python - <<'PY'
from pathlib import Path
import hashlib,json,platform
import mujoco,numpy
root=Path('/app');paths=sorted(p for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
manifest={'python':platform.python_version(),'mujoco':mujoco.__version__,'numpy':numpy.__version__,'scope':'event_monitoring_focus_v1','review_status_at_build':'candidate-awaiting-human-validation','files':{p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
(root/'source_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
PY
RUN useradd --uid 10001 --no-create-home twin && mkdir -p /app/output && chown twin /app/output
ARG DT_VERSION=candidate-20261106-monitoring-focus
LABEL org.opencontainers.image.title="Event-Based Predictive Monitoring Testbed" org.opencontainers.image.version="${DT_VERSION}"
USER 10001
ENTRYPOINT ["python"]
CMD ["-m", "unittest", "discover", "-s", "mujoco", "-p", "test_eta*.py", "-v"]
