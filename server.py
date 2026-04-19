import html
import os

from flask import Flask, abort, jsonify, request, send_file, send_from_directory
from werkzeug.utils import safe_join
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Initialize Application Engine
load_dotenv()
app = Flask(__name__)
# Enable CORS for local testing vs live hostings
CORS(app, resources={r"/api/*": {"origins": "*"}})


def get_database_url():
    url = (
        os.getenv("DATABASE_URL")
        or os.getenv("RENDER_DB_URL")
        or os.getenv("RENDER_INTERNAL_DATABASE_URL")
    )
    if not url:
        raise RuntimeError(
            "Set DATABASE_URL, RENDER_DB_URL, or RENDER_INTERNAL_DATABASE_URL "
            "(external URL for local dev; internal only from Render’s private network)."
        )
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    return url


def get_db_connection():
    return psycopg2.connect(get_database_url())

@app.route('/api/ping', methods=['GET'])
def ping():
    return jsonify({"status": "healthy", "database": "PostgreSQL Render Verified"}), 200

@app.route('/api/feed', methods=['GET'])
def get_feed():
    # Returns structural feed array for UI mapping.
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT id, author_name, author_role, content, likes_count, comments_count, to_char(created_at, 'YYYY-MM-DD HH24:MI:SS') as date FROM feed_posts ORDER BY created_at DESC;")
        posts = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify({"success": True, "data": posts}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/feed', methods=['POST'])
def create_post():
    try:
        data = request.json or {}
        content = (data.get("content") or "").strip()
        if not content:
            return jsonify({"success": False, "error": "content is required"}), 400
        conn = get_db_connection()
        cur = conn.cursor()
        
        # In a real environment, author_email triggers user lookup. For structural test, parsing raw from React/Vanilla.
        cur.execute(
            "INSERT INTO feed_posts (author_email, author_name, author_role, content) VALUES (%s, %s, %s, %s) RETURNING id;",
            (data.get('email', 'sys@auth.local'), data.get('name', 'Professional User'), data.get('role', 'Verified Architect'), content)
        )
        new_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"success": True, "message": "Post successfully inserted to Render PostgreSQL", "post_id": new_id}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT id, role_title, company_name, location, tier, salary, tags FROM jobs_board ORDER BY created_at DESC;")
        jobs = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify({"success": True, "data": jobs}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/funding', methods=['GET'])
def get_funding():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT id, startup_name, round_type, capital_raised, target_capital, domain_tags FROM venture_deals ORDER BY created_at DESC;")
        deals = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify({"success": True, "data": deals}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/jobs', methods=['POST'])
def create_job():
    try:
        data = request.get_json(silent=True) or {}
        role_title = (data.get("role_title") or "").strip()
        company_name = (data.get("company_name") or "").strip()
        if not role_title or not company_name:
            return jsonify({"success": False, "error": "role_title and company_name are required"}), 400
        salary = (data.get("salary") or "").strip()
        if not salary:
            return jsonify({"success": False, "error": "salary is required"}), 400
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO jobs_board (role_title, company_name, location, tier, salary, tags) VALUES (%s, %s, %s, %s, %s, %s)",
            (
                role_title,
                company_name,
                (data.get("location") or "Remote").strip() or "Remote",
                (data.get("tier") or "Full Time").strip() or "Full Time",
                salary,
                (data.get("tags") or "").strip() or "",
            ),
        )
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"success": True}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/funding', methods=['POST'])
def create_funding():
    try:
        data = request.get_json(silent=True) or {}
        startup_name = (data.get("startup_name") or "").strip()
        round_type = (data.get("round_type") or "").strip()
        target_capital = (data.get("target_capital") or "").strip()
        domain_tags = (data.get("domain_tags") or "").strip()
        if not startup_name or not target_capital or not domain_tags:
            return jsonify(
                {"success": False, "error": "startup_name, target_capital, and domain_tags are required"}
            ), 400
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO venture_deals (startup_name, round_type, capital_raised, target_capital, domain_tags) VALUES (%s, %s, %s, %s, %s)",
            (startup_name, round_type or "Seed", "$0", target_capital, domain_tags),
        )
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"success": True}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/services", methods=["GET"])
def get_services():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            SELECT id, agency_name, service_domain, starting_price, description,
                   to_char(created_at, 'YYYY-MM-DD HH24:MI:SS') AS created_at
            FROM b2b_services
            ORDER BY created_at DESC;
            """
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify({"success": True, "data": rows}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/services", methods=["POST"])
def create_service():
    try:
        data = request.get_json(silent=True) or {}
        agency_name = (data.get("agency_name") or "").strip()
        description = (data.get("description") or "").strip()
        if not agency_name or not description:
            return jsonify({"success": False, "error": "agency_name and description are required"}), 400
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO b2b_services (agency_name, service_domain, starting_price, description)
            VALUES (%s, %s, %s, %s);
            """,
            (
                agency_name,
                (data.get("service_domain") or "").strip() or "General",
                (data.get("starting_price") or "").strip() or "Contact for quote",
                description,
            ),
        )
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"success": True}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/procurement", methods=["GET"])
def get_procurement():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            SELECT id, buyer_email, budget, vendor_tier, description,
                   to_char(created_at, 'YYYY-MM-DD HH24:MI:SS') AS created_at
            FROM procurement_requests
            ORDER BY created_at DESC;
            """
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify({"success": True, "data": rows}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/procurement", methods=["POST"])
def create_procurement():
    try:
        data = request.get_json(silent=True) or {}
        description = (data.get("description") or "").strip()
        if not description:
            return jsonify({"success": False, "error": "description is required"}), 400
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO procurement_requests (buyer_email, budget, vendor_tier, description)
            VALUES (%s, %s, %s, %s);
            """,
            (
                (data.get("buyer_email") or "").strip() or None,
                (data.get("budget") or "").strip() or "",
                (data.get("vendor_tier") or "").strip() or "",
                description,
            ),
        )
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"success": True}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/events", methods=["POST"])
def create_event():
    try:
        data = request.get_json(silent=True) or {}
        event_name = (data.get("event_name") or "").strip()
        host_name = (data.get("host_name") or "").strip()
        if not event_name or not host_name:
            return jsonify({"success": False, "error": "event_name and host_name are required"}), 400
        ticket_cost = data.get("ticket_cost")
        try:
            ticket_cost = int(ticket_cost)
        except (TypeError, ValueError):
            ticket_cost = 0
        if ticket_cost < 0:
            ticket_cost = 0
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO platform_events (event_name, host_name, event_date, ticket_cost, description)
            VALUES (%s, %s, %s, %s, %s);
            """,
            (
                event_name,
                host_name,
                (data.get("event_date") or "").strip(),
                ticket_cost,
                (data.get("description") or "").strip(),
            ),
        )
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"success": True}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/events', methods=['GET'])
def get_events():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            SELECT id, event_name, host_name, event_date, ticket_cost, description,
                   to_char(created_at, 'YYYY-MM-DD HH24:MI:SS') AS created_at
            FROM platform_events
            ORDER BY created_at DESC;
            """
        )
        events = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify({"success": True, "data": events}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/wallet/<email>', methods=['GET'])
def get_wallet(email):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        # Ensure wallet exists
        cur.execute("INSERT INTO wallets (user_email, balance) VALUES (%s, 1000) ON CONFLICT (user_email) DO NOTHING;", (email,))
        cur.execute("SELECT balance FROM wallets WHERE user_email = %s;", (email,))
        balance = cur.fetchone()['balance']
        
        # Get Ledgers
        cur.execute("SELECT amount, transaction_type, description, to_char(created_at, 'YYYY-MM-DD HH24:MI:SS') as date FROM wallet_transactions WHERE user_email = %s ORDER BY created_at DESC;", (email,))
        transactions = cur.fetchall()
        
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"success": True, "balance": balance, "transactions": transactions}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/tickets/purchase', methods=['POST'])
def purchase_ticket():
    try:
        data = request.json
        email = data.get('email')
        event_id = data.get('event_id')
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get Event Cost
        cur.execute("SELECT event_name, ticket_cost FROM platform_events WHERE id = %s;", (event_id,))
        event = cur.fetchone()
        if not event:
            cur.close()
            conn.close()
            return jsonify({"success": False, "error": "Event not found."}), 404
        cost = event['ticket_cost']
        
        cur.execute(
            "INSERT INTO wallets (user_email, balance) VALUES (%s, 1000) ON CONFLICT (user_email) DO NOTHING;",
            (email,),
        )
        # Check Balance
        cur.execute("SELECT balance FROM wallets WHERE user_email = %s;", (email,))
        row = cur.fetchone()
        if not row:
            cur.close()
            conn.close()
            return jsonify({"success": False, "error": "Wallet could not be initialized."}), 400
        balance = row['balance']
        
        if balance < cost:
            return jsonify({"success": False, "error": "Insufficient wallet balance."}), 400
            
        # Deduct Balance
        cur.execute("UPDATE wallets SET balance = balance - %s WHERE user_email = %s;", (cost, email))
        
        # Append Ledger
        desc = f"Purchased Ticket: {event['event_name']}"
        cur.execute("INSERT INTO wallet_transactions (user_email, amount, transaction_type, description) VALUES (%s, %s, 'purchase', %s);", (email, -cost, desc))
        
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"success": True, "message": "Ticket generated securely."}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/tickets/refund', methods=['POST'])
def refund_ticket():
    try:
        data = request.json
        email = data.get('email')
        event_id = data.get('event_id')
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("SELECT event_name, ticket_cost FROM platform_events WHERE id = %s;", (event_id,))
        event = cur.fetchone()
        if not event:
            cur.close()
            conn.close()
            return jsonify({"success": False, "error": "Event not found."}), 404
        cost = event['ticket_cost']

        cur.execute(
            "INSERT INTO wallets (user_email, balance) VALUES (%s, 1000) ON CONFLICT (user_email) DO NOTHING;",
            (email,),
        )
        
        # Refund Balance
        cur.execute("UPDATE wallets SET balance = balance + %s WHERE user_email = %s;", (cost, email))
        
        # Append Ledger
        desc = f"Refunded Ticket: {event['event_name']}"
        cur.execute("INSERT INTO wallet_transactions (user_email, amount, transaction_type, description) VALUES (%s, %s, 'refund', %s);", (email, cost, desc))
        
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"success": True, "message": "Refund processed.", "refunded": cost}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


_FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
_DASHBOARD_PATH = os.path.join(_FRONTEND_DIR, "dashboard.html")


@app.route("/", methods=["GET", "HEAD"])
@app.route("/dashboard", methods=["GET", "HEAD"])
@app.route("/dashboard.html", methods=["GET", "HEAD"])
def serve_root():
    if not os.path.isfile(_DASHBOARD_PATH):
        safe_path = html.escape(_DASHBOARD_PATH, quote=True)
        body = (
            "<html><body><h1>Missing dashboard</h1><p>Expected file at:<br><code>"
            + safe_path
            + "</code></p><p>Run: <code>cd files/backend</code> then <code>python server.py</code></p></body></html>"
        )
        return body, 404
    return send_file(_DASHBOARD_PATH, mimetype="text/html")


@app.route("/<path:filename>", methods=["GET", "HEAD"])
def serve_frontend_asset(filename):
    if filename.startswith("api"):
        abort(404)
    candidate = safe_join(_FRONTEND_DIR, filename)
    if candidate is None or not os.path.isfile(candidate):
        abort(404)
    directory, name = os.path.split(candidate)
    return send_from_directory(directory, name)


if __name__ == '__main__':
    # Map to dynamic host ports for Render platform deployment
    port = int(os.environ.get("PORT", 5000))
    dash_ok = os.path.isfile(_DASHBOARD_PATH)
    print(
        f"\n  Hirex dashboard: http://127.0.0.1:{port}/\n"
        f"  Frontend folder: {_FRONTEND_DIR}\n"
        f"  dashboard.html:  {'OK' if dash_ok else 'MISSING — fix paths or cwd'}\n"
    )
    app.run(host="0.0.0.0", port=port, debug=False)
