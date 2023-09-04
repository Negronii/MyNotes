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

## install the Entity Framework Core CLI tools
```
dotnet tool install --global dotnet-ef
```
or update with
```
dotnet tool update --global dotnet-ef
```

## Migrate data entity
dotnet ef migrations add "InitialCreate" -o Data/Migrations

# Old




## Primary Key for a Table in C#

You can specify the primary key for a table in a C# model class like so:

```csharp
using System.ComponentModel.DataAnnotations;

namespace BulkyWeb.Models
{
    public class Category
    {
        [Key]
        public int Id { get; set; }
        public string Name { get; set; }
        public int DisplayOrder { get; set; }
    }
}
```

> **Note**: The `[Key]` attribute is not necessary when the property is named `Id` or `<ClassName>Id`. It is implicitly treated as the primary key. In other cases, such as a property named `Name`, you would need to explicitly add the `[Key]` attribute.

---

## Making a Property Non-Nullable with `[Required]`

You can make a property non-nullable using the `[Required]` attribute, often used for string properties:

```csharp
using System.ComponentModel.DataAnnotations;

namespace BulkyWeb.Models
{
    public class Category
    {
        public int Id { get; set; }
        [Required]
        public string Name { get; set; }
        public int DisplayOrder { get; set; }
    }
}
```

---

## Installing NuGet Packages in Visual Studio

1. Right-click on the project name (not the solution name), e.g., `BulkyWeb (main)`.
2. Select "Manage NuGet Package".

For database connectivity, you can install the following packages:

- Microsoft.EntityFrameworkCore
- Microsoft.EntityFrameworkCore.SqlServer
- Microsoft.EntityFrameworkCore.Tools (for migrations)


## Installing NuGet Packages with `dotnet` CLI (Command Line Interface)
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

---

## Running MSSQL on macOS via Docker

Since MSSQL does not support macOS natively, you can run it using Docker:

Run the following command in your terminal:

```zsh
docker run -e 'ACCEPT_EULA=Y' -e 'SA_PASSWORD=YourStrong!Passw0rd' -p 1433:1433 --name sql_server_container -d mcr.microsoft.com/mssql/server:2019-latest
```

### Connecting to MSSQL Using Azure Data Studio

1. Click on "New Connection".
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

---

## Updating appsettings.json for Database Connection

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

Run the following command to update your database:

```zsh
dotnet ef database update
```

---
## Migration

The command then generates a new migration file with code to upgrade the database schema. This migration file is added to a Migrations folder in your project. The name provided (AddCategoryTableToDb in this case) is used to name this new file, making it easier to identify what change this migration corresponds to.
```
dotnet ef migrations add AddCategoryTableToDb
```

After adding the migration, you can update the database with the newly added migration using the following command:
```
dotnet ef database update
```

---

### How to Create a Table in a Database Using .NET Core and Entity Framework Core

#### Step 1: Create the Model Class

Create a model class with the necessary annotations to represent the table schema.

```csharp
using System.ComponentModel.DataAnnotations;

namespace BulkyWeb.Models
{
    public class Category
    {
        [Key]
        public int Id { get; set; }
        
        [Required]
        public string Name { get; set; }
        
        public int DisplayOrder { get; set; }
    }
}
```

#### Step 2: Update the DbContext Class

Navigate to your `ApplicationDbContext` class (usually in the `Data` directory), and add a `DbSet` for your model.

```csharp
using BulkyWeb.Models;
using Microsoft.EntityFrameworkCore;

namespace BulkyWeb.Data
{
    public class ApplicationDbContext : DbContext
    {
        public ApplicationDbContext(DbContextOptions<ApplicationDbContext> options)
            : base(options)
        {
        }
        
        public DbSet<Category> Categories { get; set; }
    }
}
```

#### Step 3: Generate and Apply Migrations

Open the terminal, navigate to the directory containing your `.csproj` file, and run the following commands:

```bash
dotnet ef migrations add AddCategoryTableToDb
dotnet ef database update
```

---

After completing these steps, a new table named `Categories` should be created in your database with the schema defined in the `Category` model.