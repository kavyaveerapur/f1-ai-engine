from backend.app import app
from backend.models import Circuit
from backend.services.strategy_engine import strategy_engine


def run_test():

    with app.app_context():

        circuit = Circuit.query.filter_by(
            name="Australian Grand Prix"
        ).first()

        if not circuit:

            print(
                "ERROR: Australian Grand Prix "
                "was not found in the database."
            )

            return

        inputs = {

            "downforce": "Medium",

            "drag": "Medium",

            "tire_degradation": "Medium",

            "energy_efficiency": "Medium",

            "straight_line_speed": "Medium",

            "cornering": "Medium",

            "weather": "Dry"

        }

        result = strategy_engine.analyze(
            circuit,
            inputs
        )

        print("\n")
        print("=" * 70)
        print("F1 STRATEGY ENGINE TEST")
        print("=" * 70)

        print(
            f"\nCircuit: "
            f"{result['circuit']['name']}"
        )

        print(
            f"Weather: "
            f"{result['race_context']['weather']}"
        )

        print("\nCandidate Strategies")
        print("-" * 70)

        for strategy in result[
            "candidate_strategies"
        ]:

            print(
                f"\n{strategy['name']}"
            )

            print(
                f"Score: "
                f"{strategy['score']}"
            )

            print(
                f"Stops: "
                f"{strategy['stops']}"
            )

            print(
                f"Compounds: "
                f"{' → '.join(strategy['compounds'])}"
            )

            print(
                f"Risk: "
                f"{strategy['risk']}"
            )

        print("\n")
        print("=" * 70)

        best = result[
            "recommended_strategy"
        ]

        if best:

            print(
                "RECOMMENDED STRATEGY"
            )

            print("=" * 70)

            print(
                f"Strategy: "
                f"{best['name']}"
            )

            print(
                f"Score: "
                f"{best['score']}"
            )

            print(
                f"Compounds: "
                f"{' → '.join(best['compounds'])}"
            )

            print(
                f"Risk: "
                f"{best['risk']}"
            )

            print("\nReasoning:")

            for reason in best[
                "reasoning"
            ]:

                print(
                    f"  • {reason}"
                )

        print("=" * 70)
        print("\nStrategy engine test completed.")
        print()


if __name__ == "__main__":

    run_test()