# slim = a smaller Python base image with just enough to run Python,
# not a full OS worth of extra tools you won't use.
FROM python:3.12-slim

WORKDIR /app

# Copy just the dependency list first, before the actual code. Docker
# caches each step — as long as requirements.txt hasn't changed, this
# install step is reused instead of re-run every time you edit app code.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

# ENTRYPOINT + CMD split: ENTRYPOINT is fixed (always run Python),
# CMD is the default argument (run store.py) but can be overridden,
# e.g. `docker run <image> app/embed.py "some text"`.
ENTRYPOINT ["python"]
CMD ["app/store.py"]
