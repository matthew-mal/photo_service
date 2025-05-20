**Setup Instructions**
1. *Clone the Repository*
```bash
    git clone https://github.com/matthew-mal/photo_service
```
```bash
    cd test_assignment
```

2. *Create a .env File*
Create a .env file in the project root with the variables from .env.template
Replace the values with your own:

`POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`: Database credentials.
`SECRET_KEY`: A secure Django secret key (generate one if needed).
`DEBUG`: Set to True for development, False for production.
`ALLOWED_HOSTS`: Comma-separated list of allowed hosts (e.g., localhost,127.0.0.1).

3. *Build and Run the Services*
Build and start the Docker containers:
```bash
    docker-compose up --build
```

4. *Access the Application*
Open http://0.0.0.0:8000 in your browser.

