FROM python:3.12-slim-bookworm@sha256:e697c81897302a4c4333bade000d98038fbb21eb064f8ee1fd42d02ebcd9d337

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DT_CONTAINER_HEADLESS=1
ENV DT_DEFAULT_PROFILE=mujoco/configs/reconfigurable_cell_20261030.json
WORKDIR /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgl1 libglfw3 \
    && rm -rf /var/lib/apt/lists/*
COPY docker/requirements.lock /app/requirements.txt
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY mujoco /app/mujoco
COPY web /app/web
COPY cad_reference/production_twin_v0_parts.csv /app/cad_reference/production_twin_v0_parts.csv
COPY scripts/portable_bundle/launch.py /app/launch.py
COPY docker/snapshot.py /app/docker/snapshot.py
RUN python docker/snapshot.py \
    && useradd --uid 10001 --no-create-home twin \
    && mkdir -p /app/output \
    && chown twin /app/output
ARG DT_VERSION=candidate-20261104-sensor-drive-v2
LABEL org.opencontainers.image.title="Production Twin DT Core" \
      org.opencontainers.image.version="${DT_VERSION}" \
      vn.production-twin.review-status-at-build="candidate-awaiting-human-validation"
USER 10001
ENTRYPOINT ["python", "/app/launch.py"]
CMD ["demo"]
