FROM python:3.12-alpine

# Install git (required by cookiecutter sometimes, though we are local)
RUN apk add --no-cache git

# Install cookiecutter
RUN pip install cookiecutter

# Copy the templates
COPY templates /templates

# Copy the entrypoint script
COPY entrypoint.py /entrypoint.py

WORKDIR /workdir

ENTRYPOINT ["python3", "/entrypoint.py"]
