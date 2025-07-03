FROM python:3.10

RUN apt-get update && apt-get install -y tesseract-ocr

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r app/requirements.txt

CMD ["gunicorn", "app:create_app()"]
