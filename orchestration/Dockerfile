FROM apache/airflow:2.10.4-python3.12
USER root
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 ca-certificates \
    && update-ca-certificates && rm -rf /var/lib/apt/lists/*
USER airflow
COPY requirements-airflow.txt /tmp/req.txt
RUN pip install --no-cache-dir -r /tmp/req.txt
