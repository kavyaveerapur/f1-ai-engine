from flask import Blueprint, jsonify, request, session
from werkzeug.security import generate_password_hash, check_password_hash

from backend.extensions import db
from backend.models.user import User


auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/api/auth"
)


@auth_bp.route("/register", methods=["POST"])
def register():

    data = request.get_json(silent=True) or {}

    username = str(
        data.get("username", "")
    ).strip()

    email = str(
        data.get("email", "")
    ).strip().lower()

    password = str(
        data.get("password", "")
    )

    if not username or not email or not password:

        return jsonify({
            "success": False,
            "message": "Username, email and password are required."
        }), 400

    if len(username) < 3:

        return jsonify({
            "success": False,
            "message": "Username must contain at least 3 characters."
        }), 400

    if len(password) < 6:

        return jsonify({
            "success": False,
            "message": "Password must contain at least 6 characters."
        }), 400

    existing_username = User.query.filter_by(
        username=username
    ).first()

    if existing_username:

        return jsonify({
            "success": False,
            "message": "Username already exists."
        }), 409

    existing_email = User.query.filter_by(
        email=email
    ).first()

    if existing_email:

        return jsonify({
            "success": False,
            "message": "Email already exists."
        }), 409

    user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(
            password
        )
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Account created successfully.",
        "user": user.to_dict()
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():

    data = request.get_json(silent=True) or {}

    identifier = str(
        data.get("identifier", "")
    ).strip()

    password = str(
        data.get("password", "")
    )

    if not identifier or not password:

        return jsonify({
            "success": False,
            "message": "Username/email and password are required."
        }), 400

    user = User.query.filter(
        db.or_(
            User.username == identifier,
            User.email == identifier.lower()
        )
    ).first()

    if user is None:

        return jsonify({
            "success": False,
            "message": "Invalid username/email or password."
        }), 401

    if not check_password_hash(
        user.password_hash,
        password
    ):

        return jsonify({
            "success": False,
            "message": "Invalid username/email or password."
        }), 401

    session["user_id"] = user.id

    return jsonify({
        "success": True,
        "message": "Login successful.",
        "user": user.to_dict()
    })


@auth_bp.route("/me", methods=["GET"])
def me():

    user_id = session.get(
        "user_id"
    )

    if not user_id:

        return jsonify({
            "success": False,
            "authenticated": False
        }), 401

    user = User.query.get(
        user_id
    )

    if user is None:

        session.pop(
            "user_id",
            None
        )

        return jsonify({
            "success": False,
            "authenticated": False
        }), 401

    return jsonify({
        "success": True,
        "authenticated": True,
        "user": user.to_dict()
    })


@auth_bp.route("/logout", methods=["POST"])
def logout():

    session.pop(
        "user_id",
        None
    )

    return jsonify({
        "success": True,
        "message": "Logged out successfully."
    })
