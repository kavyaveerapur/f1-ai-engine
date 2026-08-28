from typing import Any, Dict, List


class RaceGrid:
    """
    F1 race grid and overtaking engine.

    Version 1.2 handles:
        - 22-car starting grid
        - Team/car performance
        - Driver performance
        - Race positions
        - Race gaps
        - Overtaking opportunities
        - Position changes
        - Race events

    The engine is deterministic for now.
    """

    # =====================================================
    # OVERTAKING SETTINGS
    # =====================================================

    OVERTAKE_GAP = 1.20

    OVERTAKE_MAX_GAP = 1.80

    CIRCUIT_OVERTAKING_FACTOR = {

        "Very Low": 0.55,

        "Low": 0.75,

        "Medium": 1.00,

        "High": 1.20,

        "Very High": 1.35
    }

    # =====================================================
    # CONSTRUCTOR
    # =====================================================

    def __init__(self):
        pass

    # =====================================================
    # BUILD GRID
    # =====================================================

    def build_grid(
        self,
        teams: List[Any]
    ) -> List[Dict[str, Any]]:

        entries = []

        for team in teams:

            drivers = getattr(
                team,
                "drivers",
                []
            )

            for driver in drivers:

                car_performance = getattr(
                    team,
                    "car_performance",
                    None
                )

                driver_performance = getattr(
                    driver,
                    "performance",
                    None
                )

                entries.append({

                    "team_id": team.id,

                    "team": team.name,

                    "driver_id": driver.id,

                    "driver": driver.name,

                    "car_performance":
                        self._car_performance(
                            car_performance
                        ),

                    "driver_performance":
                        self._driver_performance(
                            driver_performance
                        ),

                    "race_time": 0.0,

                    "position": None,

                    "grid_position": None,

                    "gap_to_leader": 0.0,

                    "gap_to_ahead": 0.0
                })

        return entries

    # =====================================================
    # CREATE STARTING GRID
    # =====================================================

    def create_starting_grid(
        self,
        teams: List[Any]
    ) -> List[Dict[str, Any]]:

        entries = self.build_grid(
            teams
        )

        for entry in entries:

            entry[
                "starting_performance"
            ] = self._starting_performance(
                entry
            )

        entries.sort(
            key=lambda entry:
                entry[
                    "starting_performance"
                ],
            reverse=True
        )

        for position, entry in enumerate(
            entries,
            start=1
        ):

            entry[
                "grid_position"
            ] = position

            entry[
                "position"
            ] = position

        self._calculate_gaps(
            entries
        )

        return entries

    # =====================================================
    # STARTING PERFORMANCE
    # =====================================================

    def _starting_performance(
        self,
        entry: Dict[str, Any]
    ) -> float:

        car = entry[
            "car_performance"
        ]

        driver = entry[
            "driver_performance"
        ]

        car_score = (

            car["aero"] * 0.20

            +

            car[
                "straight_line_speed"
            ] * 0.20

            +

            car["cornering"] * 0.20

            +

            car[
                "energy_efficiency"
            ] * 0.10

            +

            car[
                "tyre_management"
            ] * 0.10

            +

            car[
                "reliability"
            ] * 0.05
        )

        driver_score = (

            driver[
                "race_pace"
            ] * 0.10

            +

            driver[
                "consistency"
            ] * 0.05
        )

        return (
            car_score
            + driver_score
        )

    # =====================================================
    # UPDATE POSITIONS
    # =====================================================

    def update_positions(
        self,
        grid: List[Dict[str, Any]],
        lap_times: Dict[int, float]
    ) -> List[Dict[str, Any]]:

        for entry in grid:

            driver_id = entry[
                "driver_id"
            ]

            lap_time = lap_times.get(
                driver_id,
                0.0
            )

            entry[
                "race_time"
            ] = entry.get(
                "race_time",
                0.0
            ) + lap_time

        grid.sort(
            key=lambda entry:
                entry.get(
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

        self._calculate_gaps(
            grid
        )

        return grid

    # =====================================================
    # OVERTAKING
    # =====================================================

    def process_overtakes(
        self,
        grid: List[Dict[str, Any]],
        circuit: Any
    ) -> List[Dict[str, Any]]:

        events = []

        if len(grid) < 2:

            return events

        circuit_difficulty = getattr(
            circuit,
            "overtaking_difficulty",
            "Medium"
        )

        circuit_factor = (
            self.CIRCUIT_OVERTAKING_FACTOR.get(
                circuit_difficulty,
                1.00
            )
        )

        # -------------------------------------------------
        # Work from the back toward the front.
        #
        # This prevents one driver from making multiple
        # position jumps in a single processing pass.
        # -------------------------------------------------

        for index in range(
            len(grid) - 1,
            0,
            -1
        ):

            attacker = grid[
                index
            ]

            defender = grid[
                index - 1
            ]

            gap = (
                attacker.get(
                    "gap_to_ahead",
                    999.0
                )
            )

            if gap > self.OVERTAKE_MAX_GAP:

                continue

            if gap <= 0:

                continue

            attacker_car = attacker[
                "car_performance"
            ]

            attacker_driver = attacker[
                "driver_performance"
            ]

            defender_car = defender[
                "car_performance"
            ]

            # -------------------------------------------------
            # Straight-line advantage
            # -------------------------------------------------

            straight_line_advantage = (

                attacker_car[
                    "straight_line_speed"
                ]

                -

                defender_car[
                    "straight_line_speed"
                ]
            )

            # -------------------------------------------------
            # Driver overtaking skill
            # -------------------------------------------------

            overtaking_skill = (

                attacker_driver[
                    "overtaking"
                ] - 75.0
            )

            # -------------------------------------------------
            # Performance advantage
            # -------------------------------------------------

            performance_advantage = (

                straight_line_advantage
                * 0.025

                +

                overtaking_skill
                * 0.015
            )

            # -------------------------------------------------
            # Gap advantage
            #
            # Smaller gap = stronger opportunity.
            # -------------------------------------------------

            gap_advantage = (

                self.OVERTAKE_MAX_GAP
                - gap
            ) / self.OVERTAKE_MAX_GAP

            # -------------------------------------------------
            # Combined opportunity
            # -------------------------------------------------

            opportunity = (

                0.35

                +

                gap_advantage
                * 0.35

                +

                performance_advantage
                * 0.30
            )

            opportunity *= (
                circuit_factor
            )

            # Clamp to 0 - 1.
            opportunity = max(
                0.0,
                min(
                    opportunity,
                    1.0
                )
            )

            # -------------------------------------------------
            # Deterministic threshold
            #
            # We intentionally avoid random probability here.
            # Later versions can add controlled race variance.
            # -------------------------------------------------

            if opportunity < 0.70:

                continue

            old_position = attacker[
                "position"
            ]

            new_position = (
                old_position - 1
            )

            attacker[
                "position"
            ] = new_position

            defender[
                "position"
            ] = old_position

            # -------------------------------------------------
            # Swap grid order
            # -------------------------------------------------

            grid[
                index - 1
            ], grid[
                index
            ] = (

                attacker,
                defender
            )

            events.append({

                "type": "overtake",

                "attacker":
                    attacker[
                        "driver"
                    ],

                "attacker_team":
                    attacker[
                        "team"
                    ],

                "defender":
                    defender[
                        "driver"
                    ],

                "defender_team":
                    defender[
                        "team"
                    ],

                "from_position":
                    old_position,

                "to_position":
                    new_position,

                "gap_before":
                    round(
                        gap,
                        3
                    ),

                "opportunity":
                    round(
                        opportunity,
                        3
                    )
            })

        # -------------------------------------------------
        # Recalculate gaps after overtakes
        # -------------------------------------------------

        grid.sort(
            key=lambda entry:
                entry[
                    "position"
                ]
        )

        self._calculate_gaps(
            grid
        )

        return events

    # =====================================================
    # GAP CALCULATION
    # =====================================================

    def _calculate_gaps(
        self,
        grid: List[Dict[str, Any]]
    ) -> None:

        if not grid:

            return

        leader_time = grid[
            0
        ].get(
            "race_time",
            0.0
        )

        for index, entry in enumerate(
            grid
        ):

            current_time = entry.get(
                "race_time",
                0.0
            )

            entry[
                "gap_to_leader"
            ] = round(

                max(
                    0.0,
                    current_time
                    - leader_time
                ),

                3
            )

            if index == 0:

                entry[
                    "gap_to_ahead"
                ] = 0.0

            else:

                ahead_time = grid[
                    index - 1
                ].get(
                    "race_time",
                    0.0
                )

                entry[
                    "gap_to_ahead"
                ] = round(

                    max(
                        0.0,
                        current_time
                        - ahead_time
                    ),

                    3
                )

    # =====================================================
    # CAR PERFORMANCE
    # =====================================================

    def _car_performance(
        self,
        performance: Any
    ) -> Dict[str, float]:

        if performance is None:

            return {

                "aero": 75.0,

                "straight_line_speed": 75.0,

                "cornering": 75.0,

                "energy_efficiency": 75.0,

                "tyre_management": 75.0,

                "reliability": 75.0
            }

        return {

            "aero": float(
                performance.aero
            ),

            "straight_line_speed":
                float(
                    performance.straight_line_speed
                ),

            "cornering": float(
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

            "reliability": float(
                performance.reliability
            )
        }

    # =====================================================
    # DRIVER PERFORMANCE
    # =====================================================

    def _driver_performance(
        self,
        performance: Any
    ) -> Dict[str, float]:

        if performance is None:

            return {

                "race_pace": 75.0,

                "tyre_management": 75.0,

                "overtaking": 75.0,

                "consistency": 75.0
            }

        return {

            "race_pace": float(
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


# =========================================================
# SINGLE GRID INSTANCE
# =========================================================

race_grid = RaceGrid()