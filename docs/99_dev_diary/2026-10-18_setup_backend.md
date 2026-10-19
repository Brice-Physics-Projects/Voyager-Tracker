# Voyager Tracker — Development Diary

## October 18, 2026 — Project Structure and First Working Backend

### Session Goal

Establish the repository structure, configure the Python backend, and run a minimal FastAPI application locally.

### Architecture Decisions

- Keep the frontend and backend in one repository, with separate dependencies and deployment configurations.
- Use Next.js for the planned frontend and FastAPI for the backend.
- Manage Python dependencies and the virtual environment with uv.
- Use the Python `src` layout with a package named `voyager_tracker` rather than a generic `app` package.
- Build incrementally: establish a working backend before connecting external data sources.

### Python Project Configuration

Initialized the backend using `uv init`. The generated project was initially named `backend`, had no dependencies, and required Python 3.12 or newer.

Updated the configuration to give the project a meaningful name and make the source package installable:

```toml
[project]
name = "voyager-tracker"
version = "0.1.0"
description = "Python API for Voyager spacecraft positions, mission imagery, and history."
requires-python = ">=3.12"
dependencies = []

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/voyager_tracker"]
```

This is the configuration before dependency installation. `uv add` updates the dependency list and lockfile; the current repository files are authoritative for installed versions.

Removed the generated `readme = "README.md"` setting because it refers to a README inside `backend/`, whereas the project README is at the repository root. It can be restored if a backend-specific README is added.

The distribution name is `voyager-tracker`; the Python import name is `voyager_tracker`.

### Dependency Installation and Import Check

Installed the initial web API dependencies from `backend/`:

```bash
uv add fastapi "uvicorn[standard]"
```

- FastAPI defines the application and routes.
- Uvicorn serves the application.
- Hatchling builds and installs the Python package.

Verified that the package could be imported:

```bash
uv run python -c "import voyager_tracker; print(voyager_tracker.__file__)"
```

The import check worked, confirming that the package setup was functional.

### Virtual Environment Naming

Discussed keeping the environment directory at `backend/.venv` while using a clearer terminal prompt:

```bash
uv venv --prompt voyager-tracker
source .venv/bin/activate
```

These commands were provided as an option; execution was not confirmed in the conversation. Commands run through `uv run` do not require manual activation.

### First FastAPI Application

Provided the following application in `src/voyager_tracker/main.py`:

```python
from fastapi import FastAPI

app = FastAPI(
    title="Voyager Tracker API",
    description="Explore Voyager spacecraft positions, imagery, and mission history.",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {"status": "ok"}
```

The `/health` route is intended to confirm that the application responds. It does not check NASA or JPL service availability.

### Startup Error and Resolution

The first server startup reported:

```text
ERROR: Error loading ASGI app. Attribute "app" not found in module "voyager_tracker.main".
```

This meant Uvicorn found the module but could not find its `app` object. Reviewed the expected contents of `main.py` and the need to save the file with a module-level `app = FastAPI(...)` definition. The precise underlying edit or save issue was not independently established.

The initial command was run from `backend/src/voyager_tracker/`. Changed the recommended working directory to `backend/` so the development reloader would watch the backend directory:

```bash
uv run uvicorn voyager_tracker.main:app --reload
```

Command breakdown:

| Part | Meaning |
| --- | --- |
| `uv run` | Run within the uv-managed project environment. |
| `uvicorn` | Start the ASGI server. |
| `voyager_tracker.main` | Import the package's `main.py` module. |
| `:app` | Use the module-level FastAPI object named `app`. |
| `--reload` | Restart the development server when watched source files change. |

After troubleshooting, the backend was confirmed running.

### Local Verification Targets

These URLs were provided for checking the application:

- Health response: http://localhost:8000/health
- Interactive API documentation: http://localhost:8000/docs

Expected health response:

```json
{"status": "ok"}
```

Server startup was confirmed. Separate confirmation of the browser responses and automated tests was not recorded.

### Current Status

| Item | Status |
| --- | --- |
| Repository structure basics | Set up |
| Installable Python package | Import verified |
| FastAPI and Uvicorn setup | Working backend confirmed |
| Health endpoint and API documentation | Verification instructions provided |
| Frontend application | Not implemented in this session |
| JPL Horizons integration | Not started |
| NASA image integration | Not started |
| Automated tests | Not run in this session |
| Deployment | Not started |

### Next Step — Paused for Documentation

The proposed next step was to install `httpx` and create `src/voyager_tracker/services/horizons.py`:

```bash
uv add httpx
```

Neither installation nor service-file creation was confirmed before pausing. The intended first integration is a request for Voyager 1's position relative to the Sun, followed by inspection of the response format, units, reference frame, and timestamps before exposing normalized values through the API.

### Lessons From This Session

- A directory named `backend` does not require the Python project or import package to have that name.
- The `src` layout requires packaging configuration so the application can be imported consistently.
- Uvicorn's `module:object` syntax identifies both the module to import and the application object to serve.
- Successful package import and successful server startup verify different parts of the setup.
- A running local backend is the first milestone; external data integration remains a separate task.
