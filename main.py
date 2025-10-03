# Main script to integrate various modules and execute the functions end to end.


# Import necessary libraries


# Import modules from src

from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "<h1>Hello from Flask!</h1><p>This is a local Python website.</p>"

@app.route('/about')
def about():
    return "<h2>About Us</h2><p>We are learning to build websites with Python.</p>"

if __name__ == '__main__':
    app.run(debug=True)
