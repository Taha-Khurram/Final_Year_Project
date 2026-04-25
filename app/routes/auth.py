from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, current_app
from firebase_admin import auth as admin_auth
from datetime import datetime, timezone
from app.firebase.firestore_service import FirestoreService

auth_bp = Blueprint('auth_bp', __name__)
db_service = FirestoreService()

@auth_bp.route('/login')
def login():
    if session.get('logged_in'):
        return redirect(url_for('blog.home'))
    return render_template('login.html', firebase_config=current_app.config['FIREBASE_CONFIG'])

@auth_bp.route('/signup')
def signup():
    if session.get('logged_in'):
        return redirect(url_for('blog.home'))
    return render_template('signup.html', firebase_config=current_app.config['FIREBASE_CONFIG'])

@auth_bp.route('/api/auth/verify', methods=['POST'])
def verify_token():
    data = request.json
    id_token = data.get('idToken')
    try:
        decoded_token = admin_auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        
        user_info = {
            "uid": uid,
            "name": decoded_token.get('name') or decoded_token.get('email').split('@')[0],
            "email": decoded_token.get('email')
        }

        # Save/Retrieve user and their ROLE
        user_record = db_service.save_user(user_info)

        session.permanent = True
        session.update({
            'user_id': uid,
            'user_name': user_record['name'],
            'user_role': user_record.get('role', 'ADMIN'), # CRITICAL for routing
            'logged_in': True,
            'last_activity': datetime.now(timezone.utc).isoformat()
        })

        return jsonify({"success": True, "redirect": url_for('blog.home')})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 401

@auth_bp.route('/api/admin/create-user', methods=['POST'])
def create_sub_user():
    """Route for Admins to manually create a user."""
    if session.get('user_role') != 'ADMIN':
        return jsonify({"error": "Unauthorized"}), 403

    data = request.json
    try:
        # 1. Create in Firebase Auth (Manual Email/Password)
        user_record = admin_auth.create_user(
            email=data['email'],
            password=data['password'],
            display_name=data['name']
        )

        # 2. Store in Firestore with 'USER' role linked to this Admin
        db_service.save_user({
            "uid": user_record.uid,
            "name": data['name'],
            "email": data['email'],
            "role": "USER",
            "created_by": session.get('user_id')
        })

        return jsonify({"success": True, "message": "User created successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@auth_bp.route('/logout')
def logout():
    session.clear()
    session.modified = True 
    return redirect(url_for('auth_bp.login'))