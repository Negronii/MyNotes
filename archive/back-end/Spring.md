# Spring Boot 怎样把一次 JSON 请求接到服务和数据访问对象？

**案例背景：** 一个本地教学 API（application programming interface，应用程序编程接口）接收 `{"name":"James Bond"}`，由服务端生成 ID，保存后返回人员记录；随后可列出人员，或按 ID 查找。本章跟着这条请求区分两件事：应用启动时如何连接对象，请求到达后这些对象如何处理数据。

示例按 Spring Boot 4.1.2、Spring Framework 7.0 的 API 编排，使用 Java 17 以上语法。它展示依赖连接与请求校验，内存数据只属于一个进程；对外服务还需要[身份与逐次资源授权](../../engineering-foundations/security/web-security-and-authentication.md)。

~~~mermaid
flowchart TD
    A[SpringApplication.run] --> B["@SpringBootApplication 扫描组件"]
    B --> C["FakePersonDAO Bean（fakeDAO）"]
    B --> D[PersonService Bean]
    B --> E[PersonController Bean]
    C -->|按 PersonDAO 类型和 Qualifier fakeDAO 注入| D
    D -->|构造器注入| E
~~~

## 启动时，谁负责创建这些对象？

Dependency Injection（依赖注入，DI）让对象声明自己需要什么，由容器提供依赖。`PersonService` 需要 `PersonDAO`，但不自行 `new FakePersonDAO()`；这把业务行为与选择具体存储实现的配置分开。Spring 管理的对象称为 Bean。

入口类放在 `com.example.people`，相关组件放在该包及其子包。`@SpringBootApplication` 包含组件扫描；`@Service`、`@Repository`、`@RestController` 标记的组件才能在约定范围内被发现。把类放在无关包里，仅写注解也未必会被扫描。

~~~java
package com.example.people;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class PeopleApplication {
    public static void main(String[] args) {
        SpringApplication.run(PeopleApplication.class, args);
    }
}
~~~

项目可用 Spring Initializr 生成 Maven 配置，选择 package `com.example.people`、Spring Web 与 Validation；将下面各类型分别放在 `src/main/java/com/example/people/` 下的同名 `.java` 文件中。Boot 4 的 MVC starter 是 `spring-boot-starter-webmvc`，校验 provider 由 `spring-boot-starter-validation` 提供。让 Boot 的依赖管理选择兼容组件，而不是随意混搭框架和 JSON 库版本。

## JSON 输入与保存结果为什么分成两种类型？

客户端只应决定输入的 `name`；ID 由服务端生成。用 Data Transfer Object（数据传输对象，DTO）表达输入边界，避免把所有持久字段都开放给客户端赋值。以下各个 public 类型分别放在同名 `.java` 文件中，位于 `com.example.people`：

~~~java
package com.example.people;
import jakarta.validation.constraints.NotBlank;

public record CreatePersonRequest(@NotBlank String name) {}
~~~

~~~java
package com.example.people;
import java.util.UUID;

public record Person(UUID id, String name) {}
~~~

record（记录类）简化不可变值载体的声明。`@RequestBody` 让 HTTP 消息转换器把 JSON 变为请求对象；`@Valid` 触发 Bean Validation（Bean 校验），真正的条件来自 `@NotBlank`：名字不能为 `null`、空串或全空白。`@Valid` 本身没有定义“有效名字”是什么，静态空值注解也不能替代运行期校验约束。

## DAO 契约怎样将保存行为与实现分开？

Data Access Object（数据访问对象，DAO）定义服务需要的读写能力。这里保留“接口默认方法生成 UUID，再调用具体插入实现”的结构：

~~~java
package com.example.people;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface PersonDAO {
    Person insertPerson(UUID id, String name);
    default Person insertPerson(String name) {
        return insertPerson(UUID.randomUUID(), name);
    }
    List<Person> selectAllPeople();
    Optional<Person> selectPerson(UUID id);
}
~~~

教学存储用一个列表；Spring Bean 默认常被多个请求线程共享，因此连这个小例子也要明确并发边界：

~~~java
package com.example.people;
import org.springframework.stereotype.Repository;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository("fakeDAO")
public class FakePersonDAO implements PersonDAO {
    private final List<Person> people = new ArrayList<>();

    public synchronized Person insertPerson(UUID id, String name) {
        Person person = new Person(id, name);
        people.add(person);
        return person;
    }
    public synchronized List<Person> selectAllPeople() {
        return List.copyOf(people);
    }
    public synchronized Optional<Person> selectPerson(UUID id) {
        return people.stream().filter(p -> p.id().equals(id)).findFirst();
    }
}
~~~

三个方法使用同一个对象监视器，避免列表在遍历或复制期间被另一请求修改。返回的列表是不可修改快照，其中的 `Person` 和字段也不可变。这里没有实现数据库唯一约束、跨进程协调、分页或持久化；重启会清空，两个副本各有各的列表。singleton（单例）只描述容器中的对象作用域，不会自动让对象线程安全。

## 构造器怎样确定用哪一个 DAO？

~~~java
package com.example.people;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Service;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Service
public class PersonService {
    private final PersonDAO dao;
    public PersonService(@Qualifier("fakeDAO") PersonDAO dao) {
        this.dao = dao;
    }
    public Person addPerson(String name) { return dao.insertPerson(name); }
    public List<Person> getAllPeople() { return dao.selectAllPeople(); }
    public Optional<Person> getPerson(UUID id) { return dao.selectPerson(id); }
}
~~~

Spring 为构造器参数寻找类型匹配的 Bean；`@Qualifier("fakeDAO")` 进一步限定候选。只有一个构造器时无需再标 `@Autowired`。依赖用 `final` 字段保存，服务对象创建后不会再随意替换它。单元测试也能直接给构造器传一个测试 DAO。

换成数据库实现时，可以保留该接口，但仍要设计事务、约束、连接生命周期与错误映射。DI 改变的是对象如何连接，不会把内存列表自动升级成耐久数据库；[连接池与数据访问](../../engineering-foundations/backend/data-access-and-connection-pools.md)解释持久实现需要补上的责任。

## 从控制器返回时，HTTP 状态怎样确定？

下面把 JSON 绑定、校验分支与成功响应连起来。校验失败发生在 Controller 方法调用前；成功分支才从 Controller 进入 Service 和 DAO。

~~~mermaid
flowchart TD
    A[POST /api/v1/person] --> B{"Content-Type 支持 JSON？"}
    B -->|否| C[415；尚未绑定请求体]
    B -->|是| D[消息转换器尝试绑定 CreatePersonRequest]
    D --> E{"能绑定为 CreatePersonRequest？"}
    E -->|否| F[400；绑定失败，不进 Controller 方法]
    E -->|是| G{"@NotBlank 通过？"}
    G -->|否| H[400；校验失败，不调用 Service / DAO]
    G -->|是| I[Controller 调 Service，再由 DAO 生成 UUID 并保存]
    I --> J{"Accept 允许 JSON 响应？"}
    J -->|否| K[406；DAO 写入已发生]
    J -->|是| L[201；Location + Person JSON]
~~~

绑定失败和校验失败都返回 400，但发生在不同阶段：坏 JSON 或字段类型、结构无法转换成 `CreatePersonRequest`，都在绑定时失败；语法正确也不保证能绑定，例如 `{"name":{"nested":true}}`。成功绑定后，若 `name` 为空白，才由 `@NotBlank` 校验失败；两类请求都不会进入 Controller 方法。要看到成功响应，请同时发送 `Content-Type: application/json` 并允许 `Accept: application/json`。若客户端只接受 `text/plain`，方法和 DAO 可能已执行，之后仍会因不能生成可接受的响应而得到 406。

~~~java
package com.example.people;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;
import java.net.URI;
import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/person")
public class PersonController {
    private final PersonService service;
    public PersonController(PersonService service) { this.service = service; }

    @PostMapping
    public ResponseEntity<Person> add(
            @Valid @RequestBody CreatePersonRequest input) {
        Person saved = service.addPerson(input.name());
        return ResponseEntity.created(URI.create("/api/v1/person/" + saved.id()))
                .body(saved);
    }
    @GetMapping
    public List<Person> all() { return service.getAllPeople(); }

    @GetMapping("/{id}")
    public Person one(@PathVariable("id") UUID id) {
        return service.getPerson(id).orElseThrow(
                () -> new ResponseStatusException(HttpStatus.NOT_FOUND));
    }
}
~~~

`@RestController` 的返回值经消息转换器写入响应正文；`ResponseEntity` 还控制状态和头。`@PathVariable` 把路径中的 ID 转换为 UUID，不能解析的输入在进入查询之前失败。本轮运行的 Eclipse Temurin 17.0.21 中，Java 的 UUID 解析会接受某些非规范长度写法（例如 `1-1-1-1-1`）；这个路径参数转换只保证得到 UUID 值，不是严格的文本格式校验。若接口要求固定格式，应另行检查输入文本。查无记录用 404，不能返回一个未实现的 `null` 占位符。

> [!example] 同一请求在三个边界改变形态
> `POST /api/v1/person`，JSON 为 `{"name":"James Bond"}`。
>
> 绑定后得到 `CreatePersonRequest("James Bond")`；校验通过后 DAO 接口的默认方法分配 UUID，再由内存实现保存 `Person(id,"James Bond")`；响应为 201，`Location` 指向 `/api/v1/person/{id}`，JSON 包含相同 `id` 和 `name`。随后 GET 该地址返回同一记录。
>
> 换成 `{"name":"   "}` 时，校验失败，默认返回 400，保存方法没有执行。合法 UUID 但查无记录得到 404；无法解析为 UUID 的值（例如 `not-a-uuid`）则在参数转换时得到 400。这些是框架默认错误映射，应用自定义异常处理器时要维护同一公开契约。

打包并运行应用后，在另一终端用下面的请求验证贯穿案例；`-i` 会显示 201 和 `Location`。随后把返回的 `Location` 路径用于 GET，可读回同一个 ID 与名字：

~~~sh
curl -i http://127.0.0.1:8080/api/v1/person \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json' \
  --data '{"name":"James Bond"}'
~~~

因此成功路径是“反序列化 → 校验 → 服务调用 → 数据写入 → 序列化响应”，启动阶段的 DI 只负责让调用链事先可用。业务授权、幂等和数据库提交语义仍在各自边界内处理，见[HTTP API 契约](../../engineering-foundations/backend/http-api-contracts.md)。

## 打包后运行的是哪一份应用？

在 POM 中声明 `spring-boot-maven-plugin`，并使用 Spring Boot starter parent 所提供的 `repackage` 执行配置，或自行显式把该 goal 绑定到构建生命周期后，项目自带 Maven Wrapper 时运行 `./mvnw package`，否则运行 `mvn package`，即可构建可执行 JAR。本例的 POM 将 `artifactId` 设为 `people`、`version` 设为 `0.0.1-SNAPSHOT`，所以可运行：

~~~sh
mvn package
java -jar target/people-0.0.1-SNAPSHOT.jar
~~~

仅为本地运行不需要执行 `install`，后者还会把产物放进本地 Maven 仓库。源码、依赖、构建结果和运行配置共同决定行为，不能只看 Controller 文件就判断线上版本。

> [!info]- 来源
> - 当前示例基线：[Spring Boot 4.1.2 System Requirements](https://docs.spring.io/spring-boot/system-requirements.html)，最低 Java 17，要求 Spring Framework 7.0.10 或更高；[第一个 MVC 应用与 `spring-boot-starter-webmvc`](https://docs.spring.io/spring-boot/tutorial/first-application/index.html) 和 [Bean Validation](https://docs.spring.io/spring-boot/reference/io/validation.html)，核对 2026-11-13。
> - 构造器注入、组件发现与包布局：[Beans and Dependency Injection](https://docs.spring.io/spring-boot/reference/using/spring-beans-and-dependency-injection.html)、[Structuring Your Code](https://docs.spring.io/spring-boot/reference/using/structuring-your-code.html)。
> - JSON 绑定、默认校验错误和请求参数转换：[Spring Framework 7.0 `@RequestBody`](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-controller/ann-methods/requestbody.html)、[Validation](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-controller/ann-validation.html)、[Type Conversion](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-controller/ann-methods/typeconversion.html)；`@NotBlank` 约束：[Jakarta Bean Validation 3.0 API](https://jakarta.ee/specifications/bean-validation/3.0/apidocs/jakarta/validation/constraints/notblank)。
> - UUID 字符串契约：[Java 17 `UUID`](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/UUID.html)；不合规范的请求参数默认映射：[DefaultHandlerExceptionResolver](https://docs.spring.io/spring-framework/docs/current/javadoc-api/org/springframework/web/servlet/mvc/support/DefaultHandlerExceptionResolver.html)。容器默认作用域：[Bean Scopes](https://docs.spring.io/spring-framework/reference/core/beans/factory-scopes.html)，核对 2026-11-13。
> - 可执行 JAR：[Spring Boot Maven Plugin Packaging](https://docs.spring.io/spring-boot/maven-plugin/packaging.html)。本轮从本文提取 Java 代码，在隔离目录用 Eclipse Temurin 17.0.21、Maven 3.10.0、Boot 4.1.2 / Framework 7.0.10 构建 JAR 并运行；验证 James Bond 创建、Location 读取、列表、空白名字、坏 UUID、未知 ID 和 `1-1-1-1-1` 的参数解析。应用只有进程内存储，未验证并发负载、数据库或生产安全配置。
