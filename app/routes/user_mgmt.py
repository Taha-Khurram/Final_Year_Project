from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from firebase_admin import auth as admin_auth
from app.firebase.firestore_service import FirestoreService

# We define the blueprint. The 'url_prefix' will be handled in the app factory.
user_bp = Blueprint('user_bp', __name__)
db_service = FirestoreService()

@user_bp.route('/manage-users')
def manage_users():
    """Renders the management dashboard for Admins."""
    if session.get('user_role') != 'ADMIN':
        return redirect(url_for('blog.home'))
    return render_template('users.html')

@user_bp.route('/list', methods=['GET'])
def list_sub_users():
    """Fetches users managed by the logged-in Admin. Accessible at /users/list"""
    try:
        if session.get('user_role') != 'ADMIN':
            return jsonify({"error": "Unauthorized"}), 403
        
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
def create_sub_user():
    """Creates Auth & Firestore records. Accessible at /users/create"""
    if session.get('user_role') != 'ADMIN':
        return jsonify({"error": "Unauthorized"}), 403

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
        return jsonify({"success": True, "message": "User created successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@user_bp.route('/update-role', methods=['POST'])
def update_user_role():
    """Updates user role. Accessible at /users/update-role"""
    if session.get('user_role') != 'ADMIN':
        return jsonify({"error": "Unauthorized"}), 403
    
    data = request.json
    user_id = data.get('userId')
    new_role = data.get('role', '').upper()

    try:
        db_service.db.collection("users").document(user_id).update({"role": new_role})
        return jsonify({"success": True, "message": "Role updated"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400