import os
from flask import Flask
from endpoints.account import *

app = Flask(__name__)

# Account endpoint
app.register_blueprint(accounts, url_prefix='/')

if __name__ == "__main__":
    env_vars = [
    "POSTGRES_HOST",
    "POSTGRES_PORT",
    "POSTGRES_AUTH_USER",
    "POSTGRES_AUTH_PW",
    "POSTGRES_PUBLIC_USER",
    "POSTGRES_PUBLIC_PW",
    "POSTGRES_DB_NAME",
    ]
    print("\n--- PostgreSQL Environment Variables ---\n")
    for var in env_vars:
        value = os.getenv(var, "NOT SET")
        print(f"{var}: {value}")
    print("\n----------------------------------------\n")

    app.run(host="0.0.0.0", port=8085, debug=True)