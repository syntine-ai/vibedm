FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy dependency definition files
COPY pyproject.toml uv.lock ./

# Install dependencies using uv sync (frozen, omitting dev deps for production image size)
RUN uv sync --frozen --no-dev

# Copy application source code
COPY . .

# Expose backend API port
EXPOSE 8000

# Set environment path to use the uv virtualenv bin directory
ENV PATH="/app/.venv/bin:$PATH"

# Run Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
