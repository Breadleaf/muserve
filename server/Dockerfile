FROM python:3.13.7-alpine3.22

WORKDIR /app

COPY requirements.txt .
COPY example.json .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py", "--conf", "example.json"]
