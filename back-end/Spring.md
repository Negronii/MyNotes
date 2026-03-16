# Spring Boot

## Project Setup

Initiate project: go to https://start.spring.io/ and choose environment/dependencies.

## Dependency Injection Example

### Model — `/model/Person.java`

```java
package com.example.demo.model;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.UUID;

public class Person {
    private final UUID id;
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
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class PersonService {
    private final PersonDAO personDAO;

    @Autowired
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

    public static List<Person> DB = new ArrayList<>();

    @Override
    public int insertPerson(UUID id, Person person) {
        DB.add(new Person(id, person.getName()));
        return 0;
    }

    @Override
    public List<Person> selectAllPeople() {
        return DB;
    }
}
```

### Controller — `/api/PersonController.java`

```java
package com.example.demo.api;

import com.example.demo.model.Person;
import com.example.demo.service.PersonService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RequestMapping("api/v1/person")
@RestController
public class PersonController {
    private final PersonService personService;

    @Autowired
    public PersonController(PersonService personService) {
        this.personService = personService;
    }

    @PostMapping
    public void addPerson(@RequestBody Person person) {
        personService.addPerson(person);
    }

    @GetMapping
    public List<Person> getAllPeople() {
        return personService.getAllPeople();
    }

}
```

## Usage

Here, we established a minimum Java Spring app with one endpoint
`http://localhost:8080/api/v1/person`
test with post request and json in body

```
{
    "name":"James Bond"
}
```

or use get to get all being sent

With such design, we can inject our FakePersonDataAccessService into the PersonDAO in the service constructor. We don't need to manually instantiate it by passing in a FakePersonDataAccessService object, and it stays flexible — e.g., in the future we may have a PersonMongoService that implements PersonDAO with `@Repository("mongo")`, and we can easily switch database in one line of code.

## Path Variables and Validation

To pass a variable from the path, use

```java
@GetMapping(path = "{id}")
public Person getPersonById(@PathVariable("id") UUID id) {
    return null;
}
```

To require a request body to be non-null and valid:

```java
public void addPerson(@Valid @NonNull @RequestBody Person person) {
    personService.addPerson(person);
}
```

To require a specific field to not be blank:

```java
@NotBlank
private final String name
```

## Deployment

After running `mvn install`, a `target` folder is created containing a `.jar` file. To run it:

```
java -jar xxx.jar
```
