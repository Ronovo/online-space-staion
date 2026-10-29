import copy
import random

from space_online.game.maps import donut
from space_online.game.objects.items import build_default_locker_inventory
from space_online.game.helper_methods.power_constants import default_station_power
from space_online.game.helper_methods.stock_market import (
    create_default_companies,
    default_stock_market_state,
    serialize_companies,
)
from space_online.game.helper_methods.npc_movement import location_for_post, pick_random_hallway_location
from space_online.game.helper_methods.random_events import ensure_job_event
from space_online.game.helper_methods.game_clock import default_game_clock

NPC_NAMES = [
    "Alex Chen", "Morgan Yu", "Sarah Connor", "John Shepard", "Ellen Ripley",
    "Isaac Clarke", "Samantha Carter", "Jean-Luc Picard", "Nyota Uhura", "Malcolm Reynolds",
    "River Tam", "Kaidan Alenko", "Liara T'Soni", "James Holden", "Naomi Nagata",
    "Amos Burton", "Alex Kamal", "Camina Drummer", "Julie Mao", "Joe Miller",
    "Kara Thrace", "William Adama", "Laura Roslin", "Gaius Baltar", "Sharon Valerii",
    "David Bowman", "Frank Poole", "Chris Hadfield", "Valentina Tereshkova", "Yuri Gagarin",
    "Sally Ride", "Neil Armstrong", "Mae Jemison", "Buzz Aldrin", "Alan Shepard",
    "Jim Lovell", "John Glenn", "Peggy Whitson", "Scott Kelly", "Christina Koch",
    "Anne McClain", "Jessica Meir", "Sunita Williams", "Mark Kelly", "Michael Collins",
    "Helen Sharman", "Tim Peake", "Andreas Mogensen", "Thomas Pesquet", "Samantha Cristoforetti"
]

JOBS = {
    "Staff Assistant": {
        "department": "Civilian",
        "subdepartment": "Assistant",
        "credits": 1000,
        "description": "Staff Assistants are the backbone of daily station operations. They handle various tasks as needed across the station. Starting with 1000 credits.",
    },
    "Engineer": {
        "department": "Engineering",
        "subdepartment": "Engineer",
        "credits": 2500,
        "description": "Engineers are responsible for keeping the station's critical systems operational. They excel at repairing equipment and solving technical problems. Starting with 2500 credits and access to the Engineering Station.",
    },
    "Security Guard": {
        "department": "Security",
        "subdepartment": "Security",
        "credits": 5000,
        "description": "Security Guards maintain order and protect the station from threats. They have access to security systems and equipment. Starting with 5000 credits and access to the Security Station.",
    },
    "Doctor": {
        "department": "Medical",
        "subdepartment": "Doctor",
        "credits": 7500,
        "description": "Doctors provide medical care to the station's crew. They can diagnose and treat a variety of conditions. Starting with 7500 credits and access to the MedBay Station.",
    },
    "Captain": {
        "department": "Administration",
        "subdepartment": "Captain",
        "credits": 10000,
        "description": "The Captain is the highest authority on the station. They make critical decisions and coordinate all departments. Starting with 10000 credits and access to all station areas.",
    },
    "Bartender": {
        "department": "Civilian",
        "subdepartment": "Bar",
        "credits": 3500,
        "description": "Bartenders run the station's social hub, mixing drinks and providing a place for crew members to relax. They have deep knowledge of beverages and excellent social skills. Starting with 3500 credits and access to the Bar Station.",
    },
    "Head of Personnel": {
        "department": "Administration",
        "subdepartment": "HoP",
        "credits": 9000,
        "description": "The Head of Personnel (HoP) is the second-in-command of the station. They manage crew assignments, access permissions, and administrative matters. Starting with 9000 credits and access to the HoP Station and Bar Station.",
    },
    "Botanist": {
        "department": "Civilian",
        "subdepartment": "Botany",
        "credits": 3000,
        "description": "Botanists cultivate and maintain the station's plant life. They grow food, medicinal herbs, and decorative plants in the Botany Lab. Starting with 3000 credits and access to the Botany Station.",
    },
}


DEPARTMENT_ORDER = [
    "Civilian",
    "Medical",
    "Engineering",
    "Security",
    "Administration",
]


def group_jobs_by_department():
    """Group jobs by department, sorted by DEPARTMENT_ORDER with credits ascending within each."""
    by_dept = {}
    for job_name, job_info in JOBS.items():
        by_dept.setdefault(job_info["department"], []).append((job_name, job_info["credits"]))

    result = []
    seen = set()
    for dept in DEPARTMENT_ORDER:
        if dept in by_dept:
            jobs = sorted(by_dept[dept], key=lambda x: x[1])
            result.append((dept, [job_name for job_name, _ in jobs]))
            seen.add(dept)

    for dept in sorted(by_dept.keys()):
        if dept not in seen:
            jobs = sorted(by_dept[dept], key=lambda x: x[1])
            result.append((dept, [job_name for job_name, _ in jobs]))

    return result


SELECT_DEPARTMENT = "Select A Department"
SELECT_JOB = "Select A Job"


def get_jobs_for_department(department):
    """Return sorted job names for a department, or empty list if not found."""
    for dept, jobs in group_jobs_by_department():
        if dept == department:
            return jobs
    return []


def permissions_for_job(job):
    """Return station permission flags for the given job title."""
    if job == "Captain":
        return {
            "security_station": True,
            "medbay_station": True,
            "bridge_station": True,
            "engineering_station": True,
            "bar_station": True,
            "hop_station": True,
            "botany_station": True,
        }
    if job == "Head of Personnel":
        return {
            "security_station": False,
            "medbay_station": False,
            "bridge_station": False,
            "engineering_station": False,
            "bar_station": True,
            "hop_station": True,
            "botany_station": True,
        }
    if job == "Botanist":
        return {
            "security_station": False,
            "medbay_station": False,
            "bridge_station": False,
            "engineering_station": False,
            "bar_station": False,
            "hop_station": False,
            "botany_station": True,
        }
    return {
        "security_station": job == "Security Guard",
        "medbay_station": job == "Doctor",
        "bridge_station": job == "Captain",
        "engineering_station": job == "Engineer",
        "bar_station": job == "Bartender",
        "hop_station": False,
        "botany_station": job == "Botanist",
    }


MAX_NAME_LENGTH = 40


def _full_limbs():
    return {
        "left_arm": 100, "right_arm": 100, "left_leg": 100,
        "right_leg": 100, "chest": 100, "head": 100,
    }


def _crew_record(name, job, credits, location, permissions, *, posted):
    """Base NPC dict shared by department heads and staff assistants."""
    job_info = JOBS[job]
    record = {
        "name": name,
        "job": job,
        "department": job_info["department"],
        "subdepartment": job_info["subdepartment"],
        "credits": credits,
        "inventory": [],
        "location": location,
        "room_visit_remaining": 0,
        "npc_goal": None,
        "npc_goal_room_key": None,
        "limbs": _full_limbs(),
        "damage": {"burn": 0, "poison": 0, "oxygen": 0},
        "warrant": False,
        "warrant_reason": "",
        "fine_amount": 0,
        "fine_reason": "",
        "in_jail": False,
        "jail_release_at_seconds": None,
        "permissions": permissions,
    }
    if posted:
        record["on_duty"] = True
    return record


def _generate_station_crew(player_name, job):
    """Build the NPC crew around the player's chosen job."""
    station_crew = []
    available_names = NPC_NAMES.copy()
    if player_name in available_names:
        available_names.remove(player_name)

    department_heads = {
        "Captain": {"credits": 10000, "station": "bridge_station"},
        "Head of Personnel": {"credits": 9000, "station": "hop_station"},
        "Security Guard": {"credits": 5000, "station": "security_station"},
        "Doctor": {"credits": 7500, "station": "medbay_station"},
        "Engineer": {"credits": 2500, "station": "engineering_station"},
        "Botanist": {"credits": 3000, "station": "botany_station"},
        "Bartender": {"credits": 3500, "station": "bar_station"},
    }

    def _pick_npc_name(fallback_label):
        if not available_names:
            return f"NPC_{fallback_label.replace(' ', '')}"
        npc_name = random.choice(available_names)
        available_names.remove(npc_name)
        return npc_name

    def _make_staff_assistant(npc_name):
        # Staff Assistants have no fixed post, so they start out
        # wandering the hallway ring rather than parked in quarters.
        return _crew_record(
            npc_name,
            "Staff Assistant",
            JOBS["Staff Assistant"]["credits"],
            pick_random_hallway_location(),
            permissions_for_job("Staff Assistant"),
            posted=False,
        )

    if job == "Head of Personnel":
        # HoP always has an NPC Captain; remaining vacant head slots + 2 are Staff Assistants
        station_crew.append(
            _crew_record(
                _pick_npc_name("Captain"),
                "Captain",
                department_heads["Captain"]["credits"],
                location_for_post("Captain"),
                permissions_for_job("Captain"),
                posted=True,
            )
        )
        vacant_roles = [j for j in department_heads if j not in (job, "Captain")]
        for i in range(len(vacant_roles) + 2):
            station_crew.append(_make_staff_assistant(_pick_npc_name(f"StaffAssistant{i + 1}")))
        return station_crew

    for npc_job, data in department_heads.items():
        if npc_job == job:
            continue
        permissions = {d["station"]: (j == npc_job) for j, d in department_heads.items()}
        if npc_job == "Captain":
            permissions = {d["station"]: True for d in department_heads.values()}
        elif npc_job == "Head of Personnel":
            permissions["bar_station"] = True
            permissions["botany_station"] = True
        station_crew.append(
            _crew_record(
                _pick_npc_name(npc_job),
                npc_job,
                data["credits"],
                location_for_post(npc_job),
                permissions,
                posted=True,
            )
        )

    for i in range(2):
        station_crew.append(_make_staff_assistant(_pick_npc_name(f"StaffAssistant{i + 1}")))
    return station_crew


def create_character(player_name, department, job):
    """Validate the creation form and return a brand-new player_data save.

    Raises ValueError with a player-facing message when the input is invalid.
    """
    # botany imports this module through the special rooms, so it can't be imported at the top.
    from space_online.game.special_rooms.botany import new_botany

    player_name = (player_name or "").strip()
    if not player_name:
        raise ValueError("Please enter a character name.")
    if len(player_name) > MAX_NAME_LENGTH:
        raise ValueError(f"Character names can be at most {MAX_NAME_LENGTH} characters.")
    if not department or department == SELECT_DEPARTMENT:
        raise ValueError("Please select a department.")
    if job not in JOBS or job not in get_jobs_for_department(department):
        raise ValueError("Please select a job.")

    job_info = JOBS[job]
    station_crew = _generate_station_crew(player_name, job)

    stock_market = default_stock_market_state()
    stock_market["companies"] = serialize_companies(create_default_companies())

    # Solar ON when an NPC Engineer is present; OFF if the player is the Engineer
    station_power = default_station_power()
    station_power["solar_charging"] = job != "Engineer" and any(
        npc.get("job") == "Engineer" for npc in station_crew
    )

    player_data = {
        "name": player_name,
        "job": job,
        "department": job_info["department"],
        "subdepartment": job_info["subdepartment"],
        "inventory": [],
        "locker_inventory": build_default_locker_inventory(),
        "hands": {"left": None, "right": None},
        "credits": job_info["credits"],
        "location": {"x": -1, "y": 0},
        "stock_holdings": {},
        "bar_mixed_stock": {},
        "station_crew": station_crew,
        "stock_market": stock_market,
        "limbs": _full_limbs(),
        "damage": {"burn": 0, "poison": 0, "oxygen": 0},
        "alcohol_percent": 0,
        "warrant": False,
        "warrant_reason": "",
        "fine_amount": 0,
        "fine_reason": "",
        "in_jail": False,
        "jail_release_at_seconds": None,
        "station_power": station_power,
        "ship_map": copy.deepcopy(donut.SHIP_MAP),
        "botany": new_botany(),
        "game_clock": default_game_clock(),
        "permissions": permissions_for_job(job),
        "notes": [],
    }
    ensure_job_event(player_data)
    return player_data
