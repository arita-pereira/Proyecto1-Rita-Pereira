# 🚕 TaxiTech Solutions — Digital Taximeter

A software prototype that replaces physical taxi meters with a fully digital system, built as a pilot project for TaxiTech Solutions' operations team.

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat&logo=python&logoColor=white&labelColor=333)
![Estado](https://img.shields.io/badge/Estado-En%20revisi%C3%B3n%20final-2dd4bf?style=flat&labelColor=333)
![Prioridad](https://img.shields.io/badge/Prioridad-Alta-e63946?style=flat&labelColor=333)

🔗 [GitHub Repository](https://github.com/arita-pereira/Proyecto1-Rita-Pereira) · [Kanban Board](https://github.com/users/arita-pereira/projects/4)

## 📋 Project Context

TaxiTech Solutions has used physical Hale T200 taximeters since 2018. The manufacturer discontinued support in 2023, and devices are starting to fail across the fleet. This project is a functional prototype to validate a 100% software-based replacement before committing budget to an external vendor.

## ✨ Features

- Real-time fare calculation based on vehicle state (stopped / moving)
- Configurable tariffs via a JSON file, no code changes required
- Trip history persisted in a SQLite database for data integrity and structured queries
- Daily trip history with total earnings summary
- Password-protected access with salted PBKDF2 hashes (no plaintext passwords)
- Screen lock feature, so passengers cannot tamper with the meter mid-ride
- Two interfaces: a command-line app for the driver's console and a mobile/tablet-friendly web app
- REST API backing the web app, reusable by any future client
- Activity logging for auditability
- Unit tests for the fare calculation logic

## 💶 Current Tariffs (EMT Madrid Zone, June 2025)

| Status | Rate |
|---|---|
| Stopped or speed < 20 km/h | €0.02/second |
| Moving | €0.05/second |

Rates are editable in `config/tarifas.json` without touching the code.

## 🏗️ Architecture

The project follows a layered architecture:

- `src/domain/` — core business logic (`Carrera`, `Tarifa`), independent of any interface or storage detail
- `src/application/` — use cases (`ServicioCarrera`): start a trip, toggle its state, end it and save it to the history. It holds the active trip and orchestrates the domain and the infrastructure, so both interfaces share the same rules
- `src/infrastructure/` — technical support (logging, persistence, authentication, fare configuration)
- `src/interfaces/` — thin entry points that only read user input and show results (`cli.py` for the command line, `web.py` for the Flask web/API app)

## 🛠️ Technical Decisions

- **Flask**: lightweight enough for a prototype, no unnecessary boilerplate, and lets the same business logic (`domain/`) power both the CLI and the web app without duplication.
- **SQLite**: no external database server to install or configure, fits the single-command deployment requirement, and still gives relational integrity and structured queries — enough for a pilot with one vehicle.
- **Layered architecture** (`domain` / `infrastructure` / `interfaces`): keeps business rules independent of any specific interface or storage technology, so either can be replaced (e.g. SQLite → PostgreSQL, or adding a mobile client) without touching the fare logic.
- **Conda**: consistent, reproducible environment across development machines.

## 📁 Project Structure
```
taxitech/
├── config/
│ ├── tarifas.json # Fare configuration
│ ├── security.example.json # Format of the (git-ignored) credentials file
│ └── security.json # Salted password hash, created locally (not versioned)
├── data/
│ └── historial.db # Trip history (SQLite database)
├── logs/
│ └── taximetro.log # Application logs
├── src/
│ ├── application/
│ │ └── servicio_carrera.py # Trip use cases shared by CLI and web
│ ├── domain/
│ │ ├── carrera.py # Trip logic
│ │ └── tarifa.py # Fare calculation logic
│ ├── infrastructure/
│ │ ├── auth.py # Salted PBKDF2 password hashing and verification
│ │ ├── historial.py # Trip history persistence
│ │ ├── logger.py # Logging configuration
│ │ └── tarifas.py # Loads fares from config/tarifas.json
│ └── interfaces/
│ ├── cli.py # Command-line interface
│ └── web.py # Web app + REST API (Flask)
├── templates/
│ ├── index.html # Main taximeter screen
│ └── login.html # Access screen
├── tests/
│ └── test_tarifa.py # Unit tests
├── main.py
├── pytest.ini
└── requirements.txt
```
## ⚙️ Setup

1. Create and activate the conda environment:
```
conda create -n taximetro python=3.x
conda activate taximetro
```
2. Install dependencies:
```
pip install -r requirements.txt
```

## 🚀 Quick Start

Run the entire application with a single command:

​```
pip install -r requirements.txt && python -m scripts.set_password && python -m src.interfaces.web
​```

The `set_password` step asks you to choose an access password the first time (it is stored as a salted hash in a git-ignored file); skip it on later runs. The server starts at `http://127.0.0.1:5000`. No other manual configuration is needed beyond having Python and pip installed. Trip data persists in `data/historial.db` (SQLite) across restarts.

## ▶️ Usage

### Command-line interface
```
python -m src.interfaces.cli
```
Menu options: start trip, change state (stopped/moving), end trip and charge, view today's history, exit, lock the app.

### Web app (recommended for tablet/mobile use)
```
python -m src.interfaces.web
```

By default the server runs on `http://127.0.0.1:5000` and is also reachable from other devices on the same WiFi network at `http://YOUR_COMPUTER_IP:5000`. Find your local IP with:

- macOS: `ipconfig getifaddr en0`
- Linux: `hostname -I`
- Windows: `ipconfig` (look for "IPv4 Address" under your active network adapter)

On first load you'll be asked for the access password (numeric keypad on mobile). From the main screen you can start a trip, switch between stopped/moving, end the trip, view the daily history with total earnings, and lock the screen.

## 🔌 REST API

All endpoints require an authenticated session (login via `/login` first).

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/carrera/iniciar` | Start a new trip |
| POST | `/api/carrera/estado` | Toggle state (stopped/moving) |
| POST | `/api/carrera/finalizar` | End the trip and return the total fare |
| GET | `/api/carrera/actual` | Get the live state and running total of the active trip |
| GET | `/api/historial` | Get today's trip history |

## 🔒 Security

Access is protected by a password. It is never stored in plaintext: `config/security.json` only holds a random salt and a PBKDF2-HMAC-SHA256 hash (600,000 iterations), and passwords are compared with `hmac.compare_digest`.

That file is git-ignored, so credentials never reach the repository. Create your own password once after cloning:

```
python -m scripts.set_password
```

The script asks for the password without echoing it. See `config/security.example.json` for the file format.

The web app signs its session cookie with a secret key that is never stored in the code. Optional environment variables:

| Variable | Purpose |
|----------|---------|
| `TAXITECH_SECRET_KEY` | Key that signs the session cookie. If unset, a random key is generated at startup, so sessions end when the server restarts. Set it to keep sessions across restarts. |
| `TAXITECH_DEBUG` | Set to `1` to enable Flask debug mode. Off by default; never enable it on a shared network. |

## ✅ Testing
```
pytest
```

44 tests, all isolated from real data (temporary SQLite database, temporary credentials file and a controllable clock):

- **Fares** (`test_tarifa.py`): `Tarifa.calcular_coste` across normal, edge and zero-rate cases.
- **Authentication** (`test_auth.py`): salted PBKDF2 hashing, correct and wrong passwords, missing or old-format credentials file.
- **Use cases** (`test_servicio_carrera.py`): trip lifecycle and error cases in `ServicioCarrera`, independent of any interface.
- **REST API** (`test_api.py`): login and logout, `401` on every protected endpoint without a session, trip lifecycle (start, toggle state, live total, end), error cases and a full trip saved to the history.
- **Persistence** (`test_historial.py`): table creation, saving and reading trips, filtering by date, rounding and trips without an end time.

## 📝 Logging

All key actions (trip start/end, state changes, login attempts) are logged to `logs/taximetro.log` for auditability.

## 🗺️ Next Steps

This prototype validates the core concept. Future phases could include:

- **Multi-user accounts with role separation**: individual driver logins plus a fleet manager role, so trip history isn't tied to a single shared password
- **Integrated GPS**: automatic detection of stopped/moving state based on speed, removing the need for manual toggling
- **Centralized, extractable database**: a fleet-wide database the manager can query and export across all vehicles, not just one
- **Digital receipts**: emailed or printable receipts for passengers
- **Payment integration**: card/mobile payment support at the end of a trip
- **Admin dashboard**: a web panel for the fleet manager with aggregated stats across drivers and days
- **Push notifications**: alerts for the fleet manager (e.g. long idle periods, unusual fares)
- **Integration and end-to-end tests**: beyond the current unit tests for fare calculation, covering the full trip flow and API
- **Cloud deployment with CI/CD**: hosting the app centrally with automated testing and deployment on each change

## 👩‍💻 Author

Rita Pereira — IA School, Project P1 (TaxiTech Solutions)
