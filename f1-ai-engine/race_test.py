from backend.app import app
from backend.models import Circuit, Team
from backend.simulation.race_coordinator import race_coordinator

app.app_context().push()

circuit = Circuit.query.filter_by(
    name="Canadian Grand Prix"
).first()

teams = Team.query.order_by(
    Team.id
).all()

r = race_coordinator.run_race(
    teams,
    circuit,
    weather="Dry"
)

print("=== RACE ===")
print("Success:", r["success"])
print("Circuit:", r["race"].get("circuit"))
print("Weather:", r["race"].get("weather"))
print("Laps:", r["race"].get("laps"))
print("Drivers:", len(r["classification"]))

print()
print("=== FINAL CLASSIFICATION ===")

for i, x in enumerate(r["classification"], start=1):
    print(
        f"{i} | "
        f"{x.get('driver')} | "
        f"{x.get('team')} | "
        f"Time: {x.get('total_time', x.get('race_time', x.get('time')))} | "
        f"Gap: {x.get('gap_to_leader', 0)} | "
        f"Stops: {x.get('pit_stops', 0)}"
    )

print()
print("=== FASTEST LAP ===")
print(r["fastest_lap"])

print()
print("=== EVENT SUMMARY ===")
print(r["event_summary"])

print()
print("=== PIT EVENTS ===")

for event in r["events"]:
    if event.get("type") == "pit_stop":
        print(event)

print()
print("=== OVERTAKES ===")

for event in r["events"]:
    if event.get("type") == "overtake":
        print(event)

print()
print("=== LAP SUMMARY ===")

for lap in r["lap_history"]:
    standings = lap.get("standings", [])

    if not standings:
        continue

    leader = standings[0]

    print(
        f"Lap {lap.get('lap')} | "
        f"P1: {leader.get('driver')} | "
        f"Lap: {leader.get('lap_time')} | "
        f"Gap: {leader.get('gap_to_leader')} | "
        f"Tyre: {leader.get('compound')} | "
        f"Age: {leader.get('tyre_age')}"
    )
