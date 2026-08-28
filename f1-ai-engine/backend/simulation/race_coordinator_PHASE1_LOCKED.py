from math import sin
import random
from copy import deepcopy
from typing import Any, Dict, List

from backend.simulation.qualifying import qualifying_engine
from backend.simulation.weather_engine import weather_engine


class RaceCoordinator:
    """
    F1 Race Coordinator V2.4

    Competitive model:

        2025 historical tendency
                 +
        2026 current/predicted team profile
                 +
        circuit characteristics
                 +
        driver skill
                 +
        qualifying
                 +
        tyres
                 +
        weather
                 +
        strategy
                 +
        safety car
                 +
        incidents
                 +
        stochastic race-day variation
                 =
        final race result

    IMPORTANT:

    No team is hard-coded to win.

    No driver is hard-coded to win.

    Car performance remains important, but elite drivers can
    overcome part of a machinery deficit.

    Circuit characteristics can change the competitive order.

    Midfield and backmarker teams always retain a non-zero
    upset probability.
    """

    VERSION = "2.4"

    # =========================================================
    # CALIBRATION WEIGHTS
    # =========================================================

    HISTORICAL_2025_WEIGHT = 0.40
    CURRENT_2026_WEIGHT = 0.60

    # =========================================================
    # COMPETITIVE TIERS V2.4
    # =========================================================
    # Tier 1 is the primary win fight. Tiers 2-4 are probability
    # bands only; weather, strategy, incidents and driver skill can
    # still produce major upsets.

    TOP_WIN_TEAMS = {
        "Mercedes-AMG Petronas",
        "Scuderia Ferrari HP",
        "Oracle Red Bull Racing",
        "McLaren Mastercard",
    }

    TIER_2_TEAMS = {
        "Visa Cash App RB",
        "Atlassian Williams",
        "BWT Alpine",
        "TGR Haas",
        "Audi Revolut F1 Team",
    }

    TIER_3_TEAMS = {
        "Aston Martin Aramco",
    }

    TIER_4_TEAMS = {
        "Cadillac Formula 1",
    }

    TOTAL_SEASON_ROUNDS = 24

    TIER_1_BASE_BONUS = 0.008
    TIER_2_BASE_BONUS = 0.005
    TIER_3_FIRST_HALF_PENALTY = 0.035
    TIER_3_SECOND_HALF_PENALTY = 0.012
    TIER_4_BASE_PENALTY = 0.055


    # Dry:
    #   Car is still the largest contributor.
    #
    # Wet:
    #   Driver skill becomes significantly more important.
    DRY_CAR_WEIGHT = 0.68
    DRY_DRIVER_WEIGHT = 0.32

    WET_CAR_WEIGHT = 0.50
    WET_DRIVER_WEIGHT = 0.50

    # =========================================================
    # 2026 TEAM FEATURE VECTORS
    #
    # Source scale:
    #   negative = below benchmark
    #   positive = above benchmark
    #
    # Features:
    #   power
    #   aero
    #   low_drag
    #   braking
    #   tyre
    #   wet
    # =========================================================

    TEAM_FEATURES = {

        "Mercedes-AMG Petronas": {
            "power": 0.45,
            "aero": 0.40,
            "low_drag": 0.55,
            "braking": 0.35,
            "tyre": 0.35,
            "wet": 0.50
        },

        "Scuderia Ferrari HP": {
            "power": 0.50,
            "aero": 0.35,
            "low_drag": 0.45,
            "braking": 0.40,
            "tyre": 0.20,
            "wet": 0.25
        },

        "McLaren Mastercard": {
            "power": 0.40,
            "aero": 0.55,
            "low_drag": 0.35,
            "braking": 0.45,
            "tyre": 0.55,
            "wet": 0.45
        },

        "Oracle Red Bull Racing": {
            "power": 0.40,
            "aero": 0.45,
            "low_drag": 0.50,
            "braking": 0.35,
            "tyre": 0.45,
            "wet": 0.60
        },

        "Visa Cash App RB": {
            "power": 0.10,
            "aero": 0.05,
            "low_drag": 0.00,
            "braking": 0.15,
            "tyre": 0.05,
            "wet": 0.15
        },

        "BWT Alpine": {
            "power": -0.10,
            "aero": -0.05,
            "low_drag": 0.15,
            "braking": -0.10,
            "tyre": -0.05,
            "wet": 0.30
        },

        "TGR Haas": {
            "power": 0.20,
            "aero": -0.15,
            "low_drag": 0.15,
            "braking": 0.00,
            "tyre": -0.30,
            "wet": -0.10
        },

        "Audi Revolut F1 Team": {
            "power": -0.15,
            "aero": -0.15,
            "low_drag": -0.10,
            "braking": -0.05,
            "tyre": 0.00,
            "wet": 0.05
        },

        "Atlassian Williams": {
            "power": 0.15,
            "aero": -0.20,
            "low_drag": 0.45,
            "braking": -0.20,
            "tyre": -0.25,
            "wet": -0.05
        },

        "Aston Martin Aramco": {
            "power": -0.05,
            "aero": 0.00,
            "low_drag": -0.20,
            "braking": 0.10,
            "tyre": 0.00,
            "wet": 0.20
        },

        "Cadillac Formula 1": {
            "power": -0.30,
            "aero": -0.35,
            "low_drag": -0.25,
            "braking": -0.35,
            "tyre": -0.40,
            "wet": -0.20
        }
    }

    # =========================================================
    # DRIVER CALIBRATION
    #
    # These are intentionally separate from the car.
    #
    # Order:
    #   qualifying
    #   race craft
    #   tyre preservation
    #   wet skill
    #   street skill
    # =========================================================

    DRIVER_FEATURES = {

        "Max Verstappen": {
            "qualifying": 0.98,
            "race_craft": 0.99,
            "tyre": 0.96,
            "wet": 0.99,
            "street": 0.95
        },

        "Lando Norris": {
            "qualifying": 0.97,
            "race_craft": 0.93,
            "tyre": 0.94,
            "wet": 0.92,
            "street": 0.93
        },

        "Oscar Piastri": {
            "qualifying": 0.94,
            "race_craft": 0.94,
            "tyre": 0.91,
            "wet": 0.88,
            "street": 0.96
        },

        "George Russell": {
            "qualifying": 0.95,
            "race_craft": 0.92,
            "tyre": 0.90,
            "wet": 0.91,
            "street": 0.92
        },

        "Charles Leclerc": {
            "qualifying": 0.98,
            "race_craft": 0.92,
            "tyre": 0.89,
            "wet": 0.87,
            "street": 0.98
        },

        "Lewis Hamilton": {
            "qualifying": 0.93,
            "race_craft": 0.96,
            "tyre": 0.96,
            "wet": 0.97,
            "street": 0.92
        },

        "Kimi Antonelli": {
            "qualifying": 0.92,
            "race_craft": 0.90,
            "tyre": 0.88,
            "wet": 0.90,
            "street": 0.89
        },

        "Fernando Alonso": {
            "qualifying": 0.91,
            "race_craft": 0.96,
            "tyre": 0.94,
            "wet": 0.95,
            "street": 0.94
        },

        "Alexander Albon": {
            "qualifying": 0.90,
            "race_craft": 0.89,
            "tyre": 0.88,
            "wet": 0.86,
            "street": 0.90
        },

        "Carlos Sainz": {
            "qualifying": 0.92,
            "race_craft": 0.92,
            "tyre": 0.93,
            "wet": 0.89,
            "street": 0.94
        },

        "Nico Hülkenberg": {
            "qualifying": 0.92,
            "race_craft": 0.86,
            "tyre": 0.84,
            "wet": 0.88,
            "street": 0.87
        },

        "Liam Lawson": {
            "qualifying": 0.86,
            "race_craft": 0.87,
            "tyre": 0.86,
            "wet": 0.85,
            "street": 0.88
        },

        "Pierre Gasly": {
            "qualifying": 0.88,
            "race_craft": 0.87,
            "tyre": 0.87,
            "wet": 0.91,
            "street": 0.89
        },

        "Oliver Bearman": {
            "qualifying": 0.87,
            "race_craft": 0.88,
            "tyre": 0.85,
            "wet": 0.84,
            "street": 0.92
        }
    }

    # =========================================================
    # CIRCUIT ARCHETYPES
    #
    # These are used when the database's track_type is not
    # specific enough.
    # =========================================================

    CIRCUIT_ARCHETYPES = {

        "technical": {
            "power": 0.10,
            "aero": 0.35,
            "low_drag": 0.05,
            "braking": 0.15,
            "tyre": 0.25
        },

        "high_speed": {
            "power": 0.30,
            "aero": 0.15,
            "low_drag": 0.35,
            "braking": 0.15,
            "tyre": 0.05
        },

        "power": {
            "power": 0.40,
            "aero": 0.05,
            "low_drag": 0.35,
            "braking": 0.15,
            "tyre": 0.05
        },

        "street": {
            "power": 0.10,
            "aero": 0.30,
            "low_drag": 0.05,
            "braking": 0.25,
            "tyre": 0.20
        },

        "mixed": {
            "power": 0.20,
            "aero": 0.20,
            "low_drag": 0.20,
            "braking": 0.15,
            "tyre": 0.25
        }
    }

    # =========================================================
    # CIRCUIT-SPECIFIC CALIBRATION
    #
    # These are not winners.
    #
    # They modify the importance of the underlying car features.
    # =========================================================

    CIRCUIT_PROFILES = {

        "Australian Grand Prix": {
            "archetype": "mixed",
            "qualifying": 0.82,
            "overtaking": 0.45,
            "sc": 0.65,
            "rain": 0.35,
            "historical_2025": {
                "McLaren Mastercard": 0.90,
                "Oracle Red Bull Racing": 0.82,
                "Mercedes-AMG Petronas": 0.72,
                "Scuderia Ferrari HP": 0.72
            }
        },

        "Monaco Grand Prix": {
            "archetype": "technical",
            "qualifying": 0.99,
            "overtaking": 0.95,
            "sc": 0.83,
            "rain": 0.20,
            "historical_2025": {
                "McLaren Mastercard": 0.90,
                "Scuderia Ferrari HP": 0.86,
                "Oracle Red Bull Racing": 0.80,
                "Mercedes-AMG Petronas": 0.76
            }
        },

        "Hungarian Grand Prix": {
            "archetype": "technical",
            "qualifying": 0.88,
            "overtaking": 0.78,
            "sc": 0.35,
            "rain": 0.35,
            "historical_2025": {
                "McLaren Mastercard": 0.92,
                "Oracle Red Bull Racing": 0.84,
                "Mercedes-AMG Petronas": 0.78,
                "Scuderia Ferrari HP": 0.76
            }
        },

        "Singapore Grand Prix": {
            "archetype": "street",
            "qualifying": 0.93,
            "overtaking": 0.80,
            "sc": 0.90,
            "rain": 0.65,
            "historical_2025": {
                "Mercedes-AMG Petronas": 0.88,
                "McLaren Mastercard": 0.84,
                "Oracle Red Bull Racing": 0.83,
                "Scuderia Ferrari HP": 0.80
            }
        },

        "Italian Grand Prix": {
            "archetype": "high_speed",
            "qualifying": 0.70,
            "overtaking": 0.35,
            "sc": 0.50,
            "rain": 0.15,
            "historical_2025": {
                "Oracle Red Bull Racing": 0.91,
                "McLaren Mastercard": 0.87,
                "Scuderia Ferrari HP": 0.88,
                "Mercedes-AMG Petronas": 0.82
            }
        },

        "Azerbaijan Grand Prix": {
            "archetype": "power",
            "qualifying": 0.82,
            "overtaking": 0.35,
            "sc": 0.75,
            "rain": 0.10,
            "historical_2025": {
                "Oracle Red Bull Racing": 0.90,
                "Scuderia Ferrari HP": 0.87,
                "Mercedes-AMG Petronas": 0.85,
                "McLaren Mastercard": 0.84
            }
        },

        "Belgian Grand Prix": {
            "archetype": "high_speed",
            "qualifying": 0.72,
            "overtaking": 0.35,
            "sc": 0.42,
            "rain": 0.65,
            "historical_2025": {
                "Oracle Red Bull Racing": 0.88,
                "McLaren Mastercard": 0.87,
                "Mercedes-AMG Petronas": 0.84,
                "Scuderia Ferrari HP": 0.82
            }
        },

        "Las Vegas Grand Prix": {
            "archetype": "power",
            "qualifying": 0.75,
            "overtaking": 0.30,
            "sc": 0.45,
            "rain": 0.02,
            "historical_2025": {
                "Mercedes-AMG Petronas": 0.90,
                "Scuderia Ferrari HP": 0.86,
                "Oracle Red Bull Racing": 0.83,
                "McLaren Mastercard": 0.79
            }
        }
    }

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def __init__(
        self,
        strategy_engine,
        race_simulator,
        race_grid
    ):

        self.strategy_engine = strategy_engine
        self.race_simulator = race_simulator
        self.race_grid = race_grid

    # =========================================================
    # PUBLIC RACE METHOD
    # =========================================================

    def run_race(
        self,
        teams: List[Any],
        circuit: Any,
        weather: str = "Dry",
        laps: int = 57,
        strategy_inputs: Dict[str, Any] = None,
        weather_profile: List[Dict[str, Any]] = None,
        season_round: int = None,
        total_rounds: int = TOTAL_SEASON_ROUNDS
    ) -> Dict[str, Any]:

        if not teams:
            raise ValueError(
                "No teams supplied to race coordinator."
            )

        if laps <= 0:
            raise ValueError(
                "Race distance must be greater than zero."
            )

        if season_round is None:
            season_round = 1

        try:
            season_round = max(1, int(season_round))
        except (TypeError, ValueError):
            season_round = 1

        try:
            total_rounds = max(1, int(total_rounds))
        except (TypeError, ValueError):
            total_rounds = self.TOTAL_SEASON_ROUNDS

        weather = self.race_simulator._normalize_weather(
            weather
        )

        circuit_data = self._extract_circuit(
            circuit
        )

        profile = self._get_circuit_profile(
            circuit_data
        )

        profile = dict(profile)
        profile["season_round"] = season_round
        profile["total_rounds"] = total_rounds

        weather_profile = weather_engine.get_profile(
            circuit,
            laps,
            weather=weather,
            weather_profile=weather_profile
        )

        weather_transitions = weather_engine.transitions(
            weather_profile
        )

        race_random = random.Random()

        strategy_inputs = (
            strategy_inputs
            or
            self._default_strategy_inputs(
                weather
            )
        )

        # =====================================================
        # BASELINE GRID
        # =====================================================

        baseline_entries = (
            self.race_grid.create_starting_grid(
                teams
            )
        )

        if not baseline_entries:
            raise ValueError(
                "RaceGrid returned no drivers."
            )

        # =====================================================
        # QUALIFYING
        # =====================================================

        qualifying = qualifying_engine.qualify(
            baseline_entries,
            circuit,
            weather=weather
        )

        qualifying_grid = list(
            qualifying.get(
                "starting_grid",
                []
            )
        )

        # Apply circuit-specific qualifying adjustment.
        #
        # This changes qualifying competitiveness without
        # permanently modifying the database performance values.

        qualifying_grid = (
            self._apply_calibrated_qualifying(
                qualifying_grid,
                profile,
                weather
            )
        )

        qualifying_grid.sort(
            key=lambda entry:
                entry.get(
                    "qualifying_lap_time",
                    entry.get(
                        "position",
                        999
                    )
                )
        )

        grid = []

        for position, entry in enumerate(
            qualifying_grid,
            start=1
        ):

            row = dict(entry)

            row["position"] = position
            row["grid_position"] = position
            row["race_time"] = 0.0
            row["gap_to_leader"] = 0.0
            row["gap_to_ahead"] = 0.0

            grid.append(row)

        grid_size = len(
            grid
        )

        # =====================================================
        # RACE FORM
        # =====================================================

        field_scores = []

        for entry in grid:

            score = self._expected_competitive_score(
                entry,
                profile,
                weather
            )

            field_scores.append(
                score
            )

        field_average = (
            sum(field_scores)
            /
            len(field_scores)
            if field_scores
            else 0.80
        )

        # Safety Car state must exist before race-form calculations. 
        # It is recalculated below using the actual circuit/weather probability.
        safety_car_enabled = False

        race_form = {}

        for entry in grid:

            driver_id = entry[
                "driver_id"
            ]

            competitive_score = (
                self._expected_competitive_score(
                    entry,
                    profile,
                    weather
                )
            )

            car_score = (
                self._calibrated_car_score(
                    entry,
                    profile
                )
            )

            driver_score = (
                self._driver_score(
                    entry.get(
                        "driver_performance"
                    ),
                    entry.get(
                        "driver"
                    )
                )
            )

            # -------------------------------------------------
            # Compress the competitive field.
            #
            # This prevents a single car rating from locking
            # every race into the same top 10.
            # -------------------------------------------------

            relative = (
                competitive_score
                -
                field_average
            )

            # Keep the four Tier-1 teams inside a close race
            # window. A large multiplier here was making the
            # same teams repeat the same finishing order.
            # Lower-tier teams retain a smaller natural gap.
            tier_for_spread = self._team_tier(
                entry.get("team", ""),
                season_round,
                total_rounds
            )

            if tier_for_spread == 1:
                spread_multiplier = 0.95
            elif tier_for_spread == 2:
                spread_multiplier = 1.05
            elif tier_for_spread == 3:
                spread_multiplier = 1.15
            else:
                spread_multiplier = 1.25

            spread_adjustment = (
                field_average
                -
                competitive_score
            ) * spread_multiplier

            # -------------------------------------------------
            # Elite-driver extraction.
            # -------------------------------------------------

            driver_extraction = (
                self._driver_extraction_bonus(
                    entry,
                    car_score,
                    field_average,
                    weather
                )
            )

            # -------------------------------------------------
            # Weekend form.
            # -------------------------------------------------

            # Race-to-race performance variation. This is deliberately
            # large enough to reshuffle close cars, but still centered
            # around the calibrated pace.
            form = race_random.uniform(
                -0.40,
                0.40
            )

            if weather in {
                "Mixed",
                "Wet"
            }:

                form += race_random.uniform(
                    -0.32,
                    0.32
                )

            # -------------------------------------------------
            # Team tier for race-day opportunity and variance.
            # -------------------------------------------------
            tier = self._team_tier(
                entry.get("team", ""),
                season_round,
                total_rounds
            )

            # Tier-1 teams are intentionally given an additional
            # small race-day swing. This does not choose a winner;
            # it allows Ferrari/Mercedes/Red Bull/McLaren to rotate
            # when their underlying pace is close.
            if tier == 1:
                form += race_random.uniform(
                    -0.20,
                    0.20
                )

            chaos_factor = 1.0

            if weather in {"Mixed", "Wet"}:
                chaos_factor += 0.85

            if safety_car_enabled:
                chaos_factor += 0.35

            if tier == 2:
                if race_random.random() < (0.085 * chaos_factor):
                    form -= race_random.uniform(0.06, 0.22)

            elif tier == 3:
                if race_random.random() < (0.045 * chaos_factor):
                    form -= race_random.uniform(0.05, 0.16)

            elif tier == 4:
                if race_random.random() < (0.020 * chaos_factor):
                    form -= race_random.uniform(0.03, 0.12)

            # -------------------------------------------------
            # Upset probability.
            # -------------------------------------------------

            upset_chance = (
                self._upset_probability(
                    competitive_score,
                    field_average,
                    profile,
                    weather
                )
            )

            upset_chance += self._tier_upset_bonus(
                entry.get("team", ""),
                season_round,
                total_rounds
            )

            upset_chance = self._clamp(
                upset_chance,
                0.025,
                0.22
            )

            upset_applied = False

            if (
                race_random.random()
                <
                upset_chance
            ):

                form -= race_random.uniform(
                    0.16,
                    0.52
                )

                upset_applied = True

            # -------------------------------------------------
            # Strong teams can have bad weekends.
            # -------------------------------------------------

            bad_weekend = False

            if (
                competitive_score
                >=
                field_average
            ):

                if (
                    race_random.random()
                    <
                    0.12
                ):

                    form += race_random.uniform(
                        0.12,
                        0.45
                    )

                    bad_weekend = True

            consistency = (
                self._component_value(
                    entry.get(
                        "driver_performance"
                    ),
                    "consistency",
                    75.0
                )
            )

            form += (
                race_random.uniform(
                    -0.08,
                    0.08
                )
                *
                (
                    0.75
                    +
                    max(
                        0.0,
                        75.0 - consistency
                    )
                    /
                    100.0
                )
            )

            race_form[
                driver_id
            ] = {

                "pace":
                    (
                        spread_adjustment
                        +
                        driver_extraction
                        +
                        form
                    ),

                "competitive_score":
                    competitive_score,

                "car_score":
                    car_score,

                "driver_score":
                    driver_score,

                "upset_applied":
                    upset_applied,

                "bad_weekend":
                    bad_weekend,

                "mistake_probability":
                    self._race_mistake_probability(
                        entry,
                        weather
                    ),

                "mistake_applied":
                    False
            }

        # =====================================================
        # SAFETY CAR
        # =====================================================

        weather_has_rain = any(
            phase.get(
                "weather"
            )
            in {
                "Mixed",
                "Wet"
            }
            for phase in weather_profile
        )

        safety_car_probability = (
            profile["sc"]
            * 0.38
        )

        if weather_has_rain:
            safety_car_probability += 0.10

        safety_car_probability = (
            self._clamp(
                safety_car_probability,
                0.08,
                0.72
            )
        )

        safety_car_enabled = (
            race_random.random()
            <
            safety_car_probability
        )

        safety_car_lap = None

        if (
            safety_car_enabled
            and
            laps >= 12
        ):

            safety_car_lap = race_random.randint(
                max(
                    8,
                    int(
                        laps * 0.18
                    )
                ),
                max(
                    9,
                    int(
                        laps * 0.82
                    )
                )
            )

        # =====================================================
        # RACE STATES
        # =====================================================

        race_states = {}

        for entry in grid:

            driver_id = entry[
                "driver_id"
            ]

            race_states[
                driver_id
            ] = {

                "strategy":
                    None,

                "stints":
                    [],

                "current_stint":
                    0,

                "tyre_age":
                    0,

                "pit_stops":
                    0,

                "completed_laps":
                    0,

                "fastest_lap":
                    None,

                "fastest_lap_time":
                    None,

                "grid_position":
                    entry[
                        "grid_position"
                    ],

                "last_position":
                    entry[
                        "grid_position"
                    ]
            }

        # =====================================================
        # INDIVIDUAL STRATEGIES
        # =====================================================

        driver_strategies = {}

        for entry in grid:

            car_pace = (
                self._calibrated_car_score(
                    entry,
                    profile
                )
            )

            driver_pace = (
                self._driver_score(
                    entry.get(
                        "driver_performance"
                    ),
                    entry.get(
                        "driver"
                    )
                )
            )

            combined_pace = (
                car_pace * 0.70
                +
                driver_pace * 0.30
            )

            team_context = {

                "team_name":
                    entry.get(
                        "team",
                        "Generic Team"
                    ),

                "starting_position":
                    entry.get(
                        "grid_position",
                        grid_size
                    ),

                "grid_size":
                    grid_size,

                "car_pace":
                    combined_pace,

                "driver_pace":
                    driver_pace,

                "weather":
                    weather
            }

            analysis = (
                self.strategy_engine.analyze(
                    circuit,
                    strategy_inputs,
                    team_context=team_context
                )
            )

            recommended = (
                analysis.get(
                    "recommended_strategy"
                )
            )

            if recommended is None:

                raise ValueError(
                    "No recommended strategy found "
                    f"for {entry.get('driver', 'Unknown Driver')}."
                )

            driver_strategies[
                entry["driver_id"]
            ] = recommended

            race_states[
                entry["driver_id"]
            ]["strategy"] = recommended

        # =====================================================
        # STINT GENERATION
        # =====================================================

        simulator_circuit = (
            self.race_simulator._extract_circuit(
                circuit
            )
        )

        for entry in grid:

            driver_id = entry[
                "driver_id"
            ]

            strategy = driver_strategies[
                driver_id
            ]

            normalized_strategy = (
                self.race_simulator._normalize_strategy(
                    strategy
                )
            )

            base_stints = (
                self.race_simulator._build_stints(
                    laps,
                    normalized_strategy,
                    simulator_circuit,
                    weather
                )
            )

            stints = (
                self._apply_weather_profile_to_stints(
                    laps,
                    base_stints,
                    weather_profile
                )
            )

            race_states[
                driver_id
            ]["stints"] = stints

        # =====================================================
        # HISTORY
        # =====================================================

        lap_history = []
        race_events = []

        fastest_lap_driver = None
        fastest_lap_time = None
        fastest_lap_number = None

        # =====================================================
        # MAIN RACE LOOP
        # =====================================================

        for lap_number in range(
            1,
            laps + 1
        ):

            lap_weather = (
                weather_engine.weather_at_lap(
                    weather_profile,
                    lap_number
                )
            )

            previous_order = [
                entry["driver_id"]
                for entry in grid
            ]

            previous_times = {
                entry["driver_id"]:
                    entry.get(
                        "race_time",
                        0.0
                    )
                for entry in grid
            }

            previous_gaps = (
                self._calculate_previous_gaps(
                    grid
                )
            )

            lap_times = {}
            lap_snapshot = []

            # =================================================
            # LAP
            # =================================================

            for entry in grid:

                driver_id = entry[
                    "driver_id"
                ]

                state = race_states[
                    driver_id
                ]

                stint = (
                    self._get_current_stint(
                        state,
                        lap_number
                    )
                )

                compound = stint[
                    "compound"
                ]

                tyre_age = (
                    self._get_tyre_age(
                        stint,
                        lap_number
                    )
                )

                lap_time = (
                    self.race_simulator._calculate_lap_time(
                        simulator_circuit,
                        entry[
                            "car_performance"
                        ],
                        entry[
                            "driver_performance"
                        ],
                        compound,
                        tyre_age,
                        lap_weather
                    )
                )

                # -------------------------------------------------
                # Calibrated circuit/car effect.
                # -------------------------------------------------

                calibrated_adjustment = (
                    self._lap_calibration_adjustment(
                        entry,
                        profile,
                        lap_weather
                    )
                )

                lap_time += (
                    calibrated_adjustment
                )

                # -------------------------------------------------
                # Race form.
                # -------------------------------------------------

                lap_time += (
                    race_form[
                        driver_id
                    ]["pace"]
                )

                # -------------------------------------------------
                # Driver wet-weather advantage.
                # -------------------------------------------------

                if lap_weather in {
                    "Mixed",
                    "Wet"
                }:

                    wet_score = (
                        self._driver_wet_score(
                            entry.get(
                                "driver_performance"
                            ),
                            entry.get(
                                "driver"
                            )
                        )
                    )

                    wet_adjustment = (
                        0.82
                        -
                        wet_score
                    ) * 0.65

                    lap_time += (
                        wet_adjustment
                    )

                # -------------------------------------------------
                # Deterministic small variation.
                # -------------------------------------------------

                lap_time += (
                    self._race_form_variation(
                        driver_id,
                        lap_number
                    )
                )

                # -------------------------------------------------
                # Strategy effect.
                # -------------------------------------------------

                lap_time += (
                    self._strategy_lap_adjustment(
                        state,
                        compound,
                        tyre_age,
                        lap_weather
                    )
                )

                # -------------------------------------------------
                # Driver mistake.
                # -------------------------------------------------

                driver_risk = race_form[
                    driver_id
                ]

                if (
                    not driver_risk[
                        "mistake_applied"
                    ]
                    and
                    random.random()
                    <
                    driver_risk[
                        "mistake_probability"
                    ]
                ):

                    mistake_loss = random.uniform(
                        0.8,
                        3.8
                    )

                    if lap_weather in {
                        "Mixed",
                        "Wet"
                    }:

                        mistake_loss *= (
                            random.uniform(
                                1.10,
                                1.60
                            )
                        )

                    lap_time += (
                        mistake_loss
                    )

                    driver_risk[
                        "mistake_applied"
                    ] = True

                    race_events.append({

                        "type":
                            "driver_mistake",

                        "lap":
                            lap_number,

                        "driver":
                            entry["driver"],

                        "team":
                            entry["team"],

                        "time_loss":
                            round(
                                mistake_loss,
                                3
                            )
                    })

                lap_time = max(
                    lap_time,
                    50.0
                )

                lap_times[
                    driver_id
                ] = lap_time

                state[
                    "completed_laps"
                ] = lap_number

                state[
                    "tyre_age"
                ] = tyre_age

                # -------------------------------------------------
                # Driver fastest lap.
                # -------------------------------------------------

                if (
                    state[
                        "fastest_lap_time"
                    ] is None
                    or
                    lap_time
                    <
                    state[
                        "fastest_lap_time"
                    ]
                ):

                    state[
                        "fastest_lap_time"
                    ] = lap_time

                    state[
                        "fastest_lap"
                    ] = lap_number

                # -------------------------------------------------
                # Overall fastest lap.
                # -------------------------------------------------

                if (
                    fastest_lap_time is None
                    or
                    lap_time
                    <
                    fastest_lap_time
                ):

                    fastest_lap_time = (
                        lap_time
                    )

                    fastest_lap_driver = (
                        entry["driver"]
                    )

                    fastest_lap_number = (
                        lap_number
                    )

            # =================================================
            # ADD LAP TIMES
            # =================================================

            for entry in grid:

                driver_id = entry[
                    "driver_id"
                ]

                entry[
                    "race_time"
                ] = (
                    entry.get(
                        "race_time",
                        0.0
                    )
                    +
                    lap_times[
                        driver_id
                    ]
                )

            # =================================================
            # ORDER
            # =================================================

            grid.sort(
                key=lambda entry:
                    entry.get(
                        "race_time",
                        0.0
                    )
            )

            self._update_gaps(
                grid
            )

            # =================================================
            # OVERTAKES
            # =================================================

            race_events.extend(
                self._detect_overtakes(
                    previous_order,
                    previous_times,
                    previous_gaps,
                    grid,
                    lap_times,
                    circuit,
                    lap_number
                )
            )

            # =================================================
            # PIT STOPS
            # =================================================

            pit_events = (
                self._process_pit_stops(
                    grid,
                    race_states,
                    lap_number,
                    laps
                )
            )

            race_events.extend(
                pit_events
            )

            # =================================================
            # SAFETY CAR
            # =================================================

            if (
                safety_car_enabled
                and
                safety_car_lap
                ==
                lap_number
            ):

                ordered = sorted(
                    grid,
                    key=lambda entry:
                        entry.get(
                            "race_time",
                            0.0
                        )
                )

                if ordered:

                    leader_time = (
                        ordered[0].get(
                            "race_time",
                            0.0
                        )
                    )

                    compression = (
                        race_random.uniform(
                            0.18,
                            0.42
                        )
                    )

                    for sc_entry in ordered:

                        current_time = (
                            sc_entry.get(
                                "race_time",
                                0.0
                            )
                        )

                        gap = (
                            current_time
                            -
                            leader_time
                        )

                        sc_entry[
                            "race_time"
                        ] = (
                            leader_time
                            +
                            gap
                            *
                            compression
                        )

                    race_events.append({

                        "type":
                            "safety_car",

                        "lap":
                            lap_number,

                        "gap_compression":
                            round(
                                compression,
                                3
                            )
                    })

                    # Restart creates a small but meaningful
                    # race-order variation.
                    for driver_id in race_form:

                        race_form[
                            driver_id
                        ]["pace"] += (
                            race_random.uniform(
                                -0.08,
                                0.08
                            )
                        )

            # =================================================
            # FINAL LAP ORDER
            # =================================================

            grid.sort(
                key=lambda entry:
                    entry.get(
                        "race_time",
                        0.0
                    )
            )

            self._update_gaps(
                grid
            )

            for position, entry in enumerate(
                grid,
                start=1
            ):

                race_states[
                    entry["driver_id"]
                ]["last_position"] = (
                    position
                )

            # =================================================
            # LAP SNAPSHOT
            # =================================================

            for entry in grid:

                driver_id = entry[
                    "driver_id"
                ]

                state = race_states[
                    driver_id
                ]

                stint = (
                    self._get_current_stint(
                        state,
                        lap_number
                    )
                )

                lap_snapshot.append({

                    "position":
                        entry[
                            "position"
                        ],

                    "driver":
                        entry[
                            "driver"
                        ],

                    "team":
                        entry[
                            "team"
                        ],

                    "lap_time":
                        round(
                            lap_times[
                                driver_id
                            ],
                            3
                        ),

                    "gap_to_leader":
                        entry[
                            "gap_to_leader"
                        ],

                    "gap_to_ahead":
                        entry[
                            "gap_to_ahead"
                        ],

                    "compound":
                        stint[
                            "compound"
                        ],

                    "weather":
                        lap_weather,

                    "tyre_age":
                        state[
                            "tyre_age"
                        ],

                    "pit_stops":
                        state[
                            "pit_stops"
                        ]
                })

            lap_history.append({

                "lap":
                    lap_number,

                "weather":
                    lap_weather,

                "standings":
                    lap_snapshot
            })

        # =====================================================
        # FINAL CLASSIFICATION
        # =====================================================

        grid.sort(
            key=lambda entry:
                entry.get(
                    "race_time",
                    0.0
                )
        )

        self._update_gaps(
            grid
        )

        classification = []

        for position, entry in enumerate(
            grid,
            start=1
        ):

            driver_id = entry[
                "driver_id"
            ]

            state = race_states[
                driver_id
            ]

            classification.append({

                "position":
                    position,

                "driver":
                    entry[
                        "driver"
                    ],

                "team":
                    entry[
                        "team"
                    ],

                "driver_id":
                    driver_id,

                "team_id":
                    entry[
                        "team_id"
                    ],

                "race_time":
                    round(
                        entry.get(
                            "race_time",
                            0.0
                        ),
                        3
                    ),

                "gap_to_leader":
                    entry[
                        "gap_to_leader"
                    ],

                "pit_stops":
                    state[
                        "pit_stops"
                    ],

                "fastest_lap":
                    state[
                        "fastest_lap"
                    ],

                "fastest_lap_time":
                    (
                        round(
                            state[
                                "fastest_lap_time"
                            ],
                            3
                        )
                        if state[
                            "fastest_lap_time"
                        ] is not None
                        else None
                    ),

                "grid_position":
                    state[
                        "grid_position"
                    ],

                "strategy":
                    state[
                        "strategy"
                    ]
            })

        # =====================================================
        # STARTING GRID OUTPUT
        # =====================================================

        starting_grid = []

        for entry in qualifying[
            "starting_grid"
        ]:

            starting_grid.append({

                "position":
                    entry.get(
                        "grid_position",
                        entry.get(
                            "position"
                        )
                    ),

                "driver":
                    entry.get(
                        "driver"
                    ),

                "team":
                    entry.get(
                        "team"
                    ),

                "driver_id":
                    entry.get(
                        "driver_id"
                    ),

                "team_id":
                    entry.get(
                        "team_id"
                    ),

                "qualifying_lap_time":
                    entry.get(
                        "qualifying_lap_time"
                    ),

                "qualifying_tyre":
                    entry.get(
                        "qualifying_tyre"
                    )
            })

        starting_grid.sort(
            key=lambda entry:
                entry.get(
                    "position",
                    999
                )
        )

        # =====================================================
        # STRATEGIES OUTPUT
        # =====================================================

        strategies_output = []

        for entry in starting_grid:

            driver_id = entry[
                "driver_id"
            ]

            strategies_output.append({

                "grid_position":
                    entry[
                        "position"
                    ],

                "driver":
                    entry[
                        "driver"
                    ],

                "team":
                    entry[
                        "team"
                    ],

                "strategy":
                    race_states[
                        driver_id
                    ]["strategy"]
            })

        # =====================================================
        # EVENT SUMMARY
        # =====================================================

        overtake_count = sum(
            1
            for event in race_events
            if event.get(
                "type"
            )
            ==
            "overtake"
        )

        pit_stop_count = sum(
            1
            for event in race_events
            if event.get(
                "type"
            )
            ==
            "pit_stop"
        )

        safety_car_count = sum(
            1
            for event in race_events
            if event.get(
                "type"
            )
            ==
            "safety_car"
        )

        mistake_count = sum(
            1
            for event in race_events
            if event.get(
                "type"
            )
            ==
            "driver_mistake"
        )

        # =====================================================
        # RESULT
        # =====================================================

        return {

            "success":
                True,

            "coordinator":
                "F1 Race Coordinator",

            "version":
                self.VERSION,

            "race": {

                "circuit":
                    circuit_data[
                        "name"
                    ],

                "weather":
                    weather,

                "weather_profile":
                    weather_profile,

                "weather_transitions":
                    weather_transitions,

                "laps":
                    laps,

                "drivers":
                    len(grid),

                "race_dynamics": {

                    "stochastic":
                        True,

                    "safety_car_enabled":
                        safety_car_enabled,

                    "safety_car_lap":
                        safety_car_lap,

                    "season_round":
                        season_round,

                    "total_rounds":
                        total_rounds,

                    "competitive_tiers": {
                        entry.get("team", ""): self._team_tier(
                            entry.get("team", ""),
                            season_round,
                            total_rounds
                        )
                        for entry in grid
                    }
                }
            },

            "qualifying":
                qualifying,

            "starting_grid":
                starting_grid,

            "strategies":
                strategies_output,

            "weather_profile":
                weather_profile,

            "weather_transitions":
                weather_transitions,

            "fastest_lap": {

                "driver":
                    fastest_lap_driver,

                "lap":
                    fastest_lap_number,

                "time":
                    (
                        round(
                            fastest_lap_time,
                            3
                        )
                        if fastest_lap_time is not None
                        else None
                    )
            },

            "classification":
                classification,

            "events":
                race_events,

            "event_summary": {

                "total_events":
                    len(
                        race_events
                    ),

                "overtakes":
                    overtake_count,

                "pit_stops":
                    pit_stop_count,

                "safety_car":
                    safety_car_count,

                "driver_mistakes":
                    mistake_count
            },

            "calibration": {

                "version":
                    self.VERSION,

                "historical_2025_weight":
                    self.HISTORICAL_2025_WEIGHT,

                "current_2026_weight":
                    self.CURRENT_2026_WEIGHT,

                "dry_car_weight":
                    self.DRY_CAR_WEIGHT,

                "dry_driver_weight":
                    self.DRY_DRIVER_WEIGHT,

                "wet_car_weight":
                    self.WET_CAR_WEIGHT,

                "wet_driver_weight":
                    self.WET_DRIVER_WEIGHT,

                "circuit_profile":
                    profile
            },

            "lap_history":
                lap_history
        }

    # =========================================================
    # TEAM CIRCUIT SCORE
    # =========================================================

    def _team_circuit_score(
        self,
        entry: Dict[str, Any],
        profile: Dict[str, Any]
    ) -> float:
        """
        Calculate the team's circuit-specific qualifying score.

        The score is based on the existing calibrated car model,
        which already combines the team's current performance,
        circuit archetype and 2025 circuit evidence.

        No team or driver is locked to a qualifying position.
        """

        car_score = self._calibrated_car_score(
            entry,
            profile
        )

        return self._clamp(
            car_score,
            0.25,
            1.10
        )

    # =========================================================
    # CALIBRATED QUALIFYING
    # =========================================================

    def _apply_calibrated_qualifying(
        self,
        qualifying_grid: List[Dict[str, Any]],
        profile: Dict[str, Any],
        weather: str
    ) -> List[Dict[str, Any]]:

        result = []

        for original in qualifying_grid:

            entry = dict(
                original
            )

            team_score = (
                self._team_circuit_score(
                    entry,
                    profile
                )
            )

            driver_score = (
                self._driver_qualifying_score(
                    entry.get(
                        "driver_performance"
                    ),
                    entry.get(
                        "driver"
                    )
                )
            )

            base_time = float(
                entry.get(
                    "qualifying_lap_time",
                    90.0
                )
            )

            # Better score = lower lap time.
            #
            # The adjustment is intentionally moderate because
            # qualifying_engine already performs the core simulation.

            adjustment = (
                0.80
                -
                team_score
            ) * 0.75

            adjustment += (
                0.82
                -
                driver_score
            ) * 0.50

            if weather in {
                "Mixed",
                "Wet"
            }:

                wet_score = (
                    self._driver_wet_score(
                        entry.get(
                            "driver_performance"
                        ),
                        entry.get(
                            "driver"
                        )
                    )
                )

                adjustment += (
                    0.82
                    -
                    wet_score
                ) * 0.40

            entry[
                "qualifying_lap_time"
            ] = round(
                base_time
                +
                adjustment,
                3
            )

            result.append(
                entry
            )

        return result

    # =========================================================
    # COMPETITIVE TIER HELPERS
    # =========================================================

    def _team_tier(
        self,
        team_name: str,
        season_round: int = 1,
        total_rounds: int = TOTAL_SEASON_ROUNDS
    ) -> int:
        team_name = str(team_name or "")

        if team_name in self.TOP_WIN_TEAMS:
            return 1

        if team_name in self.TIER_2_TEAMS:
            return 2

        if team_name in self.TIER_3_TEAMS:
            half = max(1, int(total_rounds * 0.50))
            return 3 if season_round <= half else 2

        if team_name in self.TIER_4_TEAMS:
            return 4

        return 3

    def _tier_baseline_modifier(
        self,
        team_name: str,
        season_round: int = 1,
        total_rounds: int = TOTAL_SEASON_ROUNDS
    ) -> float:
        tier = self._team_tier(team_name, season_round, total_rounds)

        if tier == 1:
            return self.TIER_1_BASE_BONUS

        if tier == 2:
            return self.TIER_2_BASE_BONUS

        if tier == 3:
            half = max(1, int(total_rounds * 0.50))
            if season_round <= half:
                return -self.TIER_3_FIRST_HALF_PENALTY

            progress_window = max(1, int(total_rounds * 0.25))
            progress = self._clamp(
                (season_round - half) / progress_window,
                0.0,
                1.0
            )

            penalty = (
                self.TIER_3_FIRST_HALF_PENALTY
                -
                (
                    self.TIER_3_FIRST_HALF_PENALTY
                    - self.TIER_3_SECOND_HALF_PENALTY
                ) * progress
            )

            return -penalty

        return -self.TIER_4_BASE_PENALTY

    def _tier_upset_bonus(
        self,
        team_name: str,
        season_round: int = 1,
        total_rounds: int = TOTAL_SEASON_ROUNDS
    ) -> float:
        tier = self._team_tier(team_name, season_round, total_rounds)

        return {
            1: 0.000,
            2: 0.018,
            3: 0.010,
            4: 0.006,
        }.get(tier, 0.008)

    # =========================================================
    # EXPECTED COMPETITIVE SCORE
    # =========================================================

    def _expected_competitive_score(
        self,
        entry: Dict[str, Any],
        profile: Dict[str, Any],
        weather: str
    ) -> float:

        car_score = self._calibrated_car_score(
            entry,
            profile
        )

        # Always use the coordinator's normalized driver score.
        # This keeps driver influence consistent across qualifying,
        # race pace and race-day extraction.
        driver_score = self._driver_score(
            entry.get("driver_performance"),
            entry.get("driver")
        )

        if weather in {"Mixed", "Wet"}:
            car_weight = 0.55
            driver_weight = 0.45
        else:
            car_weight = 0.70
            driver_weight = 0.30

        competitive_score = (
            car_score * car_weight
            +
            driver_score * driver_weight
        )

        team_name = str(
            entry.get(
                "team",
                ""
            )
        )

        tier = self._team_tier(
            team_name,
            profile.get("season_round", 1),
            profile.get(
                "total_rounds",
                self.TOTAL_SEASON_ROUNDS
            )
        )

        # Elite teams share one competitive window.  This is
        # convergence, not a win quota.
        if tier == 1:

            elite_reference = 0.82

            competitive_score = (
                competitive_score * 0.50
                +
                elite_reference * 0.50
            )

        elif tier == 2:

            competitive_score *= 0.990

        elif tier == 3:

            competitive_score *= 0.972

        elif tier == 4:

            competitive_score *= 0.950

        # Wet/mixed conditions increase the driver's ability to
        # overcome a small car deficit.
        if weather in {"Mixed", "Wet"}:

            wet_driver_bonus = (
                driver_score - 0.80
            ) * 0.25

            competitive_score += wet_driver_bonus

        return self._clamp(
            competitive_score,
            0.35,
            1.10
        )

    # =========================================================
    # CALIBRATED CAR SCORE
    # =========================================================

    def _calibrated_car_score(
        self,
        entry: Dict[str, Any],
        profile: Dict[str, Any]
    ) -> float:

        existing = self._performance_score(
            entry.get("car_performance"),
            0.80
        )

        team_name = str(
            entry.get(
                "team",
                ""
            )
        )

        features = self._team_features(
            team_name
        )

        demand = self.CIRCUIT_ARCHETYPES.get(
            profile.get(
                "archetype",
                "mixed"
            ),
            self.CIRCUIT_ARCHETYPES["mixed"]
        )

        feature_score = 0.50

        feature_score += (
            features["power"]
            * demand["power"]
            * 0.22
        )

        feature_score += (
            features["aero"]
            * demand["aero"]
            * 0.22
        )

        feature_score += (
            features["low_drag"]
            * demand["low_drag"]
            * 0.22
        )

        feature_score += (
            features["braking"]
            * demand["braking"]
            * 0.18
        )

        feature_score += (
            features["tyre"]
            * demand["tyre"]
            * 0.16
        )

        feature_score = self._clamp(
            feature_score,
            0.25,
            0.95
        )

        historical = profile.get(
            "historical_2025",
            {}
        )

        historical_score = historical.get(
            team_name,
            0.50
        )

        calibrated = (
            existing * 0.36
            +
            feature_score * 0.40
            +
            historical_score * 0.24
        )

        calibrated += self._tier_baseline_modifier(
            team_name,
            profile.get("season_round", 1),
            profile.get(
                "total_rounds",
                self.TOTAL_SEASON_ROUNDS
            )
        )

        if team_name in self.TOP_WIN_TEAMS:

            # Keep all four 2026 elite teams in the same general
            # car-performance window while retaining circuit fit.
            elite_reference = 0.82

            calibrated = (
                calibrated * 0.52
                +
                elite_reference * 0.48
            )

            archetype = profile.get(
                "archetype",
                "mixed"
            )

            circuit_bias = {

                "power": {
                    "Mercedes-AMG Petronas": 0.026,
                    "Scuderia Ferrari HP": 0.024,
                    "Oracle Red Bull Racing": 0.010,
                    "McLaren Mastercard": 0.008
                },

                "low_drag": {
                    "Mercedes-AMG Petronas": 0.028,
                    "Scuderia Ferrari HP": 0.024,
                    "Oracle Red Bull Racing": 0.018,
                    "McLaren Mastercard": 0.008
                },

                "technical": {
                    "Scuderia Ferrari HP": 0.026,
                    "McLaren Mastercard": 0.022,
                    "Oracle Red Bull Racing": 0.014,
                    "Mercedes-AMG Petronas": 0.012
                },

                "high_speed": {
                    "Oracle Red Bull Racing": 0.022,
                    "McLaren Mastercard": 0.021,
                    "Mercedes-AMG Petronas": 0.018,
                    "Scuderia Ferrari HP": 0.016
                },

                "mixed": {
                    "Oracle Red Bull Racing": 0.014,
                    "McLaren Mastercard": 0.014,
                    "Scuderia Ferrari HP": 0.014,
                    "Mercedes-AMG Petronas": 0.014
                }
            }

            calibrated += (
                circuit_bias
                .get(archetype, {})
                .get(team_name, 0.0)
            )

        return self._clamp(
            calibrated,
            0.25,
            1.10
        )

    # =========================================================
    # TEAM FEATURES
    # =========================================================

    def _team_features(
        self,
        team_name: str
    ) -> Dict[str, float]:

        if team_name in self.TEAM_FEATURES:
            return self.TEAM_FEATURES[
                team_name
            ]

        # Defensive aliases.

        aliases = {

            "Mercedes":
                "Mercedes-AMG Petronas",

            "Ferrari":
                "Scuderia Ferrari HP",

            "McLaren":
                "McLaren Mastercard",

            "Red Bull":
                "Oracle Red Bull Racing",

            "Williams":
                "Atlassian Williams",

            "Alpine":
                "BWT Alpine",

            "Haas":
                "TGR Haas",

            "Audi":
                "Audi Revolut F1 Team",

            "Aston Martin":
                "Aston Martin Aramco",

            "Cadillac":
                "Cadillac Formula 1",

            "RB":
                "Visa Cash App RB"
        }

        mapped = aliases.get(
            team_name
        )

        if mapped in self.TEAM_FEATURES:
            return self.TEAM_FEATURES[
                mapped
            ]

        return {

            "power": 0.0,
            "aero": 0.0,
            "low_drag": 0.0,
            "braking": 0.0,
            "tyre": 0.0,
            "wet": 0.0
        }

    # =========================================================
    # DRIVER SCORE
    # =========================================================

    def _driver_score(
        self,
        performance: Any,
        driver_name: str = None
    ) -> float:

        calibrated = (
            self.DRIVER_FEATURES.get(
                str(
                    driver_name or ""
                )
            )
        )

        if calibrated:

            return self._clamp(
                (
                    calibrated[
                        "qualifying"
                    ] * 0.18
                    +
                    calibrated[
                        "race_craft"
                    ] * 0.42
                    +
                    calibrated[
                        "tyre"
                    ] * 0.22
                    +
                    calibrated[
                        "wet"
                    ] * 0.10
                    +
                    calibrated[
                        "street"
                    ] * 0.08
                ),
                0.25,
                1.10
            )

        if isinstance(
            performance,
            dict
        ):

            race_pace = (
                self._component_value(
                    performance,
                    "race_pace",
                    75.0
                )
            )

            tyre = (
                self._component_value(
                    performance,
                    "tyre_management",
                    75.0
                )
            )

            consistency = (
                self._component_value(
                    performance,
                    "consistency",
                    75.0
                )
            )

            overtaking = (
                self._component_value(
                    performance,
                    "overtaking",
                    75.0
                )
            )

            return self._clamp(
                (
                    race_pace * 0.50
                    +
                    tyre * 0.15
                    +
                    consistency * 0.15
                    +
                    overtaking * 0.20
                )
                /
                100.0,
                0.25,
                1.10
            )

        return 0.75

    # =========================================================
    # QUALIFYING DRIVER SCORE
    # =========================================================

    def _driver_qualifying_score(
        self,
        performance: Any,
        driver_name: str = None
    ) -> float:

        calibrated = (
            self.DRIVER_FEATURES.get(
                str(
                    driver_name or ""
                )
            )
        )

        if calibrated:
            return calibrated[
                "qualifying"
            ]

        return self._clamp(
            self._component_value(
                performance,
                "qualifying",
                self._component_value(
                    performance,
                    "race_pace",
                    75.0
                )
            )
            /
            100.0,
            0.25,
            1.10
        )

    # =========================================================
    # WET DRIVER SCORE
    # =========================================================

    def _driver_wet_score(
        self,
        performance: Any,
        driver_name: str = None
    ) -> float:

        calibrated = (
            self.DRIVER_FEATURES.get(
                str(
                    driver_name or ""
                )
            )
        )

        if calibrated:
            return calibrated[
                "wet"
            ]

        return self._clamp(
            self._component_value(
                performance,
                "wet_weather",
                self._component_value(
                    performance,
                    "race_pace",
                    75.0
                )
            )
            /
            100.0,
            0.25,
            1.10
        )

    # =========================================================
    # DRIVER EXTRACTION
    # =========================================================

    def _driver_extraction_bonus(
        self,
        entry: Dict[str, Any],
        car_score: float,
        field_average: float,
        weather: str
    ) -> float:

        driver_name = entry.get(
            "driver"
        )

        driver_data = self.DRIVER_FEATURES.get(
            str(
                driver_name or ""
            )
        )

        if not driver_data:
            return 0.0

        if weather in {
            "Mixed",
            "Wet"
        }:

            skill = (
                driver_data[
                    "wet"
                ]
                *
                0.50
                +
                driver_data[
                    "race_craft"
                ]
                *
                0.35
                +
                driver_data[
                    "tyre"
                ]
                *
                0.15
            )

        else:

            skill = (
                driver_data[
                    "race_craft"
                ]
                *
                0.55
                +
                driver_data[
                    "tyre"
                ]
                *
                0.22
                +
                driver_data[
                    "qualifying"
                ]
                *
                0.23
            )

        deficit = max(
            0.0,
            field_average
            -
            car_score
        )

        # Elite drivers can recover part of a car deficit.
        bonus = (
            deficit
            *
            max(
                0.0,
                skill - 0.82
            )
            *
            2.85
        )

        return -self._clamp(
            bonus,
            0.0,
            0.40
        )

    # =========================================================
    # UPSET PROBABILITY
    # =========================================================

    def _upset_probability(
        self,
        score: float,
        field_average: float,
        profile: Dict[str, Any],
        weather: str
    ) -> float:

        relative = (
            score
            -
            field_average
        )

        if relative >= 0.08:
            probability = 0.028

        elif relative >= 0.03:
            probability = 0.055

        elif relative >= -0.03:
            probability = 0.085

        elif relative >= -0.10:
            probability = 0.095

        elif relative >= -0.18:
            probability = 0.075

        else:
            probability = 0.040

        # High SC tracks create more opportunity.
        probability += (
            profile.get(
                "sc",
                0.40
            )
            *
            0.055
        )

        # Wet races increase variance.
        if weather in {
            "Mixed",
            "Wet"
        }:

            probability += 0.045

        return self._clamp(
            probability,
            0.025,
            0.18
        )

    # =========================================================
    # RACE MISTAKE
    # =========================================================

    def _race_mistake_probability(
        self,
        entry: Dict[str, Any],
        weather: str
    ) -> float:

        driver = entry.get(
            "driver_performance",
            {}
        )

        consistency = (
            self._component_value(
                driver,
                "consistency",
                75.0
            )
        )

        reliability = (
            self._component_value(
                entry.get(
                    "car_performance",
                    {}
                ),
                "reliability",
                75.0
            )
        )

        risk = (
            0.022
            +
            max(
                0.0,
                75.0 - consistency
            )
            *
            0.00085
            +
            max(
                0.0,
                75.0 - reliability
            )
            *
            0.00055
        )

        if weather in {
            "Mixed",
            "Wet"
        }:

            risk *= 1.45

        return self._clamp(
            risk,
            0.015,
            0.095
        )

    # =========================================================
    # LAP CALIBRATION
    # =========================================================

    def _lap_calibration_adjustment(
        self,
        entry: Dict[str, Any],
        profile: Dict[str, Any],
        weather: str
    ) -> float:

        score = self._calibrated_car_score(
            entry,
            profile
        )

        team_name = str(
            entry.get(
                "team",
                ""
            )
        )

        tier = self._team_tier(
            team_name,
            profile.get("season_round", 1),
            profile.get(
                "total_rounds",
                self.TOTAL_SEASON_ROUNDS
            )
        )

        # Race-lap pace uses the same elite convergence as the
        # pre-race score. This prevents the simulator from
        # reintroducing a large McLaren/Red Bull advantage on
        # every individual lap.
        if tier == 1:
            score = (
                score * 0.55
                +
                0.82 * 0.45
            )

        adjustment = (
            0.80
            -
            score
        ) * 0.62

        if weather in {"Mixed", "Wet"}:

            features = self._team_features(
                team_name
            )

            wet_bonus = (
                features["wet"]
                *
                0.30
            )

            adjustment -= wet_bonus

        return adjustment

    # =========================================================
    # STRATEGY LAP ADJUSTMENT
    # =========================================================

    def _strategy_lap_adjustment(
        self,
        state: Dict[str, Any],
        compound: str,
        tyre_age: int,
        weather: str
    ) -> float:

        strategy = state.get(
            "strategy"
        )

        if not strategy:
            return 0.0

        strategy_type = (
            strategy.get(
                "strategy_type",
                ""
            )
        )

        adjustment = 0.0

        if strategy_type == "attack":
            adjustment -= 0.022

        elif strategy_type == "recovery":

            if compound == "Soft":
                adjustment -= 0.032

            elif compound == "Hard":
                adjustment += 0.008

        if (
            compound == "Soft"
            and
            tyre_age <= 3
        ):

            adjustment -= 0.012

        if compound == "Intermediate":

            if weather == "Mixed":
                adjustment -= 0.018

            elif weather == "Wet":
                adjustment += 0.032

        if compound == "Full Wet":

            if weather == "Wet":
                adjustment -= 0.025

            elif weather == "Mixed":
                adjustment += 0.042

        return adjustment

    # =========================================================
    # WEATHER STINTS
    # =========================================================

    def _apply_weather_profile_to_stints(
        self,
        race_laps: int,
        base_stints: List[Dict[str, Any]],
        weather_profile: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:

        if not base_stints:
            raise ValueError(
                "Base strategy produced no stints."
            )

        lap_compounds = []

        for lap in range(
            1,
            race_laps + 1
        ):

            weather = (
                weather_engine.weather_at_lap(
                    weather_profile,
                    lap
                )
            )

            base_compound = (
                self._compound_from_base_stints(
                    base_stints,
                    lap
                )
            )

            compound = (
                self._weather_compound(
                    weather,
                    base_compound
                )
            )

            lap_compounds.append(
                compound
            )

        stints = []

        start_lap = 1

        current_compound = (
            lap_compounds[0]
        )

        for lap in range(
            2,
            race_laps + 1
        ):

            compound = (
                lap_compounds[
                    lap - 1
                ]
            )

            if compound != current_compound:

                stints.append({

                    "stint":
                        len(stints) + 1,

                    "compound":
                        current_compound,

                    "laps":
                        lap - start_lap,

                    "start_lap":
                        start_lap,

                    "end_lap":
                        lap - 1
                })

                start_lap = lap

                current_compound = (
                    compound
                )

        stints.append({

            "stint":
                len(stints) + 1,

            "compound":
                current_compound,

            "laps":
                race_laps
                -
                start_lap
                +
                1,

            "start_lap":
                start_lap,

            "end_lap":
                race_laps
        })

        return stints

    def _compound_from_base_stints(
        self,
        stints: List[Dict[str, Any]],
        lap_number: int
    ) -> str:

        for stint in stints:

            start_lap = int(
                stint.get(
                    "start_lap",
                    1
                )
            )

            end_lap = int(
                stint.get(
                    "end_lap",
                    start_lap
                )
            )

            if (
                start_lap
                <=
                lap_number
                <=
                end_lap
            ):

                return str(
                    stint.get(
                        "compound",
                        "Medium"
                    )
                ).title()

        return str(
            stints[-1].get(
                "compound",
                "Medium"
            )
        ).title()

    def _weather_compound(
        self,
        weather: str,
        base_compound: str
    ) -> str:

        weather = str(
            weather or "Dry"
        ).title()

        if weather == "Wet":
            return "Full Wet"

        if weather == "Mixed":
            return "Intermediate"

        if base_compound in {
            "Soft",
            "Medium",
            "Hard"
        }:
            return base_compound

        return "Medium"

    # =========================================================
    # CURRENT STINT
    # =========================================================

    def _get_current_stint(
        self,
        state: Dict[str, Any],
        lap_number: int
    ) -> Dict[str, Any]:

        stints = state[
            "stints"
        ]

        if not stints:
            raise ValueError(
                "Driver has no generated tyre stints."
            )

        for index, stint in enumerate(
            stints
        ):

            start_lap = int(
                stint.get(
                    "start_lap",
                    1
                )
            )

            end_lap = int(
                stint.get(
                    "end_lap",
                    start_lap
                )
            )

            if (
                start_lap
                <=
                lap_number
                <=
                end_lap
            ):

                state[
                    "current_stint"
                ] = index

                return stint

        return stints[-1]

    # =========================================================
    # TYRE AGE
    # =========================================================

    def _get_tyre_age(
        self,
        stint: Dict[str, Any],
        lap_number: int
    ) -> int:

        return max(
            1,
            lap_number
            -
            int(
                stint.get(
                    "start_lap",
                    1
                )
            )
            +
            1
        )

    # =========================================================
    # PIT STOPS
    # =========================================================

    def _process_pit_stops(
        self,
        grid: List[Dict[str, Any]],
        race_states: Dict[int, Dict[str, Any]],
        lap_number: int,
        race_laps: int
    ) -> List[Dict[str, Any]]:

        events = []

        for entry in list(
            grid
        ):

            driver_id = entry[
                "driver_id"
            ]

            state = race_states[
                driver_id
            ]

            stints = state[
                "stints"
            ]

            if len(
                stints
            ) <= 1:
                continue

            for stint_index, stint in enumerate(
                stints[:-1]
            ):

                stint_end_lap = int(
                    stint.get(
                        "end_lap",
                        lap_number
                    )
                )

                if (
                    lap_number
                    !=
                    stint_end_lap
                ):
                    continue

                next_stint = stints[
                    stint_index + 1
                ]

                next_start = int(
                    next_stint.get(
                        "start_lap",
                        race_laps + 1
                    )
                )

                if next_start > race_laps:
                    continue

                expected_stops = (
                    stint_index + 1
                )

                if (
                    state[
                        "pit_stops"
                    ]
                    >=
                    expected_stops
                ):
                    continue

                state[
                    "pit_stops"
                ] += 1

                pit_time = float(
                    getattr(
                        self.race_simulator,
                        "PIT_STOP_TIME",
                        22.0
                    )
                )

                # Wet tyre changes have a slightly larger
                # operational loss.
                if (
                    stint[
                        "compound"
                    ]
                    !=
                    next_stint[
                        "compound"
                    ]
                    and
                    (
                        stint[
                            "compound"
                        ]
                        in {
                            "Intermediate",
                            "Full Wet"
                        }
                        or
                        next_stint[
                            "compound"
                        ]
                        in {
                            "Intermediate",
                            "Full Wet"
                        }
                    )
                ):

                    pit_time += 0.8

                entry[
                    "race_time"
                ] = (
                    entry.get(
                        "race_time",
                        0.0
                    )
                    +
                    pit_time
                )

                events.append({

                    "type":
                        "pit_stop",

                    "lap":
                        lap_number,

                    "driver":
                        entry[
                            "driver"
                        ],

                    "team":
                        entry[
                            "team"
                        ],

                    "from_compound":
                        stint[
                            "compound"
                        ],

                    "to_compound":
                        next_stint[
                            "compound"
                        ],

                    "pit_time":
                        round(
                            pit_time,
                            3
                        )
                })

        return events

    # =========================================================
    # OVERTAKES
    # =========================================================

    def _detect_overtakes(
        self,
        previous_order: List[int],
        previous_times: Dict[int, float],
        previous_gaps: Dict[int, float],
        current_grid: List[Dict[str, Any]],
        lap_times: Dict[int, float],
        circuit: Any,
        lap_number: int
    ) -> List[Dict[str, Any]]:

        events = []

        circuit_data = (
            self._extract_circuit(
                circuit
            )
        )

        difficulty = self._level(
            circuit_data.get(
                "overtaking_difficulty",
                "Medium"
            )
        )

        for new_position, entry in enumerate(
            current_grid,
            start=1
        ):

            driver_id = entry[
                "driver_id"
            ]

            if driver_id not in previous_order:
                continue

            old_position = (
                previous_order.index(
                    driver_id
                )
                +
                1
            )

            if (
                new_position
                >=
                old_position
            ):
                continue

            positions_gained = (
                old_position
                -
                new_position
            )

            if positions_gained > 2:
                continue

            if old_position <= 1:
                continue

            ahead_id = (
                previous_order[
                    old_position - 2
                ]
            )

            old_gap = previous_gaps.get(
                driver_id,
                99.0
            )

            if old_gap > 3.2:
                continue

            driver_lap_time = (
                lap_times.get(
                    driver_id,
                    99.0
                )
            )

            ahead_lap_time = (
                lap_times.get(
                    ahead_id,
                    99.0
                )
            )

            pace_gain = (
                ahead_lap_time
                -
                driver_lap_time
            )

            base_threshold = (
                1.90
                -
                (
                    difficulty
                    -
                    0.50
                )
                *
                0.90
            )

            pace_bonus = (
                max(
                    0.0,
                    pace_gain
                )
                *
                1.65
            )

            opportunity_threshold = (
                self._clamp(
                    base_threshold
                    +
                    pace_bonus,
                    0.30,
                    2.90
                )
            )

            if (
                old_gap
                >
                opportunity_threshold
            ):
                continue

            if pace_gain < 0.025:
                continue

            ahead_entry = None

            for candidate in current_grid:

                if (
                    candidate[
                        "driver_id"
                    ]
                    ==
                    ahead_id
                ):

                    ahead_entry = (
                        candidate
                    )

                    break

            if ahead_entry is None:
                continue

            events.append({

                "type":
                    "overtake",

                "lap":
                    lap_number,

                "driver":
                    entry[
                        "driver"
                    ],

                "team":
                    entry[
                        "team"
                    ],

                "overtaken_driver":
                    ahead_entry[
                        "driver"
                    ],

                "from_position":
                    old_position,

                "to_position":
                    new_position,

                "gap_before":
                    round(
                        old_gap,
                        3
                    ),

                "pace_advantage":
                    round(
                        pace_gain,
                        3
                    )
            })

        return events

    # =========================================================
    # GAP CALCULATION
    # =========================================================

    def _calculate_previous_gaps(
        self,
        grid: List[Dict[str, Any]]
    ) -> Dict[int, float]:

        gaps = {}

        if not grid:
            return gaps

        ordered = sorted(
            grid,
            key=lambda entry:
                entry.get(
                    "race_time",
                    0.0
                )
        )

        leader_time = (
            ordered[0].get(
                "race_time",
                0.0
            )
        )

        for index, entry in enumerate(
            ordered
        ):

            driver_id = entry[
                "driver_id"
            ]

            gaps[
                driver_id
            ] = round(
                entry.get(
                    "race_time",
                    0.0
                )
                -
                leader_time,
                3
            )

        return gaps

    # =========================================================
    # UPDATE GAPS
    # =========================================================

    def _update_gaps(
        self,
        grid: List[Dict[str, Any]]
    ) -> None:

        if not grid:
            return

        grid.sort(
            key=lambda entry:
                entry.get(
                    "race_time",
                    0.0
                )
        )

        leader_time = (
            grid[0].get(
                "race_time",
                0.0
            )
        )

        for position, entry in enumerate(
            grid,
            start=1
        ):

            entry[
                "position"
            ] = position

            entry[
                "gap_to_leader"
            ] = round(
                entry.get(
                    "race_time",
                    0.0
                )
                -
                leader_time,
                3
            )

            if position == 1:

                entry[
                    "gap_to_ahead"
                ] = 0.0

            else:

                ahead = grid[
                    position - 2
                ]

                entry[
                    "gap_to_ahead"
                ] = round(
                    entry.get(
                        "race_time",
                        0.0
                    )
                    -
                    ahead.get(
                        "race_time",
                        0.0
                    ),
                    3
                )

    # =========================================================
    # PERFORMANCE SCORE
    # =========================================================

    def _performance_score(
        self,
        performance: Any,
        default: float = 0.80
    ) -> float:

        if isinstance(
            performance,
            (int, float)
        ):

            value = float(
                performance
            )

            if value > 1.25:
                value /= 100.0

            return self._clamp(
                value,
                0.25,
                1.25
            )

        if not isinstance(
            performance,
            dict
        ):
            return default

        for key in (
            "score",
            "overall",
            "overall_score",
            "pace",
            "performance",
            "race_pace",
            "qualifying",
            "qualifying_score"
        ):

            value = performance.get(
                key
            )

            if isinstance(
                value,
                (int, float)
            ):

                value = float(
                    value
                )

                if value > 1.25:
                    value /= 100.0

                return self._clamp(
                    value,
                    0.25,
                    1.25
                )

        values = []

        for key in (
            "aero",
            "straight_line_speed",
            "cornering",
            "energy_efficiency",
            "tyre_management",
            "reliability"
        ):

            value = performance.get(
                key
            )

            if isinstance(
                value,
                (int, float)
            ):

                values.append(
                    float(value)
                )

        if values:

            average = (
                sum(values)
                /
                len(values)
            )

            if average > 1.25:
                average /= 100.0

            return self._clamp(
                average,
                0.25,
                1.25
            )

        return default

    # =========================================================
    # COMPONENT VALUE
    # =========================================================

    def _component_value(
        self,
        performance: Any,
        key: str,
        default: float = 75.0
    ) -> float:

        if not isinstance(
            performance,
            dict
        ):
            return default

        value = performance.get(
            key,
            default
        )

        try:
            return float(
                value
            )

        except (
            TypeError,
            ValueError
        ):

            return default

    # =========================================================
    # CIRCUIT PROFILE
    # =========================================================

    def _get_circuit_profile(
        self,
        circuit: Dict[str, Any]
    ) -> Dict[str, Any]:

        name = str(
            circuit.get(
                "name",
                ""
            )
        )

        if name in self.CIRCUIT_PROFILES:

            profile = dict(
                self.CIRCUIT_PROFILES[
                    name
                ]
            )

            profile[
                "historical_2025"
            ] = dict(
                profile.get(
                    "historical_2025",
                    {}
                )
            )

            return profile

        track_type = str(
            circuit.get(
                "track_type",
                "Mixed"
            )
        ).lower()

        if (
            "street"
            in track_type
            and
            "high"
            in track_type
        ):

            archetype = "high_speed"

        elif (
            "street"
            in track_type
        ):

            archetype = "street"

        elif (
            "power"
            in track_type
        ):

            archetype = "power"

        elif (
            "high speed"
            in track_type
        ):

            archetype = "high_speed"

        elif (
            "technical"
            in track_type
        ):

            archetype = "technical"

        else:

            archetype = "mixed"

        return {

            "archetype":
                archetype,

            "qualifying":
                self._qualifying_importance(
                    circuit
                ),

            "overtaking":
                self._level(
                    circuit.get(
                        "overtaking_difficulty",
                        "Medium"
                    )
                ),

            "sc":
                0.40,

            "rain":
                0.30,

            "historical_2025":
                {}
        }

    # =========================================================
    # QUALIFYING IMPORTANCE
    # =========================================================

    def _qualifying_importance(
        self,
        circuit: Dict[str, Any]
    ) -> float:

        level = str(
            circuit.get(
                "overtaking_difficulty",
                "Medium"
            )
        )

        mapping = {

            "Very Low": 0.55,
            "Low": 0.65,
            "Medium": 0.75,
            "High": 0.88,
            "Very High": 0.95,
            "Extreme": 0.99
        }

        return mapping.get(
            level,
            0.75
        )

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
    # LEVEL
    # =========================================================

    def _level(
        self,
        value: Any
    ) -> float:

        values = {

            "Very Low":
                0.25,

            "Low":
                0.50,

            "Medium":
                0.75,

            "High":
                1.00,

            "Very High":
                1.25,

            "Extreme":
                1.35
        }

        return values.get(
            str(value),
            0.75
        )

    # =========================================================
    # RACE FORM
    # =========================================================

    def _race_form_variation(
        self,
        driver_id: Any,
        lap_number: int
    ) -> float:

        try:

            driver_id = int(
                driver_id
            )

        except (
            TypeError,
            ValueError
        ):

            driver_id = 0

        phase = (
            driver_id
            *
            0.73
            +
            lap_number
            *
            0.41
        )

        return (
            sin(
                phase
            )
            *
            0.055
        )

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
                float(value),
                maximum
            )
        )

    # =========================================================
    # DEFAULT STRATEGY INPUTS
    # =========================================================

    def _default_strategy_inputs(
        self,
        weather: str
    ) -> Dict[str, Any]:

        return {

            "downforce":
                "Medium",

            "drag":
                "Medium",

            "tire_degradation":
                "Medium",

            "energy_efficiency":
                "Medium",

            "straight_line_speed":
                "Medium",

            "cornering":
                "Medium",

            "weather":
                weather
        }


# =============================================================
# SINGLE COORDINATOR INSTANCE
# =============================================================

from backend.services.strategy_engine import strategy_engine
from backend.simulation.race_simulator import race_simulator
from backend.simulation.race_grid import race_grid


race_coordinator = RaceCoordinator(
    strategy_engine,
    race_simulator,
    race_grid
)