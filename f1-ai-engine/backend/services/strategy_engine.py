from typing import Any, Dict, List


class StrategyEngine:
    """
    F1 Deterministic Strategy Engine V1.5

    Evaluates:
        - Circuit characteristics
        - Car setup
        - Tyre degradation
        - Weather
        - Tyre compound suitability
        - Straight-line performance
        - Cornering performance
        - Energy efficiency
        - Overtaking difficulty
        - Pit-stop cost
        - Starting position
        - Car pace
        - Driver pace
        - Team characteristics

    Strategy selection is race-situation aware.

    Examples:

        Front runner:
            Medium -> Hard

        Midfield:
            Soft -> Hard
            Medium -> Hard
            Medium -> Soft

        Fast car starting near the back:
            Hard -> Soft
            Hard -> Medium -> Soft

        Aggressive recovery:
            Soft -> Medium -> Soft
            Medium -> Hard -> Soft

    Weather-aware:

        Dry:
            Soft / Medium / Hard

        Mixed:
            Slicks + Intermediate

        Wet:
            Intermediate / Full Wet
    """

    # =========================================================
    # LEVEL VALUES
    # =========================================================

    LEVEL_VALUES = {
        "Very Low": 0.25,
        "Low": 0.50,
        "Medium": 0.75,
        "High": 1.00,
        "Very High": 1.25
    }

    # =========================================================
    # TYRE LIFE
    # =========================================================

    TYRE_BASE_LIFE = {
        "soft": 18,
        "medium": 28,
        "hard": 38,
        "intermediate": 24,
        "wet": 20
    }

    # =========================================================
    # TYRE PACE
    # =========================================================

    TYRE_PACE = {
        "soft": 1.00,
        "medium": 0.94,
        "hard": 0.88,
        "intermediate": 0.86,
        "wet": 0.78
    }

    # =========================================================
    # COMPOUND NAMES
    # =========================================================

    COMPOUND_NAMES = {
        "soft": "Soft",
        "medium": "Medium",
        "hard": "Hard",
        "intermediate": "Intermediate",
        "wet": "Full Wet"
    }

    # =========================================================
    # WEATHER SUITABILITY
    # =========================================================

    WEATHER_SUITABILITY = {

        "Dry": {
            "soft": 1.00,
            "medium": 1.00,
            "hard": 1.00,
            "intermediate": 0.25,
            "wet": 0.10
        },

        "Mixed": {
            "soft": 0.72,
            "medium": 0.86,
            "hard": 0.76,
            "intermediate": 1.00,
            "wet": 0.72
        },

        "Wet": {
            "soft": 0.20,
            "medium": 0.25,
            "hard": 0.30,
            "intermediate": 1.00,
            "wet": 0.94
        }
    }

    # =========================================================
    # WEATHER PENALTIES
    # =========================================================

    WEATHER_PENALTIES = {

        "Dry": {
            "soft": 0.00,
            "medium": 0.00,
            "hard": 0.00,
            "intermediate": 0.08,
            "wet": 0.12
        },

        "Mixed": {
            "soft": 0.015,
            "medium": 0.010,
            "hard": 0.015,
            "intermediate": 0.00,
            "wet": 0.008
        },

        "Wet": {
            "soft": 0.10,
            "medium": 0.095,
            "hard": 0.09,
            "intermediate": 0.00,
            "wet": 0.006
        }
    }

    # =========================================================
    # TEAM PROFILES
    # =========================================================

    TEAM_PROFILES = {

        "Oracle Red Bull Racing": {
            "aggression": 0.90,
            "tyre_management": 0.88,
            "recovery": 0.92,
            "pit_confidence": 0.88
        },

        "McLaren Mastercard": {
            "aggression": 0.82,
            "tyre_management": 0.91,
            "recovery": 0.84,
            "pit_confidence": 0.90
        },

        "Scuderia Ferrari HP": {
            "aggression": 0.76,
            "tyre_management": 0.78,
            "recovery": 0.80,
            "pit_confidence": 0.76
        },

        "Mercedes-AMG Petronas": {
            "aggression": 0.72,
            "tyre_management": 0.84,
            "recovery": 0.80,
            "pit_confidence": 0.82
        },

        "Aston Martin Aramco": {
            "aggression": 0.65,
            "tyre_management": 0.77,
            "recovery": 0.76,
            "pit_confidence": 0.72
        },

        "Visa Cash App RB": {
            "aggression": 0.72,
            "tyre_management": 0.70,
            "recovery": 0.79,
            "pit_confidence": 0.70
        },

        "Audi Revolut F1 Team": {
            "aggression": 0.68,
            "tyre_management": 0.73,
            "recovery": 0.78,
            "pit_confidence": 0.69
        },

        "Atlassian Williams": {
            "aggression": 0.74,
            "tyre_management": 0.67,
            "recovery": 0.86,
            "pit_confidence": 0.73
        },

        "BWT Alpine": {
            "aggression": 0.70,
            "tyre_management": 0.69,
            "recovery": 0.80,
            "pit_confidence": 0.70
        },

        "TGR Haas": {
            "aggression": 0.78,
            "tyre_management": 0.64,
            "recovery": 0.82,
            "pit_confidence": 0.66
        },

        "Cadillac Formula 1": {
            "aggression": 0.75,
            "tyre_management": 0.63,
            "recovery": 0.85,
            "pit_confidence": 0.68
        }
    }

    # =========================================================
    # CONSTRUCTOR
    # =========================================================

    def __init__(self):
        pass

    # =========================================================
    # PUBLIC ANALYSIS
    # =========================================================

    def analyze(
        self,
        circuit: Any,
        inputs: Dict[str, Any],
        team_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:

        team_context = team_context or {}

        normalized = self._normalize_inputs(
            inputs
        )

        circuit_data = self._extract_circuit_data(
            circuit
        )

        race_context = self._build_race_context(
            circuit_data,
            normalized,
            team_context
        )

        candidates = self._generate_candidates(
            race_context
        )

        scored_candidates = []

        for candidate in candidates:

            scored = self._score_strategy(
                candidate,
                race_context
            )

            scored_candidates.append(
                scored
            )

        scored_candidates.sort(
            key=lambda strategy: strategy["score"],
            reverse=True
        )

        for index, strategy in enumerate(
            scored_candidates,
            start=1
        ):

            strategy["rank"] = index

            strategy["recommended"] = (
                index == 1
            )

        best_strategy = (
            scored_candidates[0]
            if scored_candidates
            else None
        )

        return {
            "success": True,

            "engine": (
                "F1 Deterministic Strategy Engine"
            ),

            "version": "1.5",

            "circuit": circuit_data,

            "race_context": race_context,

            "recommended_strategy": best_strategy,

            "candidate_strategies": scored_candidates
        }

    # =========================================================
    # INPUT NORMALIZATION
    # =========================================================

    def _normalize_inputs(
        self,
        inputs: Dict[str, Any]
    ) -> Dict[str, str]:

        allowed_levels = {
            "Very Low",
            "Low",
            "Medium",
            "High",
            "Very High"
        }

        allowed_weather = {
            "Dry",
            "Wet",
            "Mixed"
        }

        normalized = {}

        for key in (
            "downforce",
            "drag",
            "tyre_degradation",
            "energy_efficiency",
            "straight_line_speed",
            "cornering"
        ):

            value = inputs.get(
                key,
                "Medium"
            )

            if value not in allowed_levels:

                value = "Medium"

            normalized[key] = value

        weather = inputs.get(
            "weather",
            "Dry"
        )

        if weather not in allowed_weather:

            weather = "Dry"

        normalized["weather"] = weather

        return normalized

    # =========================================================
    # CIRCUIT EXTRACTION
    # =========================================================

    def _extract_circuit_data(
        self,
        circuit: Any
    ) -> Dict[str, Any]:

        if isinstance(
            circuit,
            dict
        ):

            return {
                "name": circuit.get(
                    "name",
                    "Unknown Circuit"
                ),
                "country": circuit.get(
                    "country",
                    "Unknown"
                ),
                "track_type": circuit.get(
                    "track_type",
                    "Mixed"
                ),
                "downforce_level": circuit.get(
                    "downforce_level",
                    "Medium"
                ),
                "tyre_stress": circuit.get(
                    "tyre_stress",
                    "Medium"
                ),
                "overtaking_difficulty": circuit.get(
                    "overtaking_difficulty",
                    "Medium"
                )
            }

        return {
            "name": getattr(
                circuit,
                "name",
                "Unknown Circuit"
            ),
            "country": getattr(
                circuit,
                "country",
                "Unknown"
            ),
            "track_type": getattr(
                circuit,
                "track_type",
                "Mixed"
            ),
            "downforce_level": getattr(
                circuit,
                "downforce_level",
                "Medium"
            ),
            "tyre_stress": getattr(
                circuit,
                "tyre_stress",
                "Medium"
            ),
            "overtaking_difficulty": getattr(
                circuit,
                "overtaking_difficulty",
                "Medium"
            )
        }

    # =========================================================
    # RACE CONTEXT
    # =========================================================

    def _build_race_context(
        self,
        circuit: Dict[str, Any],
        inputs: Dict[str, str],
        team_context: Dict[str, Any]
    ) -> Dict[str, Any]:

        weather = inputs[
            "weather"
        ]

        starting_position = self._safe_int(
            team_context.get(
                "starting_position",
                1
            ),
            1
        )

        grid_size = self._safe_int(
            team_context.get(
                "grid_size",
                22
            ),
            22
        )

        car_pace = self._safe_float(
            team_context.get(
                "car_pace",
                0.80
            ),
            0.80
        )

        driver_pace = self._safe_float(
            team_context.get(
                "driver_pace",
                0.80
            ),
            0.80
        )

        if car_pace > 1.50:
            car_pace /= 100.0

        if driver_pace > 1.50:
            driver_pace /= 100.0

        car_pace = self._clamp(
            car_pace,
            0.25,
            1.25
        )

        driver_pace = self._clamp(
            driver_pace,
            0.25,
            1.25
        )

        combined_pace = (
            car_pace * 0.70
            +
            driver_pace * 0.30
        )

        team_name = team_context.get(
            "team_name",
            "Generic Team"
        )

        team_profile = self.TEAM_PROFILES.get(
            team_name,
            {
                "aggression": 0.70,
                "tyre_management": 0.70,
                "recovery": 0.75,
                "pit_confidence": 0.70
            }
        )

        tyre_pressure = (
            self._level(
                circuit.get(
                    "tyre_stress"
                )
            )
        )

        aero_suitability = (
            self._calculate_aero_suitability(
                circuit,
                inputs
            )
        )

        straight_line_score = (
            self._level(
                inputs.get(
                    "straight_line_speed",
                    "Medium"
                )
            )
        )

        cornering_score = (
            self._level(
                inputs.get(
                    "cornering",
                    "Medium"
                )
            )
        )

        pit_stop_difficulty = (
            self._calculate_pit_difficulty(
                circuit
            )
        )

        overtaking_difficulty = (
            self._level(
                circuit.get(
                    "overtaking_difficulty"
                )
            )
        )

        front_running_factor = (
            max(
                0.0,
                (
                    grid_size
                    -
                    starting_position
                )
                /
                max(
                    grid_size - 1,
                    1
                )
            )
        )

        back_marker_factor = (
            1.0
            -
            front_running_factor
        )

        return {

            "weather": weather,

            "starting_position": starting_position,

            "grid_size": grid_size,

            "car_pace": car_pace,

            "driver_pace": driver_pace,

            "combined_pace": combined_pace,

            "team_name": team_name,

            "team_profile": team_profile,

            "tyre_pressure": tyre_pressure,

            "aero_suitability": aero_suitability,

            "straight_line_score": straight_line_score,

            "cornering_score": cornering_score,

            "pit_stop_difficulty": pit_stop_difficulty,

            "overtaking_difficulty": overtaking_difficulty,

            "front_running_factor": front_running_factor,

            "back_marker_factor": back_marker_factor,

            "circuit": circuit
        }

    # =========================================================
    # CANDIDATE GENERATION
    # =========================================================

    def _generate_candidates(
        self,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:

        weather = context[
            "weather"
        ]

        if weather == "Wet":

            return [

                self._strategy(
                    "Wet Conservative",
                    ["intermediate"],
                    [0.0],
                    1,
                    "conservative",
                    "Intermediate tyres provide stable wet-weather pace."
                ),

                self._strategy(
                    "Wet Flexible",
                    ["intermediate", "wet"],
                    [0.50, 0.50],
                    1,
                    "balanced",
                    "The strategy allows a transition toward heavier wet conditions."
                ),

                self._strategy(
                    "Wet Aggressive",
                    ["wet", "intermediate"],
                    [0.35, 0.65],
                    1,
                    "attack",
                    "The strategy prioritizes water evacuation before returning to intermediates."
                )
            ]

        if weather == "Mixed":

            return [

                self._strategy(
                    "Mixed Slick",
                    ["medium", "intermediate"],
                    [0.55, 0.45],
                    1,
                    "balanced",
                    "Medium tyres are used while the circuit remains sufficiently dry before switching to intermediates."
                ),

                self._strategy(
                    "Mixed Intermediate",
                    ["intermediate", "medium"],
                    [0.45, 0.55],
                    1,
                    "balanced",
                    "Intermediates protect against early rain before returning to slicks."
                ),

                self._strategy(
                    "Mixed Aggressive",
                    ["soft", "intermediate"],
                    [0.40, 0.60],
                    1,
                    "attack",
                    "Soft tyres maximize dry-track pace before the wet transition."
                )
            ]

        # =====================================================
        # DRY STRATEGIES
        # =====================================================

        return [

            self._strategy(
                "One-Stop Conservative",
                ["medium", "hard"],
                [0.48, 0.52],
                1,
                "conservative",
                "Medium tyres provide a balanced opening stint before the durable Hard compound."
            ),

            self._strategy(
                "One-Stop Balanced",
                ["soft", "hard"],
                [0.30, 0.70],
                1,
                "balanced",
                "Soft tyres create early pace before switching to Hard for race durability."
            ),

            self._strategy(
                "One-Stop Reverse",
                ["hard", "soft"],
                [0.65, 0.35],
                1,
                "recovery",
                "A long Hard opening stint creates flexibility before a late Soft attack."
            ),

            self._strategy(
                "One-Stop Medium Soft",
                ["medium", "soft"],
                [0.68, 0.32],
                1,
                "attack",
                "A durable Medium opening stint creates a late Soft pace advantage."
            ),

            self._strategy(
                "Two-Stop Balanced",
                ["soft", "medium", "soft"],
                [0.30, 0.40, 0.30],
                2,
                "balanced",
                "Two fresh Soft phases maximize pace while the Medium stint controls tyre degradation."
            ),

            self._strategy(
                "Two-Stop Aggressive",
                ["soft", "hard", "soft"],
                [0.25, 0.45, 0.30],
                2,
                "attack",
                "Fresh Soft tyres are used at both ends of the race for maximum attack."
            ),

            self._strategy(
                "Two-Stop Recovery",
                ["hard", "medium", "soft"],
                [0.42, 0.32, 0.26],
                2,
                "recovery",
                "A long Hard stint protects against early traffic before progressively faster compounds."
            ),

            self._strategy(
                "Two-Stop Reverse Attack",
                ["medium", "hard", "soft"],
                [0.35, 0.40, 0.25],
                2,
                "attack",
                "The strategy delays the final Soft attack until tyre performance matters most."
            )
        ]

    # =========================================================
    # STRATEGY FACTORY
    # =========================================================

    def _strategy(
        self,
        name: str,
        compounds: List[str],
        stint_distribution: List[float],
        stops: int,
        strategy_type: str,
        description: str
    ) -> Dict[str, Any]:

        return {

            "name": name,

            "compounds": compounds,

            "stint_distribution": stint_distribution,

            "stops": stops,

            "strategy_type": strategy_type,

            "description": description
        }

    # =========================================================
    # STRATEGY SCORING
    # =========================================================

    def _score_strategy(
        self,
        strategy: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:

        weather = context[
            "weather"
        ]

        compounds = strategy[
            "compounds"
        ]

        stops = strategy[
            "stops"
        ]

        starting_position = context[
            "starting_position"
        ]

        grid_size = context[
            "grid_size"
        ]

        car_pace = context[
            "car_pace"
        ]

        driver_pace = context[
            "driver_pace"
        ]

        combined_pace = context[
            "combined_pace"
        ]

        team_profile = context[
            "team_profile"
        ]

        tyre_pressure = context[
            "tyre_pressure"
        ]

        pit_difficulty = context[
            "pit_stop_difficulty"
        ]

        overtaking_difficulty = context[
            "overtaking_difficulty"
        ]

        # -----------------------------------------------------
        # Base strategy fit
        # -----------------------------------------------------

        pace_score = self._compound_pace_score(
            compounds
        )

        tyre_life_score = self._compound_life_score(
            compounds
        )

        weather_score = self._weather_score(
            compounds,
            weather
        )

        degradation_score = self._degradation_score(
            compounds,
            tyre_pressure
        )

        circuit_score = self._circuit_fit_score(
            compounds,
            context
        )

        # -----------------------------------------------------
        # Team characteristics
        # -----------------------------------------------------

        team_aggression = team_profile[
            "aggression"
        ]

        team_management = team_profile[
            "tyre_management"
        ]

        recovery_strength = team_profile[
            "recovery"
        ]

        pit_confidence = team_profile[
            "pit_confidence"
        ]

        # -----------------------------------------------------
        # Starting position
        # -----------------------------------------------------

        front_runner = (
            starting_position <= 5
        )

        midfield = (
            6 <= starting_position <= 14
        )

        deep_field = (
            starting_position >= 15
        )

        # -----------------------------------------------------
        # Track position value
        # -----------------------------------------------------

        if overtaking_difficulty >= 1.00:

            track_position_value = 1.00

        elif overtaking_difficulty >= 0.75:

            track_position_value = 0.80

        else:

            track_position_value = 0.55

        # -----------------------------------------------------
        # Position fit
        # -----------------------------------------------------

        position_fit = 0.0

        strategy_type = strategy[
            "strategy_type"
        ]

        if front_runner:

            if strategy_type == "conservative":

                position_fit += 0.20

            elif strategy_type == "balanced":

                position_fit += 0.12

            elif strategy_type == "attack":

                position_fit -= (
                    0.10
                    *
                    track_position_value
                )

            elif strategy_type == "recovery":

                position_fit -= 0.16

            if stops >= 2:

                position_fit -= (
                    0.08
                    *
                    track_position_value
                )

        elif midfield:

            if strategy_type == "balanced":

                position_fit += 0.10

            elif strategy_type == "attack":

                position_fit += (
                    0.07
                    *
                    team_aggression
                )

            elif strategy_type == "recovery":

                position_fit += (
                    0.05
                    *
                    recovery_strength
                )

        elif deep_field:

            if strategy_type == "recovery":

                position_fit += (
                    0.19
                    *
                    recovery_strength
                )

            elif strategy_type == "attack":

                position_fit += (
                    0.15
                    *
                    team_aggression
                )

            elif strategy_type == "conservative":

                position_fit -= 0.10

            # A fast car starting near the back has more to gain
            # from fresh tyres and strategic flexibility.
            if combined_pace >= 0.90:

                if stops >= 2:

                    position_fit += 0.11

                if "soft" in compounds:

                    position_fit += 0.07

        # -----------------------------------------------------
        # Pace advantage
        # -----------------------------------------------------

        pace_advantage = (
            combined_pace
            -
            0.80
        )

        if deep_field and pace_advantage > 0:

            position_fit += (
                pace_advantage
                *
                0.45
            )

        # -----------------------------------------------------
        # Overtaking circuit
        # -----------------------------------------------------

        if overtaking_difficulty <= 0.60:

            if deep_field and stops >= 2:

                position_fit += 0.06

        elif overtaking_difficulty >= 1.00:

            if front_runner and stops >= 2:

                position_fit -= 0.06

        # -----------------------------------------------------
        # Two-stop decision
        # -----------------------------------------------------

        stop_score = 0.0

        if stops == 1:

            stop_score += 0.07

            stop_score += (
                pit_difficulty
                *
                -0.04
            )

        else:

            # Two stops need a real reason to win.
            stop_score -= 0.06

            stop_score += (
                team_pit_confidence := (
                    pit_confidence
                    *
                    0.08
                )
            )

            stop_score += (
                team_aggression
                *
                0.05
            )

            if deep_field:

                stop_score += 0.09

            if combined_pace >= 0.92:

                stop_score += 0.08

            if tyre_pressure >= 1.00:

                stop_score += 0.06

            if overtaking_difficulty <= 0.60:

                stop_score += 0.05

            if overtaking_difficulty >= 1.00:

                stop_score -= 0.06

        # -----------------------------------------------------
        # Compound-specific strategic fit
        # -----------------------------------------------------

        compound_fit = 0.0

        if weather == "Dry":

            if "soft" in compounds:

                compound_fit += 0.03

            if "medium" in compounds:

                compound_fit += 0.04

            if "hard" in compounds:

                compound_fit += 0.02

        # Late Soft attack is particularly useful for recovery.
        if deep_field:

            if compounds[-1] == "soft":

                compound_fit += (
                    0.10
                    *
                    team_aggression
                )

        # Front runners benefit from durable closing stints.
        if front_runner:

            if compounds[-1] == "hard":

                compound_fit += 0.07

            if compounds[-1] == "soft":

                compound_fit -= 0.03

        # -----------------------------------------------------
        # Car/driver performance interaction
        # -----------------------------------------------------

        performance_fit = (
            combined_pace
            *
            0.15
        )

        if strategy_type == "attack":

            performance_fit += (
                combined_pace
                *
                team_aggression
                *
                0.08
            )

        if strategy_type == "recovery":

            performance_fit += (
                combined_pace
                *
                recovery_strength
                *
                0.07
            )

        # -----------------------------------------------------
        # Risk
        # -----------------------------------------------------

        risk = self._strategy_risk(
            strategy
        )

        risk_penalty = (
            self._risk_penalty(
                risk
            )
        )

        # Strong teams can tolerate risk better.
        risk_penalty *= (
            1.0
            -
            (
                team_aggression
                *
                0.18
            )
        )

        # -----------------------------------------------------
        # Final score
        # -----------------------------------------------------

        raw_score = (

            pace_score
            * 0.20

            +

            tyre_life_score
            * 0.12

            +

            weather_score
            * 0.20

            +

            degradation_score
            * 0.12

            +

            circuit_score
            * 0.10

            +

            position_fit
            * 0.16

            +

            stop_score
            * 0.08

            +

            compound_fit
            * 0.06

            +

            performance_fit
            * 0.08

            -

            risk_penalty
        )

        # -----------------------------------------------------
        # Normalize into dashboard-friendly score.
        # -----------------------------------------------------

        score = self._clamp(
            raw_score * 100.0,
            0.0,
            100.0
        )

        reasoning = self._build_reasoning(
            strategy,
            context,
            score / 100.0
        )

        result = dict(
            strategy
        )

        result["score"] = round(
            score,
            2
        )

        result["risk"] = risk

        result["reasoning"] = reasoning

        result["starting_position"] = (
            starting_position
        )

        result["team_name"] = (
            context["team_name"]
        )

        result["car_pace"] = round(
            car_pace,
            3
        )

        result["driver_pace"] = round(
            driver_pace,
            3
        )

        result["strategy_fit"] = round(
            self._clamp(
                raw_score,
                0.0,
                1.0
            ),
            3
        )

        return result

    # =========================================================
    # COMPOUND PACE
    # =========================================================

    def _compound_pace_score(
        self,
        compounds: List[str]
    ) -> float:

        values = []

        for compound in compounds:

            values.append(
                self.TYRE_PACE.get(
                    compound,
                    0.80
                )
            )

        if not values:

            return 0.80

        return sum(
            values
        ) / len(values)

    # =========================================================
    # TYRE LIFE
    # =========================================================

    def _compound_life_score(
        self,
        compounds: List[str]
    ) -> float:

        values = []

        for compound in compounds:

            life = (
                self.TYRE_BASE_LIFE.get(
                    compound,
                    25
                )
            )

            values.append(
                min(
                    life / 38.0,
                    1.0
                )
            )

        if not values:

            return 0.70

        return sum(
            values
        ) / len(values)

    # =========================================================
    # WEATHER SCORE
    # =========================================================

    def _weather_score(
        self,
        compounds: List[str],
        weather: str
    ) -> float:

        values = []

        suitability = (
            self.WEATHER_SUITABILITY.get(
                weather,
                self.WEATHER_SUITABILITY["Dry"]
            )
        )

        for compound in compounds:

            values.append(
                suitability.get(
                    compound,
                    0.50
                )
            )

        if not values:

            return 0.50

        return sum(
            values
        ) / len(values)

    # =========================================================
    # DEGRADATION SCORE
    # =========================================================

    def _degradation_score(
        self,
        compounds: List[str],
        tyre_pressure: float
    ) -> float:

        life_score = (
            self._compound_life_score(
                compounds
            )
        )

        pressure_effect = (
            tyre_pressure
            -
            0.75
        )

        if pressure_effect > 0:

            life_score += (
                pressure_effect
                *
                0.12
            )

        return self._clamp(
            life_score,
            0.0,
            1.0
        )

    # =========================================================
    # CIRCUIT FIT
    # =========================================================

    def _circuit_fit_score(
        self,
        compounds: List[str],
        context: Dict[str, Any]
    ) -> float:

        circuit = context[
            "circuit"
        ]

        track_type = str(
            circuit.get(
                "track_type",
                "Mixed"
            )
        )

        score = 0.75

        if track_type in {
            "Power",
            "High Speed",
            "Street High Speed"
        }:

            if "soft" in compounds:

                score += 0.05

            if "medium" in compounds:

                score += 0.03

        elif track_type in {
            "Technical",
            "Street Technical",
            "Street"
        }:

            if "medium" in compounds:

                score += 0.04

            if "hard" in compounds:

                score += 0.02

        if (
            context[
                "aero_suitability"
            ]
            >= 0.90
        ):

            score += 0.04

        return self._clamp(
            score,
            0.0,
            1.0
        )

    # =========================================================
    # AERO SUITABILITY
    # =========================================================

    def _calculate_aero_suitability(
        self,
        circuit: Dict[str, Any],
        inputs: Dict[str, str]
    ) -> float:

        circuit_level = (
            self._level(
                circuit.get(
                    "downforce_level"
                )
            )
        )

        setup_level = (
            self._level(
                inputs.get(
                    "downforce",
                    "Medium"
                )
            )
        )

        difference = abs(
            circuit_level
            -
            setup_level
        )

        return self._clamp(
            1.0
            -
            (
                difference
                *
                0.55
            ),
            0.50,
            1.0
        )

    # =========================================================
    # PIT STOP DIFFICULTY
    # =========================================================

    def _calculate_pit_difficulty(
        self,
        circuit: Dict[str, Any]
    ) -> float:

        overtaking = self._level(
            circuit.get(
                "overtaking_difficulty"
            )
        )

        return self._clamp(
            (
                0.50
                +
                (
                    overtaking
                    *
                    0.45
                )
            ),
            0.50,
            1.10
        )

    # =========================================================
    # STRATEGY RISK
    # =========================================================

    def _strategy_risk(
        self,
        strategy: Dict[str, Any]
    ) -> str:

        stops = strategy[
            "stops"
        ]

        strategy_type = strategy[
            "strategy_type"
        ]

        if stops >= 2:

            if strategy_type == "attack":

                return "High"

            return "Medium"

        if strategy_type == "attack":

            return "Medium"

        if strategy_type == "recovery":

            return "Medium"

        return "Low"

    # =========================================================
    # REASONING
    # =========================================================

    def _build_reasoning(
        self,
        strategy: Dict[str, Any],
        context: Dict[str, Any],
        strategy_fit: float
    ) -> List[str]:

        reasons = []

        weather = context[
            "weather"
        ]

        starting_position = context.get(
            "starting_position",
            1
        )

        team_name = context.get(
            "team_name",
            "Generic Team"
        )

        combined_pace = context.get(
            "combined_pace",
            0.80
        )

        overtaking_difficulty = context.get(
            "overtaking_difficulty",
            0.75
        )

        # -----------------------------------------------------
        # Weather
        # -----------------------------------------------------

        if weather == "Wet":

            reasons.append(
                "Wet conditions make Intermediate and Full Wet "
                "tyres the primary strategic choices."
            )

        elif weather == "Mixed":

            reasons.append(
                "Mixed conditions increase the importance of "
                "timing the transition between slick and wet tyres."
            )

        else:

            reasons.append(
                "Dry conditions allow the strategy to balance "
                "pace, tyre life and pit timing."
            )

        # -----------------------------------------------------
        # Starting position
        # -----------------------------------------------------

        if starting_position <= 5:

            reasons.append(
                f"{team_name} starts near the front, so track "
                "position is highly valuable."
            )

        elif starting_position >= 15:

            reasons.append(
                f"{team_name} starts deep in the field, so the "
                "strategy can accept more risk to recover positions."
            )

        else:

            reasons.append(
                f"{team_name} starts in the midfield, where tyre "
                "timing and traffic management are important."
            )

        # -----------------------------------------------------
        # Pace
        # -----------------------------------------------------

        if combined_pace >= 0.92:

            reasons.append(
                "Strong underlying car and driver pace makes "
                "aggressive recovery strategies more viable."
            )

        elif combined_pace <= 0.72:

            reasons.append(
                "Lower underlying pace makes tyre efficiency and "
                "track position more important than pure aggression."
            )

        # -----------------------------------------------------
        # Overtaking
        # -----------------------------------------------------

        if overtaking_difficulty >= 1.00:

            reasons.append(
                "Overtaking is difficult, increasing the value of "
                "track position and reducing the appeal of unnecessary stops."
            )

        elif overtaking_difficulty <= 0.60:

            reasons.append(
                "Overtaking is relatively achievable, making fresher "
                "tyres and additional strategic attacks more viable."
            )

        # -----------------------------------------------------
        # Strategy type
        # -----------------------------------------------------

        if strategy.get(
            "strategy_type"
        ) == "recovery":

            reasons.append(
                "The strategy is designed to recover positions through "
                "tyre flexibility and late-race pace."
            )

        elif strategy.get(
            "strategy_type"
        ) == "attack":

            reasons.append(
                "The strategy accepts additional risk to create "
                "overtaking opportunities with fresher tyres."
            )

        elif strategy.get(
            "strategy_type"
        ) == "conservative":

            reasons.append(
                "The strategy prioritizes tyre life, track position "
                "and reduced execution risk."
            )

        else:

            reasons.append(
                "The strategy balances race pace, tyre life and "
                "pit-stop exposure."
            )

        # -----------------------------------------------------
        # Stops
        # -----------------------------------------------------

        if strategy[
            "stops"
        ] == 1:

            reasons.append(
                "A one-stop plan minimizes pit-lane time and "
                "execution exposure."
            )

        else:

            reasons.append(
                "A two-stop plan accepts additional pit time in "
                "exchange for fresher tyres and stronger late-race pace."
            )

        # -----------------------------------------------------
        # Fit
        # -----------------------------------------------------

        if strategy_fit >= 0.85:

            reasons.append(
                "The strategy has strong overall compatibility "
                "with the current race conditions."
            )

        elif strategy_fit >= 0.70:

            reasons.append(
                "The strategy provides a balanced compromise "
                "between pace, tyre life and execution risk."
            )

        else:

            reasons.append(
                "The strategy has weaker overall compatibility "
                "under the current conditions."
            )

        return reasons

    # =========================================================
    # SAFE FLOAT
    # =========================================================

    def _safe_float(
        self,
        value: Any,
        default: float
    ) -> float:

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
    # SAFE INT
    # =========================================================

    def _safe_int(
        self,
        value: Any,
        default: int
    ) -> int:

        try:

            return int(
                value
            )

        except (
            TypeError,
            ValueError
        ):

            return default

    # =========================================================
    # LEVEL
    # =========================================================

    def _level(
        self,
        value: Any
    ) -> float:

        if value is None:

            return self.LEVEL_VALUES[
                "Medium"
            ]

        return self.LEVEL_VALUES.get(
            str(value),
            self.LEVEL_VALUES[
                "Medium"
            ]
        )

    # =========================================================
    # RISK PENALTY
    # =========================================================

    def _risk_penalty(
        self,
        risk: str
    ) -> float:

        penalties = {

            "Low": 0.005,

            "Medium": 0.015,

            "High": 0.030
        }

        return penalties.get(
            risk,
            0.015
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


# =============================================================
# SINGLE ENGINE INSTANCE
# =============================================================

strategy_engine = StrategyEngine()