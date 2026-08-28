from typing import Any, Dict, List


class QualifyingEngine:
    """
    Deterministic F1 qualifying engine.

    Runs a simplified Q1 / Q2 / Q3 qualifying session and converts
    the resulting qualifying performance into the race starting grid.

    Qualifying is affected by:

        - Car performance
        - Driver performance
        - Circuit characteristics
        - Aerodynamic requirement
        - Straight-line requirement
        - Cornering requirement
        - Energy efficiency
        - Tyre management
        - Tyre compound
        - Weather
        - Track evolution
        - Driver qualifying form

    The engine uses the existing RaceGrid performance data as the
    baseline, but qualifying is NOT the same as the static baseline
    order.
    """

    # =========================================================
    # BASE VALUES
    # =========================================================

    BASE_LAP_TIME = 90.0

    # =========================================================
    # TYRE QUALIFYING EFFECT
    # =========================================================

    TYRE_BONUS = {

        "Soft":
            0.00,

        "Medium":
            0.35,

        "Hard":
            0.80,

        "Intermediate":
            2.80,

        "Full Wet":
            5.00
    }

    # =========================================================
    # WEATHER PENALTIES
    # =========================================================

    WEATHER_PENALTY = {

        "Dry": {

            "Soft":
                0.0,

            "Medium":
                0.5,

            "Hard":
                1.2,

            "Intermediate":
                8.0,

            "Full Wet":
                15.0
        },

        "Mixed": {

            "Soft":
                0.8,

            "Medium":
                1.2,

            "Hard":
                2.0,

            "Intermediate":
                0.0,

            "Full Wet":
                2.0
        },

        "Wet": {

            "Soft":
                14.0,

            "Medium":
                12.0,

            "Hard":
                10.0,

            "Intermediate":
                0.0,

            "Full Wet":
                -0.8
        }
    }

    # =========================================================
    # PUBLIC QUALIFYING METHOD
    # =========================================================

    def qualify(
        self,
        entries: List[Dict[str, Any]],
        circuit: Any,
        weather: str = "Dry"
    ) -> Dict[str, Any]:

        if not entries:

            raise ValueError(
                "No entries supplied to qualifying engine."
            )

        weather = self._normalize_weather(
            weather
        )

        circuit_data = self._extract_circuit(
            circuit
        )

        pool = [
            dict(entry)
            for entry in entries
        ]

        # =====================================================
        # Q1
        # =====================================================

        q1 = self._run_session(
            pool,
            circuit_data,
            weather,
            "Q1",
            self._tyre_for_session(
                weather,
                "Q1"
            )
        )

        q1_sorted = list(
            q1["classified"]
        )

        # Standard 22-car format:
        # Top 16 advance.
        # Bottom 6 eliminated.

        q2_pool = q1_sorted[
            :min(
                16,
                len(q1_sorted)
            )
        ]

        q1_eliminated = q1_sorted[
            min(
                16,
                len(q1_sorted)
            ):
        ]

        # =====================================================
        # Q2
        # =====================================================

        q2 = self._run_session(
            q2_pool,
            circuit_data,
            weather,
            "Q2",
            self._tyre_for_session(
                weather,
                "Q2"
            )
        )

        q2_sorted = list(
            q2["classified"]
        )

        # Standard 22-car format:
        # Top 10 advance.
        # Bottom 6 eliminated.

        q3_pool = q2_sorted[
            :min(
                10,
                len(q2_sorted)
            )
        ]

        q2_eliminated = q2_sorted[
            min(
                10,
                len(q2_sorted)
            ):
        ]

        # =====================================================
        # Q3
        # =====================================================

        q3 = self._run_session(
            q3_pool,
            circuit_data,
            weather,
            "Q3",
            self._tyre_for_session(
                weather,
                "Q3"
            )
        )

        q3_sorted = list(
            q3["classified"]
        )

        # =====================================================
        # FINAL QUALIFYING ORDER
        # =====================================================

        final_order = (
            q3_sorted
            +
            q2_eliminated
            +
            q1_eliminated
        )

        starting_grid = []

        for position, entry in enumerate(
            final_order,
            start=1
        ):

            row = dict(entry)

            row["position"] = (
                position
            )

            row["grid_position"] = (
                position
            )

            row["qualifying_position"] = (
                position
            )

            starting_grid.append(
                row
            )

        # Explicit final ordering.

        starting_grid.sort(
            key=lambda item: (
                item.get(
                    "position",
                    999
                )
            )
        )

        # Re-apply sequential positions.

        for position, row in enumerate(
            starting_grid,
            start=1
        ):

            row["position"] = (
                position
            )

            row["grid_position"] = (
                position
            )

            row["qualifying_position"] = (
                position
            )

        return {

            "success":
                True,

            "engine":
                "F1 Qualifying Engine",

            "version":
                "2.0",

            "weather":
                weather,

            "circuit":
                circuit_data,

            "sessions": {

                "Q1":
                    q1,

                "Q2":
                    q2,

                "Q3":
                    q3
            },

            "starting_grid":
                starting_grid
        }

    # =========================================================
    # QUALIFYING SESSION
    # =========================================================

    def _run_session(
        self,
        entries: List[Dict[str, Any]],
        circuit: Dict[str, Any],
        weather: str,
        session: str,
        compound: str
    ) -> Dict[str, Any]:

        results = []

        for entry in entries:

            lap_time = (
                self._qualifying_lap_time(
                    entry,
                    circuit,
                    weather,
                    session,
                    compound
                )
            )

            row = dict(entry)

            row["qualifying_session"] = (
                session
            )

            row["qualifying_tyre"] = (
                compound
            )

            row["qualifying_lap_time"] = (
                round(
                    lap_time,
                    3
                )
            )

            results.append(
                row
            )

        # Fastest lap first.

        results.sort(
            key=lambda item: (
                item[
                    "qualifying_lap_time"
                ],

                item.get(
                    "driver_id",
                    999
                )
            )
        )

        for position, row in enumerate(
            results,
            start=1
        ):

            row["session_position"] = (
                position
            )

        return {

            "session":
                session,

            "compound":
                compound,

            "drivers":
                len(results),

            "classified":
                results
        }

    # =========================================================
    # QUALIFYING LAP TIME
    # =========================================================

    def _qualifying_lap_time(
        self,
        entry: Dict[str, Any],
        circuit: Dict[str, Any],
        weather: str,
        session: str,
        compound: str
    ) -> float:

        car = (
            entry.get(
                "car_performance"
            )
            or {}
        )

        driver = (
            entry.get(
                "driver_performance"
            )
            or {}
        )

        # -----------------------------------------------------
        # Car performance values
        # -----------------------------------------------------

        aero = self._performance_value(
            car.get(
                "aero"
            ),
            75.0
        )

        straight_line = (
            self._performance_value(
                car.get(
                    "straight_line_speed"
                ),
                75.0
            )
        )

        cornering = (
            self._performance_value(
                car.get(
                    "cornering"
                ),
                75.0
            )
        )

        energy = (
            self._performance_value(
                car.get(
                    "energy_efficiency"
                ),
                75.0
            )
        )

        tyre_management = (
            self._performance_value(
                car.get(
                    "tyre_management"
                ),
                75.0
            )
        )

        # -----------------------------------------------------
        # Driver performance
        # -----------------------------------------------------

        race_pace = (
            self._performance_value(
                driver.get(
                    "race_pace"
                ),
                80.0
            )
        )

        consistency = (
            self._performance_value(
                driver.get(
                    "consistency"
                ),
                80.0
            )
        )

        # Driver qualifying proxy.

        driver_score = (
            race_pace * 0.65
            +
            consistency * 0.35
        )

        # -----------------------------------------------------
        # Circuit characteristics
        # -----------------------------------------------------

        circuit_weights = (
            self._circuit_weights(
                circuit
            )
        )

        # -----------------------------------------------------
        # Circuit-specific car score
        # -----------------------------------------------------

        car_score = (

            aero
            *
            circuit_weights[
                "aero"
            ]

            +

            straight_line
            *
            circuit_weights[
                "straight_line"
            ]

            +

            cornering
            *
            circuit_weights[
                "cornering"
            ]

            +

            energy
            *
            circuit_weights[
                "energy"
            ]

            +

            tyre_management
            *
            circuit_weights[
                "tyre_management"
            ]
        )

        # -----------------------------------------------------
        # Driver influence
        # -----------------------------------------------------

        performance = (

            car_score * 0.72

            +

            driver_score * 0.28
        )

        # -----------------------------------------------------
        # Convert performance to lap-time delta.
        #
        # 75 -> slower
        # 90 -> competitive
        # 100 -> very fast
        # -----------------------------------------------------

        performance_delta = (
            90.0
            -
            performance
        ) * 0.17

        # -----------------------------------------------------
        # Circuit base factor
        # -----------------------------------------------------

        track_type = str(
            circuit.get(
                "track_type",
                "Mixed"
            )
        )

        if track_type in {

            "Power",

            "High Speed",

            "Street High Speed"

        }:

            circuit_factor = 0.20

        elif track_type in {

            "Technical",

            "Street Technical",

            "Street"

        }:

            circuit_factor = 0.12

        else:

            circuit_factor = 0.16

        # -----------------------------------------------------
        # Downforce requirement
        # -----------------------------------------------------

        downforce = str(
            circuit.get(
                "downforce_level",
                "Medium"
            )
        )

        downforce_bonus = (
            self._downforce_effect(
                aero,
                downforce
            )
        )

        # -----------------------------------------------------
        # Tyre stress
        # -----------------------------------------------------

        tyre_stress = str(
            circuit.get(
                "tyre_stress",
                "Medium"
            )
        )

        tyre_effect = (
            self._tyre_management_effect(
                tyre_management,
                tyre_stress
            )
        )

        # -----------------------------------------------------
        # Track evolution
        # -----------------------------------------------------

        session_evolution = {

            "Q1":
                0.55,

            "Q2":
                0.28,

            "Q3":
                0.00

        }.get(
            session,
            0.25
        )

        # -----------------------------------------------------
        # Tyre
        # -----------------------------------------------------

        weather_penalty = (
            self.WEATHER_PENALTY[
                weather
            ][
                compound
            ]
        )

        tyre_bonus = (
            self.TYRE_BONUS[
                compound
            ]
        )

        # -----------------------------------------------------
        # Deterministic driver form
        # -----------------------------------------------------

        driver_id = int(
            entry.get(
                "driver_id",
                0
            )
            or 0
        )

        form_seed = (
            driver_id * 37
        ) % 101

        form = (
            form_seed / 100.0
        )

        form_variation = (
            form - 0.5
        ) * 0.42

        # -----------------------------------------------------
        # Weather skill
        # -----------------------------------------------------

        wet_skill = (
            self._weather_skill(
                entry,
                weather
            )
        )

        if weather == "Wet":

            wet_adjustment = (
                -0.30
                *
                wet_skill
            )

        elif weather == "Mixed":

            wet_adjustment = (
                -0.16
                *
                wet_skill
            )

        else:

            wet_adjustment = 0.0

        # -----------------------------------------------------
        # Final lap time
        # -----------------------------------------------------

        return (

            self.BASE_LAP_TIME

            +

            performance_delta

            +

            circuit_factor

            +

            downforce_bonus

            +

            tyre_effect

            +

            session_evolution

            +

            tyre_bonus

            +

            weather_penalty

            +

            form_variation

            +

            wet_adjustment
        )

    # =========================================================
    # CIRCUIT PERFORMANCE WEIGHTS
    # =========================================================

    def _circuit_weights(
        self,
        circuit: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Determines which car characteristics matter most
        during qualifying.

        The weights always add up to 1.0.
        """

        track_type = str(
            circuit.get(
                "track_type",
                "Mixed"
            )
        )

        downforce = str(
            circuit.get(
                "downforce_level",
                "Medium"
            )
        )

        tyre_stress = str(
            circuit.get(
                "tyre_stress",
                "Medium"
            )
        )

        # -----------------------------------------------------
        # Base circuit profile
        # -----------------------------------------------------

        if track_type == "Power":

            weights = {

                "aero":
                    0.12,

                "straight_line":
                    0.40,

                "cornering":
                    0.20,

                "energy":
                    0.20,

                "tyre_management":
                    0.08
            }

        elif track_type in {

            "High Speed",

            "Street High Speed"

        }:

            weights = {

                "aero":
                    0.18,

                "straight_line":
                    0.34,

                "cornering":
                    0.22,

                "energy":
                    0.18,

                "tyre_management":
                    0.08
            }

        elif track_type in {

            "Technical",

            "Street Technical"

        }:

            weights = {

                "aero":
                    0.32,

                "straight_line":
                    0.10,

                "cornering":
                    0.36,

                "energy":
                    0.08,

                "tyre_management":
                    0.14
            }

        elif track_type == "Street":

            weights = {

                "aero":
                    0.34,

                "straight_line":
                    0.10,

                "cornering":
                    0.38,

                "energy":
                    0.05,

                "tyre_management":
                    0.13
            }

        else:

            weights = {

                "aero":
                    0.22,

                "straight_line":
                    0.22,

                "cornering":
                    0.28,

                "energy":
                    0.14,

                "tyre_management":
                    0.14
            }

        # -----------------------------------------------------
        # Downforce adjustment
        # -----------------------------------------------------

        if downforce == "Very High":

            weights["aero"] += 0.08
            weights["cornering"] += 0.04

            weights["straight_line"] -= 0.06
            weights["energy"] -= 0.03
            weights["tyre_management"] -= 0.03

        elif downforce == "High":

            weights["aero"] += 0.05
            weights["cornering"] += 0.02

            weights["straight_line"] -= 0.03
            weights["energy"] -= 0.02
            weights["tyre_management"] -= 0.02

        elif downforce == "Low":

            weights["straight_line"] += 0.05
            weights["energy"] += 0.02

            weights["aero"] -= 0.04
            weights["cornering"] -= 0.02
            weights["tyre_management"] -= 0.01

        # -----------------------------------------------------
        # Tyre stress adjustment
        # -----------------------------------------------------

        if tyre_stress == "Very High":

            weights["tyre_management"] += 0.06

            weights["energy"] -= 0.02
            weights["straight_line"] -= 0.01
            weights["aero"] -= 0.01
            weights["cornering"] -= 0.02

        elif tyre_stress == "High":

            weights["tyre_management"] += 0.04

            weights["energy"] -= 0.015
            weights["aero"] -= 0.01
            weights["cornering"] -= 0.01
            weights["straight_line"] -= 0.005

        # -----------------------------------------------------
        # Normalize
        # -----------------------------------------------------

        total = sum(
            weights.values()
        )

        if total <= 0:

            return {

                "aero":
                    0.20,

                "straight_line":
                    0.20,

                "cornering":
                    0.25,

                "energy":
                    0.15,

                "tyre_management":
                    0.20
            }

        return {

            key:
                value / total

            for key, value
            in weights.items()
        }

    # =========================================================
    # DOWNFORCE EFFECT
    # =========================================================

    def _downforce_effect(
        self,
        aero: float,
        requirement: str
    ) -> float:
        """
        Penalizes or rewards aerodynamic performance depending
        on circuit downforce requirement.
        """

        if requirement == "Very High":

            target = 95.0

        elif requirement == "High":

            target = 90.0

        elif requirement == "Medium":

            target = 80.0

        elif requirement == "Low":

            target = 72.0

        else:

            target = 80.0

        difference = (
            aero - target
        )

        return (
            -difference
            *
            0.012
        )

    # =========================================================
    # TYRE MANAGEMENT EFFECT
    # =========================================================

    def _tyre_management_effect(
        self,
        tyre_management: float,
        stress: str
    ) -> float:
        """
        Small qualifying influence from tyre preparation and
        thermal control.

        It is deliberately smaller than the main car-performance
        weighting because qualifying is primarily about peak pace.
        """

        if stress == "Very High":

            target = 92.0

        elif stress == "High":

            target = 87.0

        elif stress == "Medium":

            target = 80.0

        else:

            target = 72.0

        difference = (
            tyre_management - target
        )

        return (
            -difference
            *
            0.008
        )

    # =========================================================
    # PERFORMANCE VALUE
    # =========================================================

    def _performance_value(
        self,
        value: Any,
        default: float
    ) -> float:

        if not isinstance(
            value,
            (int, float)
        ):

            return default

        return float(
            value
        )

    # =========================================================
    # WEATHER SKILL
    # =========================================================

    def _weather_skill(
        self,
        entry: Dict[str, Any],
        weather: str
    ) -> float:

        if weather == "Dry":

            return 0.0

        performance = (
            entry.get(
                "driver_performance"
            )
        )

        if isinstance(
            performance,
            dict
        ):

            for key in (

                "wet_skill",

                "wet_weather",

                "rain",

                "weather_skill"
            ):

                value = (
                    performance.get(
                        key
                    )
                )

                if isinstance(
                    value,
                    (int, float)
                ):

                    return self._clamp(
                        float(value),
                        0.0,
                        1.0
                    )

        # Existing dataset has no dedicated wet-skill field.
        # Use baseline driver performance as a conservative proxy.

        race_pace = (
            self._performance_value(
                performance.get(
                    "race_pace"
                )
                if isinstance(
                    performance,
                    dict
                )
                else None,
                80.0
            )
        )

        return self._clamp(
            (
                race_pace
                -
                70.0
            )
            /
            30.0,
            0.0,
            0.30
        )

    # =========================================================
    # QUALIFYING TYRE SELECTION
    # =========================================================

    def _tyre_for_session(
        self,
        weather: str,
        session: str
    ) -> str:

        # -----------------------------------------------------
        # FULL WET
        # -----------------------------------------------------

        if weather == "Wet":

            if session == "Q3":

                return "Full Wet"

            return "Intermediate"

        # -----------------------------------------------------
        # MIXED
        # -----------------------------------------------------

        if weather == "Mixed":

            if session == "Q1":

                return "Intermediate"

            return "Soft"

        # -----------------------------------------------------
        # DRY
        # -----------------------------------------------------

        return "Soft"

    # =========================================================
    # CIRCUIT EXTRACTION
    # =========================================================

    def _extract_circuit(
        self,
        circuit: Any
    ) -> Dict[str, Any]:

        if isinstance(
            circuit,
            dict
        ):

            return {

                "name":
                    circuit.get(
                        "name",
                        "Unknown Circuit"
                    ),

                "country":
                    circuit.get(
                        "country",
                        "Unknown"
                    ),

                "track_type":
                    circuit.get(
                        "track_type",
                        "Mixed"
                    ),

                "downforce_level":
                    circuit.get(
                        "downforce_level",
                        "Medium"
                    ),

                "tyre_stress":
                    circuit.get(
                        "tyre_stress",
                        "Medium"
                    ),

                "overtaking_difficulty":
                    circuit.get(
                        "overtaking_difficulty",
                        "Medium"
                    )
            }

        return {

            "name":
                getattr(
                    circuit,
                    "name",
                    "Unknown Circuit"
                ),

            "country":
                getattr(
                    circuit,
                    "country",
                    "Unknown"
                ),

            "track_type":
                getattr(
                    circuit,
                    "track_type",
                    "Mixed"
                ),

            "downforce_level":
                getattr(
                    circuit,
                    "downforce_level",
                    "Medium"
                ),

            "tyre_stress":
                getattr(
                    circuit,
                    "tyre_stress",
                    "Medium"
                ),

            "overtaking_difficulty":
                getattr(
                    circuit,
                    "overtaking_difficulty",
                    "Medium"
                )
        }

    # =========================================================
    # WEATHER NORMALIZATION
    # =========================================================

    def _normalize_weather(
        self,
        weather: Any
    ) -> str:

        value = str(
            weather or "Dry"
        ).strip().title()

        if value in {

            "Dry",

            "Wet",

            "Mixed"
        }:

            return value

        return "Dry"

    # =========================================================
    # CLAMP
    # =========================================================

    def _clamp(
        self,
        value: float,
        minimum: float,
        maximum: float
    ) -> float:

        return max(
            minimum,
            min(
                value,
                maximum
            )
        )


# =============================================================
# SINGLE ENGINE INSTANCE
# =============================================================

qualifying_engine = QualifyingEngine()