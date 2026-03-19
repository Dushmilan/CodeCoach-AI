FROM python:3.11-alpine

WORKDIR /app
COPY qa.py pyproject.toml ./
RUN pip install -e .

ENV NVIDIA_API_KEY=""

CMD ["uvicorn", "qa:app", "--host", "0.0.0.0", "--port", "8000"]