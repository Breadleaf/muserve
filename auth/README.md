# Muserve Auth Server

## Usage

### /health

`/health` is the endpoint anyone can call to see if the auth server is online

```
curl -f http://localhost:7000/auth/health
```

### /register

`/register` is the endpoint to register a new user in the database

```
curl -i -X POST http://localhost:7000/auth/register \
    -H 'Content-Type: application/json' \
    -d '{"name": "test", "email": "test@example.com", "password": "test1234"}'
```

### /login

`/login` is the endpoint which a user can receive a new action and refresh token

```
ACTION_TOKEN=$(curl -s -X POST http://localhost:7000/auth/login \
    -H 'Content-Type: application/json' \
    -d '{"email": "test@example.com", "password": "test1234"}' \
    -c rt.txt | jq -r .action_token)
```

### /refresh

`/refresh` is the endpoint a user can rotate their refresh token

```
ACTION_TOKEN=$(curl -s -X POST http://localhost:7000/auth/refresh \
    -b rt.txt -c rt.txt | jq -r .action_token)
```

### /logout

`/logout` is the endpoint the user can revoke their current refresh token, this
is also known as a device logout

```
curl -i -b rt.txt -c /dev/null -X POST http://localhost:7000/auth/logout
```

### /logout_all

`/logout_all` is the endpoint where the user can revoke their whole family, this
is also known as signout of all devices

```
curl -i -b rt.txt -H "Authorization: Bearer $ACTION_TOKEN" \
    -X POST http://localhost:7000/auth/logout_all
```

### /me

`/me` is the endpoint which a user can use to find their user id

```
curl -s -H "Authorization: Bearer $ACTION_TOKEN" http://localhost:7000/auth/me
```

### TODO update sections

```
ACTION_TOKEN=$(curl -k -s -c rt.txt \
-H 'Content-Type: application/json' \
-d '{"email": "admin", "password": "admin"}' \
-X POST https://localhost:8443/auth/login \
| jq -r .action_token)
```

```
$ curl -k -i -X POST https://localhost:8443/auth/register \
-H 'Content-Type: application/json' \
-H "Authorization: Bearer $ACTION_TOKEN" \
-d '{"name": "test", "email": "test@gmail.com", "password": "1234"}'
```
