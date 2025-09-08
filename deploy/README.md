## Usage

```
docker compose up --build # initial build
docker compose up -d # detach and send all to background
docker ps <service> # view process
docker compose logs -f <service> # follow process (like --tail)
docker compose logs --tail=<N> -f <service> # follow a process up to N lines
docker compose exec <service> # interactive shell of process
```

Note: if you are not in the `deploy/` dir, you should use the
`-f "path/to/docker-compose.yaml"` in the commands
