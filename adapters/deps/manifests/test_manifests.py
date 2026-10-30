"""manifests: each Compose service and Kubernetes object as a passage, with
names but never values for environments, ConfigMaps and Secrets; the shared
reader contract; and a refusal, never a quiet skip, without PyYAML."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
KERNEL = HERE.parents[2] / "kernel.py"
SCRIPT = HERE / "manifests.py"
NOW = ["--now", "2026-10-29T09:00:00Z"]

COMPOSE = """\
services:
  web:
    image: nginx:1.27
    ports: ["8080:80", {target: 443, published: 8443, protocol: tcp}]
    volumes:
      - ./site:/usr/share/nginx/html:ro
      - {type: volume, source: logs, target: /var/log/nginx}
    depends_on: [db]
    environment:
      DEBUG: "1"
      DB_PASSWORD: hunter2
  db:
    build: {context: ./db}
    environment: [POSTGRES_PASSWORD=s3cret, POSTGRES_DB]
    env_file: db.env
    restart: always
volumes:
  logs: {}
"""

K8S = """\
apiVersion: apps/v1
kind: Deployment
metadata: {name: web, namespace: shop, labels: {app: web}}
spec:
  replicas: 3
  template:
    spec:
      containers:
        - name: web
          image: nginx:1.27
          ports: [{containerPort: 80}]
          volumeMounts: [{name: site, mountPath: /usr/share/nginx/html}]
          env: [{name: API_TOKEN, value: abc123}]
      volumes: [{name: site, persistentVolumeClaim: {claimName: site-pvc}}]
---
apiVersion: apps/v1
kind: StatefulSet
metadata: {name: db, namespace: shop}
spec:
  template: {spec: {containers: [{name: pg, image: "postgres:17"}]}}
  volumeClaimTemplates:
    - metadata: {name: data}
      spec: {resources: {requests: {storage: 10Gi}}}
---
apiVersion: v1
kind: Service
metadata: {name: web, namespace: shop}
spec:
  type: NodePort
  selector: {app: web}
  ports: [{port: 80, targetPort: 8080, nodePort: 30080}]
---
apiVersion: v1
kind: Secret
metadata: {name: db, namespace: shop}
stringData: {password: hunter2}
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata: {name: front}
spec:
  rules:
    - host: shop.example
      http:
        paths: [{path: /, backend: {service: {name: web, port: {number: 80}}}}]
---
apiVersion: batch/v1
kind: CronJob
metadata: {name: backup}
spec:
  schedule: "0 3 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers: [{name: dump, image: "postgres:17"}]
"""


def run(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *argv], capture_output=True, text=True)


def folder(tmp_path: Path) -> Path:
    src = tmp_path / "infra"
    (src / "k8s").mkdir(parents=True)
    (src / "compose.yaml").write_text(COMPOSE)
    (src / "k8s" / "shop.yml").write_text(K8S)
    (src / "ci.yml").write_text("on: push\njobs: {test: {runs-on: ubuntu}}\n")
    (src / "broken.yaml").write_text("services: [unclosed\n")
    marker = tmp_path / "ran"
    (src / "danger.yaml").write_text(
        f"!!python/object/apply:os.system ['touch {marker}']\n"
    )
    (src / ".hidden").mkdir()
    (src / ".hidden" / "x.yml").write_text(COMPOSE)
    return src


def mirror(src: Path, dst: Path) -> subprocess.CompletedProcess:
    return run(str(SCRIPT), "mirror", "--from", str(src), "--to", str(dst))


def test_each_compose_service_is_a_passage(tmp_path):
    src, dst = folder(tmp_path), tmp_path / "mirror"
    got = mirror(src, dst)
    assert got.returncode == 0, got.stderr
    assert got.stdout.strip().endswith("; 1 other YAML; skipped 2")
    assert (dst / "compose.yaml.txt").read_text() == (
        "== service web\n"
        "image nginx:1.27\n"
        "ports 8080:80, 8443:443/tcp\n"
        "volumes ./site:/usr/share/nginx/html:ro, logs:/var/log/nginx\n"
        "depends on db\n"
        "environment names DEBUG, DB_PASSWORD\n"
        "\n"
        "== service db\n"
        "build ./db\n"
        "environment names POSTGRES_PASSWORD, POSTGRES_DB\n"
        "env files db.env\n"
        "restart always\n"
        "\n"
        "== volumes\n"
        "logs\n"
    )


def test_each_kubernetes_object_is_a_passage(tmp_path):
    src, dst = folder(tmp_path), tmp_path / "mirror"
    mirror(src, dst)
    assert (dst / "k8s" / "shop.yml.txt").read_text() == (
        "== Deployment shop/web\n"
        "labels app=web\n"
        "replicas 3\n"
        "container web: image nginx:1.27\n"
        "container web: ports 80/TCP\n"
        "container web: mounts site at /usr/share/nginx/html\n"
        "container web: environment names API_TOKEN\n"
        "volume site: persistentVolumeClaim site-pvc\n"
        "\n"
        "== StatefulSet shop/db\n"
        "container pg: image postgres:17\n"
        "claim data: 10Gi\n"
        "\n"
        "== Service shop/web\n"
        "type NodePort\n"
        "ports 80 to 8080/TCP node 30080\n"
        "selects app=web\n"
        "\n"
        "== Secret shop/db\n"
        "keys password\n"
        "\n"
        "== Ingress front\n"
        "route shop.example/ to web:80\n"
        "\n"
        "== CronJob backup\n"
        "schedule 0 3 * * *\n"
        "container dump: image postgres:17\n"
    )


def test_no_value_of_a_secret_or_an_environment_reaches_the_mirror(tmp_path):
    src, dst = folder(tmp_path), tmp_path / "mirror"
    mirror(src, dst)
    every = "".join(p.read_text() for p in dst.rglob("*.txt"))
    for secret in ("hunter2", "s3cret", "abc123"):
        assert secret not in every


def test_yaml_is_read_safely(tmp_path):
    """A tag that would run a command builds nothing: the file is skipped."""
    src, dst = folder(tmp_path), tmp_path / "mirror"
    mirror(src, dst)
    assert not (tmp_path / "ran").exists()
    assert not (dst / "danger.yaml.txt").exists()


def test_the_kernel_finds_which_service_uses_a_port(tmp_path):
    src, dst = folder(tmp_path), tmp_path / "mirror"
    mirror(src, dst)
    b = tmp_path / "box"
    run(str(KERNEL), "init", "--box", str(b), "--pile", str(dst),
        "--key", str(tmp_path / "k"), *NOW)  # fmt: skip
    got = json.loads(
        run(str(KERNEL), "bite", "--box", str(b), *NOW, "which service nodeport").stdout
    )
    assert got["state"] == "populated"
    assert got["served"][0]["where"] == "k8s/shop.yml.txt:14"


def test_the_same_file_gives_the_same_bytes_and_originals_are_untouched(tmp_path):
    src = folder(tmp_path)
    before = {p: p.read_bytes() for p in src.rglob("*") if p.is_file()}
    for name in ("one", "two"):
        mirror(src, tmp_path / name)
    for rel in ("compose.yaml.txt", "k8s/shop.yml.txt"):
        assert (tmp_path / "one" / rel).read_bytes() == (
            tmp_path / "two" / rel
        ).read_bytes()
    assert {p: p.read_bytes() for p in src.rglob("*") if p.is_file()} == before


def test_refusals_and_nothing_readable(tmp_path):
    src = folder(tmp_path)
    assert mirror(src, src / "m").returncode == 2
    assert mirror(src, tmp_path).returncode == 2
    assert run(str(SCRIPT), "mirror", "--from", str(src)).returncode == 2
    empty = tmp_path / "empty"
    empty.mkdir()
    (empty / "ci.yml").write_text("on: push\n")
    assert mirror(empty, tmp_path / "m2").returncode == 42


def test_without_pyyaml_it_refuses_and_names_the_install(tmp_path):
    blocker = tmp_path / "block"
    blocker.mkdir()
    (blocker / "yaml.py").write_text("raise ImportError('hidden')\n")
    src = folder(tmp_path)
    script = (
        "import runpy, sys\n"
        f"sys.path.insert(0, {str(blocker)!r})\n"
        f"sys.argv = [{str(SCRIPT)!r}] + sys.argv[1:]\n"
        f"runpy.run_path({str(SCRIPT)!r}, run_name='__main__')\n"
    )
    got = run("-c", script, "mirror", "--from", str(src), "--to", str(tmp_path / "m"))
    assert got.returncode == 2 and "requirements.txt" in got.stderr
