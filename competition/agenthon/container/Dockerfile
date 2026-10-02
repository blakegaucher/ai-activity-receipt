ARG PYTHON_BASE
FROM ${PYTHON_BASE}
LABEL qfbench2.interface_version="2.0"
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY baseline_agent ./baseline_agent
COPY baseline_agent.py ./baseline_agent.py
USER 65534:65534
ENTRYPOINT ["python", "baseline_agent.py"]
CMD ["analyze", "--help"]
