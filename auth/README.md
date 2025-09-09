## usage

login: capture HttpOnly refresh cookie and action token from JSON
```
ACTION_TOKEN=$(curl -s -X POST http://localhost:7000/login -c cookies.txt | jq -r .action_token)
```

call protected endpoint using action token
```
curl -s http://localhost:7000/me -H "Authorization: Bearer $ACTION_TOKEN"
```

when the action token expires (or when you want to rotate)
```
ACTION_TOKEN=$(curl -s -X POST http://localhost:7000/refresh -b cookies.txt -c cookies.txt | jq -r .action_token)
```

use the new action token
```
curl -s http://localhost:7000/me -H "Authorization: Bearer $ACTION_TOKEN"
```
