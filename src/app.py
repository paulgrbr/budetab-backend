import os
import logging
from flask import Flask
from flask_compress import Compress
from flask_jwt_extended import verify_jwt_in_request
from endpoints.account import *
from endpoints.user import *
from endpoints.product import *
from endpoints.misc import *
from endpoints.jwt_handlers import jwt
from flask_cors import CORS

app = Flask(__name__)
Compress(app)

# Environment check for production
RUN_ENV = os.environ.get('RUN_ENV', 'PROD')
# Logging!!

# Configuration
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
app.config["JWT_SECRET_KEY"] = os.environ['JWT_SECRET_KEY']
app.config['JWT_TOKEN_LOCATION'] = ['headers']
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 60 * \
    30  # 1 hour expiry for access tokens
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = 60 * \
    60 * 24 * 14  # 24 hours expiry for refresh tokens
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10MB (in bytes)

# CORS Configuration
CORS(app, resources={r"/*": {"origins": "*"}})


jwt.init_app(app)

# Account endpoint
app.register_blueprint(accounts, url_prefix='/account')
app.register_blueprint(users, url_prefix='/user')
app.register_blueprint(products, url_prefix='/product')

app.register_blueprint(misc, url_prefix='/misc')


if __name__ == "__main__":
    env_vars = [
        "RUN_ENV",
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
