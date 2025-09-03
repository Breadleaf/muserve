FROM python:3.13.7-alpine3.22

WORKDIR /app

COPY . .

RUN apk add --no-cache libmagic ffmpeg libvorbis dash

RUN pip install --no-cache-dir -r requirements.txt

CMD ["gunicorn", "app:server"]
# CMD ["python", "main.py"]
