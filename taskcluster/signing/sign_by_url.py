import yaml
import taskcluster
from jinja2 import Template, StrictUndefined
from taskcluster import stringDate, fromNow, stableSlugId, slugId
from jose.constants import ALGORITHMS
from jose import jws
import time
import datetime
from functools import partial
import json
import os


def sign_task(task_id, pvt_key, valid_for=3600, algorithm=ALGORITHMS.RS512):
    # reserved JWT claims, to be verified
    # Issued At
    iat = int(time.time())
    # Expiration Time
    exp = iat + valid_for
    claims = {
        "iat": iat,
        "exp": exp,
        "taskId": task_id,
        "version": "1",
    }
    return jws.sign(claims, pvt_key, algorithm=algorithm)

config = json.load(open("secrets.json"))
config["credentials"]["certificate"] = json.dumps(config["credentials"]["certificate"])
scheduler = taskcluster.Scheduler(config)
# funsize scheduler key
pvt_key = open("id_rsa").read()

template_vars = {
    "stableSlugId": stableSlugId(),
    "now": stringDate(datetime.datetime.utcnow()),
    "now_ms": time.time() * 1000,
    "fromNow": fromNow,
    "sign_task": partial(sign_task, pvt_key=pvt_key),
    ### TODO: change these
    "url": "http://people.mozilla.org/~raliiev/bouncer.apk",
    "filename": "bouncer.apk",
    "signign_format": "jar",
    "hash": "8f4210c62cf533322b09237a3741bc3e9bb52582b8d0b88c52a0d78a6eabe08e29b636d5c9668e8db721c9dead36736db643c53231e966c86dbc28d86b9eb699",
}

template_file = os.path.join(os.path.dirname(__file__), "graph.yml")
with open(template_file) as f:
    template = Template(f.read(), undefined=StrictUndefined)
rendered = template.render(**template_vars)
graph = yaml.safe_load(rendered)
import pprint
pprint.pprint(graph)
graph_id = slugId()

print "submitting", graph_id
print scheduler.createTaskGraph(graph_id, graph)
print "https://tools.taskcluster.net/task-graph-inspector/#{}/".format(graph_id)
