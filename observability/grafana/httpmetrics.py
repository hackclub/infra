import sys
import threading, statsd, os
from flask import Flask, Response, request
from dotenv import load_dotenv
from functools import wraps

load_dotenv()
app = Flask(__name__)
app.secret_key = os.urandom(50)

graphite = os.environ.get("GRAPHITE")
if graphite is None:
    raise ValueError("Graphite host not configured!")
metrics = statsd.StatsClient(graphite, 8125, prefix='')

def check_auth(username, password):
    return username == 'hackclub' and password == os.environ["BASIC_HTTP_AUTH_SECRET"]

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return "nope", 401
        return f(*args, **kwargs)
    return decorated_function

@app.route("/", methods=["GET"])
def index():
    return Response("Yo", status=200)

required_args = ["key", "type", "value"]
@app.route("/upload", methods=["POST"])
@login_required
def upload():
    args = request.args
    key = args.get("key", None)
    type = args.get("type", None)
    value = args.get("value", None)

    if key == None or type == None or value == None:
        return Response("Must supply key, type, and value", status=400)

    if type == "c":
        # Counter, integers
        metrics.incr(key, int(value))
    elif type == "t":
        # Time, milliseconds
        metrics.timer(key, int(value))
    elif type == "g":
        # Custom sampling - floating point
        metrics.gauge(key, value)

    metrics.incr(key, value)
    return Response(status=200)


def start_server():
    app.run(port=8080, debug=True, use_reloader=False)

threading.Thread(target=start_server).start()

