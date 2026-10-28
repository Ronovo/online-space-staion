# Space Station Explorer Online

A text-based exploration game set on a space station, played in the browser. It is a Flask web app with
accounts, where each account owns one character whose progress is saved on the server.

## Core Features

- **Accounts**: Register with a username and password; each account owns exactly one character
- **Character System**: Create a character with unique jobs (Staff Assistant to Captain), each with special access and starting credits
- **Station Navigation**: Explore a donut-shaped ring of hallways and department rooms with random events
- **Inventory System**: Carry items, store them in your quarters locker, and examine, read, drop, or drink them
- **Health System**: Track limb damage plus burns, poison, and oxygen; seek treatment in MedBay
- **Crew Roster**: Start alongside procedurally staffed NPC crew (department heads and assistants)
- **Persistent Progress**: Your character's progress is saved to the server after every action. Deleting the character erases that progress so you can roll a new one

## Station Systems

### Power Management
- Monitor and manage station battery levels
- Control system power allocation (life support, lighting, security, communications)
- Solar panel charging system
- Power modes including emergency settings
- Engineering panel access for Engineers and the Captain

### Medical System
- Health tracking for limbs, burns, poison, and oxygen
- Paid medical treatment and health assessments in MedBay
- Free self-treatment and crew vitals monitoring for Doctors
- Oxygen damage when life support is underpowered, with emergency revive if it reaches critical levels

### Security System
- Access control for restricted areas
- Door locking and unlocking for authorized personnel
- Crew manifest for Security staff

### Stock Market
- Real-time market simulation with automatic updates
- Buy and sell shares in various companies from your quarters computer
- Price history tracking and visualization
- Portfolio management and profit tracking
- Filtering options and detailed transaction history

### Bar System
- Order drinks from the menu
- Bartender drink mixing and recipe list
- Alcohol tracking on your character sheet
- Social interactions

### Botany System
- Seed collection from the botanist station
- Plant seeds across multiple planters
- Planter status monitoring
- Special access for Botanists

### Life Support
- Oxygen levels tied to power allocation
- Emergency protocols from Engineering
- Effects on player and crew safety when systems are underpowered

### Bridge and Personnel
- Talk to ship leadership when present
- Crew manifest and NPC job assignment for the Head of Personnel
- Public Access Control terminal for job-change requests
- Captain and HoP door control for the Bridge

### Engineering
- Fabricator for creating tools, books, and components
- Full power management panel for authorized staff

## Running it

Requires Python 3.9 or newer.

```sh
python -m venv .venv
.venv\Scripts\activate          # Windows; use `source .venv/bin/activate` elsewhere
pip install -r requirements.txt
python run_server.py
```

Open http://127.0.0.1:5000, register an account, and create your character.

`run_server.py` uses Flask's built-in server, which is fine for playing on your own machine or a LAN.

### Settings

| Environment variable | Default | What it does |
| --- | --- | --- |
| `HOST` | `127.0.0.1` | Interface to bind. Use `0.0.0.0` so other machines on your network can connect. |
| `PORT` | `5000` | Port to listen on. |
| `SPACE_ONLINE_SECRET_KEY` | generated | Session signing key. If unset, one is generated once into `instance/secret_key`. |

Accounts and characters are stored in `instance/space_online.sqlite3`, next to `run_server.py`. The
`instance/` folder is the game's only data: back it up to keep your players, delete it to start fresh.

### Docker

The `Dockerfile` runs the game under gunicorn on port 5000, with the data in a volume at `/app/instance`:

```sh
docker build -t space-station-explorer-online .
docker run -d -p 5000:5000 -v space-online-data:/app/instance space-station-explorer-online
```

Set `SPACE_ONLINE_SECRET_KEY` with `-e` so logins survive the key file being lost.

### Inside another site

`space_online.webapp.create_app()` returns a normal WSGI app, so a larger Flask site can mount it under a
path. Two settings make it fit there:

- `SESSION_COOKIE_PATH`: keep the game's login cookie to its own path, e.g. `/games/space-online/`.
- `BACK_LINK`: a `{"href", "label"}` pair shown as a back link at the top of every page.

```python
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from space_online.webapp import create_app as create_space_online

app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
    "/games/space-online": create_space_online({
        "SESSION_COOKIE_PATH": "/games/space-online/",
        "BACK_LINK": {"href": "/games", "label": "Games"},
    }),
})
```

## Tests

```sh
pip install -r requirements-dev.txt
python -m pytest
```

The tests cover accounts, character creation, playing and saving, mounting under a path, and the core game
rules (jobs, door access, inventory).

## Project layout

```
run_server.py            Starts the game with Flask's built-in server
space_online/webapp/     Flask app: routes, accounts, SQLite storage, templates, static files
space_online/game/       The game itself: station map, rooms, items, crew, jobs, power, market
tests/                   pytest suite
instance/                Created on first run: the database and secret key (not committed)
```

## Station Layout

The station uses a hollow-square hallway ring with special rooms branching off it:
- Quarters attached at the hallway junction
- Connected hallways forming a complete circuit
- Special rooms:
  - Bridge
  - MedBay
  - Security
  - Engineering Bay
  - Bar
  - Botany Lab

## Job Access Levels

- **Staff Assistant**: Basic access
- **Engineer**: Engineering Bay + power management
- **Security Guard**: Security systems + door control
- **Doctor**: MedBay + advanced treatment
- **Bartender**: Bar + drink mixing
- **Botanist**: Botany Lab + plant cultivation
- **Head of Personnel**: Multiple department access + personnel tools
- **Captain**: Full station access

## Tips

- Monitor your health and seek treatment in MedBay when needed
- Keep track of power levels and oxygen status from Engineering
- Use the stock market on your quarters computer to earn additional credits
- Explore all rooms to discover features, items, and job-specific stations
- Progress saves automatically; Save and Exit returns you to your account page
