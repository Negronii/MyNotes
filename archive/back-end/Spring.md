# Spring Boot Dependency-Injection Example / Spring Boot 依赖注入示例

This note keeps a small Spring MVC example showing constructor injection, a DAO interface, request binding, validation, and an in-memory implementation. The validation/import examples below use Spring Boot 3.x conventions (`jakarta.validation`); Spring Boot 2.x uses the older `javax.validation` namespace.

核心逻辑：构造器注入明确服务依赖，`@Qualifier` 选择具体 DAO Bean；`@Valid` 会触发已有约束，但不会自己创建约束，Boot 3 使用 `jakarta.validation` 且需要校验 provider。示例仓库只在单个进程内保存数据。

## Project Setup

Initiate project: go to https://start.spring.io/ and choose environment/dependencies.

## Dependency injection / 依赖注入

### Model — `/model/Person.java`

```java
package com.example.demo.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.NotBlank;

import java.util.UUID;

public class Person {
    private final UUID id;

    @NotBlank
    private final String name;

    public Person(@JsonProperty("id") UUID id,
                  @JsonProperty("name") String name) {
        this.id = id;
        this.name = name;
    }

    public UUID getId() {
        return id;
    }

    public String getName() {
        return name;
    }
}
```

### Service — `/service/PersonService.java`

```java
package com.example.demo.service;

import com.example.demo.dao.PersonDAO;
import com.example.demo.model.Person;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class PersonService {
    private final PersonDAO personDAO;

    public PersonService(@Qualifier("fakeDAO") PersonDAO personDAO) {
        this.personDAO = personDAO;
    }

    public int addPerson(Person person) {
        return personDAO.insertPerson(person);
    }

    public List<Person> getAllPeople() {
        return personDAO.selectAllPeople();
    }
}
```

### DAO Interface — `/dao/PersonDAO.java`

```java
package com.example.demo.dao;

import com.example.demo.model.Person;

import java.util.List;
import java.util.UUID;

public interface PersonDAO {
    int insertPerson(UUID id, Person person);

    default int insertPerson(Person person) {
        UUID id = UUID.randomUUID();
        return insertPerson(id, person);
    }

    List<Person> selectAllPeople();

}

```

### Repository — `/dao/FakePersonDataAccessService.java`

```java
package com.example.demo.dao;

import com.example.demo.model.Person;
import org.springframework.stereotype.Repository;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

@Repository("fakeDAO")
public class FakePersonDataAccessService implements PersonDAO{

    private final List<Person> database = new ArrayList<>();

    @Override
    public int insertPerson(UUID id, Person person) {
        database.add(new Person(id, person.getName()));
        return 1;
    }

    @Override
    public List<Person> selectAllPeople() {
        return List.copyOf(database);
    }
}
```

### Controller — `/api/PersonController.java`

```java
package com.example.demo.api;

import com.example.demo.model.Person;
import com.example.demo.service.PersonService;
import org.springframework.web.bind.annotation.*;
import jakarta.validation.Valid;

import java.util.List;

@RequestMapping("api/v1/person")
@RestController
public class PersonController {
    private final PersonService personService;

    public PersonController(PersonService personService) {
        this.personService = personService;
    }

    @PostMapping
    public void addPerson(@Valid @RequestBody Person person) {
        personService.addPerson(person);
    }

    @GetMapping
    public List<Person> getAllPeople() {
        return personService.getAllPeople();
    }

}
```

## Usage

Here, we established a minimal Java Spring app with one resource path and two endpoints (POST and GET):
`http://localhost:8080/api/v1/person`
Test with a POST request and JSON in the body:

```
{
    "name":"James Bond"
}
```

Or use GET to retrieve all stored people.

This repository is an in-memory teaching example: data is local to one application process, disappears when it restarts, and the `ArrayList` is not safe for concurrent mutation. Spring discovers the repository bean, and `@Qualifier("fakeDAO")` selects it for this constructor parameter. A different `PersonDAO` implementation can be wired through configuration or a qualifier, but a database change may also require changes to persistence behavior and configuration; it is not necessarily a one-line swap.

## Path variables and request validation / 路径变量与请求校验

To pass a variable from the path, use

```java
@GetMapping(path = "{id}")
public Person getPersonById(@PathVariable("id") UUID id) {
    return null; // Signature example only; implement lookup and the missing-record response.
}
```

The method above shows only binding the path value; the `null` return is an unimplemented lookup placeholder.

For Spring Boot 3, add a Bean Validation provider such as `spring-boot-starter-validation`. `@Valid` asks Spring MVC to validate the bound object; it does not define a constraint by itself. Here, the model's `@NotBlank` constraint on `name` supplies one. Do not use Spring's `@NonNull` annotation as a replacement for a Bean Validation constraint.

```java
public void addPerson(@Valid @RequestBody Person person) {
    personService.addPerson(person);
}
```

On Spring Boot 2, replace the `jakarta.validation` imports in this example with `javax.validation` imports and use the validation provider compatible with that Boot version.

## Deployment

With the Spring Boot Maven plugin configured, `package` builds a runnable executable JAR. `install` is not needed just to run the app locally.

```
./mvnw package
java -jar target/<artifact-name>.jar
```

## Sources / 参考资料

- Spring Boot 3.5: [constructor injection](https://docs.spring.io/spring-boot/3.5/reference/using/spring-beans-and-dependency-injection.html), [validation](https://docs.spring.io/spring-boot/3.5/reference/io/validation.html), [building an executable JAR](https://docs.spring.io/spring-boot/3.5/how-to/build.html), and [running a packaged application](https://docs.spring.io/spring-boot/3.5/reference/using/running-your-application.html).
- Spring Framework 6.2: [Spring MVC request-body validation](https://docs.spring.io/spring-framework/reference/6.2/web/webmvc/mvc-controller/ann-methods/requestbody.html) and [bean scopes](https://docs.spring.io/spring-framework/reference/6.2/core/beans/factory-scopes.html). A Spring singleton is scoped per bean definition and container; it is not a thread-safety guarantee.
- The single-constructor `@Autowired` omission has been supported since Spring Framework 4.3; see the [Spring Framework reference](https://docs.spring.io/spring-framework/docs/4.3.x/spring-framework-reference/html/beans.html).
