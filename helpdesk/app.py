from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from config import SECRET_KEY
from database import get_connection

app = Flask(__name__)
app.secret_key = SECRET_KEY


# =========================================================
# DECORATOR LOGIN
# =========================================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))

        return f(*args, **kwargs)

    return decorated_function


# =========================================================
# DECORATOR ADMIN
# =========================================================

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):

        if "user_id" not in session:
            return redirect(url_for("login"))

        if session.get("role") != "admin":
            flash("Akses hanya untuk admin.", "danger")
            return redirect(url_for("dashboard"))

        return f(*args, **kwargs)

    return decorated_function


# =========================================================
# INDEX
# =========================================================

@app.route("/")
def index():

    if "user_id" in session:
        return redirect(url_for("dashboard"))

    return redirect(url_for("login"))



# =========================================================
# LOGIN
# =========================================================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT
                id,
                username,
                password,
                nama,
                role
            FROM helpdesk_users
            WHERE username = %s
        """

        cursor.execute(query, (username,))
        user = cursor.fetchone()

        cursor.close()
        conn.close()

        password_valid = False

        if user:
            stored_password = user["password"]

            # Password akun yang sudah di-hash
            if stored_password.startswith(("scrypt:", "pbkdf2:")):
                password_valid = check_password_hash(
                    stored_password,
                    password
                )

            # Untuk akun lama yang password-nya masih teks biasa
            else:
                password_valid = stored_password == password

        if password_valid:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["nama"] = user["nama"]
            session["role"] = user["role"]

            return redirect(url_for("dashboard"))

        flash("Username atau password salah.", "danger")

    return render_template("login.html") 

# =========================================================
# REGISTER USER
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        nama = request.form.get("nama", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        konfirmasi_password = request.form.get(
            "konfirmasi_password", ""
        )

        if not nama or not username or not password:
            flash("Semua kolom wajib diisi", "danger")
            return render_template("register.html")

        if password != konfirmasi_password:
            flash("Konfirmasi password tidak sesuai", "danger")
            return render_template("register.html")

        if len(password) < 8:
            flash("Password minimal 8 karakter", "danger")
            return render_template("register.html")

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT id FROM helpdesk_users WHERE username = %s",
            (username,)
        )
        user_exists = cursor.fetchone()

        if user_exists:
            cursor.close()
            conn.close()
            flash("Username sudah digunakan", "danger")
            return render_template("register.html")

        password_hash = generate_password_hash(password)

        cursor.execute(
            """
            INSERT INTO helpdesk_users
                (nama, username, password, role)
            VALUES (%s, %s, %s, 'user')
            """,
            (nama, username, password_hash)
        )

        conn.commit()
        cursor.close()
        conn.close()

        flash("Pendaftaran berhasil,  Silakan login", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
@login_required
def dashboard():

    # Jika admin
    if session.get("role") == "admin":
        return redirect(url_for("admin_dashboard"))

    # Jika user
    return render_template(
        "user/dashboard.html",
        nama=session.get("nama")
    )


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.route("/admin")
@admin_required
def admin_dashboard():

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            p.*,
            u.nama AS nama_user,
            u.username
        FROM pengaduan p
        JOIN helpdesk_users u
            ON p.user_id = u.id
        ORDER BY p.created_at DESC
    """)

    pengaduan = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "admin/dashboard.html",
        pengaduan=pengaduan
    )


# =========================================================
# BUAT PENGADUAN
# =========================================================

@app.route("/pengaduan/buat", methods=["GET", "POST"])
@login_required
def buat_pengaduan():

    # Admin tidak boleh membuat pengaduan
    if session.get("role") == "admin":

        flash(
            "Admin tidak dapat membuat pengaduan sebagai user.",
            "danger"
        )

        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":

        judul = request.form.get("judul")
        deskripsi = request.form.get("deskripsi")
        kategori = request.form.get("kategori")
        prioritas = request.form.get("prioritas")

        conn = get_connection()
        cursor = conn.cursor()

        query = """
            INSERT INTO pengaduan
            (
                user_id,
                judul,
                deskripsi,
                kategori,
                prioritas,
                status
            )
            VALUES (%s, %s, %s, %s, %s, 'Menunggu')
        """

        cursor.execute(
            query,
            (
                session["user_id"],
                judul,
                deskripsi,
                kategori,
                prioritas
            )
        )

        conn.commit()

        cursor.close()
        conn.close()

        flash(
            "Pengaduan berhasil dibuat.",
            "success"
        )

        return redirect(url_for("pengaduan_saya"))

    return render_template("buat_pengaduan.html")


# =========================================================
# PENGADUAN SAYA
# =========================================================

@app.route("/pengaduan-saya")
@login_required
def pengaduan_saya():

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT *
        FROM pengaduan
        WHERE user_id = %s
        ORDER BY created_at DESC
    """

    cursor.execute(
        query,
        (session["user_id"],)
    )

    pengaduan = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "user/pengaduan_saya.html",
        pengaduan=pengaduan
    )


# =========================================================
# DETAIL PENGADUAN USER
# =========================================================

@app.route("/pengaduan/<int:id>")
@login_required
def detail_pengaduan(id):

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT *
        FROM pengaduan
        WHERE id = %s
        AND user_id = %s
    """

    cursor.execute(
        query,
        (
            id,
            session["user_id"]
        )
    )

    pengaduan = cursor.fetchone()

    cursor.close()
    conn.close()

    if not pengaduan:

        flash(
            "Pengaduan tidak ditemukan.",
            "danger"
        )

        return redirect(url_for("pengaduan_saya"))

    return render_template(
        "user/detail_pengaduan.html",
        pengaduan=pengaduan
    )


# =========================================================
# ADMIN - DETAIL PENGADUAN
# =========================================================

@app.route("/admin/pengaduan/<int:id>")
@admin_required
def admin_detail_pengaduan(id):

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT
            p.*,
            u.nama AS nama_user,
            u.username
        FROM pengaduan p
        JOIN helpdesk_users u
            ON p.user_id = u.id
        WHERE p.id = %s
    """

    cursor.execute(
        query,
        (id,)
    )

    pengaduan = cursor.fetchone()

    cursor.close()
    conn.close()

    if not pengaduan:

        flash(
            "Pengaduan tidak ditemukan.",
            "danger"
        )

        return redirect(url_for("admin_dashboard"))

    return render_template(
        "admin/detail.html",
        pengaduan=pengaduan
    )


# =========================================================
# ADMIN - UPDATE PENGADUAN
# =========================================================

@app.route(
    "/admin/pengaduan/<int:id>/update",
    methods=["POST"]
)
@admin_required
def update_pengaduan(id):

    status = request.form.get("status")
    tindakan = request.form.get("tindakan")

    conn = get_connection()
    cursor = conn.cursor()

    query = """
        UPDATE pengaduan
        SET
            status = %s,
            tindakan = %s
        WHERE id = %s
    """

    cursor.execute(
        query,
        (
            status,
            tindakan,
            id
        )
    )

    conn.commit()

    cursor.close()
    conn.close()

    flash(
        "Pengaduan berhasil diperbarui.",
        "success"
    )

    return redirect(
        url_for(
            "admin_detail_pengaduan",
            id=id
        )
    )

# =========================================================
# ADMIN - DELETE PENGADUAN
# =========================================================

@app.route("/admin/pengaduan/<int:id>/hapus", methods=["POST"])
@login_required
@admin_required
def hapus_pengaduan(id):
    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM pengaduan WHERE id = %s",
            (id,)
        )

        jumlah_dihapus = cursor.rowcount

        if jumlah_dihapus > 0:
            conn.commit()
            flash("Pengaduan berhasil dihapus.", "success")
        else:
            conn.rollback()
            flash("Pengaduan tidak ditemukan atau sudah dihapus.", "warning")

    except Exception as e:
        if conn:
            conn.rollback()

        print("Error menghapus pengaduan:", e)
        flash("Pengaduan gagal dihapus.", "danger")

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return redirect(url_for("admin_dashboard"))

# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )