from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, abort
from firebase_admin import auth as admin_auth
from app.firebase.firestore_service import FirestoreService
from functools import wraps

# We define the blueprint. The 'url_prefix' will be handled in the app factory.
user_bp = Blueprint('user_bp', __name__)
db_service = FirestoreService()


def admin_required(f):
    """Decorator to restrict routes to admin users only"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('auth_bp.login'))
        if session.get('user_role') != 'ADMIN':
            abort(404)  # Show 404 instead of 403 to hide the existence of the page
        return f(*args, **kwargs)
    return decorated_function


@user_bp.route('/manage-users')
@admin_required
def manage_users():
    """Renders the management dashboard for Admins."""
    return render_template('users.html')


@user_bp.route('/list', methods=['GET'])
@admin_required
def list_sub_users():
    """Fetches users managed by the logged-in Admin. Accessible at /users/list"""
    try:
        admin_id = session.get('user_id')
        print(f"🔍 Fetching users for admin ID: {admin_id}")
        users = db_service.get_my_sub_users(admin_id)
        
        # Clean up users for JSON (handle datetimes if any)
        safe_users = []
        for u in users:
            clean_u = {}
            for k, v in u.items():
                if hasattr(v, 'isoformat'): # Handle datetime objects
                    clean_u[k] = v.isoformat()
                else:
                    clean_u[k] = v
            safe_users.append(clean_u)
            
        print(f"✅ Found {len(safe_users)} users. Returning JSON...")
        return jsonify({"success": True, "users": safe_users})
    except Exception as e:
        print(f"❌ Error in /users/list: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@user_bp.route('/create', methods=['POST'])
@admin_required
def create_sub_user():
    """Creates Auth & Firestore records. Accessible at /users/create"""
    data = request.json
    try:
        # 1. Create in Firebase Auth
        user_record = admin_auth.create_user(
            email=data.get('email'),
            password=data.get('password'),
            display_name=data.get('username')
        )

        # 2. Save to Firestore via Service
        db_service.save_user({
            "uid": user_record.uid,
            "email": data.get('email'),
            "name": data.get('username'),
            "role": data.get('role', 'EDITOR').upper(),
            "created_by": session.get('user_id')
        })

        db_service.log_activity(
            user_id=session.get('user_id'),
            user_name=session.get('user_name', 'Admin'),
            type="user",
            action_text=f"Created user '{data.get('username')}'",
            target_type="user",
            target_id=user_record.uid,
            target_name=data.get('username'),
            metadata={"role": data.get('role', 'EDITOR').upper(), "email": data.get('email')}
        )

        return jsonify({"success": True, "message": "User created successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@user_bp.route('/update-role', methods=['POST'])
@admin_required
def update_user_role():
    """Updates user role. Accessible at /users/update-role"""
    data = request.json
    user_id = data.get('userId')
    new_role = data.get('role', '').upper()

    try:
        db_service.db.collection("users").document(user_id).update({"role": new_role})
        db_service.log_activity(
            user_id=session.get('user_id'),
            user_name=session.get('user_name', 'Admin'),
            type="user",
            action_text=f"Changed role to {new_role}",
            target_type="user",
            target_id=user_id,
            target_name=data.get('username', user_id),
            metadata={"new_role": new_role}
        )
        return jsonify({"success": True, "message": "Role updated"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400