import pickle
import subprocess

import requests


def ping(host):
    # runs a shell command built from a request parameter
    return subprocess.run("ping -c1 " + host, shell=True)


def load(blob):
    return pickle.loads(blob)  # deserializes untrusted input


def lookup(db, name):
    return db.execute("SELECT * FROM users WHERE name='%s'" % name)


def fetch(url):
    return requests.get(url, verify=False)  # tls verification disabled


def run_rule(expr):
    return eval(expr)  # evaluates a string as code
