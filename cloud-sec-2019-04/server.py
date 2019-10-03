"""Basic Flask app that prints Hello World! as found in most tutorials."""
"""Does specify host and port 8080 when ran"""

from flask import Flask

app = Flask(__name__)

@app.route('/')
def root():
    return 'Hello World!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port='8080')
