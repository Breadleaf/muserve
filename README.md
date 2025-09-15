# Muserve

Muserve is a self hosted music streaming platform that allows for multiple users
to occupy one cloud, share music, and build playlists. Bring your own mp3, wav,
etc and stream it from your server to your computer and eventually phone!

## Topology

![topology](./topology.png)

![graph editor](https://csacademy.com/app/graph_editor/)

config:
```
postgres
minio
nginx

auth_state
auth

bootstrap_admin

database_handler

storage_handler

app

VOLUME:postgres_data
VOLUME:minio_data
VOLUME:auth_sock
VOLUME:auth_state

nginx app
app nginx

nginx auth
auth nginx

postgres database_handler
database_handler postgres

minio storage_handler
storage_handler minio

VOLUME:postgres_data postgres
postgres VOLUME:postgres_data

VOLUME:minio_data minio
minio VOLUME:minio_data

auth_state auth
auth auth_state

auth_state VOLUME:auth_sock
VOLUME:auth_sock auth_state

auth_state VOLUME:auth_state
VOLUME:auth_state auth_state

auth VOLUME:auth_sock
VOLUME:auth_sock auth

nginx storage_handler
storage_handler nginx

bootstrap_admin postgres

nginx database_handler
database_handler nginx
```
