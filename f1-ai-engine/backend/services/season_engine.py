from typing import Any, Dict, List, Optional
import random

from backend.extensions import db
from backend.models import Circuit, Team
from backend.simulation.race_coordinator import race_coordinator


class SeasonEngine:
    """
    F1 Season Engine V1.0

    Runs every circuit as an independent championship round.

    Each race gets its own:
        - circuit characteristics
        - race distance
        - weather
        - weather profile
        - qualifying
        - individual strategies
        - lap history
        - tyre changes
        - pit stops
        - overtakes
        - classification

    Championship points are accumulated across all rounds.
    """

    VERSION = "1.0"

    # Standard F1 points for the top 10.
    POINTS = {
        1: 25,
        2: 18,
        3: 15,
        4: 12,
        5: 10,
        6: 8,
        7: 6,
        8: 4,
        9: 2,
        10: 1,
    }

    FASTEST_LAP_BONUS_POSITION_LIMIT = 10
    FASTEST_LAP_BONUS = 1

    # Default distances used when the database does not yet contain
    # an explicit lap count for a circuit.
    DEFAULT_LAPS = 57

    CIRCUIT_LAPS = {
        "Australian Grand Prix": 58,
        "Japanese Grand Prix": 53,
        "Bahrain Grand Prix": 57,
        "Saudi Arabian Grand Prix": 50,
        "Miami Grand Prix": 57,
        "Emilia-Romagna Grand Prix": 63,
        "Monaco Grand Prix": 78,
        "Spanish Grand Prix": 66,
        "Canadian Grand Prix": 70,
        "Austrian Grand Prix": 71,
        "British Grand Prix": 52,
        "Belgian Grand Prix": 44,
        "Hungarian Grand Prix": 70,
        "Dutch Grand Prix": 72,
        "Italian Grand Prix": 53,
        "Azerbaijan Grand Prix": 51,
        "Singapore Grand Prix": 62,
        "United States Grand Prix": 56,
        "Mexico City Grand Prix": 71,
        "São Paulo Grand Prix": 71,
        "Las Vegas Grand Prix": 50,
        "Qatar Grand Prix": 57,
        "Abu Dhabi Grand Prix": 58,
    }

    # Default weather tendencies. These are only used when no explicit
    # weather profile is supplied. The weather engine/coordinator remains
    # responsible for converting this into a lap-by-lap profile.
    WEATHER_BY_CIRCUIT = {
        "Australian Grand Prix": "Dry",
        "Japanese Grand Prix": "Mixed",
        "Bahrain Grand Prix": "Dry",
        "Saudi Arabian Grand Prix": "Dry",
        "Miami Grand Prix": "Mixed",
        "Emilia-Romagna Grand Prix": "Dry",
        "Monaco Grand Prix": "Mixed",
        "Spanish Grand Prix": "Dry",
        "Canadian Grand Prix": "Mixed",
        "Austrian Grand Prix": "Mixed",
        "British Grand Prix": "Mixed",
        "Belgian Grand Prix": "Mixed",
        "Hungarian Grand Prix": "Dry",
        "Dutch Grand Prix": "Mixed",
        "Italian Grand Prix": "Dry",
        "Azerbaijan Grand Prix": "Dry",
        "Singapore Grand Prix": "Dry",
        "United States Grand Prix": "Dry",
        "Mexico City Grand Prix": "Dry",
        "São Paulo Grand Prix": "Mixed",
        "Las Vegas Grand Prix": "Dry",
        "Qatar Grand Prix": "Dry",
        "Abu Dhabi Grand Prix": "Dry",
    }

    def __init__(self, coordinator=None):
        self.race_coordinator = coordinator or race_coordinator

    # ============================================================
    # PUBLIC API
    # ============================================================

    def run_season(
        self,
        circuits: Optional[List[Any]] = None,
        teams: Optional[List[Any]] = None,
        season_year: int = 2026,
        weather_profiles: Optional[Dict[str, List[Dict[str, Any]]]] = None,
    ) -> Dict[str, Any]:
        """
        Run the complete season.

        weather_profiles may optionally contain a custom profile keyed by
        circuit name. When a circuit has no custom profile, the coordinator
        receives the circuit's default weather condition and generates its
        own lap-by-lap profile.
        """

        circuits = circuits or self._load_circuits()
        teams = teams or self._load_teams()

        if not circuits:
            raise ValueError("No circuits supplied to season engine.")

        if not teams:
            raise ValueError("No teams supplied to season engine.")

        weather_profiles = weather_profiles or {}

        driver_standings: Dict[Any, Dict[str, Any]] = {}
        constructor_standings: Dict[Any, Dict[str, Any]] = {}

        self._initialize_standings(
            teams,
            driver_standings,
            constructor_standings,
        )

        race_results = []

        for round_number, circuit in enumerate(circuits, start=1):
            circuit_name = self._circuit_name(circuit)
            laps = self._race_laps(circuit)

            base_weather = self._default_weather(circuit)

            custom_profile = self._find_weather_profile(
                weather_profiles,
                circuit_name,
            )

            race_result = self.race_coordinator.run_race(
                teams=teams,
                circuit=circuit,
                weather=base_weather,
                laps=laps,
                weather_profile=custom_profile,
            )

            points_result = self._apply_points(
                race_result,
                driver_standings,
                constructor_standings,
            )

            race_record = {
                "round": round_number,
                "season": season_year,
                "circuit": circuit_name,
                "country": self._circuit_country(circuit),
                "laps": laps,
                "weather": race_result.get("race", {}).get(
                    "weather",
                    base_weather,
                ),
                "weather_profile": race_result.get(
                    "weather_profile",
                    race_result.get("race", {}).get(
                        "weather_profile",
                        [],
                    ),
                ),
                "weather_transitions": race_result.get(
                    "weather_transitions",
                    race_result.get("race", {}).get(
                        "weather_transitions",
                        [],
                    ),
                ),
                "qualifying": race_result.get(
                    "qualifying",
                    {},
                ),
                "starting_grid": race_result.get(
                    "starting_grid",
                    [],
                ),
                "strategies": race_result.get(
                    "strategies",
                    [],
                ),
                "fastest_lap": race_result.get(
                    "fastest_lap",
                    {},
                ),
                "classification": race_result.get(
                    "classification",
                    [],
                ),
                "events": race_result.get(
                    "events",
                    [],
                ),
                "event_summary": race_result.get(
                    "event_summary",
                    {},
                ),
                "lap_history": race_result.get(
                    "lap_history",
                    [],
                ),
                "points": points_result,
            }

            race_results.append(race_record)

        self._sort_standings(
            driver_standings,
            constructor_standings,
        )

        return {
            "success": True,
            "engine": "F1 Season Engine",
            "version": self.VERSION,
            "season": season_year,
            "rounds": len(race_results),
            "races": race_results,
            "driver_standings": list(
                driver_standings.values()
            ),
            "constructor_standings": list(
                constructor_standings.values()
            ),
        }

    # ============================================================
    # SINGLE ROUND / CAREER MODE
    # ============================================================

    def run_single_round(
        self,
        circuits: Optional[List[Any]] = None,
        teams: Optional[List[Any]] = None,
        season_year: int = 2026,
        round_number: int = 1,
        weather_profiles: Optional[Dict[str, List[Dict[str, Any]]]] = None,
        previous_driver_standings: Optional[Dict[Any, Dict[str, Any]]] = None,
        previous_constructor_standings: Optional[Dict[Any, Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:

        circuits = circuits or self._load_circuits()
        teams = teams or self._load_teams()
        weather_profiles = weather_profiles or {}

        if not circuits:
            raise ValueError("No circuits supplied to season engine.")

        if not teams:
            raise ValueError("No teams supplied to season engine.")

        if round_number < 1 or round_number > len(circuits):
            raise ValueError(
                f"Invalid round number {round_number}. "
                f"Available rounds: 1-{len(circuits)}."
            )

        driver_standings = (
            previous_driver_standings
            if previous_driver_standings is not None
            else {}
        )

        constructor_standings = (
            previous_constructor_standings
            if previous_constructor_standings is not None
            else {}
        )

        if not driver_standings and not constructor_standings:
            self._initialize_standings(
                teams,
                driver_standings,
                constructor_standings,
            )

        circuit = circuits[round_number - 1]
        circuit_name = self._circuit_name(circuit)
        laps = self._race_laps(circuit)
        base_weather = self._default_weather(circuit)

        custom_profile = self._find_weather_profile(
            weather_profiles,
            circuit_name,
        )

        race_result = self.race_coordinator.run_race(
            teams=teams,
            circuit=circuit,
            weather=base_weather,
            laps=laps,
            weather_profile=custom_profile,
        )

        points_result = self._apply_points(
            race_result,
            driver_standings,
            constructor_standings,
        )

        race_record = {
            "round": round_number,
            "season": season_year,
            "circuit": circuit_name,
            "country": self._circuit_country(circuit),
            "laps": laps,
            "weather": race_result.get(
                "race",
                {}
            ).get(
                "weather",
                base_weather,
            ),
            "weather_profile": race_result.get(
                "weather_profile",
                race_result.get(
                    "race",
                    {}
                ).get(
                    "weather_profile",
                    [],
                ),
            ),
            "weather_transitions": race_result.get(
                "weather_transitions",
                race_result.get(
                    "race",
                    {}
                ).get(
                    "weather_transitions",
                    [],
                ),
            ),
            "qualifying": race_result.get(
                "qualifying",
                {},
            ),
            "starting_grid": race_result.get(
                "starting_grid",
                [],
            ),
            "strategies": race_result.get(
                "strategies",
                [],
            ),
            "fastest_lap": race_result.get(
                "fastest_lap",
                {},
            ),
            "classification": race_result.get(
                "classification",
                [],
            ),
            "events": race_result.get(
                "events",
                [],
            ),
            "event_summary": race_result.get(
                "event_summary",
                {},
            ),
            "lap_history": race_result.get(
                "lap_history",
                [],
            ),
            "points": points_result,
        }

        self._sort_standings(
            driver_standings,
            constructor_standings,
        )

        return {
            "success": True,
            "engine": "F1 Season Engine",
            "version": self.VERSION,
            "season": season_year,
            "round": round_number,
            "rounds": 1,
            "race": race_record,
            "races": [race_record],
            "driver_standings": list(
                driver_standings.values()
            ),
            "constructor_standings": list(
                constructor_standings.values()
            ),
        }

    # ============================================================
    # DATABASE LOADERS
    # ============================================================

    def _load_circuits(self) -> List[Any]:
        return Circuit.query.order_by(Circuit.id.asc()).all()

    def _load_teams(self) -> List[Any]:
        return Team.query.order_by(Team.id.asc()).all()

    # ============================================================
    # STANDINGS INITIALIZATION
    # ============================================================

    def _initialize_standings(
        self,
        teams: List[Any],
        driver_standings: Dict[Any, Dict[str, Any]],
        constructor_standings: Dict[Any, Dict[str, Any]],
    ) -> None:

        for team in teams:
            team_id = getattr(team, "id", None)
            team_name = getattr(
                team,
                "name",
                "Unknown Team",
            )

            if team_id not in constructor_standings:
                constructor_standings[team_id] = {
                    "position": 0,
                    "team_id": team_id,
                    "team": team_name,
                    "points": 0,
                    "wins": 0,
                    "podiums": 0,
                    "race_starts": 0,
                }

            drivers = getattr(
                team,
                "drivers",
                [],
            ) or []

            for driver in drivers:
                driver_id = getattr(
                    driver,
                    "id",
                    None,
                )

                driver_name = getattr(
                    driver,
                    "name",
                    "Unknown Driver",
                )

                driver_standings[driver_id] = {
                    "position": 0,
                    "driver_id": driver_id,
                    "driver": driver_name,
                    "team_id": team_id,
                    "team": team_name,
                    "points": 0,
                    "wins": 0,
                    "podiums": 0,
                    "poles": 0,
                    "fastest_laps": 0,
                    "race_starts": 0,
                }

    # ============================================================
    # POINTS
    # ============================================================

    def _apply_points(
        self,
        race_result: Dict[str, Any],
        driver_standings: Dict[Any, Dict[str, Any]],
        constructor_standings: Dict[Any, Dict[str, Any]],
    ) -> Dict[str, Any]:

        classification = race_result.get(
            "classification",
            [],
        )

        qualifying = race_result.get(
            "starting_grid",
            [],
        )

        race_points = []
        fastest_lap_driver_id = self._fastest_lap_driver_id(
            race_result
        )

        # Pole position is determined by qualifying position 1.
        if qualifying:
            pole_driver_id = qualifying[0].get(
                "driver_id"
            )

            if pole_driver_id in driver_standings:
                driver_standings[
                    pole_driver_id
                ]["poles"] += 1

        for result in classification:
            position = int(
                result.get(
                    "position",
                    999,
                )
            )

            driver_id = result.get(
                "driver_id"
            )

            team_id = result.get(
                "team_id"
            )

            base_points = self.POINTS.get(
                position,
                0,
            )

            fastest_bonus = 0

            if (
                driver_id == fastest_lap_driver_id
                and position <= self.FASTEST_LAP_BONUS_POSITION_LIMIT
            ):
                fastest_bonus = self.FASTEST_LAP_BONUS

            total_points = (
                base_points
                +
                fastest_bonus
            )

            driver_row = driver_standings.get(
                driver_id
            )

            if driver_row is not None:
                driver_row["points"] += total_points
                driver_row["race_starts"] += 1

                if position == 1:
                    driver_row["wins"] += 1

                if position <= 3:
                    driver_row["podiums"] += 1

                if fastest_bonus:
                    driver_row["fastest_laps"] += 1

            constructor_row = constructor_standings.get(
                team_id
            )

            if constructor_row is not None:
                constructor_row["points"] += total_points
                constructor_row["race_starts"] += 1

                if position == 1:
                    constructor_row["wins"] += 1

                if position <= 3:
                    constructor_row["podiums"] += 1

            race_points.append({
                "position": position,
                "driver_id": driver_id,
                "driver": result.get(
                    "driver"
                ),
                "team_id": team_id,
                "team": result.get(
                    "team"
                ),
                "base_points": base_points,
                "fastest_lap_bonus": fastest_bonus,
                "points": total_points,
            })

        return {
            "driver_points": race_points,
        }

    # ============================================================
    # FASTEST LAP
    # ============================================================

    def _fastest_lap_driver_id(
        self,
        race_result: Dict[str, Any],
    ) -> Any:

        fastest = race_result.get(
            "fastest_lap",
            {},
        )

        fastest_driver = fastest.get(
            "driver"
        )

        if fastest_driver is None:
            return None

        for row in race_result.get(
            "classification",
            [],
        ):
            if row.get("driver") == fastest_driver:
                return row.get("driver_id")

        return None

    # ============================================================
    # SORT STANDINGS
    # ============================================================

    def _sort_standings(
        self,
        driver_standings: Dict[Any, Dict[str, Any]],
        constructor_standings: Dict[Any, Dict[str, Any]],
    ) -> None:

        drivers = sorted(
            driver_standings.values(),
            key=lambda row: (
                -row["points"],
                -row["wins"],
                -row["podiums"],
                -row["fastest_laps"],
            ),
        )

        for position, row in enumerate(
            drivers,
            start=1,
        ):
            row["position"] = position

        constructors = sorted(
            constructor_standings.values(),
            key=lambda row: (
                -row["points"],
                -row["wins"],
                -row["podiums"],
            ),
        )

        for position, row in enumerate(
            constructors,
            start=1,
        ):
            row["position"] = position

    # ============================================================
    # CIRCUIT HELPERS
    # ============================================================

    def _circuit_name(
        self,
        circuit: Any,
    ) -> str:

        if isinstance(circuit, dict):
            return circuit.get(
                "name",
                "Unknown Circuit",
            )

        return getattr(
            circuit,
            "name",
            "Unknown Circuit",
        )

    def _circuit_country(
        self,
        circuit: Any,
    ) -> str:

        if isinstance(circuit, dict):
            return circuit.get(
                "country",
                "Unknown",
            )

        return getattr(
            circuit,
            "country",
            "Unknown",
        )

    def _race_laps(
        self,
        circuit: Any,
    ) -> int:

        name = self._circuit_name(
            circuit
        )

        return int(
            self.CIRCUIT_LAPS.get(
                name,
                self.DEFAULT_LAPS,
            )
        )

    def _default_weather(
        self,
        circuit: Any,
    ) -> str:

        name = self._circuit_name(
            circuit
        )

        return self.WEATHER_BY_CIRCUIT.get(
            name,
            "Dry",
        )

    # ============================================================
    # WEATHER PROFILE LOOKUP
    # ============================================================

    def _find_weather_profile(
        self,
        weather_profiles: Dict[str, List[Dict[str, Any]]],
        circuit_name: str,
    ) -> Optional[List[Dict[str, Any]]]:

        if circuit_name in weather_profiles:
            return weather_profiles[circuit_name]

        # Case-insensitive fallback.
        normalized = circuit_name.strip().lower()

        for name, profile in weather_profiles.items():
            if str(name).strip().lower() == normalized:
                return profile

        return None


# ================================================================
# SINGLE ENGINE INSTANCE
# ================================================================

season_engine = SeasonEngine()