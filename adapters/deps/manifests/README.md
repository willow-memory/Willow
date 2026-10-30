<!-- willow-addon
section: Reading more kinds of files
line: Docker Compose and Kubernetes YAML: each service, image, port and volume as a passage.
source: new
added: 2026-10-29
needs: PyYAML; MIT
floor: PyYAML 5.3.1
writes: to
network: none
tags: needs-install, offline, writes-output, file-reader
-->
# manifests

"Which service listens on 8080?", "what image does the backup job run?",
"where does postgres keep its data?": the answers are in a Compose file or a
Kubernetes manifest, written as nested YAML the kernel would serve a line of.
This writes each service and each object as one passage that holds the
answer, into a mirror folder the kernel can search.

    pip install -r adapters/deps/manifests/requirements.txt
    python adapters/deps/manifests/manifests.py mirror --from FOLDER --to MIRROR
    python kernel.py init --box BOX --pile MIRROR --key KEY

Each .yml or .yaml that is a Compose file (it has `services:`) or holds
Kubernetes objects (each with `apiVersion` and `kind`) becomes
`MIRROR/<same path>.txt`:

    == service web
    image nginx:1.27
    ports 8080:80
    volumes ./site:/usr/share/nginx/html:ro
    depends on db
    environment names DEBUG, DB_HOST

    == Deployment shop/web
    replicas 3
    container web: image nginx:1.27
    container web: ports 80/TCP
    container web: mounts site at /usr/share/nginx/html

**What each says.** A Compose service: its image or build, ports, exposed
ports, volumes, what it depends on, its networks, its environment's names and
env files, its restart rule; then the file's named volumes, networks,
secrets and configs. A Kubernetes workload (Deployment, StatefulSet,
DaemonSet, Job, CronJob, Pod and the rest): its labels, replicas, schedule,
each container's image, ports, mounts and environment's names, its volumes
and claim templates. A Service: its type, ports and selector. An Ingress:
each route. A PersistentVolumeClaim: its size and access. A `List` is read
item by item.

**Names, never values.** An environment variable, a ConfigMap or a Secret is
written by its names only. A manifest often holds a password, and a mirror
is for finding things, not for making another copy of one.

**Read safely.** YAML is loaded with PyYAML's safe loader, so a tag that
would build an object or run a command builds nothing: the file is skipped
and counted. A YAML file of neither kind (a CI workflow, say) is left alone
and counted as other YAML.

**The reader contract** (shared with every file reader): hidden files and
folders are skipped; nothing is written inside FOLDER and no original
changes; MIRROR inside FOLDER, or the other way round, is refused; the same
file always gives the same bytes.

**Can't:** fill in a Helm template (`{{ .Values.x }}` isn't YAML until Helm
renders it), merge Compose overrides, or follow `extends:`.

On twelve real files, from Docker's awesome-compose and Kubernetes' own
examples, it wrote all twelve, the same bytes at the pins and at the floor. willow's four demo
folders hold no YAML.

**Without PyYAML** it refuses and names the install: exit 2, never a quiet
skip.

**Uses:** the kernel's exit codes: 0 wrote at least one file; 42 nothing
readable; 2 refused.

**Never:** writes inside your folder, changes an original, writes a value of
a secret or an environment, or goes online.
