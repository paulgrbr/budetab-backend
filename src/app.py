from flask import Flask
from endpoints.account import *

app = Flask(__name__)

# Account endpoint
app.register_blueprint(accounts, url_prefix='/')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8085, debug=True)