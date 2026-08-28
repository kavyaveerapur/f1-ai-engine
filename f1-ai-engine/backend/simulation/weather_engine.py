from typing import Any, Dict, List, Optional


class WeatherEngine:
    """
    Deterministic race-weather engine.

    Supports:
        Dry
        Mixed
        Wet

    A race can contain multiple weather phases.
    """

    VALID_WEATHER = {"Dry", "Mixed", "Wet"}

    DEFAULT_PROFILE = [
        {
            "start_lap": 1,
            "end_lap": None,
            "weather": "Dry"
        }
    ]

    PRESET_PROFILES = {
        "dry": [
            {"start_lap": 1, "end_lap": None, "weather": "Dry"}
        ],
        "wet": [
            {"start_lap": 1, "end_lap": None, "weather": "Wet"}
        ],
        "mixed": [
            {"start_lap": 1, "end_lap": None, "weather": "Mixed"}
        ],
        "dry_to_wet": [
            {"start_lap": 1, "end_lap": None, "weather": "Dry"},
            {"start_lap": 20, "end_lap": None, "weather": "Mixed"},
            {"start_lap": 27, "end_lap": None, "weather": "Wet"}
        ],
        "wet_to_dry": [
            {"start_lap": 1, "end_lap": None, "weather": "Wet"},
            {"start_lap": 20, "end_lap": None, "weather": "Mixed"},
            {"start_lap": 30, "end_lap": None, "weather": "Dry"}
        ],
        "dry_rain_dry": [
            {"start_lap": 1, "end_lap": None, "weather": "Dry"},
            {"start_lap": 18, "end_lap": None, "weather": "Mixed"},
            {"start_lap": 24, "end_lap": None, "weather": "Wet"},
            {"start_lap": 34, "end_lap": None, "weather": "Mixed"},
            {"start_lap": 42, "end_lap": None, "weather": "Dry"}
        ]
    }

    CIRCUIT_DEFAULT_PROFILES = {
        "Canadian Grand Prix": "dry_rain_dry",
        "British Grand Prix": "mixed",
        "Belgian Grand Prix": "mixed",
        "Japanese Grand Prix": "mixed",
        "Dutch Grand Prix": "mixed",
        "Brazilian Grand Prix": "mixed"
    }

    def normalize_weather(self, weather: Any) -> str:
        value = str(weather or "Dry").strip().title()
        return value if value in self.VALID_WEATHER else "Dry"

    def normalize_profile(
        self,
        profile: Optional[List[Dict[str, Any]]],
        laps: int
    ) -> List[Dict[str, Any]]:
        if not profile:
            profile = self.DEFAULT_PROFILE

        normalized = []

        for phase in profile:
            start_lap = max(1, int(phase.get("start_lap", 1)))
            end_lap = phase.get("end_lap")
            end_lap = laps if end_lap is None else min(laps, int(end_lap))

            if start_lap > laps or end_lap < start_lap:
                continue

            normalized.append({
                "start_lap": start_lap,
                "end_lap": end_lap,
                "weather": self.normalize_weather(
                    phase.get("weather", "Dry")
                )
            })

        normalized.sort(key=lambda item: item["start_lap"])

        return normalized or [
            {
                "start_lap": 1,
                "end_lap": laps,
                "weather": "Dry"
            }
        ]

    def get_profile(
        self,
        circuit: Any,
        laps: int,
        weather: Optional[str] = None,
        weather_profile: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        if weather_profile:
            return self.normalize_profile(weather_profile, laps)

        if weather:
            return self.normalize_profile([
                {
                    "start_lap": 1,
                    "end_lap": laps,
                    "weather": self.normalize_weather(weather)
                }
            ], laps)

        circuit_name = self._circuit_name(circuit)
        preset_name = self.CIRCUIT_DEFAULT_PROFILES.get(circuit_name)

        if preset_name:
            preset = self.PRESET_PROFILES.get(preset_name)
            if preset:
                return self.normalize_profile(preset, laps)

        return self.normalize_profile(self.DEFAULT_PROFILE, laps)

    def weather_at_lap(
        self,
        profile: List[Dict[str, Any]],
        lap: int
    ) -> str:
        selected = "Dry"
        for phase in profile:
            if phase["start_lap"] <= lap <= phase["end_lap"]:
                selected = phase["weather"]
        return selected

    def transitions(
        self,
        profile: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        transitions = []
        previous = None

        for phase in profile:
            current = phase["weather"]
            if previous is not None and current != previous:
                transitions.append({
                    "lap": phase["start_lap"],
                    "from": previous,
                    "to": current
                })
            previous = current

        return transitions

    def summary(
        self,
        profile: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        return {
            "phases": profile,
            "transitions": self.transitions(profile)
        }

    def _circuit_name(self, circuit: Any) -> str:
        if isinstance(circuit, dict):
            return str(circuit.get("name", ""))
        return str(getattr(circuit, "name", ""))


weather_engine = WeatherEngine()