import os, sqlite3, secrets
from datetime import datetime, timezone
from functools import wraps
from flask import Flask, jsonify, request, render_template, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()
BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.getenv("DATABASE_PATH", os.path.join(BASE, "crevault.db"))
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-this-secret-key")
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")

def db():
    c = sqlite3.connect(DB_PATH); c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    return c

def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def init_db():
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS admins(id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS applications(id INTEGER PRIMARY KEY, application_id TEXT UNIQUE NOT NULL, name TEXT NOT NULL, phone TEXT NOT NULL, gender TEXT NOT NULL, city TEXT NOT NULL, state TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'Pending', submitted_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS certificates(id INTEGER PRIMARY KEY, certificate_id TEXT UNIQUE NOT NULL, application_id TEXT UNIQUE NOT NULL REFERENCES applications(application_id), issued_on TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'Valid');
        """)
        u, p = os.getenv("ADMIN_USERNAME", "admin"), os.getenv("ADMIN_PASSWORD", "ChangeMe123!")
        if not c.execute("SELECT id FROM admins WHERE username=?", (u,)).fetchone():
            c.execute("INSERT INTO admins(username,password_hash) VALUES(?,?)", (u, generate_password_hash(p)))

def admin_only(fn):
    @wraps(fn)
    def inner(*a, **k):
        if not session.get("admin"): return jsonify(success=False, message="Admin login required."), 401
        return fn(*a, **k)
    return inner

@app.get("/")
@app.get("/request")
@app.get("/track")
@app.get("/verify")
@app.get("/admin/login")
@app.get("/admin/applications")
@app.get("/admin/certificates")
def website():
    if request.path.startswith("/admin/") and request.path != "/admin/login" and not session.get("admin"):
        return redirect("/admin/login")
    return render_template("index.html")

@app.get("/api/health")
def health(): return jsonify(name="CredVault API", status="running", version="1.0.0")

@app.post("/api/applications")
def create_application():
    d = request.get_json(silent=True) or request.form.to_dict()
    fields = ["name","phone","gender","city","state"]
    missing = [x for x in fields if not str(d.get(x,"")).strip()]
    if missing: return jsonify(success=False,message="Fill in all required fields.",missing=missing),400
    phone = str(d["phone"]).strip()
    if not phone.isdigit() or not 10 <= len(phone) <= 15:
        return jsonify(success=False,message="Enter a valid phone number (10–15 digits)."),400
    aid = "APP-" + datetime.now().strftime("%Y%m%d") + "-" + secrets.token_hex(3).upper()
    submitted = now()
    with db() as c:
        c.execute("INSERT INTO applications(application_id,name,phone,gender,city,state,status,submitted_at) VALUES(?,?,?,?,?,?,'Pending',?)",
                  (aid,d["name"].strip(),phone,d["gender"].strip(),d["city"].strip(),d["state"].strip(),submitted))
    return jsonify(success=True,message="Application submitted.",applicationId=aid),201

@app.get("/api/applications/track/<aid>")
def track(aid):
    with db() as c:
        r=c.execute("SELECT application_id AS applicationId,name,phone,gender,city,state,status,submitted_at AS submittedAt FROM applications WHERE application_id=?",(aid.upper(),)).fetchone()
    if not r: return jsonify(success=False,message="Application not found."),404
    return jsonify(success=True,application=dict(r))

@app.get("/api/certificates/verify/<cid>")
def verify(cid):
    with db() as c:
        r=c.execute("""SELECT c.certificate_id AS certificateId,c.application_id AS applicationId,c.issued_on AS issuedOn,c.status,a.name,a.phone,a.city,a.state
        FROM certificates c JOIN applications a ON a.application_id=c.application_id WHERE c.certificate_id=?""",(cid.upper(),)).fetchone()
    if not r: return jsonify(success=False,message="Certificate not found."),404
    return jsonify(success=True,certificate=dict(r))

@app.post("/api/admin/login")
def login():
    d=request.get_json(silent=True) or request.form.to_dict()
    with db() as c: r=c.execute("SELECT * FROM admins WHERE username=?",(str(d.get("username","")).strip(),)).fetchone()
    if not r or not check_password_hash(r["password_hash"],str(d.get("password",""))):
        return jsonify(success=False,message="Incorrect username or password."),401
    session.clear(); session["admin"]=r["username"]
    return jsonify(success=True,message="Login successful.",username=r["username"])

@app.post("/api/admin/logout")
@admin_only
def logout(): session.clear(); return jsonify(success=True,message="Logged out.")

@app.get("/api/admin/me")
def me():
    if not session.get("admin"): return jsonify(success=False,message="Not logged in."),401
    return jsonify(success=True,username=session["admin"])

@app.get("/api/admin/applications")
@admin_only
def applications():
    with db() as c: rows=c.execute("SELECT application_id AS applicationId,name,phone,gender,city,state,status,submitted_at AS submittedAt FROM applications ORDER BY id DESC").fetchall()
    return jsonify(success=True,applications=[dict(x) for x in rows])

@app.patch("/api/admin/applications/<aid>/approve")
@admin_only
def approve(aid):
    with db() as c:
        a=c.execute("SELECT status FROM applications WHERE application_id=?",(aid.upper(),)).fetchone()
        if not a: return jsonify(success=False,message="Application not found."),404
        if a["status"]=="Rejected": return jsonify(success=False,message="Rejected application cannot be approved."),409
        old=c.execute("SELECT certificate_id FROM certificates WHERE application_id=?",(aid.upper(),)).fetchone()
        if old: return jsonify(success=True,message="Certificate already issued.",certificateId=old["certificate_id"])
        cid="CERT-"+datetime.now().strftime("%Y")+"-"+secrets.token_hex(3).upper()
        c.execute("UPDATE applications SET status='Approved' WHERE application_id=?",(aid.upper(),))
        c.execute("INSERT INTO certificates(certificate_id,application_id,issued_on,status) VALUES(?,?,?,'Valid')",(cid,aid.upper(),now()))
    return jsonify(success=True,message="Approved; certificate issued.",certificateId=cid)

@app.patch("/api/admin/applications/<aid>/reject")
@admin_only
def reject(aid):
    with db() as c:
        a=c.execute("SELECT status FROM applications WHERE application_id=?",(aid.upper(),)).fetchone()
        if not a: return jsonify(success=False,message="Application not found."),404
        if a["status"]=="Approved": return jsonify(success=False,message="Approved application cannot be rejected."),409
        c.execute("UPDATE applications SET status='Rejected' WHERE application_id=?",(aid.upper(),))
    return jsonify(success=True,message="Application rejected.")

@app.get("/api/admin/certificates")
@admin_only
def certificates():
    with db() as c:
        rows=c.execute("""SELECT c.certificate_id AS certificateId,c.application_id AS applicationId,c.issued_on AS issuedOn,c.status,a.name,a.phone
        FROM certificates c JOIN applications a ON a.application_id=c.application_id ORDER BY c.id DESC""").fetchall()
    return jsonify(success=True,certificates=[dict(x) for x in rows])

@app.patch("/api/admin/certificates/<cid>/revoke")
@admin_only
def revoke(cid):
    with db() as c:
        r=c.execute("SELECT status FROM certificates WHERE certificate_id=?",(cid.upper(),)).fetchone()
        if not r: return jsonify(success=False,message="Certificate not found."),404
        c.execute("UPDATE certificates SET status='Revoked' WHERE certificate_id=?",(cid.upper(),))
    return jsonify(success=True,message="Certificate revoked.")

if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1",port=int(os.getenv("PORT","5000")),debug=os.getenv("FLASK_DEBUG","false").lower()=="true")
