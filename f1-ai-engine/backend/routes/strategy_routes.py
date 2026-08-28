from flask import Blueprint, jsonify, request

from backend.models import Circuit
from backend.services.strategy_engine import strategy_engine
from backend.services.llm_service import explain_strategy


strategy_bp = Blueprint(
    "strategy",
    __name__,
    url_prefix="/api/strategy"
)


# ============================================================
# FRONTEND TRACK NAME -> DATABASE CIRCUIT NAME
# ============================================================

TRACK_ALIASES = {
    "Australia": "Australian Grand Prix",
    "China": "Chinese Grand Prix",
    "Japan": "Japanese Grand Prix",
    "Bahrain": "Bahrain Grand Prix",
    "Saudi Arabia": "Saudi Arabian Grand Prix",
    "Miami": "Miami Grand Prix",
    "Emilia-Romagna": "Emilia-Romagna Grand Prix",
    "Monaco": "Monaco Grand Prix",
    "Canada": "Canadian Grand Prix",
    "Spain": "Spanish Grand Prix",
    "Austria": "Austrian Grand Prix",
    "Great Britain": "British Grand Prix",
    "Belgium": "Belgian Grand Prix",
    "Hungary": "Hungarian Grand Prix",
    "Netherlands": "Dutch Grand Prix",
    "Italy": "Italian Grand Prix",
    "Azerbaijan": "Azerbaijan Grand Prix",
    "Singapore": "Singapore Grand Prix",
    "USA Austin": "United States Grand Prix",
    "United States": "United States Grand Prix",
    "Mexico": "Mexico City Grand Prix",
    "Mexico City": "Mexico City Grand Prix",
    "Brazil": "São Paulo Grand Prix",
    "São Paulo": "São Paulo Grand Prix",
    "Sao Paulo": "São Paulo Grand Prix",
    "Las Vegas": "Las Vegas Grand Prix",
    "Qatar": "Qatar Grand Prix",
    "Abu Dhabi": "Abu Dhabi Grand Prix",
    "Madrid": "Madrid Grand Prix",
}


def _normalize_track_name(value):
    """
    Normalize a track name for reliable comparison.

    This allows values such as:

        Great Britain
        great britain
        Great-Britain
        Great Britain Grand Prix

    to be compared consistently.
    """

    if value is None:
        return ""

    value = str(value).strip().lower()

    replacements = {
        "-": " ",
        "_": " ",
        "’": "'",
        "–": " ",
        "—": " ",
        "ã": "a",
        "á": "a",
        "à": "a",
        "â": "a",
        "ä": "a",
        "é": "e",
        "è": "e",
        "ê": "e",
        "ë": "e",
        "í": "i",
        "ì": "i",
        "î": "i",
        "ï": "i",
        "ó": "o",
        "ò": "o",
        "ô": "o",
        "ö": "o",
        "ú": "u",
        "ù": "u",
        "û": "u",
        "ü": "u",
        "ç": "c",
        "ñ": "n",
    }

    for old, new in replacements.items():
        value = value.replace(old, new)

    while "  " in value:
        value = value.replace("  ", " ")

    return value.strip()


def _find_circuit(track_name):
    """
    Resolve a frontend track name to the actual Circuit database row.

    Resolution order:

    1. Exact database name.
    2. Known frontend alias.
    3. Normalized exact comparison.
    4. Normalized partial comparison.

    This keeps the existing database untouched.
    """

    if not track_name:
        return None

    requested = str(
        track_name
    ).strip()

    # --------------------------------------------------------
    # 1. Exact database match
    # --------------------------------------------------------

    circuit = Circuit.query.filter(
        Circuit.name.ilike(
            requested
        )
    ).first()

    if circuit:
        return circuit

    # --------------------------------------------------------
    # 2. Known frontend alias
    # --------------------------------------------------------

    canonical_name = TRACK_ALIASES.get(
        requested
    )

    if canonical_name:

        circuit = Circuit.query.filter(
            Circuit.name.ilike(
                canonical_name
            )
        ).first()

        if circuit:
            return circuit

    # --------------------------------------------------------
    # 3. Normalized comparison
    # --------------------------------------------------------

    requested_normalized = _normalize_track_name(
        requested
    )

    circuits = Circuit.query.all()

    for circuit in circuits:

        database_normalized = _normalize_track_name(
            circuit.name
        )

        if (
            requested_normalized
            == database_normalized
        ):
            return circuit

    # --------------------------------------------------------
    # 4. Normalized comparison against aliases
    # --------------------------------------------------------

    for alias, canonical in TRACK_ALIASES.items():

        if (
            _normalize_track_name(alias)
            == requested_normalized
        ):

            canonical_normalized = (
                _normalize_track_name(
                    canonical
                )
            )

            for circuit in circuits:

                database_normalized = (
                    _normalize_track_name(
                        circuit.name
                    )
                )

                if (
                    database_normalized
                    == canonical_normalized
                ):
                    return circuit

    # --------------------------------------------------------
    # 5. Partial normalized comparison
    # --------------------------------------------------------

    for circuit in circuits:

        database_normalized = (
            _normalize_track_name(
                circuit.name
            )
        )

        if (
            requested_normalized
            in database_normalized
            or
            database_normalized
            in requested_normalized
        ):
            return circuit

    return None


@strategy_bp.route(
    "/analyze",
    methods=["POST"]
)
def analyze_strategy():

    """
    Analyze an F1 race strategy using:

    1. Deterministic strategy engine
    2. AI/LLM explanation layer

    The deterministic engine remains the source of truth.
    The LLM explains the calculated result.
    """

    try:

        data = request.get_json(
            silent=True
        ) or {}

        # -------------------------------------------------
        # Track
        # -------------------------------------------------

        track_name = data.get(
            "track"
        )

        if not track_name:

            return jsonify({
                "success": False,
                "error": "Track is required."
            }), 400

        # -------------------------------------------------
        # Find circuit
        # -------------------------------------------------

        circuit = _find_circuit(
            track_name
        )

        if not circuit:

            return jsonify({
                "success": False,
                "error": (
                    f"Circuit '{track_name}' "
                    "was not found."
                )
            }), 404

        # -------------------------------------------------
        # Build strategy inputs
        # -------------------------------------------------

        strategy_inputs = {

            "downforce": data.get(
                "downforce",
                "Medium"
            ),

            "drag": data.get(
                "drag",
                "Medium"
            ),

            "tire_degradation": data.get(
                "tire_degradation",
                "Medium"
            ),

            "energy_efficiency": data.get(
                "energy_efficiency",
                "Medium"
            ),

            "straight_line_speed": data.get(
                "straight_line_speed",
                "Medium"
            ),

            "cornering": data.get(
                "cornering",
                "Medium"
            ),

            "weather": data.get(
                "weather",
                "Dry"
            )
        }

        # -------------------------------------------------
        # Run deterministic engine
        # -------------------------------------------------

        result = strategy_engine.analyze(
            circuit,
            strategy_inputs
        )

        # -------------------------------------------------
        # Add request metadata
        # -------------------------------------------------

        result["request"] = {

            "team": data.get(
                "team",
                "Unknown Team"
            ),

            "track": track_name,

            "resolved_circuit": circuit.name,

            "settings": strategy_inputs

        }

        # -------------------------------------------------
        # Generate AI explanation
        # -------------------------------------------------

        try:

            ai_result = explain_strategy(
                result
            )

        except Exception as ai_exc:

            ai_result = {

                "success": False,

                "mode": "mock",

                "error": (
                    "AI explanation failed."
                ),

                "details": str(
                    ai_exc
                )

            }

        # -------------------------------------------------
        # Attach AI result
        # -------------------------------------------------

        result["ai_explanation"] = (
            ai_result
        )

        # -------------------------------------------------
        # Return complete response
        # -------------------------------------------------

        return jsonify(
            result
        ), 200

    except Exception as exc:

        return jsonify({

            "success": False,

            "error": (
                "Strategy analysis failed."
            ),

            "details": str(
                exc
            )

        }), 500