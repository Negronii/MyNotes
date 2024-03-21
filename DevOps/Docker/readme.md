## Docker Operations

Docker is a powerful tool for managing containers, allowing you to package your applications and dependencies into a portable container that can easily be transferred and run across systems. Understanding Docker operations is crucial for developers to ensure their applications can be deployed consistently and efficiently.

### Downloading Images from Docker Hub
- **Command:** `docker pull <image name>`
- **Example:** `docker pull redis`
- This command downloads an image from Docker Hub to your local machine. Images are pre-configured environments that contain your application and all of its dependencies.

### Checking All Downloaded Images
- **Command:** `docker images`
- **Example:** `docker images`
- Lists all Docker images that have been downloaded or built on your machine.

### Starting a Container from an Image
- **Command:** `docker run <image name>`
- **Example:** `docker run redis`
- This command creates a new container from a specified image and starts it. If the image is not available locally, Docker will attempt to pull it from Docker Hub.

### Stopping a Running Container
- **Command:** `docker stop <container ID>`
- **Example:** `docker stop 8381867e8242`
- Stops a running container. You can get the container ID by using the `docker ps` command.

### Checking the State of Running Containers
- **Command:** `docker ps`
- **Example:** `docker ps`
- Lists all currently running containers.

### Checking the State of All Containers
- **Command:** `docker ps -a`
- **Example:** `docker ps -a`
- Lists all containers, including those that are stopped.

### Running a Stopped Container
- **Command:** `docker start <container ID>`
- **Example:** `docker start 8381867e8242`
- Starts a previously stopped container.

### Binding Ports to Solve Port Conflicts
- **Command:** `docker run -p <host port>:<container port> --name <defined name>`
- **Example:** `docker run -d -p 6000:6379 --name redis-new redis`
- This command maps a port on the host to a port on the container, allowing you to avoid port conflicts and access the container's services from the host.

### Showing Logs of a Container
- **Command:** `docker logs <container ID or name>`
- **Example:** `docker logs ppppp`
- Retrieves logs from a container. Useful for debugging and monitoring container activity.

### Naming a Container
- **Command:** `docker run --name <name> <image name>`
- **Example:** `docker run --name redis-latest redis`
- Allows you to assign a custom name to your container, making it easier to reference than the default generated ID.

### Setting a Tag (Version) for an Image
- **Command:** `docker tag <image name>:<version name> <desired name>:<desired version name>`
- **Example:** `docker tag my-app:1.0 my-app-on-aws-cloud:1.1`
- Tags an image with a version or a name, useful for version control and organizing images.

### Accessing a Container
- **Command:** `docker exec -it <container ID> <path>`
- **Example:** `docker exec -it cae903a74202 /bin/bash`
- Executes a command inside a running container, such as opening a bash shell. Use `exit` to leave the shell.

### Creating a Docker Network
- **Command:** `docker network create <name>`
- **Example:** `docker network create mongo-network`
- Creates a new network, allowing containers to communicate with each other more securely and efficiently.

### Running an Image Within a Network
- **Command:** `docker run --net <network name> <image name>`
- **Example:** `docker run --net mongo-network mongo`
- Starts a container within a specified network, facilitating communication between containers within the same network.

### Deleting a Container
- **Command:** `docker rm <container ID>`
- **Example:** `docker rm cae903a74202`
- Removes a stopped container from your machine.

### Deleting an Image
- **Command:** `docker rmi <Image ID>`
- **Example:** `docker rmi cae903a74202`
- Removes an image from your local machine, freeing up space.

### Running a Container with a Named Volume
- **Command:** `docker run -v <name for data>:<container data address>`
- **Example:** `docker run -v db-data:/var/lib/mysql/data`
- Mounts a named volume at a specified path within the container. This is useful for persistent or shared data between containers.

### Running a Container in Detached Mode
- **Command:** `docker run -d <image name>`
- **Example:** `docker run -d redis`
- This command runs the container in the background (detached mode), allowing it to run as a background process. When a container is started in detached mode, it does not block the terminal session that started it. This is particularly useful when running applications or services that should continue running without active supervision.

Running a container in detached mode is essential for services that need to run continuously, such as web servers, databases, or any application that should be accessible at all times without tying up a terminal session. It also helps in managing multiple containers efficiently, allowing developers and system administrators to start, stop, and inspect services without having to keep a terminal window open for each.

When running in detached mode, you won't see any output from the container directly in your terminal. To check on the container's logs or status, you'll need to use commands like `docker logs` for output or `docker ps` to see running containers.

This mode is particularly relevant in production environments or when deploying services on a server, where direct interaction with the container is not required for normal operation. It's also handy during development for services that don't need constant monitoring, allowing developers to focus on other tasks while the services remain available.

## Run Docker with YAML

Docker Compose allows you to define and run multi-container Docker applications. With a YAML file, you can configure your application’s services, networks, and volumes.

### Important Points
- **Network Creation**: There is no need to manually create a network when using a YAML file to define a series of containers. Docker Compose automatically creates a network for the services defined in the `docker-compose.yml` file, facilitating communication between containers without specifying IP addresses and ports. You can reference services by their names (e.g., `admin.xxx.@mongodb` instead of `admin.xxx.@localhost:27017`).

### Template
```yaml
version: '3'
services: 
  <service-name>:
    image: <image-name>
    ports:
      - "<port-on-host>:<port-in-container>"
    environment:
      - <ENV_VAR_NAME>=<value>
```

### Example
```yaml
version: '3'
services: 
  mongodb:
    image: mongo
    ports:
      - "27017:27017"
    environment:
      - MONGO_INITDB_ROOT_USERNAME=admin
      - MONGO_INITDB_ROOT_PASSWORD=password
  mongo-express:
    image: mongo-express
    ports:
      - "8080:8080"
    environment:
      - ME_CONFIG_MONGODB_ADMINUSERNAME=admin
      - ME_CONFIG_MONGODB_ADMINPASSWORD=password
```

### How to Run This YAML
- **Start Containers**: `docker-compose -f <filename> up` (e.g., `docker-compose -f my_compose.yaml up`)
- **Stop Containers**: `docker-compose -f <filename> down` (e.g., `docker-compose -f my_compose.yaml down`)

## Dockerfile

A Dockerfile is a text document that contains all the commands a user could call on the command line to assemble an image. It is often used in continuous integration pipelines, such as setting up a Jenkins pipeline.

### Template
```dockerfile
FROM <base-image>
ENV <environment-variables>
RUN <command>
COPY . <destination-in-container>
CMD ["<entrypoint-command>"]
```

### Example
```dockerfile
FROM node
ENV MONGO_DB_USERNAME=admin \ 
    MONGO_DB_PWD=password
RUN mkdir -p /home/app
COPY . /home/app
CMD ["node", "/home/app/server.js"]
```

### Key Differences
- **RUN**: Executes commands in a new layer on top of the current image and commits the results. Used for installing software packages.
- **CMD**: Sets the default command to execute when the container starts. It can be overridden by providing a different command when starting the container.

## Building an Image
- Command: `docker build -t <image-name>:<tag> .`
- Example: `docker build -t my-app:1.0 .`

## Use Amazon Elastic Container Registry (ECR)
- Create a repository on Amazon ECR for each image.
- Ensure AWS CLI is installed on the host.
- Use the repository URI provided by Amazon ECR to push images.

## Docker Volumes
Docker volumes are used to persist data generated by and used by Docker containers.

### Types of Volumes
- **Host Volumes**: Specify an explicit location on the host for the volume (`docker run -v <host-path>:<container-path>`).
- **Anonymous Volumes**: Docker automatically assigns a location on the host (`docker run -v <container-path>`).
- **Named Volumes** (Preferred): Specify a name for the volume which Docker manages (`docker run -v <volume-name>:<container-path>`). Preferred in production for ease of management.

### Usage in Docker Compose
In `docker-compose.yml`, volumes can be declared as follows:
```yaml
volumes: 
  db-data:/var/lib/mysql/data
```