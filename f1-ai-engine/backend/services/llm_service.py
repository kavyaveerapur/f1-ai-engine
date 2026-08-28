import json
import os
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv


# =========================================================
# ENVIRONMENT
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")


LLM_MODE = os.getenv(
    "LLM_MODE",
    "mock"
).lower()

OPENAI_MODEL = os.getenv(
    "OPENAI_MODEL",
    "gpt-5-mini"
)


# =========================================================
# OPTIONAL OPENAI CLIENT
# =========================================================

client = None

if LLM_MODE == "openai":

    from openai import OpenAI

    OPENAI_API_KEY = os.getenv(
        "OPENAI_API_KEY"
    )

    if OPENAI_API_KEY:

        client = OpenAI(
            api_key=OPENAI_API_KEY
        )


# =========================================================
# SYSTEM INSTRUCTIONS
# =========================================================

SYSTEM_INSTRUCTIONS = """
You are the AI race engineer for an F1 strategy analysis system.

The deterministic strategy engine is the source of truth.

Your job is to explain the strategy selected by that engine.

Rules:

1. Never change the recommended strategy.
2. Never invent scores or strategy data.
3. Never invent tyre compounds.
4. Never invent weather conditions.
5. Never invent circuit characteristics.
6. Explain why the recommended strategy ranked first.
7. Explain tyre choice and pit-stop logic.
8. Explain the main strategic strengths.
9. Explain the primary risk.
10. Give practical race-engineer advice.
11. Use professional F1 race-engineering language.
12. Keep the explanation technically meaningful but concise.

The deterministic engine chooses the strategy.
You explain the decision.
"""


# =========================================================
# HELPERS
# =========================================================

def _get_strategy_name(strategy: Any) -> str:

    if isinstance(strategy, str):
        return strategy

    if isinstance(strategy, dict):

        return str(
            strategy.get("name")
            or strategy.get("strategy")
            or strategy.get("strategy_name")
            or "Recommended Strategy"
        )

    return "Recommended Strategy"


def _get_score(strategy: Any) -> Any:

    if isinstance(strategy, dict):

        return (
            strategy.get("score")
            or strategy.get("total_score")
            or strategy.get("final_score")
        )

    return None


def _get_compounds(strategy: Any) -> str:

    if not isinstance(strategy, dict):
        return "Not specified"

    compounds = (
        strategy.get("compounds")
        or strategy.get("tyres")
        or strategy.get("tires")
        or strategy.get("compound_sequence")
    )

    if isinstance(compounds, list):
        return " → ".join(
            str(compound)
            for compound in compounds
        )

    if compounds:
        return str(compounds)

    return "Not specified"


def _get_stops(strategy: Any) -> Any:

    if isinstance(strategy, dict):

        return (
            strategy.get("stops")
            or strategy.get("pit_stops")
            or strategy.get("pitstops")
        )

    return None


def _get_risk(strategy: Any) -> str:

    if isinstance(strategy, dict):

        return str(
            strategy.get("risk")
            or strategy.get("risk_level")
            or "Not specified"
        )

    return "Not specified"


# =========================================================
# MOCK AI ENGINEER
# =========================================================

def _mock_explanation(
    analysis_result: Dict[str, Any]
) -> str:

    recommended = analysis_result.get(
        "recommended_strategy"
    )

    candidates = analysis_result.get(
        "candidate_strategies",
        []
    )

    circuit = analysis_result.get(
        "circuit",
        {}
    )

    race_context = analysis_result.get(
        "race_context",
        {}
    )

    request = analysis_result.get(
        "request",
        {}
    )

    strategy_name = _get_strategy_name(
        recommended
    )

    score = _get_score(
        recommended
    )

    compounds = _get_compounds(
        recommended
    )

    stops = _get_stops(
        recommended
    )

    risk = _get_risk(
        recommended
    )

    circuit_name = (
        circuit.get("name")
        if isinstance(circuit, dict)
        else None
    )

    if not circuit_name:

        circuit_name = request.get(
            "track",
            "the selected circuit"
        )

    weather = (
        race_context.get("weather")
        if isinstance(race_context, dict)
        else None
    )

    if not weather:

        settings = request.get(
            "settings",
            {}
        )

        weather = settings.get(
            "weather",
            "Dry"
        )

    candidate_count = (
        len(candidates)
        if isinstance(candidates, list)
        else 0
    )

    # -----------------------------------------------------
    # Score text
    # -----------------------------------------------------

    if score is not None:

        score_text = (
            f"with a strategy score of {score}"
        )

    else:

        score_text = (
            "with the highest calculated strategy score"
        )

    # -----------------------------------------------------
    # Stops text
    # -----------------------------------------------------

    if stops is not None:

        stops_text = (
            f"{stops} pit stop"
            if str(stops) == "1"
            else f"{stops} pit stops"
        )

    else:

        stops_text = (
            "the calculated pit-stop plan"
        )

    # -----------------------------------------------------
    # Candidate comparison
    # -----------------------------------------------------

    if candidate_count > 1:

        comparison_text = (
            f"The engine evaluated {candidate_count} "
            "candidate strategies and ranked this option first."
        )

    else:

        comparison_text = (
            "The strategy engine ranked this option first "
            "among the available strategies."
        )

    # -----------------------------------------------------
    # Weather guidance
    # -----------------------------------------------------

    weather_lower = str(
        weather
    ).lower()

    if weather_lower == "wet":

        weather_text = (
            "The wet-weather context makes tyre selection "
            "and maintaining sufficient surface grip a "
            "critical part of the strategy."
        )

    elif weather_lower == "mixed":

        weather_text = (
            "The mixed-weather context means tyre crossover "
            "conditions will be important, so the team must "
            "react quickly if track conditions change."
        )

    else:

        weather_text = (
            "With dry conditions, the strategy can focus on "
            "the balance between tyre life, race pace and "
            "pit-stop loss."
        )

    # -----------------------------------------------------
    # Build explanation
    # -----------------------------------------------------

    explanation = f"""
RECOMMENDATION

{strategy_name} is the recommended strategy for {circuit_name},
{score_text}. {comparison_text}


WHY IT WORKS

The deterministic engine has identified this strategy as the
best overall balance for the selected circuit, setup and race
conditions. The calculated risk level is {risk}.


TYRE STRATEGY

The planned compound sequence is {compounds}. The strategy uses
{stops_text}, allowing the team to balance tyre performance
against pit-lane time loss.

{weather_text}


KEY STRENGTH

The main advantage is that the strategy provides the strongest
overall calculated performance among the available candidates
while remaining consistent with the selected race conditions.


MAIN RISK

The biggest risk is that actual race conditions can change.
Tyre degradation, traffic, safety cars and weather evolution
can all alter the ideal race window.


RACE ENGINEER ADVICE

Start from the recommended plan, but monitor tyre degradation
closely during the opening stint. If the observed degradation
moves significantly away from the expected window, reassess
the pit-stop timing rather than blindly following the original
plan.
"""

    return explanation.strip()


# =========================================================
# OPENAI EXPLANATION
# =========================================================

def _openai_explanation(
    analysis_result: Dict[str, Any]
) -> Dict[str, Any]:

    if client is None:

        return {
            "success": False,
            "error": (
                "OpenAI client is not configured."
            ),
            "model": OPENAI_MODEL
        }

    engine_data = {

        "circuit": analysis_result.get(
            "circuit",
            {}
        ),

        "race_context": analysis_result.get(
            "race_context",
            {}
        ),

        "recommended_strategy": analysis_result.get(
            "recommended_strategy"
        ),

        "candidate_strategies": analysis_result.get(
            "candidate_strategies",
            []
        )

    }

    user_prompt = f"""
Analyze this deterministic F1 strategy engine result.

ENGINE OUTPUT:

{json.dumps(
    engine_data,
    indent=2,
    ensure_ascii=False
)}

The recommended strategy has already been selected by the
deterministic engine.

Do not change it.

Explain:

1. Why it ranked first.
2. Why the tyre compounds fit the conditions.
3. Why the pit-stop plan makes sense.
4. The effect of tyre degradation.
5. The main strategic strength.
6. The main risk.
7. What the race engineer should monitor.

Keep the response concise and professional.
"""

    try:

        response = client.responses.create(

            model=OPENAI_MODEL,

            instructions=SYSTEM_INSTRUCTIONS,

            input=user_prompt

        )

        explanation = (
            response.output_text
            if response.output_text
            else ""
        ).strip()

        if not explanation:

            return {
                "success": False,
                "error": (
                    "LLM returned an empty explanation."
                ),
                "model": OPENAI_MODEL
            }

        return {

            "success": True,

            "mode": "openai",

            "model": OPENAI_MODEL,

            "explanation": explanation

        }

    except Exception as exc:

        return {

            "success": False,

            "mode": "openai",

            "model": OPENAI_MODEL,

            "error": (
                "OpenAI strategy explanation failed."
            ),

            "details": str(exc)

        }


# =========================================================
# PUBLIC FUNCTION
# =========================================================

def explain_strategy(
    analysis_result: Dict[str, Any]
) -> Dict[str, Any]:

    """
    Public entry point for the LLM layer.

    MOCK mode:
        No API call.
        No credits required.

    OPENAI mode:
        Uses the OpenAI Responses API.
    """

    if LLM_MODE == "openai":

        result = _openai_explanation(
            analysis_result
        )

        return result

    # -----------------------------------------------------
    # Default development mode
    # -----------------------------------------------------

    return {

        "success": True,

        "mode": "mock",

        "model": "local-mock",

        "explanation": _mock_explanation(
            analysis_result
        )

    }