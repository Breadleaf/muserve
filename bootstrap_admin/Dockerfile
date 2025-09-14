FROM python:3.13.7-alpine3.22

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

ENV \
	BOOTSTRAP_ADMIN_NAME="admin" \
	BOOTSTRAP_ADMIN_EMAIL="admin" \
	BOOTSTRAP_ADMIN_PASSWORD="admin"

CMD ["python", "bootstrap_admin.py"]
