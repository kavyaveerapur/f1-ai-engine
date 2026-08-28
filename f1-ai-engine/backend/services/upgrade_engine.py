from typing import Any, Dict

from backend.extensions import db
from backend.models import (
    CarPerformance,
    Team,
    TeamDevelopment,
    Upgrade
)


class UpgradeEngine:
    """
    F1 Team Development / Upgrade Engine.

    Resources:

        Budget
        Research Points
        Development Points

    Upgrade categories:

        Aero
        Power Unit
        Chassis
        Tyres
        Reliability

    Every completed upgrade:

        1. Checks the team.
        2. Checks TeamDevelopment.
        3. Checks budget.
        4. Checks research points.
        5. Checks development points.
        6. Applies the performance gains.
        7. Increases the relevant development level.
        8. Deducts the required resources.
        9. Saves the upgrade history.
    """

    # =========================================================
    # PERFORMANCE LIMITS
    # =========================================================

    MIN_PERFORMANCE = 50.0

    MAX_PERFORMANCE = 100.0

    # =========================================================
    # RESOURCE COSTS
    # =========================================================

    BASE_RESEARCH_COST = 20.0

    BASE_DEVELOPMENT_COST = 25.0

    # =========================================================
    # UPGRADE DEFINITIONS
    # =========================================================

    UPGRADE_DEFINITIONS = {

        "Aero": {

            "name":
                "Aerodynamic Development",

            "base_cost":
                100,

            "aero_gain":
                2.00,

            "straight_line_gain":
                0.00,

            "cornering_gain":
                1.25,

            "energy_gain":
                0.00,

            "tyre_management_gain":
                0.00,

            "reliability_gain":
                0.00
        },

        "Power Unit": {

            "name":
                "Power Unit Development",

            "base_cost":
                120,

            "aero_gain":
                0.00,

            "straight_line_gain":
                1.75,

            "cornering_gain":
                0.00,

            "energy_gain":
                1.25,

            "tyre_management_gain":
                0.00,

            "reliability_gain":
                0.15
        },

        "Chassis": {

            "name":
                "Chassis Development",

            "base_cost":
                110,

            "aero_gain":
                0.50,

            "straight_line_gain":
                0.25,

            "cornering_gain":
                1.75,

            "energy_gain":
                0.00,

            "tyre_management_gain":
                0.75,

            "reliability_gain":
                0.00
        },

        "Tyres": {

            "name":
                "Tyre Management Development",

            "base_cost":
                90,

            "aero_gain":
                0.00,

            "straight_line_gain":
                0.00,

            "cornering_gain":
                0.25,

            "energy_gain":
                0.00,

            "tyre_management_gain":
                2.25,

            "reliability_gain":
                0.00
        },

        "Reliability": {

            "name":
                "Reliability Development",

            "base_cost":
                80,

            "aero_gain":
                0.00,

            "straight_line_gain":
                0.00,

            "cornering_gain":
                0.00,

            "energy_gain":
                0.25,

            "tyre_management_gain":
                0.25,

            "reliability_gain":
                2.50
        }
    }

    # =========================================================
    # CONSTRUCTOR
    # =========================================================

    def __init__(self):

        pass

    # =========================================================
    # DEVELOP UPGRADE
    # =========================================================

    def develop_upgrade(
        self,
        team_id: int,
        category: str
    ) -> Dict[str, Any]:

        category = self._normalize_category(
            category
        )

        definition = (
            self.UPGRADE_DEFINITIONS.get(
                category
            )
        )

        if definition is None:

            raise ValueError(
                "Invalid upgrade category. "
                "Choose from: "
                +
                ", ".join(
                    self.UPGRADE_DEFINITIONS.keys()
                )
            )

        # -----------------------------------------------------
        # Team
        # -----------------------------------------------------

        team = Team.query.get(
            team_id
        )

        if team is None:

            raise ValueError(
                f"Team {team_id} does not exist."
            )

        # -----------------------------------------------------
        # Development record
        # -----------------------------------------------------

        development = (
            TeamDevelopment.query
            .filter_by(
                team_id=team_id
            )
            .first()
        )

        if development is None:

            development = TeamDevelopment(

                team_id=team_id,

                budget=1000.0,

                research_points=100.0,

                development_points=100.0
            )

            db.session.add(
                development
            )

            db.session.flush()

        # -----------------------------------------------------
        # Existing upgrade
        # -----------------------------------------------------

        existing_upgrade = (
            Upgrade.query
            .filter_by(
                team_id=team_id,
                category=category
            )
            .first()
        )

        if existing_upgrade:

            current_level = (
                existing_upgrade.level
            )

        else:

            current_level = 0

        next_level = (
            current_level + 1
        )

        # -----------------------------------------------------
        # Calculate costs.
        # -----------------------------------------------------

        budget_cost = (
            self._calculate_cost(
                definition[
                    "base_cost"
                ],
                next_level
            )
        )

        research_cost = (
            self._calculate_research_cost(
                next_level
            )
        )

        development_cost = (
            self._calculate_development_cost(
                next_level
            )
        )

        # -----------------------------------------------------
        # Resource check.
        # -----------------------------------------------------

        if development.budget < budget_cost:

            raise ValueError(
                f"{team.name} does not have enough budget. "
                f"Required: {budget_cost}, "
                f"Available: "
                f"{development.budget:.1f}"
            )

        if (
            development.research_points
            <
            research_cost
        ):

            raise ValueError(
                f"{team.name} does not have enough "
                "research points. "
                f"Required: {research_cost}, "
                f"Available: "
                f"{development.research_points:.1f}"
            )

        if (
            development.development_points
            <
            development_cost
        ):

            raise ValueError(
                f"{team.name} does not have enough "
                "development points. "
                f"Required: {development_cost}, "
                f"Available: "
                f"{development.development_points:.1f}"
            )

        # -----------------------------------------------------
        # Car performance.
        # -----------------------------------------------------

        performance = (
            CarPerformance.query
            .filter_by(
                team_id=team_id
            )
            .first()
        )

        if performance is None:

            performance = CarPerformance(
                team_id=team_id
            )

            db.session.add(
                performance
            )

            db.session.flush()

        # -----------------------------------------------------
        # Make sure the upgrade is not useless.
        #
        # If every affected performance category has already
        # reached 100, don't spend resources.
        # -----------------------------------------------------

        if not self._upgrade_can_improve(
            performance,
            definition
        ):

            raise ValueError(
                f"{team.name}'s {category} performance "
                "is already at its development limit."
            )

        # -----------------------------------------------------
        # Apply performance.
        # -----------------------------------------------------

        before_performance = (
            performance.to_dict()
        )

        self._apply_performance_gain(
            performance,
            definition
        )

        after_performance = (
            performance.to_dict()
        )

        # -----------------------------------------------------
        # Update upgrade record.
        # -----------------------------------------------------

        if existing_upgrade:

            upgrade = (
                existing_upgrade
            )

            upgrade.level = (
                next_level
            )

            upgrade.cost = (
                budget_cost
            )

            upgrade.name = (
                definition[
                    "name"
                ]
            )

        else:

            upgrade = Upgrade(

                team_id=team_id,

                category=category,

                name=definition[
                    "name"
                ],

                level=next_level,

                cost=budget_cost,

                aero_gain=0.0,

                straight_line_gain=0.0,

                cornering_gain=0.0,

                energy_gain=0.0,

                tyre_management_gain=0.0,

                reliability_gain=0.0
            )

            db.session.add(
                upgrade
            )

        # -----------------------------------------------------
        # Accumulate upgrade effects.
        # -----------------------------------------------------

        upgrade.aero_gain = (
            upgrade.aero_gain
            +
            definition[
                "aero_gain"
            ]
        )

        upgrade.straight_line_gain = (
            upgrade.straight_line_gain
            +
            definition[
                "straight_line_gain"
            ]
        )

        upgrade.cornering_gain = (
            upgrade.cornering_gain
            +
            definition[
                "cornering_gain"
            ]
        )

        upgrade.energy_gain = (
            upgrade.energy_gain
            +
            definition[
                "energy_gain"
            ]
        )

        upgrade.tyre_management_gain = (
            upgrade.tyre_management_gain
            +
            definition[
                "tyre_management_gain"
            ]
        )

        upgrade.reliability_gain = (
            upgrade.reliability_gain
            +
            definition[
                "reliability_gain"
            ]
        )

        # -----------------------------------------------------
        # Update development category level.
        # -----------------------------------------------------

        self._set_development_level(
            development,
            category,
            next_level
        )

        # -----------------------------------------------------
        # Deduct resources.
        # -----------------------------------------------------

        development.budget = (
            round(
                development.budget
                -
                budget_cost,
                2
            )
        )

        development.research_points = (
            round(
                development.research_points
                -
                research_cost,
                2
            )
        )

        development.development_points = (
            round(
                development.development_points
                -
                development_cost,
                2
            )
        )

        db.session.commit()

        # -----------------------------------------------------
        # Result
        # -----------------------------------------------------

        return {

            "success":
                True,

            "team":
                team.name,

            "team_id":
                team.id,

            "upgrade":
                upgrade.to_dict(),

            "performance_before":
                before_performance,

            "performance_after":
                after_performance,

            "development":
                development.to_dict(),

            "cost": {

                "budget":
                    budget_cost,

                "research_points":
                    research_cost,

                "development_points":
                    development_cost
            },

            "message":
                (
                    f"{team.name} completed "
                    f"{definition['name']} "
                    f"Level {next_level}."
                )
        }

    # =========================================================
    # APPLY PERFORMANCE GAIN
    # =========================================================

    def _apply_performance_gain(
        self,
        performance: CarPerformance,
        definition: Dict[str, float]
    ) -> None:

        performance.aero = (
            self._clamp(
                performance.aero
                +
                definition[
                    "aero_gain"
                ]
            )
        )

        performance.straight_line_speed = (
            self._clamp(
                performance.straight_line_speed
                +
                definition[
                    "straight_line_gain"
                ]
            )
        )

        performance.cornering = (
            self._clamp(
                performance.cornering
                +
                definition[
                    "cornering_gain"
                ]
            )
        )

        performance.energy_efficiency = (
            self._clamp(
                performance.energy_efficiency
                +
                definition[
                    "energy_gain"
                ]
            )
        )

        performance.tyre_management = (
            self._clamp(
                performance.tyre_management
                +
                definition[
                    "tyre_management_gain"
                ]
            )
        )

        performance.reliability = (
            self._clamp(
                performance.reliability
                +
                definition[
                    "reliability_gain"
                ]
            )
        )

    # =========================================================
    # UPGRADE IMPROVEMENT CHECK
    # =========================================================

    def _upgrade_can_improve(
        self,
        performance: CarPerformance,
        definition: Dict[str, float]
    ) -> bool:

        affected_fields = (

            (
                "aero",
                definition[
                    "aero_gain"
                ]
            ),

            (
                "straight_line_speed",
                definition[
                    "straight_line_gain"
                ]
            ),

            (
                "cornering",
                definition[
                    "cornering_gain"
                ]
            ),

            (
                "energy_efficiency",
                definition[
                    "energy_gain"
                ]
            ),

            (
                "tyre_management",
                definition[
                    "tyre_management_gain"
                ]
            ),

            (
                "reliability",
                definition[
                    "reliability_gain"
                ]
            )
        )

        for field, gain in affected_fields:

            if gain <= 0:

                continue

            current_value = getattr(
                performance,
                field
            )

            if current_value < (
                self.MAX_PERFORMANCE
            ):

                return True

        return False

    # =========================================================
    # DEVELOPMENT LEVEL
    # =========================================================

    def _set_development_level(
        self,
        development: TeamDevelopment,
        category: str,
        level: int
    ) -> None:

        if category == "Aero":

            development.aero_level = (
                level
            )

        elif category == "Power Unit":

            development.power_unit_level = (
                level
            )

        elif category == "Chassis":

            development.chassis_level = (
                level
            )

        elif category == "Tyres":

            development.tyre_level = (
                level
            )

        elif category == "Reliability":

            development.reliability_level = (
                level
            )

    # =========================================================
    # TEAM DEVELOPMENT
    # =========================================================

    def get_team_development(
        self,
        team_id: int
    ) -> Dict[str, Any]:

        team = Team.query.get(
            team_id
        )

        if team is None:

            raise ValueError(
                f"Team {team_id} does not exist."
            )

        performance = (
            CarPerformance.query
            .filter_by(
                team_id=team_id
            )
            .first()
        )

        development = (
            TeamDevelopment.query
            .filter_by(
                team_id=team_id
            )
            .first()
        )

        upgrades = (
            Upgrade.query
            .filter_by(
                team_id=team_id
            )
            .order_by(
                Upgrade.id
            )
            .all()
        )

        return {

            "success":
                True,

            "team_id":
                team.id,

            "team":
                team.name,

            "performance":
                (
                    performance.to_dict()
                    if performance
                    else None
                ),

            "development":
                (
                    development.to_dict()
                    if development
                    else None
                ),

            "upgrades":
                [
                    upgrade.to_dict()
                    for upgrade in upgrades
                ]
        }

    # =========================================================
    # ALL TEAM DEVELOPMENT
    # =========================================================

    def get_all_development(
        self
    ) -> list:

        teams = (
            Team.query
            .order_by(
                Team.id
            )
            .all()
        )

        return [

            self.get_team_development(
                team.id
            )

            for team in teams
        ]

    # =========================================================
    # AVAILABLE UPGRADES
    # =========================================================

    def get_available_upgrades(
        self
    ) -> Dict[str, Any]:

        upgrades = []

        for category, definition in (
            self.UPGRADE_DEFINITIONS.items()
        ):

            upgrades.append({

                "category":
                    category,

                "name":
                    definition[
                        "name"
                    ],

                "base_cost":
                    definition[
                        "base_cost"
                    ],

                "research_cost":
                    self.BASE_RESEARCH_COST,

                "development_cost":
                    self.BASE_DEVELOPMENT_COST,

                "effects": {

                    "aero":
                        definition[
                            "aero_gain"
                        ],

                    "straight_line_speed":
                        definition[
                            "straight_line_gain"
                        ],

                    "cornering":
                        definition[
                            "cornering_gain"
                        ],

                    "energy_efficiency":
                        definition[
                            "energy_gain"
                        ],

                    "tyre_management":
                        definition[
                            "tyre_management_gain"
                        ],

                    "reliability":
                        definition[
                            "reliability_gain"
                        ]
                }
            })

        return {

            "success":
                True,

            "upgrades":
                upgrades
        }

    # =========================================================
    # COST CALCULATION
    # =========================================================

    def _calculate_cost(
        self,
        base_cost: int,
        level: int
    ) -> int:

        multiplier = (
            1.0
            +
            (
                max(
                    0,
                    level - 1
                )
                *
                0.35
            )
        )

        return int(
            round(
                base_cost
                *
                multiplier
            )
        )

    # =========================================================
    # RESEARCH COST
    # =========================================================

    def _calculate_research_cost(
        self,
        level: int
    ) -> float:

        return round(
            self.BASE_RESEARCH_COST
            *
            (
                1.0
                +
                (
                    max(
                        0,
                        level - 1
                    )
                    *
                    0.25
                )
            ),
            2
        )

    # =========================================================
    # DEVELOPMENT COST
    # =========================================================

    def _calculate_development_cost(
        self,
        level: int
    ) -> float:

        return round(
            self.BASE_DEVELOPMENT_COST
            *
            (
                1.0
                +
                (
                    max(
                        0,
                        level - 1
                    )
                    *
                    0.25
                )
            ),
            2
        )

    # =========================================================
    # NORMALIZE CATEGORY
    # =========================================================

    def _normalize_category(
        self,
        category: str
    ) -> str:

        if not category:

            return ""

        value = (
            str(category)
            .strip()
            .lower()
        )

        aliases = {

            "aero":
                "Aero",

            "aerodynamics":
                "Aero",

            "aerodynamic":
                "Aero",

            "power":
                "Power Unit",

            "power unit":
                "Power Unit",

            "engine":
                "Power Unit",

            "pu":
                "Power Unit",

            "chassis":
                "Chassis",

            "tyre":
                "Tyres",

            "tyres":
                "Tyres",

            "tire":
                "Tyres",

            "tires":
                "Tyres",

            "tyre management":
                "Tyres",

            "tire management":
                "Tyres",

            "reliability":
                "Reliability"
        }

        return aliases.get(
            value,
            str(category).strip()
        )

    # =========================================================
    # CLAMP
    # =========================================================

    def _clamp(
        self,
        value: float
    ) -> float:

        return max(
            self.MIN_PERFORMANCE,
            min(
                float(value),
                self.MAX_PERFORMANCE
            )
        )


# =============================================================
# SINGLE ENGINE INSTANCE
# =============================================================

upgrade_engine = UpgradeEngine()