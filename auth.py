from flask import Blueprint

auth = Blueprint('auth', __name__)

@auth.route("/signin")
def signin():
    return 'logged in'