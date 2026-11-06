# How do images, containers, volumes, and networks determine state and connectivity? / 镜像、容器、卷和网络如何决定状态留存与服务连通？

An image supplies the read-only filesystem and configuration template; a container adds a writable runtime layer; a volume stores data beyond container replacement; and a shared network gives services a path to reach one another. Port publishing exposes a container port through the host, while secrets belong in the build or runtime channel that needs them. The commands and Compose examples below show what survives removal and how services connect. / 镜像提供只读文件系统和配置模板，容器增加运行时可写层，卷让数据独立于容器替换而留存，共享网络则让服务彼此连通。端口发布通过宿主机暴露容器端口；密钥应只进入实际需要它的构建或运行时通道。下面的命令和 Compose 示例说明删除容器后什么会保留，以及服务如何通信。

Before starting a fresh `postgres:16` instance in the examples below, provide a non-empty `POSTGRES_PASSWORD` through the shell environment or a secret manager. The official image requires it to initialize an empty data directory; it can be passed at runtime without placing a credential in the image or source file. Changing the variable later does not rotate a password in an already initialized volume.

## Common operations

| Task | Command | Notes |
|---|---|---|
| Download an image | `docker pull redis:7` | Pin a tag or digest when repeatability matters; a tag may move. |
| List local images | `docker image ls` | Images can have multiple tags. |
| Create and start a container | `docker run --name cache -d redis:7` | Pulls the image if it is not available locally. |
| List running containers | `docker ps` | Add `-a` to include stopped containers. |
| Stop / start a container | `docker stop cache` / `docker start cache` | A stopped container still exists. |
| Read container logs | `docker logs cache` | Add `-f` to follow new output. |
| Run a command in a running container | `docker exec -it cache /bin/sh` | Run only when the image includes `/bin/sh`; minimal images may contain no shell. |
| Remove a stopped container | `docker rm cache` | `-f` also stops and removes a running container. |
| Remove an image | `docker image rm redis:7` | Refer to an image tag or image ID, not a container ID. |

Detached mode (such as `docker run -d`) returns the terminal while the container's main process runs. It does not supervise an application or guarantee that the container stays healthy. Use `docker ps` and `docker logs` to inspect it.

---

## Publish ports

A port mapping forwards a host port to a port in the container. This publishes a container service to the host network; it does not make the service healthy or authenticated.

~~~bash
docker run -d --name cache -p 127.0.0.1:6000:6379 redis:7
~~~

For the default bridge/NAT configuration on Docker Engine 28 and later, a localhost-published port is scoped to the Docker host. Earlier Engine releases had an exception where hosts on the same Layer 2 network could reach a localhost-published port. Check the actual Engine version, network mode and routing before relying on the bind for exposure control. [Docker port publishing, checked 2026-11-06](https://docs.docker.com/engine/network/port-publishing/) Omitting the host IP generally publishes on all host interfaces, subject to the host and Docker networking configuration. Container-to-container traffic on a shared Docker network normally uses the container port directly, not a published host port.

---

## Networks

A user-defined bridge network lets attached containers communicate by container or service name through Docker's embedded DNS. Network membership controls which containers can connect at the Docker network layer; it is not application authentication or authorization.

~~~bash
docker network create app-net
docker run -d --name db --network app-net \
  --env POSTGRES_PASSWORD postgres:16
~~~

Only expose a host port when a process outside the network needs to connect. In Compose, services join a project network by default and can usually use each other's service names as hostnames.

---

## Volumes and persistent data

Container writable layers are removed with their containers. A **named volume / 命名卷** is managed by Docker and remains after the container is removed. A **bind mount / 绑定挂载** maps a host path into the container and is useful when both host and container need the files. A volume is not a backup; plan backups and restore tests separately.

The examples pin PostgreSQL 16 and mount `/var/lib/postgresql/data`. Starting with the official PostgreSQL 18 image, the default data directory is version-specific and the recommended volume mount is `/var/lib/postgresql`. Check the image's data path when upgrading and migrate or restore the data explicitly. Changing the tag and mount point alone does not upgrade the database files. [Official Postgres image, PGDATA](https://github.com/docker-library/docs/blob/master/postgres/README.md#pgdata)

Omitting the volume source creates an anonymous volume with a generated name; it normally persists after container removal but is not automatically reused by a later container.

~~~bash
docker volume create db-data
docker run -d --name db --env POSTGRES_PASSWORD \
  --mount type=volume,src=db-data,dst=/var/lib/postgresql/data postgres:16
~~~

The destination path belongs to the image or application, so check that product's documentation. Compose declares named volumes at the top level:

~~~yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?set POSTGRES_PASSWORD}
    volumes:
      - db-data:/var/lib/postgresql/data

volumes:
  db-data:
~~~

Compose normally preserves declared named volumes on `docker compose down`. Adding `-v` removes project volumes and their data; review that effect before using it.

---

## Compose

Compose describes a multi-container application in a YAML file. The default project network provides service-name discovery, so an application container can address the database as `db` on its container port. Publish a port only when the host or another external network needs access.

~~~yaml
services:
  app:
    build: .
    environment:
      DATABASE_HOST: db
  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?set POSTGRES_PASSWORD}
    volumes:
      - db-data:/var/lib/postgresql/data

volumes:
  db-data:
~~~

~~~bash
docker compose up -d
docker compose ps
docker compose logs -f app
docker compose down
~~~

The current Compose Specification is used by Compose V2. Its top-level `version` field is obsolete and does not select a schema version. The older standalone `docker-compose` command is a legacy interface; use `docker compose` with the Compose CLI plugin.

---

## Dockerfile and image builds

A Dockerfile describes image build steps. `RUN` executes during build; `CMD` supplies a default command or arguments when a container starts; `ENTRYPOINT` defines the executable to run. A runtime command can override `CMD`.

~~~dockerfile
FROM node:22-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:22-alpine AS runtime
WORKDIR /app
ENV NODE_ENV=production
COPY package*.json ./
RUN npm ci --omit=dev
COPY --from=build /app/dist ./dist
CMD ["node", "dist/index.js"]
~~~

Build with `docker build -t my-app:1.0 .`. This example assumes a package lockfile. The build context is the set of files sent to the builder; use a `.dockerignore` file to exclude files such as local dependencies, version-control data, and secrets. Multi-stage builds keep build-only stages out of the final image unless files are copied from them. Copy only the runtime files and dependencies the application needs.

Do not put credentials in a Dockerfile's `ENV` or `ARG` values. Use a BuildKit secret mount for a credential needed during build; it is made available to the build instruction without baking it into the image. At runtime, Compose secrets can be granted to selected services and mounted as files; protect the source secret file and host.

~~~dockerfile
# syntax=docker/dockerfile:1
RUN --mount=type=secret,id=npmrc,target=/root/.npmrc npm ci
~~~

~~~bash
docker build --secret id=npmrc,src=.npmrc -t my-app:1.0 .
~~~

To push an image to a registry, authenticate with that registry, tag the image with its repository address, and push the tag. These commands use placeholders; `docker login` prompts or uses configured credentials, which should not be committed:

~~~bash
docker login registry.example.com
docker tag my-app:1.0 registry.example.com/team/my-app:1.0
docker push registry.example.com/team/my-app:1.0
~~~

Sources: [official PostgreSQL image environment variables and secrets](https://github.com/docker-library/docs/blob/master/postgres/README.md#environment-variables), [Docker image and container concepts](https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-an-image/), [Docker networking](https://docs.docker.com/engine/network/), [port publishing](https://docs.docker.com/engine/network/port-publishing/), [Docker volumes](https://docs.docker.com/engine/storage/volumes/), [Compose file reference](https://docs.docker.com/compose/compose-file/), [Compose variable interpolation](https://docs.docker.com/compose/how-tos/environment-variables/variable-interpolation/), [`docker run` environment variables](https://docs.docker.com/reference/cli/docker/container/run/#set-environment-variables--e---env), [Docker build secrets](https://docs.docker.com/build/building/secrets/), [Docker Compose secrets](https://docs.docker.com/compose/how-tos/use-secrets/), [`docker login`](https://docs.docker.com/reference/cli/docker/login/), [`docker tag`](https://docs.docker.com/reference/cli/docker/image/tag/), and [`docker push`](https://docs.docker.com/reference/cli/docker/image/push/). Docker documentation checked 2026-10-15.
