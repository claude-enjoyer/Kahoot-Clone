FROM python:3.12.3-slim

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libcurl4-openssl-dev \
    make \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY . .

RUN python3 manage.py migrate

EXPOSE 8000 

CMD sh -c "python manage.py runserver 0.0.0.0:8000"