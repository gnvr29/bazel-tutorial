# Bazel Microservices Monorepo

A minimal monorepo with two independent REST services built by the same Bazel workspace:

| Service    | Stack                         | Endpoint                 | Port |
|------------|-------------------------------|--------------------------|------|
| `java_api` | Java 21, Spring Boot 4.1      | `GET /api/java/status`   | 8080 |
| `python_api` | Python 3.12, FastAPI + Uvicorn | `GET /api/python/status` | 8000 |

## Structure

```
.
├── MODULE.bazel            # Bzlmod: rules_java, rules_jvm_external, rules_python + deps
├── maven_install.json      # Pinned Maven dependency list (Spring Boot)
├── BUILD.bazel             # Exposes maven_install.json to Bazel
├── .bazelrc                # Shared flags (hermetic JDK 21, rules_python options)
├── .bazelversion           # Bazel version used by Bazelisk (9.3.0)
├── java_api/
│   ├── BUILD.bazel         # java_binary target
│   └── src/main/
│       ├── java/com/example/javaapi/
│       │   ├── Application.java       # Spring Boot entry point
│       │   └── StatusController.java  # GET /api/java/status
│       └── resources/application.properties
└── python_api/
    ├── BUILD.bazel         # py_binary target
    ├── main.py             # FastAPI app + GET /api/python/status
    ├── requirements.in     # Direct Python dependencies
    └── requirements_lock.txt  # Fully pinned, hashed lock file
```

How dependencies flow:

- Java: `MODULE.bazel` declares the Spring Boot starter via `rules_jvm_external`. Resolved versions are pinned in `maven_install.json` and exposed as `@maven//:<group>_<artifact>` targets.
- Python: `rules_python` downloads a hermetic Python 3.12 interpreter and installs wheels from `requirements_lock.txt`, exposed as `@pypi//<package>` targets.

No local JDK or Python install is required; Bazel fetches both toolchains.

## Prerequisites

[Bazelisk](https://github.com/bazelbuild/bazelisk) (installed as `bazel`). It reads `.bazelversion` and downloads the right Bazel.

```bash
brew install bazelisk
```

## Build and run

```bash
# Build everything
bazel build //...

# Run the Java service (terminal 1)
bazel run //java_api

# Run the Python service (terminal 2)
bazel run //python_api
```

Check the endpoints:

```bash
curl http://127.0.0.1:8080/api/java/status
# {"service":"java-api","status":"ok"}

curl http://127.0.0.1:8000/api/python/status
# {"service":"python-api","status":"ok"}
```

Both services bind to `127.0.0.1` only. Use `0.0.0.0` (`server.address` in `application.properties`, `host` in `main.py`) when running in containers. The endpoints have no authentication; this is a demo.

## Updating dependencies

Java: edit `maven.install(artifacts = [...])` in `MODULE.bazel`, then re-pin:

```bash
REPIN=1 bazel run @maven//:pin
```

Python: edit `python_api/requirements.in`, then regenerate the lock file (requires [uv](https://docs.astral.sh/uv/)):

```bash
cd python_api
uv pip compile requirements.in --generate-hashes --universal --python-version 3.12 -o requirements_lock.txt
```

## Behind a corporate TLS proxy (optional)

If downloads fail with `PKIX path building failed` or `certificate verify failed`, create a gitignored `user.bazelrc` at the repo root (auto-loaded by `.bazelrc`) that points Bazel, Coursier and pip at a trust store containing your proxy's root CA:

```
startup --host_jvm_args=-Djavax.net.ssl.trustStore=/abs/path/truststore.jks
startup --host_jvm_args=-Djavax.net.ssl.trustStorePassword=changeit
common --repo_env="COURSIER_OPTS=-Djavax.net.ssl.trustStore=/abs/path/truststore.jks -Djavax.net.ssl.trustStorePassword=changeit"
common --repo_env=PIP_CERT=/abs/path/ca-bundle.pem
common --repo_env=SSL_CERT_FILE=/abs/path/ca-bundle.pem
```

Build `truststore.jks` by copying a JDK's `lib/security/cacerts` and importing the proxy CA with `keytool -importcert`. Build `ca-bundle.pem` by concatenating certifi's bundle with the proxy CA in PEM format.
