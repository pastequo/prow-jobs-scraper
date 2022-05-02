Start ES and Kibana stack
=========================

# Prerequisites

`docker-compose` is installed on your system, and your `vm.max_map_count` is large enough:
```
$ sysctl -w vm.max_map_count=262144
```

# Start ES and Kibana

```
$ docker-compose up -d
```

Kibana should be accessible on `http://localhost:5601/` use `elastic` as user, the password is defined in the `.env` file.