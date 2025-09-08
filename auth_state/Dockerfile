FROM python:3.13.7-alpine3.22

# NOTE: install dash for diagnostics
# NOTE: install tini as a small init system on PID 1. this will ensure things
#       like SIGTERM make it to python cleanly
RUN apk add --no-cache tini dash

# PYTHONDONTWRITEBYTECODE=1 prevent python from making *.pyc files
# PYTHONUNBUFFERED=1 force python to flush stdout/stderr immediately
ENV \
	PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1

# SOCK_PATH is where the unix socket will live so `auth` container can connect
# STATE_PATH is where the json file will live to have persistent state
# REFRESH_TTL_DAYS https://www.varonis.com/blog/dns-ttl
ENV \
	SOCK_PATH=/sockets/refresh_state.sock \
	STATE_PATH=/state/refresh_state.json \
	REFRESH_TTL_DAYS=14

# NOTE: docker containers are run as root by default usually, this is bad for
#       an user auth system, we make a new user so if someone escapes the app,
#       they cannot get root in the container
# create new user and group 'app' with UID=10001 and GID=10001
ARG UID=10001
ARG GID=10001
RUN addgroup -g ${GID} app && adduser -D -u ${UID} -G app app

WORKDIR /app
COPY . .

# create runtime dirs for socket + persisted state, ensure ownership is 'app'
RUN mkdir -p /sockets /state && chown -R app:app /sockets /state

# make container run as the user 'app' not root
USER app:app

# NOTE: run tini first so it gets assigned PID 1, also it needs to be running
#       first so the state_server can use it without delay
ENTRYPOINT ["/sbin/tini", "-g", "--"]

CMD ["python", "state_server.py"]
