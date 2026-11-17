# 本地 PostgreSQL 与 SQL Server 容器怎样连接到 .NET 服务？

**案例：** 开发拍卖服务时，ASP.NET Core 应用在开发机上运行，数据库放在 Docker 容器中。连接字符串里的主机名取决于“应用在哪里”：应用直接跑在宿主机上时，连接容器发布到宿主机的 `localhost` 端口；应用和数据库都在同一个 Compose 网络中时，使用数据库的服务名。数据存放在命名卷中，删除或重建容器不会丢数据，因为容器的生命周期和数据的生命周期是分开的。

## 数据库地址为什么随应用所在位置变化？

~~~mermaid
flowchart TD
    HostApp[宿主机 .NET 服务] -->|localhost:5432| PublishedPort[已发布端口]
    PublishedPort --> Pg[(PostgreSQL 容器)]
    ComposeApp[Compose 内 .NET 服务] -->|postgres:5432| Pg
    Pg --> Volume[(命名卷：数据库文件)]
~~~

下面先用 PostgreSQL 走完这两种连接方式，再说明换成 SQL Server 时有哪些额外条件。

## PostgreSQL 18 的数据目录怎样挂载？

把以下内容保存为项目目录中的 `compose.yaml`。它使用 PostgreSQL 官方镜像 `postgres:18.7`（2026-11-16 核对的最新 18.x 标签），用 named volume（命名卷）保存数据，容器重建后数据仍在。启动前先在 shell 中设置一个只供本地使用的密码：

~~~yaml
services:
  postgres:
    image: postgres:18.7
    environment:
      POSTGRES_DB: auctions
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?set a local password}
    ports:
      - "127.0.0.1:5432:5432"
    volumes:
      - auction_pgdata:/var/lib/postgresql

volumes:
  auction_pgdata:
~~~

~~~sh
export POSTGRES_PASSWORD='<本地开发密码>'
docker compose up -d postgres
docker compose logs -f postgres
~~~

`up -d` 返回时容器已经启动，但 PostgreSQL 可能还不接受 TCP 连接。卷为空时，镜像会先启动一个只监听 Unix socket 的临时 PostgreSQL 来完成初始化；它也会打印 `database system is ready to accept connections`，但此时宿主机应用还无法通过发布的端口连接。所以跟随日志时，要先看到 `PostgreSQL init process complete; ready for start up.`，再等正式服务器打印下一条 `database system is ready to accept connections`，然后按 Ctrl+C 退出日志、启动应用。卷里已有数据时会跳过临时初始化，只需等正式服务器的那一行。

如果 .NET 服务也运行在 Compose 中，要用环境变量覆盖连接串中的主机和凭据，因为 User Secrets 只存在于开发机，不会自动传进容器：

~~~yaml
environment:
  ConnectionStrings__DefaultConnection: "Host=postgres;Port=5432;Username=postgres;Password=${POSTGRES_PASSWORD};Database=auctions"
~~~

ASP.NET Core 把环境变量 `ConnectionStrings__DefaultConnection` 映射为配置键 `ConnectionStrings:DefaultConnection`，应用再用 `UseNpgsql(connectionString)` 注册 PostgreSQL。应用直接运行在宿主机上时，连接串改用发布到本机的端口（示例密码不含分号；若实际密码含分号，要按对应 provider 的连接串语法给值加引号）：

~~~text
Host=localhost;Port=5432;Username=postgres;Password=<本地密码>;Database=auctions
~~~

在服务项目目录执行以下命令，把连接串存入开发环境的 User Secrets，而不是提交到 `appsettings.json`：

~~~sh
dotnet user-secrets init
connectionString="Host=localhost;Port=5432;Username=postgres;\
Password=<本地密码>;Database=auctions"
dotnet user-secrets set "ConnectionStrings:DefaultConnection" "$connectionString"
~~~

从 Web 项目目录运行宿主机服务：

~~~sh
dotnet run
~~~

再强调一次两种位置的区别：应用在 Compose 网络中时主机名必须用 `postgres`，因为容器内的 `localhost` 指向应用容器自己，而不是数据库容器。

关于 `compose.yaml` 中的卷路径：PostgreSQL 18 官方镜像把默认数据目录改成带版本号的 `/var/lib/postgresql/18/docker`，卷的挂载点相应改为上一级的 `/var/lib/postgresql`。命名卷在重建容器时保留数据库文件；`POSTGRES_USER`、`POSTGRES_DB` 等初始化变量只在数据目录为空、首次初始化时生效。本地开发密码只放在 User Secrets 或本地环境变量中，不要提交到 `appsettings.json`。

## SQL Server 容器有哪些主机和证书条件？

如果项目改用 SQL Server，思路相同：容器发布端口、数据放在命名卷里，但运行平台和证书有额外限制。下面使用当前的 SQL Server 2025（17.x）Linux 容器，需要在受支持的 Linux x86-64 主机上运行：

~~~sh
export MSSQL_SA_PASSWORD='<本地开发密码>'
docker run -e ACCEPT_EULA=Y -e MSSQL_SA_PASSWORD \
  -p 127.0.0.1:1433:1433 --name sql1 --hostname sql1 \
  --mount source=sqlserverdata,target=/var/opt/mssql \
  -d mcr.microsoft.com/mssql/server:2025-latest
~~~

只写 `-e MSSQL_SA_PASSWORD` 而不带值时，Docker 会从当前 shell 已导出的环境变量读取；密码至少 8 个字符，并要满足 SQL Server 的密码复杂度策略。`docker run -d` 返回时数据库可能还没就绪，先用 `docker logs -f sql1` 跟随日志，等日志报告已可接受客户端连接，再按 Ctrl+C 退出。

连接字符串不会替你创建数据库。用 SQL 客户端以登录名 `sa` 连接 `localhost,1433`（SQL Server 用逗号分隔主机和端口）上的内置 `master` 数据库，执行 `CREATE DATABASE SampleDb;`；或者把连接字符串指向一个已存在的数据库。EF Core 项目使用 `Microsoft.EntityFrameworkCore.SqlServer` provider 的 `UseSqlServer(connectionString)`，与上面 PostgreSQL 的 `UseNpgsql` 是两套不同配置。连接字符串可写成：

~~~text
Server=localhost,1433;Database=SampleDb;User Id=sa;Password=<本地密码>;Encrypt=True;TrustServerCertificate=True;
~~~

容器使用自签名证书，`TrustServerCertificate=True` 让客户端在加密连接时跳过证书校验，只适合本机开发；部署环境应配置可验证的证书。SQL Server 容器镜像只在 Intel/AMD x86-64 Linux 主机受支持，不支持 macOS，也不支持 Rosetta、QEMU 等架构仿真环境；在 Apple Silicon Mac 上不要把 Docker Desktop 仿真当成受支持运行方式。PostgreSQL 与 SQL Server 是不同 EF provider，连接字符串和 provider 专属迁移也应分开配置，见[EF Core 模型怎样变成关系表，并让迁移与数据库结构保持一致？](aspnet-ef-model-and-migrations.md)。

> [!info]- 使用 SQL Server 客户端
> Microsoft 已于 2026-02-28 结束 Azure Data Studio 支持。可在受支持的平台上使用 Visual Studio Code 的 MSSQL 扩展或 SQL Server Management Studio；连接地址为 `localhost,1433`。本例使用 Developer 容器进行本地开发，不是生产部署模板。

> [!info]- 维护 PostgreSQL 17 旧卷
> 本页的 PostgreSQL 18 样例使用官方镜像默认的 `PGDATA`（数据目录），并挂载 `/var/lib/postgresql`。PostgreSQL 17 及更早版本的镜像在使用默认 `PGDATA` 时应挂载 `/var/lib/postgresql/data`；自定义 `PGDATA` 时，卷必须覆盖对应的数据目录。把旧卷路径直接改为 18 的布局不会迁移其中的数据。需要跨主版本升级时，按 PostgreSQL 官方升级流程迁移和验证数据，不要仅替换镜像标签。

> [!info]- 来源
> - PostgreSQL 18 官方镜像的 `PGDATA` 与卷路径，以及 17 与更早版本的挂载差异：[Docker Official Image PostgreSQL 文档](https://github.com/docker-library/docs/blob/master/postgres/content.md#pgdata)，于 2026-11-13 核对；`18.7` 为当前最新 18.x 标签：[Docker Hub postgres 标签](https://hub.docker.com/_/postgres/tags?name=18.)，于 2026-11-16 核对。
> - 官方 entrypoint 的空卷初始化顺序、临时服务器仅监听 Unix socket，以及初始化完成后启动最终服务器：[PostgreSQL 18 entrypoint](https://github.com/docker-library/postgres/blob/master/docker-entrypoint.sh)，核对日期 2026-11-13。
> - Npgsql 连接串的 `Host`、`Port`、`Username`、`Password`、`Database` 参数：[Npgsql Connection String Parameters](https://www.npgsql.org/doc/connection-string-parameters)，核对日期 2026-11-06。
> - ASP.NET Core 环境配置以 `__` 代替层级键中的冒号；EF Core 分别由 Npgsql 与 SQL Server provider 的 `UseNpgsql` / `UseSqlServer` 配置：[ASP.NET Core 环境变量配置](https://learn.microsoft.com/en-us/aspnet/core/fundamentals/configuration/?view=aspnetcore-10.0#environment-variables)、[Npgsql EF Core provider](https://www.npgsql.org/efcore/)、[SQL Server EF Core provider](https://learn.microsoft.com/en-us/ef/core/providers/sql-server/)，核对日期 2026-11-13。
> - SQL Server 2025 Linux 容器命令与 `MSSQL_SA_PASSWORD`：[Microsoft Learn Docker quickstart](https://learn.microsoft.com/en-us/sql/linux/quickstart-install-connect-docker?pivots=cs1-bash&tabs=cli)，核对版本 SQL Server 2025 (17.x)，日期 2026-11-13。
> - SQL Server 容器支持范围（仅 Intel/AMD x86-64 Linux 主机，不含仿真/翻译环境）：[Linux 支持平台](https://learn.microsoft.com/en-us/sql/linux/install-upgrade/setup?view=sql-server-ver17)，核对日期 2026-11-13。
> - 可用 SQL 客户端与 Azure Data Studio 退役说明：[Microsoft Learn SQL Server 工具说明](https://learn.microsoft.com/en-us/sql/tools/whats-happening-azure-data-studio)，核对日期 2026-11-06。
