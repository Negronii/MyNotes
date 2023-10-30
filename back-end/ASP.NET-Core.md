# Setups

## Create project/components

If you are not working on Rider (JetBrains series) or Visual Studio Windows, you may need use CLI to initiate project/files. Following command gives a list of things we can create with CLI

```
dotnet new list
```

For our case we are building microservices, a 'solution' may be wonderful, and we are using web api in the solution, so use following command to initiate.

```
dotnet new sln
dotnet new webapi -o src/AuctionService
dotnet sln add src/AuctionService
```

## run app in CLI

```
cd src/AuctionService
dotnet watch
```

## Nuget

install extension Nuget Gallery for VSCode, then in search section on the top, type

```
>Nuget Gallery: Open Nuget Gallery
```

Then in the window, install whatever needed, simplly search for packages, e.g. here's what we gonna use

- Microsoft.EntityFrameworkCore.Design
- Npgsql.EntityFrameworkCore.PostgreSQL
- AutoMapper.Extensions.Microsoft.DependencyInjection

### Installing NuGet Packages in Visual Studio

1. Right-click on the project name (not the solution name), e.g., `BulkyWeb (main)`.
2. Select "Manage NuGet Package".

For database connectivity, you can install the following packages:

- Microsoft.EntityFrameworkCore
- Microsoft.EntityFrameworkCore.SqlServer
- Microsoft.EntityFrameworkCore.Tools (for migrations)

### Installing NuGet Packages with `dotnet` CLI (Command Line Interface)

Install Microsoft.EntityFrameworkCore

```bash
dotnet add package Microsoft.EntityFrameworkCore
```

Install Microsoft.EntityFrameworkCore.SqlServer

```bash
dotnet add package Microsoft.EntityFrameworkCore.SqlServer
```

Install Microsoft.EntityFrameworkCore.Tools for Migrations

```bash
dotnet add package Microsoft.EntityFrameworkCore.Tools
```

Run these commands in the terminal, making sure you are in the directory where your `.csproj` file resides.

## install the Entity Framework Core CLI tools

```
dotnet tool install --global dotnet-ef
```

or update with

```
dotnet tool update --global dotnet-ef
```

## Primary Key for a Table in C#

You can specify the primary key for a table in a C# model class like so:

```csharp
public class Category
{
    [Key]
    public int Id { get; set; }
    public string Name { get; set; }
    public int DisplayOrder { get; set; }
}
```

## Making a Property Non-Nullable with `[Required]`

You can make a property non-nullable using the `[Required]` attribute, often used for string properties:

```csharp
public class Category
{
    public int Id { get; set; }
    [Required]
    public string Name { get; set; }
    public int DisplayOrder { get; set; }
}
```

> **Note**: The `[Key]` attribute is not necessary when the property is named `Id` or `<ClassName>Id`. It is implicitly treated as the primary key. In other cases, such as a property named `Name`, you would need to explicitly add the `[Key]` attribute.

## Migrate data entity

The command then generates a new migration file with code to upgrade the database schema. This migration file is added to a Migrations folder in your project. The name provided (AddCategoryTableToDb in this case) is used to name this new file, making it easier to identify what change this migration corresponds to. When you run the migration command, it will look at your DbContext class to determine the schema of the database, comparing it to the current database schema to generate the appropriate SQL code to update the schema.

```
dotnet ef migrations add "InitialCreate" -o Data/Migrations
```

After adding the migration, you can update the database with the newly added migration using the following command:

```
dotnet ef database update
```

## Add a gitignore file

```
dotnet new gitignore
```

# Concepts

## Entities

They are often used to map directly to database tables. They are part of your domain model and can be used throughout the application. Usually tied to your database schema, meaning any changes to them could affect the database directly. Can be heavily interconnected through relationships like foreign keys, navigation properties, etc.  
In other words, the object classes in domain layer taught in SDA (SWEN90007) classes are entities.

## DTO

In the context of ASP.NET and generally in software development, DTO stands for Data Transfer Object. A DTO is an object that carries data between processes. While it may seem similar to an entity, it serves a different purpose. They are used to transfer data and do not contain behavior. They are plain objects with properties and are usually "dumb" objects.  
In the context of a web API project, a Data Transfer Object (DTO) is often used to define the data structure for the request body as well as the response body. Essentially, it helps define the contract between the client and the server about what data is expected to be sent and received.

## Mappings

Example

```csharp
using AuctionService.DTOs;
using AuctionServices.Entities;
using AutoMapper;

namespace AuctionService.RequestHelpers;

public class MappingProfiles: Profile
{
    public MappingProfiles()
    {
        CreateMap<Auction, AuctionDto>().IncludeMembers(x => x.Item);
        CreateMap<Item, AuctionDto>();
        CreateMap<CreateAuctionDto, Auction>()
            .ForMember(d => d.Item, o => o.MapFrom(s => s));
        CreateMap<CreateAuctionDto, Item>();
    }
}
```

`CreateMap`  
CreateMap essentially sets up a mapping profile to convert one object type into another. AutoMapper uses these profiles to know how to automatically perform the conversion when you call \_mapper.Map<>().

`AutoMapper`

A Profile in AutoMapper allows you to organize your mappings. You could potentially have different profiles for different parts of your application or different mapping scenarios. In essence, it encapsulates configurations for your object-object mappings. When you register your profiles, AutoMapper knows which mappings are valid.

The Map method infers the source type from the object you pass to it. If you have more than one mapping that starts from AuctionDto, AutoMapper will throw an exception when you try to map it, saying that it's ambiguous. You have to specify more information to help it choose the correct mapping. Also, AutoMapper is smart enough to map collections. If you've configured how to map Auction to AuctionDto, AutoMapper knows how to map `List<Auction>` to `List<AuctionDto>`.

## DbContext

A simple Db context example:

```Csharp
using AuctionServices.Entities;
using Microsoft.EntityFrameworkCore;

namespace AuctionServices.Data;

public class AuctionDbContext : DbContext {

    public AuctionDbContext(DbContextOptions options) : base(options) {}

    public DbSet<Auction> Auctions { get; set; }
}
```

`base()`  
base(options) in the AuctionDbContext constructor is equivalent to super(options) in Java. It calls the base class (DbContext) constructor and passes the options parameter to it.

`DbSet<Auction> Auctions { get; set; }`
This line creates a property in the AuctionDbContext class that represents a table in the database. The table will have columns and data types that correspond to the properties and data types of the Auction class. The `{ get; set; }` is syntactic sugar for getter and setter methods, similar to how you'd have `@Getter` and `@Setter` annotations in Java.

## Dependency Injection in .NET CORE

Example partial code in program.cs

```csharp
var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
builder.Services.AddControllers();
builder.Services.AddDbContext<AuctionDbContext>(options => {
    options.UseNpgsql(builder.Configuration.GetConnectionString("DefaultConnection"));
});
builder.Services.AddAutoMapper(AppDomain.CurrentDomain.GetAssemblies());

var app = builder.Build();
```

### Services

The Dependency Injection (DI) container is like a recipe book. When you use builder.Services.AddXYZ(), you're essentially adding a recipe to that book. These recipes tell the DI system how to create instances of particular services when they're needed. You aren't actually cooking (instantiating) anything at this point; you're just describing how to do it.

### Scope

Scopes can be seen as "kitchen counters" where the cooking (instantiation) happens. Each counter (scope) can have its own set of cooked dishes (instances), created according to the recipes in the main book (DI container).

When a new scope is created using CreateScope(), it inherits all the recipes from the main recipe book but has its own counter space to prepare dishes. This is especially useful for Scoped services, which you might want to instantiate once per request or operation and then share within that specific operation.

### Code Analogy

builder = WebApplication.CreateBuilder(args); - You're preparing to create your kitchen (application) and recipe book (DI container).
builder.Services.AddXYZ(...); - You're adding recipes to the recipe book.

### Assemble automappers

```csharp
builder.Services.AddAutoMapper(AppDomain.CurrentDomain.GetAssemblies());
```

It registers AutoMapper with the DI container, scanning through the assemblies to find all classes that inherit from AutoMapper's Profile class and registering them.

## Initialize DbContext

It is often required to have a DBInitializer class

```csharp
using AuctionServices.Data;
using AuctionServices.Entities;
using Microsoft.EntityFrameworkCore;
namespace AuctionService.Data;
public class DbInitializer
{
    public static void InitDb(WebApplication app) {
        using var scope = app.Services.CreateScope();
        SeedData(scope.ServiceProvider.GetService<AuctionDbContext>());
    }
    private static void SeedData(AuctionDbContext context)
    {
        context.Database.Migrate();
        if (context.Auctions.Any())
        {
            Console.WriteLine("Auction data already exists.");
            return;
        }
        var auctions = new List<Auction>()
        {
            // auctions
            new Auction
            {
               ...
            },
            ...
        };
        context.AddRange(auctions);
        context.SaveChanges();
    }
}
```

`Seed function`  
The seed function is essentially initializing the database with some default data. context.Database.Migrate() ensures that the database schema is up-to-date, context.Auctions.Any() checks if there's already any data in the Auctions table, and context.AddRange(auctions) and context.SaveChanges() add new rows to the table and save those changes, respectively.

`scope.ServiceProvider.GetService<AuctionDbContext>()`  
This line is using the dependency injection framework to get an instance of AuctionDbContext. This is similar to asking the application's "container" for an instance of a particular service that's been registered.

`using var scope = app.Services.CreateScope();`  
You're setting up a kitchen counter (scope) to start cooking.  
In C#, using has two purposes. One is for importing namespaces (like import in Java or Python), and the other is for resource management. In this case, it's the latter. When you declare a variable with using, it's automatically disposed of when it goes out of scope. This is similar to Java's try-with-resources statement for automatic resource management. i.e.

```java
try (scope = app.Services.CreateScope();) {
    SeedData(scope.ServiceProvider.GetService<AuctionDbContext>());
}
```

CreateScope() creates a new scope for retrieving services from the dependency injection container. This is useful for scoped services, meaning services that are created once per client request. Creating a scope allows you to resolve these scoped services for a specific block of code.

`SeedData(scope.ServiceProvider.GetService<AuctionDbContext>());`  
You're following a recipe to cook a specific dish (AuctionDbContext) for this kitchen counter (scope).

## Controllers

Example code:

```csharp
using AuctionService.DTOs;
using AuctionServices.Data;
using AuctionServices.Entities;
using AutoMapper;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;

namespace AuctionService.Controllers;

[ApiController]
[Route("api/auctions")]
public class AuctionsController: ControllerBase
{
    private readonly AuctionDbContext _context;
    private readonly IMapper _mapper;

    public AuctionsController(AuctionDbContext context, IMapper mapper)
    {
        _context = context;
        _mapper = mapper;
    }

    [HttpGet]
    public async Task<ActionResult<List<AuctionDto>>> GetAllAuctions()
    {
        var auctions = await _context.Auctions
            .Include(x => x.Item)
            .OrderBy(x => x.Item.Make)
            .ToListAsync();
        return _mapper.Map<List<AuctionDto>>(auctions);
    }

    [HttpGet("{id}")]
    public async Task<ActionResult<AuctionDto>> GetAuctionById(Guid id)
    {
        var auction = await _context.Auctions
            .Include(x => x.Item)
            .FirstOrDefaultAsync(x => x.Id == id);
        if (auction == null) return NotFound();
        return _mapper.Map<AuctionDto>(auction);
    }

    [HttpPost]
    public async Task<ActionResult<AuctionDto>> CreateAuction(CreateAuctionDto createAuctionDto)
    {
        var auction = _mapper.Map<Auction>(createAuctionDto);
        auction.Seller = "test";
        _context.Auctions.Add(auction);
        var result = await _context.SaveChangesAsync() > 0;
        if (!result) return BadRequest("Failed to create auction");
        return CreatedAtAction(nameof(GetAuctionById), new {auction.Id}, _mapper.Map<AuctionDto>(auction));
    }
}
```

### `Task`

It is pretty much Promise in Javascript.

### How `_context` and `_mapper` are resolved

The AuctionDbContext and IMapper instances are automatically injected into your controller's constructor by ASP.NET Core's Dependency Injection (DI) mechanism. This is because these types are registered in the DI container in the Program.cs.

### Return Type of Controller Endpoints

Returning `Task<ActionResult<T>>` is a common pattern for asynchronous endpoints in ASP.NET Core, but it's not a fixed or forced pattern. You can return other types as well. This particular return type gives you a lot of flexibility:

`Task` makes it asynchronous.
`ActionResult` allows you to return different HTTP status codes.
The generic `T` allows you to specify the data type that should be serialized into the response body.

## Working with MongoDB in a .NET Environment

### 1. Required NuGet Packages:

These are the necessary packages you'd need to work with MongoDB and other related tasks:

```xml
<!-- Provides functionality to map object properties to each other -->
<PackageReference Include="AutoMapper.Extensions.Microsoft.DependencyInjection" Version="12.0.1" />

<!-- Enables the generation of OpenAPI/Swagger documentation -->
<PackageReference Include="Microsoft.AspNetCore.OpenApi" Version="7.0.10" />

<!-- Provides a convenient API to interact with MongoDB -->
<PackageReference Include="MongoDB.Entities" Version="22.1.0" />
```

### 2. Setting Up MongoDB Using Docker:

Here's a Docker Compose file that sets up both PostgreSQL and MongoDB:

```yml
services:
  postgres:
    image: postgres
    environment:
      - POSTGRES_PASSWORD=postgrespwd
    ports:
      - 5432:5432
    volumes:
      - pgdata:/var/lib/postgresql/data
  mongodb:
    image: mongo
    environment:
      - MONGO_INITDB_ROOT_USERNAME=root
      - MONGO_INITDB_ROOT_PASSWORD=mongopwd
    ports:
      - 27017:27017
    volumes:
      - mongodata:/var/lib/mongo/data

volumes:
  pgdata:
  mongodata:
```

**Steps to Use:**

- Run the `docker-compose` command to create the containers.
- Install the MongoDB extension for VSCode.
- Use the "new connection" feature, choose "Username/Password" authentication, and input the credentials specified in the Docker Compose file to connect.

### 3. Setting Up Models and Database Initialization:

- Create a "Models" folder to define the data schemas.
- Create a `DbInitializer` to initialize the database from a prepared JSON file if the database is empty.

```csharp
using System.Text.Json;
using MongoDB.Driver;
using MongoDB.Entities;

namespace SearchService;

public class DbInitializer
{
    public static async Task InitDb(WebApplication app)
    {
        // Initialize the MongoDB database
        await DB.InitAsync("SearchDB", MongoClientSettings
            .FromConnectionString(app.Configuration.GetConnectionString("MongoDbConnection")));

        // Create indexes for the Item entity
        await DB.Index<Item>()
            .Key(x => x.Make, KeyType.Text)
            .Key(x => x.Model, KeyType.Text)
            .Key(x => x.Color , KeyType.Text)
            .CreateAsync();

        // Check if any data exists
        var count = await DB.CountAsync<Item>();
        if (count == 0)
        {
            Console.WriteLine("No data - will attempt to seed");
            var itemData = await File.ReadAllTextAsync("Data/ItemData.json");
            var options = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };
            var items = JsonSerializer.Deserialize<List<Item>>(itemData, options);
            await DB.SaveAsync(items);
        }
    }
}
```

To run the initializer, add the following in your `program.cs`:

```csharp
try {
    await DbInitializer.InitDb(app);
} catch (Exception ex) {
    Console.WriteLine(ex.Message);
}
```

### 4. Setting Up Controllers:

Here's an example of a simple search controller:

```csharp
using Microsoft.AspNetCore.Mvc;
using MongoDB.Entities;

namespace SearchService;

[ApiController]
[Route("api/search")]
public class SearchController: ControllerBase
{
    [HttpGet]
    public async Task<ActionResult<List<Item>>> SearchItems(string searchTerm)
    {
        var query = DB.Find<Item>();
        query.Sort(x => x.Ascending(a => a.Make));

        // If a search term is provided, perform a full-text search
        if (!string.IsNullOrEmpty(searchTerm))
        {
            query.Match(Search.Full, searchTerm).SortByTextScore();
        }

        var result = await query.ExecuteAsync();
        return result;
    }
}
```

**Explanation:** This controller contains an endpoint that allows for searching items. If a `searchTerm` is provided, it performs a full-text search on the MongoDB collection; otherwise, it simply fetches and sorts the data by the "Make" attribute.

# Appendix

## Run a postgres db

Create a docker compose file with following

```yml
services:
  postgres:
    image: postgres
    environment:
      - POSTGRES_PASSWORD=postgrespwd
    ports:
      - 5432:5432
    volumes:
      - pgdata:/var/lib/postgresql/data
volumes:
  pgdata:
```

Then run

```
docker compose up -d
```

And in appsettings.Development.json, use correct authentication and port

```json
{
  "Logging": {
    "LogLevel": {
      "Default": "Information",
      "Microsoft.AspNetCore": "Information"
    }
  },
  "ConnectionStrings": {
    "DefaultConnection": "Server=localhost:5432;User Id=postgres;Password=postgrespwd;Database=auctions"
  }
}
```

## Running MSSQL on macOS via Docker

Since MSSQL does not support macOS natively, you can run it using Docker:

Run the following command in your terminal:

```zsh
docker run -e 'ACCEPT_EULA=Y' -e 'SA_PASSWORD=YourStrong!Passw0rd' -p 1433:1433 --name sql_server_container -d mcr.microsoft.com/mssql/server:2019-latest
```

### Connecting to MSSQL Using Azure Data Studio

1. Download and install Azure Data Studio, open and click on "New Connection".
2. Fill in the details:
   - Server: `localhost,1433`
   - Authentication Type: SQL Login
   - User name: `sa`
   - Password: `YourStrong!Passw0rd`
3. Click "Connect".

### Creating a New Database

1. Right-click on the "Databases" folder under the connected server in the "SERVERS" panel.
2. Select "New Database" and name your database `Bulky`.
3. Click "OK".

### Updating appsettings.json for Database Connection

Update `appsettings.json` to include your database connection string:

```json
{
  "Logging": {
    "LogLevel": {
      "Default": "Information",
      "Microsoft.AspNetCore": "Warning"
    }
  },
  "AllowedHosts": "*",
  "ConnectionStrings": {
    "DefaultConnection": "Server=localhost,1433;Database=Bulky;User Id=sa;Password=YourStrong!Passw0rd;TrustServerCertificate=True;"
  }
}
```
