from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Hello, Flask in Docker!"

def add(x):
    return x+x

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8085)