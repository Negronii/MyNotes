# 本地 PostgreSQL 与 SQL Server 容器怎样连接到 .NET 服务？

**案例：** ASP.NET Core 服务在开发机运行，数据库在 Docker 容器中。连接字符串的主机名取决于“客户端在哪里”：服务在宿主机上时使用已发布的 `localhost` 端口；服务和数据库都在 Compose 网络中时使用数据库服务名。命名卷保存容器替换后的数据，容器生命周期和数据生命周期是两件事。

## 数据库地址为什么随应用所在位置变化？

~~~mermaid
flowchart TD
    HostApp[宿主机 .NET 服务] -->|localhost:5432| PublishedPort[已发布端口]
    PublishedPort --> Pg[(PostgreSQL 容器)]
    ComposeApp[Compose 内 .NET 服务] -->|postgres:5432| Pg
    Pg --> Volume[(命名卷：数据库文件)]
~~~

## PostgreSQL 18 的数据目录怎样挂载？

以下内容保存为项目目录中的 `compose.yaml`，使用 2026-11-13 核对的 PostgreSQL 官方镜像 `postgres:18.6`。named volume（命名卷）让容器重建后仍保留数据；在该目录先从 shell 环境提供仅供本地使用的密码，再启动服务：

~~~yaml
services:
  postgres:
    image: postgres:18.6
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

`up -d` 返回时容器已启动，但 PostgreSQL 可能还没有接受 TCP 连接。空卷首次初始化会先启动一个只监听 Unix socket 的临时 PostgreSQL；这时也会打印 `database system is ready to accept connections`，但宿主机应用还不能通过已发布端口连接。跟随日志，先等 `PostgreSQL init process complete; ready for start up.`，再等最终服务器出现后续的 `database system is ready to accept connections`；然后按 Ctrl+C 退出日志并启动宿主机服务。已有数据卷会跳过临时初始化，只需等待最终服务器的 ready 行。Compose 内 .NET 服务应通过环境变量覆盖连接串中的主机和凭据，因为 User Secrets 不会自动传进容器：

~~~yaml
environment:
  ConnectionStrings__DefaultConnection: "Host=postgres;Port=5432;Username=postgres;Password=${POSTGRES_PASSWORD};Database=auctions"
~~~

ASP.NET Core 的 `ConnectionStrings__DefaultConnection` 映射到配置键 `ConnectionStrings:DefaultConnection`；PostgreSQL 项目注册 `UseNpgsql(connectionString)`。宿主机运行的 ASP.NET Core 使用：

连接串示例用不含分号的本地开发密码；若实际密码含分号，要按相应 provider 的连接串语法引用该值。

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

若 ASP.NET Core 也运行在同一个 Compose 网络，连接串主机名改为 `postgres`；容器内的 `localhost` 指回应用容器自身。PostgreSQL 18 官方镜像将默认数据目录设为版本路径 `/var/lib/postgresql/18/docker`，并把卷挂载点改为上层 `/var/lib/postgresql`。命名卷在重建容器时保留数据库文件；初始用户和数据库环境变量只在空数据目录的初始化过程中生效。使用本地开发密码，放在 User Secrets 或本地环境中，不能提交到 `appsettings.json`。

## SQL Server 容器有哪些主机和证书条件？

若选择 SQL Server，当前 Linux 容器示例是 SQL Server 2025（17.x）。在受支持的 Linux x86-64 主机上运行：

~~~sh
export MSSQL_SA_PASSWORD='<本地开发密码>'
docker run -e ACCEPT_EULA=Y -e MSSQL_SA_PASSWORD \
  -p 127.0.0.1:1433:1433 --name sql1 --hostname sql1 \
  --mount source=sqlserverdata,target=/var/opt/mssql \
  -d mcr.microsoft.com/mssql/server:2025-latest
~~~

Docker 的 `-e MSSQL_SA_PASSWORD` 会从已导出的进程环境读取值；密码至少 8 个字符并满足 SQL Server 密码复杂度策略。`docker run -d` 返回时容器可能还未就绪；先跟随 `docker logs -f sql1`，等 SQL Server 日志报告已接受客户端连接，再按 Ctrl+C 退出日志。随后用 SQL 客户端连接内置 `master` 数据库，执行 `CREATE DATABASE SampleDb;`；也可以把连接字符串指向已经创建的数据库。连接字符串不会替服务创建 `SampleDb`。客户端通过宿主机映射端口 `localhost,1433`、登录名 `sa` 连接；EF Core 项目使用 `Microsoft.EntityFrameworkCore.SqlServer` provider 的 `UseSqlServer(connectionString)`。这和上面的 PostgreSQL `UseNpgsql` 是两种不同配置。连接字符串可写成：

~~~text
Server=localhost,1433;Database=SampleDb;User Id=sa;Password=<本地密码>;Encrypt=True;TrustServerCertificate=True;
~~~

`TrustServerCertificate=True` 只是本机开发时的证书简化；部署环境应配置证书验证。SQL Server 容器镜像只在 Intel/AMD x86-64 Linux 主机受支持，不支持 macOS，也不支持 Rosetta、QEMU 等架构仿真环境；在 Apple Silicon Mac 上不要把 Docker Desktop 仿真当成受支持运行方式。PostgreSQL 与 SQL Server 是不同 EF provider，连接字符串和 provider 专属迁移也应分开配置，见[EF Core 模型怎样变成关系表，并让迁移与数据库结构保持一致？](aspnet-ef-model-and-migrations.md)。

> [!info]- 使用 SQL Server 客户端
> Microsoft 已于 2026-02-28 结束 Azure Data Studio 支持。可在受支持的平台上使用 Visual Studio Code 的 MSSQL 扩展或 SQL Server Management Studio；连接地址为 `localhost,1433`。本例使用 Developer 容器进行本地开发，不是生产部署模板。

> [!info]- 维护 PostgreSQL 17 旧卷
> 本页的 PostgreSQL 18.6 样例使用官方镜像默认 `PGDATA` 并挂载 `/var/lib/postgresql`。若仍使用官方镜像默认 `PGDATA`，PostgreSQL 17 及更早版本应挂载 `/var/lib/postgresql/data`；自定义 `PGDATA` 时，卷必须覆盖对应的数据目录。把旧卷路径直接改为 18 的布局不会迁移其中的数据。需要跨主版本升级时，按 PostgreSQL 官方升级流程迁移和验证数据，不要仅替换镜像标签。

> [!info]- 来源
> - PostgreSQL Official Image `18.6` 的 `PGDATA` 与卷路径，以及 17 与更早版本的挂载差异：[Docker Official Image PostgreSQL 文档](https://github.com/docker-library/docs/blob/master/postgres/content.md#pgdata)，于 2026-11-13 核对。
> - 官方 entrypoint 的空卷初始化顺序、临时服务器仅监听 Unix socket，以及初始化完成后启动最终服务器：[PostgreSQL 18 entrypoint](https://github.com/docker-library/postgres/blob/master/docker-entrypoint.sh)，核对日期 2026-11-13。
> - Npgsql 连接串的 `Host`、`Port`、`Username`、`Password`、`Database` 参数：[Npgsql Connection String Parameters](https://www.npgsql.org/doc/connection-string-parameters)，核对日期 2026-11-06。
> - ASP.NET Core 环境配置以 `__` 代替层级键中的冒号；EF Core 分别由 Npgsql 与 SQL Server provider 的 `UseNpgsql` / `UseSqlServer` 配置：[ASP.NET Core 环境变量配置](https://learn.microsoft.com/en-us/aspnet/core/fundamentals/configuration/?view=aspnetcore-10.0#environment-variables)、[Npgsql EF Core provider](https://www.npgsql.org/efcore/)、[SQL Server EF Core provider](https://learn.microsoft.com/en-us/ef/core/providers/sql-server/)，核对日期 2026-11-13。
> - SQL Server 2025 Linux 容器命令与 `MSSQL_SA_PASSWORD`：[Microsoft Learn Docker quickstart](https://learn.microsoft.com/en-us/sql/linux/quickstart-install-connect-docker?pivots=cs1-bash&tabs=cli)，核对版本 SQL Server 2025 (17.x)，日期 2026-11-13。
> - SQL Server 容器支持范围（仅 Intel/AMD x86-64 Linux 主机，不含仿真/翻译环境）：[Linux 支持平台](https://learn.microsoft.com/en-us/sql/linux/install-upgrade/setup?view=sql-server-ver17)，核对日期 2026-11-13。
> - 可用 SQL 客户端与 Azure Data Studio 退役说明：[Microsoft Learn SQL Server 工具说明](https://learn.microsoft.com/en-us/sql/tools/whats-happening-azure-data-studio)，核对日期 2026-11-06。
