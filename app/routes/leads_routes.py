from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, abort
from app.firebase.firestore_service import FirestoreService
from functools import wraps

leads_bp = Blueprint('leads', __name__)
db_service = FirestoreService()


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('auth_bp.login'))
        if session.get('user_role') != 'ADMIN':
            abort(404)
        return f(*args, **kwargs)
    return decorated_function


@leads_bp.route('/leads')
@admin_required
def leads_page():
    admin_id = session.get('user_id')
    stats = db_service.get_contact_stats(admin_id)
    return render_template('leads.html', stats=stats)


@leads_bp.route('/api/leads', methods=['GET'])
@admin_required
def api_get_leads():
    admin_id = session.get('user_id')
    status_filter = request.args.get('status', 'all')
    search = request.args.get('search', '').strip()
    page = int(request.args.get('page', 1))
    per_page = 10

    result = db_service.get_contact_submissions(
        user_id=admin_id,
        page=page,
        per_page=per_page,
        status_filter=status_filter,
        search=search
    )
    return jsonify({"success": True, **result})


@leads_bp.route('/api/leads/stats', methods=['GET'])
@admin_required
def api_get_leads_stats():
    admin_id = session.get('user_id')
    stats = db_service.get_contact_stats(admin_id)
    return jsonify({"success": True, "stats": stats})


@leads_bp.route('/api/leads/<submission_id>/read', methods=['POST'])
@admin_required
def api_mark_lead_read(submission_id):
    success = db_service.mark_contact_read(submission_id)
    if success:
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Failed to mark as read"}), 500


@leads_bp.route('/api/leads/<submission_id>/delete', methods=['POST'])
@admin_required
def api_delete_lead(submission_id):
    success = db_service.delete_contact_submission(submission_id)
    if success:
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Failed to delete"}), 500
