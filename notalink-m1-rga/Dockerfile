FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir hatchling && pip install --no-cache-dir -e .
COPY . .
RUN adduser --disabled-password --gecos '' nota
USER nota
ENV FLASK_APP=app:create_app
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
