## Docker reference environment variables

### PostgreSQL

**Postgreql cli**

```bash
podman exec -it <postgresql container> psql -U <username> -d <database name>
```

- List of roles

```bash
<database name>=# \du
```

- List of tables

```bash
<database name>=# \dt
```

**Reference**

[PostgreSQL docker hub](https://hub.docker.com/_/postgres#environment-variables)

### Redis

**Redis cli**

```bash
podman exec -it <redis container> redis-cli
```

**Reference**

[Redis docker hub](https://hub.docker.com/_/redis)
[Redis CLI](https://redis.io/docs/latest/develop/tools/cli/)
[Redis configuration](https://redis.io/docs/latest/operate/oss_and_stack/management/config/)

ในการ Set password หรือ environment ต่างๆ Redis นิยมใช้ผ่าน Redis cli
นอกจากนี้ยังสามารถใช้ Redis config โดยใช้ file `redis.conf` เพื่อใช้เป็น config ให้กับ Redis ใน docker image ได้ด้วย
