# Shared-password gate for Caddy forward_auth (see auth_gate.py).
# Flask is baked in so the gate starts instantly and doesn't need the internet to boot.
FROM python:3.12-alpine
RUN pip install --no-cache-dir flask==3.1.3
COPY auth_gate.py /app/auth_gate.py
WORKDIR /app
USER nobody
CMD ["python3", "auth_gate.py"]
