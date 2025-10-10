# Main script to integrate various modules and execute the functions end to end.


# Import necessary libraries


# Import modules from src

from flask import Flask, render_template, redirect, url_for, request

app = Flask(__name__)

@app.route('/')
def home():
    return "<h1>Hello from Flask!</h1><p>This is a local Python website.</p>"

@app.route('/about')
def about():
    return render_template(
        'index.html',
        title='About Page',
        content='This is the about page of the Flask application.')
if __name__ == '__main__':
    app.run(debug=True)
