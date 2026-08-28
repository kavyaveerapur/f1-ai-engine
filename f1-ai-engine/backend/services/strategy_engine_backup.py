from typing import Any, Dict, List


class StrategyEngine:
    """
    Deterministic F1 race strategy engine.

    The engine evaluates:
        - Circuit characteristics
        - Car setup
        - Tyre degradation
        - Weather
        - Straight-line performance
        - Cornering performance
        - Energy efficiency
        - Overtaking difficulty
        - Pit-stop cost
        - Strategy risk

    The engine is intentionally independent from Flask so it can later
    be reused by:

        - Flask REST APIs
        - Race simulations
        - AI/LLM explanation layer
        - Strategy comparison
        - Upgrade simulations
        - Driver/team performance models
    """

    # =========================================================
    # BASE VALUES
    # =========================================================

    LEVEL_VALUES = {
        "Very Low": 0.25,
        "Low": 0.50,
        "Medium": 0.75,
        "High": 1.00,
        "Very High": 1.25
    }

    WEATHER_MULTIPLIERS = {
        "Dry": {
            "soft": 1.00,
            "medium": 1.00,
            "hard": 1.00
        },

        "Mixed": {
            "soft": 0.92,
            "medium": 1.00,
            "hard": 0.96
        },

        # NOTE:
        # Wet tyre logic is intentionally left for the next update.
        # This currently preserves the existing slick-compound model.
        "Wet": {
            "soft": 0.55,
            "medium": 0.70,
            "hard": 0.78
        }
    }

    TYRE_BASE_LIFE = {
        "soft": 18,
        "medium": 28,
        "hard": 38
    }

    TYRE_PACE = {
        "soft": 1.00,
        "medium": 0.94,
        "hard": 0.88
    }

    COMPOUND_NAMES = {
        "soft": "Soft",
        "medium": "Medium",
        "hard": "Hard"
    }

    # =========================================================
    # CONSTRUCTOR
    # =========================================================

    def __init__(self):
        pass

    # =========================================================
    # PUBLIC METHOD
    # =========================================================

    def analyze(
        self,
        circuit: Any,
        inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze race conditions and return the best strategy
        along with all candidate strategies.
        """

        normalized = self._normalize_inputs(inputs)

        circuit_data = self._extract_circuit_data(circuit)

        race_context = self._build_race_context(
            circuit_data,
            normalized
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

            scored_candidates.append(scored)

        # Highest score first
        scored_candidates.sort(
            key=lambda strategy: strategy["score"],
            reverse=True
        )

        # Add ranking after sorting
        for index, strategy in enumerate(
            scored_candidates,
            start=1
        ):
            strategy["rank"] = index

        best_strategy = (
            scored_candidates[0]
            if scored_candidates
            else None
        )

        # Mark recommendation explicitly.
        if best_strategy:
            best_strategy["recommended"] = True

        for strategy in scored_candidates:
            if strategy is not best_strategy:
                strategy["recommended"] = False

        return {
            "success": True,
            "engine": "F1 Deterministic Strategy Engine",
            "version": "1.1",

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

        def normalize_level(
            value: Any,
            default: str = "Medium"
        ) -> str:

            if value is None:
                return default

            value = str(value).strip()

            if value not in allowed_levels:
                return default

            return value

        weather = str(
            inputs.get(
                "weather",
                "Dry"
            )
        ).strip()

        if weather not in allowed_weather:
            weather = "Dry"

        return {
            "downforce": normalize_level(
                inputs.get("downforce")
            ),

            "drag": normalize_level(
                inputs.get("drag")
            ),

            "tire_degradation": normalize_level(
                inputs.get("tire_degradation")
            ),

            "energy_efficiency": normalize_level(
                inputs.get("energy_efficiency")
            ),

            "straight_line_speed": normalize_level(
                inputs.get("straight_line_speed")
            ),

            "cornering": normalize_level(
                inputs.get("cornering")
            ),

            "weather": weather
        }

    # =========================================================
    # CIRCUIT DATA
    # =========================================================

    def _extract_circuit_data(
        self,
        circuit: Any
    ) -> Dict[str, Any]:

        if circuit is None:

            return {
                "name": "Unknown Circuit",
                "country": "Unknown",
                "track_type": "Mixed",
                "downforce_level": "Medium",
                "tyre_stress": "Medium",
                "overtaking_difficulty": "Medium"
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
        inputs: Dict[str, str]
    ) -> Dict[str, Any]:

        circuit_downforce = self._level(
            circuit["downforce_level"]
        )

        tyre_stress = self._level(
            circuit["tyre_stress"]
        )

        overtaking_difficulty = self._level(
            circuit["overtaking_difficulty"]
        )

        setup_downforce = self._level(
            inputs["downforce"]
        )

        setup_drag = self._level(
            inputs["drag"]
        )

        energy_efficiency = self._level(
            inputs["energy_efficiency"]
        )

        straight_line_speed = self._level(
            inputs["straight_line_speed"]
        )

        cornering = self._level(
            inputs["cornering"]
        )

        tire_degradation = self._level(
            inputs["tire_degradation"]
        )

        weather = inputs["weather"]

        aero_suitability = self._calculate_aero_suitability(
            circuit_downforce,
            setup_downforce
        )

        straight_line_score = self._calculate_straight_line_score(
            setup_drag,
            straight_line_speed
        )

        cornering_score = self._calculate_cornering_score(
            circuit_downforce,
            setup_downforce,
            cornering
        )

        tyre_pressure = self._calculate_tyre_pressure(
            tyre_stress,
            tire_degradation
        )

        energy_score = self._calculate_energy_score(
            energy_efficiency,
            setup_drag
        )

        overtaking_score = self._calculate_overtaking_score(
            overtaking_difficulty,
            straight_line_score
        )

        # Overall circuit/setup compatibility.
        setup_balance = self._calculate_setup_balance(
            aero_suitability,
            straight_line_score,
            cornering_score,
            energy_score
        )

        # Determines how valuable tyre life is at this circuit.
        tyre_strategy_pressure = self._calculate_strategy_pressure(
            tyre_pressure,
            tyre_stress
        )

        # Pit stops become more expensive strategically when:
        # - overtaking is difficult
        # - tyre stress is low
        #
        # If overtaking is difficult, losing track position is harder
        # to recover from.
        pit_stop_difficulty = self._calculate_pit_stop_difficulty(
            overtaking_difficulty,
            tyre_stress
        )

        return {
            "weather": weather,

            "circuit_downforce": round(
                circuit_downforce,
                3
            ),

            "tyre_stress": round(
                tyre_stress,
                3
            ),

            "overtaking_difficulty": round(
                overtaking_difficulty,
                3
            ),

            "aero_suitability": round(
                aero_suitability,
                3
            ),

            "straight_line_score": round(
                straight_line_score,
                3
            ),

            "cornering_score": round(
                cornering_score,
                3
            ),

            "tyre_pressure": round(
                tyre_pressure,
                3
            ),

            "energy_score": round(
                energy_score,
                3
            ),

            "overtaking_score": round(
                overtaking_score,
                3
            ),

            "setup_balance": round(
                setup_balance,
                3
            ),

            "tyre_strategy_pressure": round(
                tyre_strategy_pressure,
                3
            ),

            "pit_stop_difficulty": round(
                pit_stop_difficulty,
                3
            )
        }

    # =========================================================
    # PERFORMANCE CALCULATIONS
    # =========================================================

    def _calculate_aero_suitability(
        self,
        circuit_downforce: float,
        setup_downforce: float
    ) -> float:

        difference = abs(
            circuit_downforce -
            setup_downforce
        )

        score = 1.0 - (
            difference * 0.75
        )

        return self._clamp(
            score,
            0.25,
            1.0
        )

    # ---------------------------------------------------------

    def _calculate_straight_line_score(
        self,
        drag: float,
        straight_line_speed: float
    ) -> float:

        drag_penalty = (
            drag * 0.35
        )

        speed_score = (
            straight_line_speed * 0.75
        )

        score = (
            speed_score +
            (1.0 - drag_penalty)
        ) / 2

        return self._clamp(
            score,
            0.25,
            1.0
        )

    # ---------------------------------------------------------

    def _calculate_cornering_score(
        self,
        circuit_downforce: float,
        setup_downforce: float,
        cornering: float
    ) -> float:

        aero_match = (
            1.0 -
            abs(
                circuit_downforce -
                setup_downforce
            ) * 0.5
        )

        score = (
            aero_match * 0.55
            +
            cornering * 0.45
        )

        return self._clamp(
            score,
            0.25,
            1.0
        )

    # ---------------------------------------------------------

    def _calculate_tyre_pressure(
        self,
        tyre_stress: float,
        tire_degradation: float
    ) -> float:

        combined = (
            tyre_stress * 0.65
            +
            tire_degradation * 0.35
        )

        return self._clamp(
            combined,
            0.25,
            1.25
        )

    # ---------------------------------------------------------

    def _calculate_energy_score(
        self,
        energy_efficiency: float,
        drag: float
    ) -> float:

        efficiency_bonus = (
            energy_efficiency * 0.7
        )

        drag_penalty = (
            drag * 0.25
        )

        score = (
            efficiency_bonus +
            (1.0 - drag_penalty)
        ) / 2

        return self._clamp(
            score,
            0.25,
            1.0
        )

    # ---------------------------------------------------------

    def _calculate_overtaking_score(
        self,
        overtaking_difficulty: float,
        straight_line_score: float
    ) -> float:

        difficulty_factor = (
            1.25 -
            overtaking_difficulty
        )

        score = (
            straight_line_score * 0.7
            +
            difficulty_factor * 0.3
        )

        return self._clamp(
            score,
            0.25,
            1.0
        )

    # ---------------------------------------------------------

    def _calculate_setup_balance(
        self,
        aero_score: float,
        straight_line_score: float,
        cornering_score: float,
        energy_score: float
    ) -> float:

        score = (
            aero_score * 0.30
            +
            straight_line_score * 0.25
            +
            cornering_score * 0.30
            +
            energy_score * 0.15
        )

        return self._clamp(
            score,
            0.25,
            1.0
        )

    # ---------------------------------------------------------

    def _calculate_strategy_pressure(
        self,
        tyre_pressure: float,
        tyre_stress: float
    ) -> float:

        score = (
            tyre_pressure * 0.65
            +
            tyre_stress * 0.35
        )

        return self._clamp(
            score,
            0.25,
            1.25
        )

    # ---------------------------------------------------------

    def _calculate_pit_stop_difficulty(
        self,
        overtaking_difficulty: float,
        tyre_stress: float
    ) -> float:

        # Difficult overtaking means track position is more valuable.
        position_loss = overtaking_difficulty * 0.70

        # Low tyre stress means there is less benefit from stopping.
        tyre_need = (
            1.25 -
            tyre_stress
        ) * 0.30

        score = (
            position_loss +
            tyre_need
        )

        return self._clamp(
            score,
            0.25,
            1.25
        )

    # =========================================================
    # STRATEGY GENERATION
    # =========================================================

    def _generate_candidates(
        self,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:

        weather = context["weather"]

        candidates = [

            {
                "name": "One-Stop Conservative",
                "stops": 1,
                "compounds": [
                    "medium",
                    "hard"
                ],
                "risk": "Low"
            },

            {
                "name": "One-Stop Balanced",
                "stops": 1,
                "compounds": [
                    "soft",
                    "hard"
                ],
                "risk": "Medium"
            },

            {
                "name": "Two-Stop Aggressive",
                "stops": 2,
                "compounds": [
                    "soft",
                    "medium",
                    "soft"
                ],
                "risk": "High"
            },

            {
                "name": "Two-Stop Balanced",
                "stops": 2,
                "compounds": [
                    "medium",
                    "medium",
                    "soft"
                ],
                "risk": "Medium"
            }
        ]

        # -----------------------------------------------------
        # Weather candidates
        #
        # NOTE:
        # The Wet tyre model is intentionally NOT fixed here yet.
        # We will introduce Intermediates and Full Wets as a
        # dedicated weather-strategy update.
        # -----------------------------------------------------

        if weather == "Wet":

            candidates.append(
                {
                    "name": "Wet-Weather Conservative",
                    "stops": 1,
                    "compounds": [
                        "hard",
                        "hard"
                    ],
                    "risk": "Low"
                }
            )

        elif weather == "Mixed":

            candidates.append(
                {
                    "name": "Mixed-Weather Adaptive",
                    "stops": 2,
                    "compounds": [
                        "medium",
                        "hard",
                        "medium"
                    ],
                    "risk": "Medium"
                }
            )

        return candidates

    # =========================================================
    # STRATEGY SCORING
    # =========================================================

    def _score_strategy(
        self,
        strategy: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:

        compounds = strategy["compounds"]

        weather = context["weather"]

        tyre_pressure = context["tyre_pressure"]

        aero_score = context[
            "aero_suitability"
        ]

        straight_line_score = context[
            "straight_line_score"
        ]

        cornering_score = context[
            "cornering_score"
        ]

        energy_score = context[
            "energy_score"
        ]

        overtaking_score = context[
            "overtaking_score"
        ]

        setup_balance = context[
            "setup_balance"
        ]

        tyre_strategy_pressure = context[
            "tyre_strategy_pressure"
        ]

        pit_stop_difficulty = context[
            "pit_stop_difficulty"
        ]

        # -----------------------------------------------------
        # Tyre calculations
        # -----------------------------------------------------

        pace_score = 0.0

        tyre_score = 0.0

        weather_score = 0.0

        tyre_life_score = 0.0

        for compound in compounds:

            pace_score += self.TYRE_PACE[
                compound
            ]

            base_life = self.TYRE_BASE_LIFE[
                compound
            ]

            degradation_factor = (
                1.0 -
                (
                    tyre_pressure *
                    0.18
                )
            )

            tyre_life = (
                base_life *
                degradation_factor
            )

            tyre_score += (
                tyre_life / 40
            )

            tyre_life_score += self._clamp(
                tyre_life / 40,
                0.0,
                1.0
            )

            weather_score += (
                self.WEATHER_MULTIPLIERS[
                    weather
                ][compound]
            )

        compound_count = len(
            compounds
        )

        pace_score /= compound_count

        tyre_score /= compound_count

        weather_score /= compound_count

        tyre_life_score /= compound_count

        # -----------------------------------------------------
        # Strategy-specific fit
        # -----------------------------------------------------

        strategy_fit = self._calculate_strategy_fit(
            strategy,
            tyre_strategy_pressure,
            tyre_life_score,
            pit_stop_difficulty,
            setup_balance,
            overtaking_score
        )

        # -----------------------------------------------------
        # Pit-stop penalty
        # -----------------------------------------------------

        pit_penalty = self._calculate_pit_penalty(
            strategy["stops"],
            pit_stop_difficulty
        )

        # -----------------------------------------------------
        # Risk penalty
        # -----------------------------------------------------

        risk_penalty = self._risk_penalty(
            strategy["risk"]
        )

        # -----------------------------------------------------
        # Overall score
        # -----------------------------------------------------

        overall_score = (

            pace_score * 0.18

            +

            tyre_score * 0.18

            +

            weather_score * 0.14

            +

            aero_score * 0.10

            +

            straight_line_score * 0.08

            +

            cornering_score * 0.08

            +

            energy_score * 0.06

            +

            overtaking_score * 0.05

            +

            setup_balance * 0.05

            +

            strategy_fit * 0.08

            -

            pit_penalty

            -

            risk_penalty
        )

        overall_score = self._clamp(
            overall_score,
            0.0,
            1.0
        )

        return {
            "name": strategy["name"],

            "stops": strategy["stops"],

            "compounds": [
                self.COMPOUND_NAMES[
                    compound
                ]
                for compound in compounds
            ],

            "risk": strategy["risk"],

            "score": round(
                overall_score * 100,
                2
            ),

            "components": {
                "pace": round(
                    pace_score * 100,
                    2
                ),

                "tyre_management": round(
                    tyre_score * 100,
                    2
                ),

                "weather_adaptation": round(
                    weather_score * 100,
                    2
                ),

                "aero": round(
                    aero_score * 100,
                    2
                ),

                "straight_line": round(
                    straight_line_score * 100,
                    2
                ),

                "cornering": round(
                    cornering_score * 100,
                    2
                ),

                "energy": round(
                    energy_score * 100,
                    2
                ),

                "overtaking": round(
                    overtaking_score * 100,
                    2
                ),

                "setup_balance": round(
                    setup_balance * 100,
                    2
                ),

                "strategy_fit": round(
                    strategy_fit * 100,
                    2
                )
            },

            "strategy_metrics": {
                "tyre_life": round(
                    tyre_life_score * 100,
                    2
                ),

                "pit_stop_penalty": round(
                    pit_penalty * 100,
                    2
                ),

                "risk_penalty": round(
                    risk_penalty * 100,
                    2
                )
            },

            "reasoning": self._build_reasoning(
                strategy,
                context,
                strategy_fit
            )
        }

    # =========================================================
    # STRATEGY FIT
    # =========================================================

    def _calculate_strategy_fit(
        self,
        strategy: Dict[str, Any],
        tyre_strategy_pressure: float,
        tyre_life_score: float,
        pit_stop_difficulty: float,
        setup_balance: float,
        overtaking_score: float
    ) -> float:

        stops = strategy["stops"]

        # -----------------------------------------------------
        # Tyre pressure
        # -----------------------------------------------------

        if tyre_strategy_pressure >= 0.95:

            # High degradation favors strategies that can
            # refresh tyres more frequently.
            if stops >= 2:
                tyre_strategy_score = 1.00
            else:
                tyre_strategy_score = 0.82

        elif tyre_strategy_pressure >= 0.75:

            if stops == 1:
                tyre_strategy_score = 0.95
            else:
                tyre_strategy_score = 0.88

        else:

            # Low degradation favors fewer stops.
            if stops == 1:
                tyre_strategy_score = 1.00
            else:
                tyre_strategy_score = 0.78

        # -----------------------------------------------------
        # Pit-stop environment
        # -----------------------------------------------------

        if pit_stop_difficulty >= 0.90:

            # When track position is valuable, fewer stops are
            # generally more attractive.
            if stops == 1:
                pit_strategy_score = 1.00
            else:
                pit_strategy_score = 0.76

        else:

            # When overtaking is easier, extra stops are easier
            # to recover from.
            if stops == 2:
                pit_strategy_score = 0.95
            else:
                pit_strategy_score = 0.90

        # -----------------------------------------------------
        # Combine
        # -----------------------------------------------------

        score = (

            tyre_strategy_score * 0.35

            +

            tyre_life_score * 0.20

            +

            pit_strategy_score * 0.20

            +

            setup_balance * 0.15

            +

            overtaking_score * 0.10
        )

        return self._clamp(
            score,
            0.25,
            1.0
        )

    # =========================================================
    # PIT STOP PENALTY
    # =========================================================

    def _calculate_pit_penalty(
        self,
        stops: int,
        pit_stop_difficulty: float
    ) -> float:

        # Base cost per stop.
        base_cost = 0.025

        # Additional strategic cost when track position matters.
        position_cost = (
            pit_stop_difficulty *
            0.012
        )

        penalty = (
            stops *
            (
                base_cost +
                position_cost
            )
        )

        return self._clamp(
            penalty,
            0.0,
            0.12
        )

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

        # -----------------------------------------------------
        # Tyre degradation
        # -----------------------------------------------------

        if context["tyre_pressure"] >= 0.95:

            reasons.append(
                "Tyre degradation pressure is high, "
                "making tyre life a major strategic factor."
            )

        elif context["tyre_pressure"] >= 0.75:

            reasons.append(
                "Tyre degradation is moderate, "
                "so the strategy must balance pace and tyre life."
            )

        else:

            reasons.append(
                "Tyre degradation pressure is manageable, "
                "allowing greater flexibility in compound selection."
            )

        # -----------------------------------------------------
        # Aero
        # -----------------------------------------------------

        if context["aero_suitability"] >= 0.85:

            reasons.append(
                "The selected aerodynamic setup is well matched "
                "to the circuit's downforce requirement."
            )

        else:

            reasons.append(
                "The aerodynamic setup has some mismatch with "
                "the circuit characteristics."
            )

        # -----------------------------------------------------
        # Straight-line performance
        # -----------------------------------------------------

        if context["straight_line_score"] >= 0.75:

            reasons.append(
                "Strong straight-line performance should provide "
                "useful opportunities for defending or overtaking."
            )

        else:

            reasons.append(
                "Straight-line performance is less favorable, "
                "increasing the importance of track position."
            )

        # -----------------------------------------------------
        # Cornering
        # -----------------------------------------------------

        if context["cornering_score"] >= 0.75:

            reasons.append(
                "Cornering performance is favorable for "
                "technical and high-downforce sections."
            )

        else:

            reasons.append(
                "Cornering performance is not optimal for "
                "the circuit's technical sections."
            )

        # -----------------------------------------------------
        # Pit stops
        # -----------------------------------------------------

        if context["pit_stop_difficulty"] >= 0.90:

            reasons.append(
                "Pit stops carry a higher strategic cost because "
                "track position is difficult to recover."
            )

        else:

            reasons.append(
                "The circuit environment makes additional pit stops "
                "more recoverable through race pace."
            )

        # -----------------------------------------------------
        # Strategy type
        # -----------------------------------------------------

        if strategy["stops"] == 1:

            reasons.append(
                "A one-stop strategy reduces pit-lane time "
                "and generally lowers execution risk."
            )

        else:

            reasons.append(
                "The two-stop strategy accepts additional pit time "
                "in exchange for fresher tyre performance."
            )

        # -----------------------------------------------------
        # Weather
        # -----------------------------------------------------

        if context["weather"] == "Wet":

            reasons.append(
                "Wet conditions increase the importance of "
                "weather-adaptive tyre decisions."
            )

        elif context["weather"] == "Mixed":

            reasons.append(
                "Mixed conditions increase the value of "
                "an adaptive strategy."
            )

        else:

            reasons.append(
                "Dry conditions allow the strategy to focus "
                "primarily on pace, tyre life and pit timing."
            )

        # -----------------------------------------------------
        # Strategy fit
        # -----------------------------------------------------

        if strategy_fit >= 0.85:

            reasons.append(
                "The strategy has strong overall compatibility "
                "with the current circuit and setup."
            )

        elif strategy_fit >= 0.70:

            reasons.append(
                "The strategy provides a balanced compromise "
                "between pace, tyre life and execution risk."
            )

        else:

            reasons.append(
                "The strategy has weaker overall fit under "
                "the current race conditions."
            )

        return reasons

    # =========================================================
    # UTILITIES
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

    # ---------------------------------------------------------

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

    # ---------------------------------------------------------

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

strategy_engine = StrategyEngine()