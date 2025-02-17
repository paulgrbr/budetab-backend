# BudeTab Backend

This is the backend service for Budetab, a financial budgeting (checklist) application for groups or clubs. Focus lies on beverages, but can be extended to all kinds of products.

This is service by **Bude Berkach**. For further information on usage and deployment contact budeberkach@gmail.com.

## Features

- REST API for budget and finance management
- Dockerized for easy deployment
- Uses Python and dependencies listed in `requirements.txt`
- Follows PEP8 coding style

## Installation

1. Clone the repository:

   ```sh
   git clone <repo-url>
   cd budetab-backend
   ```

2. Create a virtual environment and install dependencies:

   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   pip install -r requirements.txt
   ```

## Running the Application

### Or Using Docker

1. Build and start the container:

   ```sh
   docker-compose up backend
   ```

2. Stop the container:

   ```sh
   docker-compose down
   ```

### Without Docker

Run the application manually:

   ```sh
   python src/app.py
   ```


## Database Setup

This project uses **PostgreSQL** as its database. The database service is included in `docker-compose.yaml`.

### Running the Database

If using Docker, the database will be automatically started. To manually start it:

```sh
docker-compose up -d db
```


### Database Configuration

Ensure the `.env` file includes the following variables:

```

POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# User for authenticated use
POSTGRES_AUTH_USER=
POSTGRES_AUTH_PW=

# User without authentication
POSTGRES_PUBLIC_USER=
POSTGRES_PUBLIC_PW=
POSTGRES_DB_NAME=bude_transactions

# JWT secrets
SECRET_KEY=
JWT_SECRET_KEY=
```

You can change these values as needed.

## Testing

Run tests with:

   ```sh
   pytest
   ```

## License

This project is licensed under the terms specified in the `LICENSE` file.

Copyright (c) 2025 Bude Berkach