# Docker 如何把报表服务的源码构建成可运行镜像？

报表平台工程师已修复 tenant-a 对 report 42 的读取条件，现在要确保测试过的提交确实构建成可复用镜像。container image（容器镜像）是只读文件系统和默认配置；container（容器）启动时增加可写层；volume（数据卷）把数据库数据放在容器外；network（网络）让 application programming interface（应用程序接口，API）、worker（工作进程）和数据库互通。发布时把 Git 提交固定为镜像摘要，并把数据库、密钥和运行配置放在镜像之外。下面用示意提交 c4f2a91 演示本地构建；本地验证不会自动发布或部署。

~~~mermaid
flowchart TD
    A[源码提交 c4f2a91 + 依赖锁文件] --> B[多阶段构建与依赖安装]
    B --> C[镜像 report-api，记录摘要]
    C --> D[API 容器与 worker 容器]
    D --> E[同一 Compose 网络中的 db:5432]
    E --> F[命名卷独立保存数据库文件]
    C --> G[构建流水线测试精确镜像，再发布相同摘要]
~~~

图里的 c4f2a91 和 report-api 都是示意值。image digest（镜像摘要）是内容身份；tag（可变标签）只是可变别名。同一提交可有不同构建结果，必须记录实际摘要才能确认 staging（预发布环境）与 production（生产环境）用的是相同镜像内容。

## 按运行所需文件分层构建

Python 报表 API 和 worker 可以来自同一个多阶段镜像：构建阶段下载由 dependency lock file（依赖锁定文件）固定的依赖，最终阶段只复制运行所需依赖和代码。下面基础镜像 tag 只用于说明结构；实际 CI 应记录所解析的基础镜像摘要，或直接固定摘要。

~~~dockerfile
FROM python:3.12-slim AS wheels
WORKDIR /build
COPY requirements.txt .
RUN python -m pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

FROM python:3.12-slim AS runtime
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
COPY requirements.txt .
COPY --from=wheels /wheels /wheels
RUN python -m pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt && rm -rf /wheels
COPY app ./app
USER 10001:10001
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
~~~

为减少无关输入，先复制依赖清单再复制频繁改变的源码；这样源码改动不会使依赖安装层失效。`.dockerignore` 应排除 `.git/`、`.venv/`、`__pycache__/`、本机日志、真实 `.env` 和 secret（密钥）文件。Build context（构建上下文）是发送给 builder 的文件集合；若把密钥放进 context 再 COPY，镜像历史里就可能留下它。构建阶段需要私有包凭据时使用 BuildKit secret mount（构建时临时挂载密钥），而不是 Dockerfile `ARG` 或 `ENV`。运行期配置和密钥再由所选运行平台注入。

例如本地单平台构建并记录元数据的命令是：

~~~bash
docker buildx build --load --metadata-file /tmp/report-api-build.json -t report-api:c4f2a91 .
docker image inspect report-api:c4f2a91
docker image history report-api:c4f2a91
~~~

`--load` 将单平台镜像载入本地 Docker Engine；本地 `containerimage.digest` 只标识该 build 输出，不能当作 registry 已发布的摘要。示例 tag `report-api:c4f2a91` 只是本地引用：要将镜像归到该提交，CI 必须 checkout 确切的 `c4f2a91` 并从干净工作区构建，因为 tag 名不会约束 Build context。生产发布由 CI 从受控提交执行 `--push`，记录实际 push 的 `containerimage.digest` 并从 registry 核对目标 manifest；之后 staging 与 production 晋级同一不可变引用，不要分别重建。单平台摘要指向一个平台 manifest；多平台索引摘要指向多个平台 manifest，不同架构实际运行的内容可能不同。跨架构部署须记录并验收每个目标平台的 manifest digest，或明确预发布和生产使用同一平台。

Dockerfile 中的 `RUN` 在构建镜像时执行；`CMD` 提供容器启动时的默认命令或参数，`ENTRYPOINT` 指定主要可执行程序。Compose 的 `command` 覆盖镜像的默认 `CMD`，不会自动替换 `ENTRYPOINT`。因此 API 和 worker 可通过各自的 `command` 使用同一镜像启动不同进程。

## 容器、服务网络与数据存留是不同状态

下面的 Compose 片段复用上一条命令已载入的 `report-api:c4f2a91`，不再设置 `build:`，因此 API 与 worker 使用同一份本地镜像。若开发环境另用 `build: .` 和 `report-api:local`，那是从当前目录再构建的一份本地拓扑样例，不等于上面已验收提交的镜像。

API 与 worker 使用不同 command，但在 Compose 网络内访问数据库服务名 `db` 和容器端口 5432。容器间通信无需公开数据库端口。只将需要本机浏览器访问的 API 发布到宿主机回环地址：

~~~yaml
services:
  api:
    image: report-api:c4f2a91
    pull_policy: never
    ports:
      - "127.0.0.1:8080:8080"
    environment:
      DATABASE_HOST: db
  worker:
    image: report-api:c4f2a91
    pull_policy: never
    command: ["python", "-m", "app.worker"]
    environment:
      DATABASE_HOST: db
  db:
    image: postgres:18
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    secrets:
      - db_password
    volumes:
      - report-data:/var/lib/postgresql

secrets:
  db_password:
    file: ./secrets/db_password.txt

volumes:
  report-data:
~~~

此片段只演示 API/worker 到 `db:5432` 的服务发现和网络可达，并未配置应用数据库凭据。`db_password` 当前只挂给 db，用于初始化 Postgres 默认管理员；官方镜像的 `POSTGRES_PASSWORD_FILE` 只在数据目录为空时用于初始化，后来修改 secret 文件不会轮换已有数据库中的密码。改密码须在数据库中执行凭据变更，并同步更新应用 secret。实际应用应另行创建最小权限账号，把用户名和独立密码注入 API/worker，并让代码从受控 secret 路径读取。不能从只有 `DATABASE_HOST` 推出应用已登录数据库。生产部署应让平台 secret store（密钥存储服务）管理凭据，不应把示意文件加入版本控制。受支持的 Docker Compose CLI v2 和 v5 都使用 `docker compose` 命令与 Compose Specification；Compose 文件顶层 `version` 字段已废弃，旧版独立 `docker-compose` 命令应迁移到该 CLI。服务加入项目网络后可通过服务名发现彼此；主机只在 API 的 127.0.0.1:8080 上可访问。网络成员关系限制可达路径，但不代替数据库身份、应用认证或租户授权。port mapping（端口映射）只转发连接，不证明进程健康。Docker Engine 28 及之后的默认 bridge/NAT 配置下，本机回环发布只在 Docker 主机可达；更早版本存在同一 Layer 2 网络主机可访问的例外。省略主机 IP 通常会绑定全部宿主接口，必须按 Engine 版本、network mode（网络模式）和路由判断暴露范围。

容器写层随容器删除而丢失；命名卷由 Docker 管理，在容器替换后仍可复用。匿名卷也可存活，但新容器通常不会自动重新挂上相同卷。bind mount 直接把宿主路径映射到容器，适合需要共同读写的开发文件。volume 不是备份；还需独立恢复演练。普通 `docker compose down` 保留声明的 named volumes，`docker compose down -v` 会删除项目卷和其中的数据。

本例使用官方 Postgres 18 镜像，把 volume 挂到 `/var/lib/postgresql`，由版本专属的数据目录组织数据库文件。旧版本镜像常见挂载点是 `/var/lib/postgresql/data`；现有旧卷不能只改 image tag 后直接按新目录启动，必须按官方镜像和 PostgreSQL 大版本迁移说明备份、转换或恢复。

## 从构建状态检查到运行状态观察

常见本地查看命令用于分开判断镜像、容器和服务：

| 命令 | 读取的状态 | 适合确认 |
|---|---|---|
| `docker image ls` | 本机镜像和 tag | 镜像是否已载入，不能证明运行中 |
| `docker ps -a` | 创建过的容器 | 容器是否运行或退出 |
| `docker compose logs api worker` | Compose 服务日志 | 启动错误或应用输出 |
| `docker compose exec api /bin/sh` | api 服务容器内进程环境 | 仅当镜像里确实有 shell；精简镜像可能没有 |
| `docker compose ps` | Compose 服务 | 容器状态；实际容器名由项目名和服务名生成 |
| `docker image history report-api:c4f2a91` | 镜像层历史 | COPY/RUN 的构建结果，不是镜像里的完整文件审计 |

detached mode（后台运行模式）返回 shell 不表示程序有监督，也不证明容器健康。启动探针、就绪探针和应用 SLI 属于运行平台与服务观测，不由镜像构建证明；参见[容器运行时如何承接 API 和 worker？](production-application-runtime.md)。ACK、队列延迟与业务完成由[消息交付如何确认](../reliability/queue-delivery-and-acknowledgement.md)说明。

基本操作可按 image/container 两种对象查看：`docker pull redis:7` 拉取镜像，`docker run --name cache -d redis:7` 创建并启动容器，`docker ps -a` 查看含已停止的容器，`docker stop cache` 与 `docker start cache` 停止或重新启动已有容器，`docker rm cache` 移除已停止容器，`docker image rm redis:7` 移除镜像标签。对正在运行的容器使用 `docker rm -f` 会同时停止并删除它，先确认容器写层中没有要保留的数据。

手动推送镜像时先用 `docker login registry.example.com` 验证 registry 身份，再 `docker tag` 赋上 registry 地址并 `docker push`。这会发布镜像，不能用可变 tag 代替部署时的 digest；生产中由受控 CI 身份执行该步骤，本文不运行登录或推送。

> [!info]- 来源
> - Image、Dockerfile 指令与多阶段构建：[Docker image concepts](https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-an-image/)、[Dockerfile reference](https://docs.docker.com/reference/dockerfile/) 与[多阶段构建](https://docs.docker.com/get-started/docker-concepts/building-images/multi-stage-builds/)，checked 2026-11-06；Compose 服务的 [`command`](https://docs.docker.com/reference/compose-file/services/#command) 覆盖默认 `CMD`。
> - Layer cache、context 和 secret：[Build cache](https://docs.docker.com/build/cache/)、[Build secrets](https://docs.docker.com/build/building/secrets/)、[buildx build --metadata-file](https://docs.docker.com/reference/cli/docker/buildx/build/)，checked 2026-11-06。
> - Network、port publish 和 volume：[Docker networking](https://docs.docker.com/engine/network/)、[port publishing](https://docs.docker.com/engine/network/port-publishing/)、[volumes](https://docs.docker.com/engine/storage/volumes/)，checked 2026-11-06；Docker Engine localhost publishing 语义须按 Engine 版本、network mode 和路由核对。
> - Compose 默认网络、volume、secret 与 CLI 版本：[Compose file reference](https://docs.docker.com/compose/compose-file/)、[Compose secrets](https://docs.docker.com/compose/how-tos/use-secrets/) 和[Compose history](https://docs.docker.com/compose/intro/history/)，checked 2026-11-06；当前 v2/v5 使用 `docker compose` 与 Compose Specification。
> - Postgres image 的初始化变量和数据路径：[官方 image 环境变量](https://hub.docker.com/_/postgres#environment-variables)与[PGDATA 说明](https://github.com/docker-library/docs/blob/master/postgres/README.md#pgdata)，checked 2026-11-06。`POSTGRES_PASSWORD_FILE` 不会更新既有数据目录中的账号密码；PostgreSQL 18 路径与旧镜像迁移边界适用于相应官方 image，换版不迁移数据。
> - 固定发布标识：[Docker image digests](https://docs.docker.com/dhi/explore/security-concepts/digests/)，checked 2026-11-06；具体多平台 manifest 应读 builder 和 registry 的实际 metadata。
> - 基本操作：[docker run](https://docs.docker.com/reference/cli/docker/container/run/)、[docker stop](https://docs.docker.com/reference/cli/docker/container/stop/)、[docker rm](https://docs.docker.com/reference/cli/docker/container/rm/)、[docker login](https://docs.docker.com/reference/cli/docker/login/)、[docker tag](https://docs.docker.com/reference/cli/docker/image/tag/) 和[docker push](https://docs.docker.com/reference/cli/docker/image/push/)，checked 2026-11-06。
