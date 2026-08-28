from typing import Any, Dict, List, Optional


class RaceSimulator:
    """
    Deterministic F1 race simulator.

    Version 2.0 adds circuit-sensitive race performance.

    The simulator respects the strategy engine's:

        - Compound order
        - Stop count
        - Strategy name
        - Risk

    Race performance is affected by:

        - Circuit characteristics
        - Aero
        - Straight-line speed
        - Cornering
        - Energy efficiency
        - Tyre management
        - Reliability
        - Driver race pace
        - Driver tyre management
        - Tyre compound
        - Tyre degradation
        - Weather

    Upgrades made through CarPerformance therefore affect both
    qualifying and race pace.
    """

    # =====================================================
    # SIMULATION CONSTANTS
    # =====================================================

    DEFAULT_LAPS = 57

    BASE_LAP_TIME = 90.0

    PIT_STOP_TIME = 22.0

    # =====================================================
    # BASE TYRE PACE
    # =====================================================

    TYRE_BASE_PACE = {

        "Soft": 0.00,

        "Medium": 0.45,

        "Hard": 1.05,

        "Intermediate": 2.50,

        "Full Wet": 4.00
    }

    # =====================================================
    # NOMINAL TYRE LIFE
    # =====================================================

    TYRE_LIFE = {

        "Soft": 18,

        "Medium": 28,

        "Hard": 38,

        "Intermediate": 24,

        "Full Wet": 20
    }

    # =====================================================
    # TYRE DEGRADATION
    # =====================================================

    TYRE_DEGRADATION = {

        "Soft": 0.085,

        "Medium": 0.050,

        "Hard": 0.032,

        "Intermediate": 0.040,

        "Full Wet": 0.035
    }

    # =====================================================
    # WEATHER PENALTIES
    # =====================================================

    WEATHER_PENALTY = {

        "Dry": {

            "Soft": 0.0,

            "Medium": 0.0,

            "Hard": 0.0,

            "Intermediate": 8.0,

            "Full Wet": 15.0
        },

        "Mixed": {

            "Soft": 2.0,

            "Medium": 1.0,

            "Hard": 2.0,

            "Intermediate": 0.0,

            "Full Wet": 1.0
        },

        "Wet": {

            "Soft": 14.0,

            "Medium": 12.0,

            "Hard": 10.0,

            "Intermediate": 0.0,

            "Full Wet": -1.0
        }
    }

    # =====================================================
    # CIRCUIT TRACK EFFECT
    # =====================================================

    CIRCUIT_TRACK_EFFECT = {

        "High Speed": {

            "straight_line": 1.20,

            "cornering": 0.90
        },

        "Street High Speed": {

            "straight_line": 1.15,

            "cornering": 0.95
        },

        "Power": {

            "straight_line": 1.30,

            "cornering": 0.85
        },

        "Technical": {

            "straight_line": 0.85,

            "cornering": 1.25
        },

        "Street": {

            "straight_line": 0.80,

            "cornering": 1.30
        },

        "Street Technical": {

            "straight_line": 0.80,

            "cornering": 1.35
        },

        "Mixed": {

            "straight_line": 1.00,

            "cornering": 1.00
        }
    }

    # =====================================================
    # CIRCUIT PERFORMANCE WEIGHTS
    # =====================================================

    CIRCUIT_PERFORMANCE_WEIGHTS = {

        "Power": {

            "aero": 0.12,

            "straight_line": 0.34,

            "cornering": 0.18,

            "energy": 0.22,

            "tyre_management": 0.14
        },

        "High Speed": {

            "aero": 0.16,

            "straight_line": 0.30,

            "cornering": 0.20,

            "energy": 0.20,

            "tyre_management": 0.14
        },

        "Street High Speed": {

            "aero": 0.20,

            "straight_line": 0.27,

            "cornering": 0.23,

            "energy": 0.16,

            "tyre_management": 0.14
        },

        "Technical": {

            "aero": 0.28,

            "straight_line": 0.10,

            "cornering": 0.34,

            "energy": 0.10,

            "tyre_management": 0.18
        },

        "Street": {

            "aero": 0.30,

            "straight_line": 0.08,

            "cornering": 0.37,

            "energy": 0.08,

            "tyre_management": 0.17
        },

        "Street Technical": {

            "aero": 0.31,

            "straight_line": 0.07,

            "cornering": 0.38,

            "energy": 0.07,

            "tyre_management": 0.17
        },

        "Mixed": {

            "aero": 0.22,

            "straight_line": 0.20,

            "cornering": 0.27,

            "energy": 0.15,

            "tyre_management": 0.16
        }
    }

    # =====================================================
    # CIRCUIT TYRE-STRESS MULTIPLIERS
    # =====================================================

    TYRE_STRESS_MULTIPLIER = {

        "Very Low": 0.80,

        "Low": 0.90,

        "Medium": 1.00,

        "High": 1.12,

        "Very High": 1.25
    }

    # =====================================================
    # WEATHER STINT MULTIPLIERS
    # =====================================================

    WEATHER_STINT_MULTIPLIER = {

        "Dry": {

            "Soft": 1.00,

            "Medium": 1.00,

            "Hard": 1.00,

            "Intermediate": 0.70,

            "Full Wet": 0.60
        },

        "Mixed": {

            "Soft": 0.82,

            "Medium": 0.90,

            "Hard": 0.88,

            "Intermediate": 1.00,

            "Full Wet": 0.90
        },

        "Wet": {

            "Soft": 0.45,

            "Medium": 0.55,

            "Hard": 0.60,

            "Intermediate": 1.00,

            "Full Wet": 1.00
        }
    }

    # =====================================================
    # CONSTRUCTOR
    # =====================================================

    def __init__(self):

        pass

    # =====================================================
    # PUBLIC API
    # =====================================================

    def simulate(
        self,
        circuit: Any,
        team: Any,
        driver: Any,
        strategy: Dict[str, Any],
        weather: str = "Dry",
        laps: Optional[int] = None
    ) -> Dict[str, Any]:

        race_laps = (

            laps

            if laps is not None

            else self.DEFAULT_LAPS
        )

        weather = (
            self._normalize_weather(
                weather
            )
        )

        circuit_data = (
            self._extract_circuit(
                circuit
            )
        )

        car_performance = (
            self._extract_car_performance(
                team
            )
        )

        driver_performance = (
            self._extract_driver_performance(
                driver
            )
        )

        strategy_data = (
            self._normalize_strategy(
                strategy
            )
        )

        stints = (
            self._build_stints(
                race_laps,
                strategy_data,
                circuit_data,
                weather
            )
        )

        lap_results = []

        current_lap = 1

        total_race_time = 0.0

        pit_stops = 0

        fastest_lap = None

        fastest_lap_time = None

        for stint_index, stint in enumerate(
            stints
        ):

            compound = stint[
                "compound"
            ]

            stint_length = stint[
                "laps"
            ]

            tyre_age = 0

            for _ in range(
                stint_length
            ):

                if current_lap > race_laps:

                    break

                tyre_age += 1

                lap_time = (
                    self._calculate_lap_time(

                        circuit_data,

                        car_performance,

                        driver_performance,

                        compound,

                        tyre_age,

                        weather
                    )
                )

                total_race_time += (
                    lap_time
                )

                lap_results.append({

                    "lap":
                        current_lap,

                    "lap_time":
                        round(
                            lap_time,
                            3
                        ),

                    "compound":
                        compound,

                    "tyre_age":
                        tyre_age,

                    "stint":
                        stint_index + 1
                })

                if (

                    fastest_lap_time
                    is None

                    or

                    lap_time
                    <
                    fastest_lap_time
                ):

                    fastest_lap_time = (
                        lap_time
                    )

                    fastest_lap = (
                        current_lap
                    )

                current_lap += 1

            # -------------------------------------------------
            # Pit stop after every stint except final stint.
            # -------------------------------------------------

            if (

                stint_index
                <
                len(stints) - 1

                and

                current_lap
                <=
                race_laps
            ):

                total_race_time += (
                    self.PIT_STOP_TIME
                )

                pit_stops += 1

        result = {

            "success":
                True,

            "simulator":
                "F1 Race Simulator",

            "version":
                "2.0",

            "race": {

                "laps":
                    race_laps,

                "weather":
                    weather,

                "circuit":
                    circuit_data,

                "team":
                    self._get_name(
                        team
                    ),

                "driver":
                    self._get_name(
                        driver
                    )
            },

            "strategy": {

                "name":
                    strategy_data[
                        "name"
                    ],

                "stops":
                    strategy_data[
                        "stops"
                    ],

                "compounds":
                    strategy_data[
                        "compounds"
                    ],

                "risk":
                    strategy_data[
                        "risk"
                    ]
            },

            "result": {

                "total_time_seconds":
                    round(
                        total_race_time,
                        3
                    ),

                "pit_stops":
                    pit_stops,

                "fastest_lap":
                    fastest_lap,

                "fastest_lap_time_seconds":

                    (
                        round(
                            fastest_lap_time,
                            3
                        )

                        if fastest_lap_time
                        is not None

                        else None
                    )
            },

            "stints":
                stints,

            "laps":
                lap_results
        }

        return result

    # =====================================================
    # CIRCUIT
    # =====================================================

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

    # =====================================================
    # CAR PERFORMANCE
    # =====================================================

    def _extract_car_performance(
        self,
        team: Any
    ) -> Dict[str, float]:

        performance = getattr(
            team,
            "car_performance",
            None
        )

        if performance is None:

            return {

                "aero":
                    75.0,

                "straight_line_speed":
                    75.0,

                "cornering":
                    75.0,

                "energy_efficiency":
                    75.0,

                "tyre_management":
                    75.0,

                "reliability":
                    75.0
            }

        return {

            "aero":
                float(
                    performance.aero
                ),

            "straight_line_speed":
                float(
                    performance.straight_line_speed
                ),

            "cornering":
                float(
                    performance.cornering
                ),

            "energy_efficiency":
                float(
                    performance.energy_efficiency
                ),

            "tyre_management":
                float(
                    performance.tyre_management
                ),

            "reliability":
                float(
                    performance.reliability
                )
        }

    # =====================================================
    # DRIVER PERFORMANCE
    # =====================================================

    def _extract_driver_performance(
        self,
        driver: Any
    ) -> Dict[str, float]:

        performance = getattr(
            driver,
            "performance",
            None
        )

        if performance is None:

            return {

                "race_pace":
                    75.0,

                "tyre_management":
                    75.0,

                "overtaking":
                    75.0,

                "consistency":
                    75.0
            }

        return {

            "race_pace":
                float(
                    performance.race_pace
                ),

            "tyre_management":
                float(
                    performance.tyre_management
                ),

            "overtaking":
                float(
                    performance.overtaking
                ),

            "consistency":
                float(
                    performance.consistency
                )
        }

    # =====================================================
    # STRATEGY NORMALIZATION
    # =====================================================

    def _normalize_strategy(
        self,
        strategy: Dict[str, Any]
    ) -> Dict[str, Any]:

        compounds = strategy.get(
            "compounds",
            []
        )

        normalized_compounds = []

        for compound in compounds:

            value = str(
                compound
            ).strip()

            mapping = {

                "soft":
                    "Soft",

                "medium":
                    "Medium",

                "hard":
                    "Hard",

                "intermediate":
                    "Intermediate",

                "wet":
                    "Full Wet",

                "full wet":
                    "Full Wet"
            }

            normalized_compounds.append(
                mapping.get(
                    value.lower(),
                    value
                )
            )

        return {

            "name":
                strategy.get(
                    "name",
                    "Unknown Strategy"
                ),

            "stops":
                int(
                    strategy.get(
                        "stops",
                        max(
                            len(
                                normalized_compounds
                            ) - 1,
                            0
                        )
                    )
                ),

            "compounds":
                normalized_compounds,

            "risk":
                strategy.get(
                    "risk",
                    "Medium"
                )
        }

    # =====================================================
    # REALISTIC STINT BUILDING
    # =====================================================

    def _build_stints(
        self,
        race_laps: int,
        strategy: Dict[str, Any],
        circuit: Dict[str, Any],
        weather: str
    ) -> List[Dict[str, Any]]:

        compounds = strategy[
            "compounds"
        ]

        if not compounds:

            raise ValueError(
                "Strategy contains no tyre compounds."
            )

        stint_count = len(
            compounds
        )

        if race_laps < stint_count:

            raise ValueError(
                "Race distance is shorter than "
                "the number of strategy stints."
            )

        stress_multiplier = (
            self.TYRE_STRESS_MULTIPLIER.get(
                circuit[
                    "tyre_stress"
                ],
                1.00
            )
        )

        weather_multipliers = (
            self.WEATHER_STINT_MULTIPLIER.get(
                weather,
                self.WEATHER_STINT_MULTIPLIER[
                    "Dry"
                ]
            )
        )

        effective_life = []

        for compound in compounds:

            base_life = (
                self.TYRE_LIFE.get(
                    compound,
                    25
                )
            )

            weather_multiplier = (
                weather_multipliers.get(
                    compound,
                    1.00
                )
            )

            life = (

                base_life

                /

                stress_multiplier

                *

                weather_multiplier
            )

            effective_life.append(
                max(
                    2,
                    int(
                        round(
                            life
                        )
                    )
                )
            )

        total_life = sum(
            effective_life
        )

        raw_lengths = [

            (
                race_laps
                *
                life
                /
                total_life
            )

            for life in effective_life
        ]

        stint_lengths = [

            max(
                1,
                int(
                    round(
                        value
                    )
                )
            )

            for value in raw_lengths
        ]

        difference = (
            race_laps
            -
            sum(
                stint_lengths
            )
        )

        while difference != 0:

            if difference > 0:

                candidate_index = max(

                    range(
                        stint_count
                    ),

                    key=lambda index:

                        effective_life[
                            index
                        ]
                        -
                        stint_lengths[
                            index
                        ]
                )

                stint_lengths[
                    candidate_index
                ] += 1

                difference -= 1

            else:

                candidates = [

                    index

                    for index in range(
                        stint_count
                    )

                    if stint_lengths[
                        index
                    ] > 1
                ]

                if not candidates:

                    break

                candidate_index = max(

                    candidates,

                    key=lambda index:

                        stint_lengths[
                            index
                        ]
                )

                stint_lengths[
                    candidate_index
                ] -= 1

                difference += 1

        stints = []

        start_lap = 1

        for index, compound in enumerate(
            compounds
        ):

            stint_laps = (
                stint_lengths[
                    index
                ]
            )

            end_lap = (

                start_lap
                +
                stint_laps
                -
                1
            )

            stints.append({

                "stint":
                    index + 1,

                "compound":
                    compound,

                "laps":
                    stint_laps,

                "start_lap":
                    start_lap,

                "end_lap":
                    end_lap,

                "effective_tyre_life":
                    effective_life[
                        index
                    ]
            })

            start_lap = (
                end_lap + 1
            )

        return stints

    # =====================================================
    # LAP TIME
    # =====================================================

    def _calculate_lap_time(
        self,
        circuit: Dict[str, Any],
        car: Dict[str, float],
        driver: Dict[str, float],
        compound: str,
        tyre_age: int,
        weather: str
    ) -> float:

        track_type = circuit[
            "track_type"
        ]

        track_effect = (
            self.CIRCUIT_TRACK_EFFECT.get(
                track_type,
                self.CIRCUIT_TRACK_EFFECT[
                    "Mixed"
                ]
            )
        )

        performance_weights = (
            self.CIRCUIT_PERFORMANCE_WEIGHTS.get(
                track_type,
                self.CIRCUIT_PERFORMANCE_WEIGHTS[
                    "Mixed"
                ]
            )
        )

        # =================================================
        # CAR PERFORMANCE
        # =================================================

        aero_effect = (

            (
                car[
                    "aero"
                ]
                -
                75.0
            )

            *

            0.018

            *

            performance_weights[
                "aero"
            ]
            *
            5.0
        )

        straight_line_effect = (

            (
                car[
                    "straight_line_speed"
                ]
                -
                75.0
            )

            *

            0.040

            *

            track_effect[
                "straight_line"
            ]

            *

            (
                0.75
                +
                performance_weights[
                    "straight_line"
                ]
            )
        )

        cornering_effect = (

            (
                car[
                    "cornering"
                ]
                -
                75.0
            )

            *

            0.038

            *

            track_effect[
                "cornering"
            ]

            *

            (
                0.75
                +
                performance_weights[
                    "cornering"
                ]
            )
        )

        energy_effect = (

            (
                car[
                    "energy_efficiency"
                ]
                -
                75.0
            )

            *

            0.014

            *

            performance_weights[
                "energy"
            ]

            *

            5.0
        )

        # =================================================
        # DRIVER PERFORMANCE
        # =================================================

        driver_effect = (

            (
                driver[
                    "race_pace"
                ]
                -
                75.0
            )

            *

            0.045
        )

        consistency_effect = (

            (
                driver[
                    "consistency"
                ]
                -
                75.0
            )

            *

            0.008
        )

        # =================================================
        # TYRE MANAGEMENT
        # =================================================

        tyre_management_average = (

            driver[
                "tyre_management"
            ]

            +

            car[
                "tyre_management"
            ]

        ) / 2.0

        tyre_management_effect = (

            (
                tyre_management_average
                -
                75.0
            )

            *

            0.014

            *

            (
                0.80
                +
                performance_weights[
                    "tyre_management"
                ]
            )
        )

        # =================================================
        # RELIABILITY
        # =================================================
        #
        # Reliability is intentionally a small pace factor.
        # It becomes more important later when mechanical
        # failure / incidents are added.
        # =================================================

        reliability_effect = (

            (
                car[
                    "reliability"
                ]
                -
                75.0
            )

            *

            0.004
        )

        # =================================================
        # TYRE
        # =================================================

        tyre_base = (
            self.TYRE_BASE_PACE.get(
                compound,
                1.0
            )
        )

        degradation_rate = (
            self.TYRE_DEGRADATION.get(
                compound,
                0.05
            )
        )

        degradation = (

            max(
                tyre_age - 1,
                0
            )

            *

            degradation_rate
        )

        # =================================================
        # TYRE STRESS
        # =================================================

        tyre_stress = circuit.get(
            "tyre_stress",
            "Medium"
        )

        stress_multiplier = (
            self.TYRE_STRESS_MULTIPLIER.get(
                tyre_stress,
                1.00
            )
        )

        degradation *= (
            stress_multiplier
        )

        # =================================================
        # WEATHER
        # =================================================

        weather_penalty = (

            self.WEATHER_PENALTY.get(

                weather,

                self.WEATHER_PENALTY[
                    "Dry"
                ]

            ).get(

                compound,

                0.0
            )
        )

        # =================================================
        # WEATHER COMPATIBILITY
        # =================================================

        if weather == "Dry":

            weather_management_effect = 0.0

        elif weather == "Mixed":

            if compound == "Intermediate":

                weather_management_effect = (
                    -0.10
                )

            elif compound == "Full Wet":

                weather_management_effect = (
                    -0.05
                )

            else:

                weather_management_effect = 0.0

        else:

            if compound == "Intermediate":

                weather_management_effect = (
                    -0.12
                )

            elif compound == "Full Wet":

                weather_management_effect = (
                    -0.18
                )

            else:

                weather_management_effect = 0.0

        # =================================================
        # FINAL LAP TIME
        # =================================================

        lap_time = (

            self.BASE_LAP_TIME

            +

            tyre_base

            +

            degradation

            +

            weather_penalty

            +

            weather_management_effect

            -

            straight_line_effect

            -

            cornering_effect

            -

            aero_effect

            -

            energy_effect

            -

            driver_effect

            -

            consistency_effect

            -

            tyre_management_effect

            -

            reliability_effect
        )

        return max(
            60.0,
            lap_time
        )

    # =====================================================
    # WEATHER
    # =====================================================

    def _normalize_weather(
        self,
        weather: str
    ) -> str:

        allowed = {

            "Dry",

            "Mixed",

            "Wet"
        }

        weather = str(
            weather or "Dry"
        ).strip()

        if weather not in allowed:

            return "Dry"

        return weather

    # =====================================================
    # NAME
    # =====================================================

    def _get_name(
        self,
        obj: Any
    ) -> str:

        return str(

            getattr(
                obj,
                "name",
                "Unknown"
            )
        )


# =========================================================
# SINGLE SIMULATOR INSTANCE
# =========================================================

race_simulator = RaceSimulator()