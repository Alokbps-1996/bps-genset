"""
BHOLA POWER SOLUTION - Tata Motors Genset Dealer Dashboard
BPS | Data same | Backup | User ID login | Change password
"""

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date, timedelta
import os
import hashlib
import shutil
from pathlib import Path
import mimetypes
from io import BytesIO

st.set_page_config(
    page_title="BPS | Tata Genset Dealer",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Tata-inspired colors
st.markdown("""
<style>
    :root {
        --tata-blue: #0B1F3A;
        --tata-blue2: #1A3A6B;
        --tata-red: #E31937;
        --tata-gold: #C4A35A;
    }
    .stApp { background: linear-gradient(180deg, #f4f6f9 0%, #e8eef5 100%); }
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0B1F3A 0%, #1A3A6B 100%);
    }
    section[data-testid="stSidebar"] * { color: #f0f4f8 !important; }
    section[data-testid="stSidebar"] .stRadio label { color: #e8eef5 !important; }
    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #d0d7e2;
        border-left: 4px solid #E31937;
        border-radius: 8px;
        padding: 8px 12px;
    }
    .bps-header {
        background: linear-gradient(90deg, #0B1F3A, #1A3A6B);
        color: white;
        padding: 14px 20px;
        border-radius: 10px;
        margin-bottom: 16px;
        border-bottom: 3px solid #E31937;
    }
    .bps-header h1 { color: white !important; margin: 0; font-size: 1.5rem; }
    .bps-header p { color: #C4A35A; margin: 4px 0 0 0; font-size: 0.9rem; }
    .login-box {
        max-width: 400px;
        margin: 60px auto;
        padding: 32px;
        background: white;
        border-radius: 12px;
        box-shadow: 0 8px 32px rgba(11,31,58,0.15);
        border-top: 4px solid #E31937;
    }
</style>
""", unsafe_allow_html=True)

DB_PATH = "bhola_power.db"
UPLOAD_DIR = "uploads"
BACKUP_DIR = "backups"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)

# ============================================================
# DB
# ============================================================
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS gensets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            genset_sr TEXT,
            customer_name TEXT,
            address TEXT,
            district TEXT,
            contact_person TEXT,
            mobile TEXT,
            kva TEXT,
            model TEXT,
            engine_no TEXT,
            alternator_no TEXT,
            commissioning_date TEXT,
            initial_hours TEXT,
            commissioning_remarks TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS service_matrix (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            genset_id INTEGER UNIQUE,
            comm_complain_no TEXT, comm_date TEXT, comm_status TEXT,
            comm_resolve_date TEXT, comm_running_hrs TEXT, comm_report TEXT,
            first_due_hours TEXT, first_due_months TEXT, first_complain_no TEXT,
            first_date TEXT, first_running_hrs TEXT, first_status TEXT,
            first_resolve_date TEXT, first_report TEXT,
            second_due_hours TEXT, second_due_months TEXT, second_complain_no TEXT,
            second_date TEXT, second_running_hrs TEXT, second_status TEXT,
            second_resolve_date TEXT, second_report TEXT,
            third_due_hours TEXT, third_due_months TEXT, third_complain_no TEXT,
            third_date TEXT, third_running_hrs TEXT, third_status TEXT,
            third_resolve_date TEXT, third_report TEXT,
            fourth_due_hours TEXT, fourth_due_months TEXT, fourth_complain_no TEXT,
            fourth_date TEXT, fourth_running_hrs TEXT, fourth_status TEXT,
            fourth_resolve_date TEXT, fourth_report TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS breakdowns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            genset_id INTEGER,
            complaint_no TEXT,
            complaint_date TEXT,
            complaint_by TEXT,
            mobile TEXT,
            problem TEXT,
            action_taken TEXT,
            technician TEXT,
            status TEXT DEFAULT 'Open',
            closed_date TEXT,
            report_file TEXT,
            remarks TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    for col in ["comm_report", "comm_running_hrs", "first_report", "second_report",
                "third_report", "fourth_report"]:
        try:
            c.execute(f"ALTER TABLE service_matrix ADD COLUMN {col} TEXT")
        except Exception:
            pass
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        pw = hashlib.sha256("admin123".encode()).hexdigest()
        c.execute("INSERT INTO users (username, password_hash, full_name) VALUES (?,?,?)",
                  ("admin", pw, "Administrator"))
    conn.commit()
    conn.close()

init_db()

# ============================================================
# AUTH
# ============================================================
def hash_pw(p):
    return hashlib.sha256(p.encode()).hexdigest()

def login_user(u, p):
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE username=?", (u.strip(),)).fetchone()
    conn.close()
    if row and row["password_hash"] == hash_pw(p):
        return dict(row)
    return None

def login_page():
    st.markdown("""
    <div class="login-box">
        <div style="text-align:center;margin-bottom:20px;">
            <div style="font-size:2rem;">⚡</div>
            <div style="font-size:1.4rem;font-weight:700;color:#0B1F3A;">BHOLA POWER SOLUTION</div>
            <div style="color:#E31937;font-weight:600;font-size:0.95rem;">Tata Motors Genset Dealer</div>
            <div style="color:#666;font-size:0.8rem;margin-top:4px;">Authorized Service Partner</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        with st.form("login"):
            st.markdown("**User ID**")
            u = st.text_input("User ID", placeholder="User ID enter karein", label_visibility="collapsed")
            st.markdown("**Password**")
            p = st.text_input("Password", type="password", placeholder="Password", label_visibility="collapsed")
            if st.form_submit_button("Login", use_container_width=True, type="primary"):
                user = login_user(u, p)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user = user
                    st.rerun()
                else:
                    st.error("User ID ya Password galat hai")
        st.caption("Default → User ID: **admin**  |  Password: **admin123**")

# ============================================================
# HELPERS
# ============================================================
def get_gensets(search=None, district=None):
    conn = get_conn()
    q = "SELECT * FROM gensets WHERE 1=1"
    params = []
    if search:
        s = f"%{search}%"
        q += " AND (genset_sr LIKE ? OR customer_name LIKE ? OR mobile LIKE ? OR model LIKE ? OR kva LIKE ?)"
        params.extend([s, s, s, s, s])
    if district:
        q += " AND district LIKE ?"
        params.append(f"%{district}%")
    q += " ORDER BY id DESC"
    df = pd.read_sql_query(q, conn, params=params)
    conn.close()
    return df

def get_genset(gid):
    conn = get_conn()
    row = conn.execute("SELECT * FROM gensets WHERE id=?", (gid,)).fetchone()
    conn.close()
    return dict(row) if row else None

def get_matrix(gid):
    conn = get_conn()
    row = conn.execute("SELECT * FROM service_matrix WHERE genset_id=?", (gid,)).fetchone()
    conn.close()
    return dict(row) if row else {}

def ensure_matrix(gid):
    conn = get_conn()
    if not conn.execute("SELECT id FROM service_matrix WHERE genset_id=?", (gid,)).fetchone():
        conn.execute("INSERT INTO service_matrix (genset_id) VALUES (?)", (gid,))
        conn.commit()
    conn.close()

def is_done(status):
    if not status:
        return False
    return str(status).strip().lower() in ("completed", "done", "closed", "resolved", "ok")

def status_label(status):
    return "✅ DONE" if is_done(status) else "🔴 PENDING"

def get_dashboard_df(search=None, district=None, pmc_filter=None):
    gensets = get_gensets(search, district)
    rows = []
    for _, g in gensets.iterrows():
        gid = int(g["id"])
        ensure_matrix(gid)
        m = get_matrix(gid)
        row = {
            "Sr": len(rows) + 1,
            "Genset SR": g.get("genset_sr") or "",
            "Customer Name": g.get("customer_name") or "",
            "Address": g.get("address") or "",
            "District": g.get("district") or "",
            "Contact Person": g.get("contact_person") or "",
            "Mobile": g.get("mobile") or "",
            "Genset Rating": g.get("kva") or "",
            "Model": g.get("model") or "",
            "Commissioning Date": g.get("commissioning_date") or m.get("comm_date") or "",
            "Commissioning": status_label(m.get("comm_status")),
            "1st PMC": status_label(m.get("first_status")),
            "2nd PMC": status_label(m.get("second_status")),
            "3rd PMC": status_label(m.get("third_status")),
            "4th PMC": status_label(m.get("fourth_status")),
            "_id": gid,
        }
        if pmc_filter:
            key_map = {"1st PMC": "first_status", "2nd PMC": "second_status",
                       "3rd PMC": "third_status", "4th PMC": "fourth_status",
                       "Commissioning": "comm_status"}
            col = key_map.get(pmc_filter)
            if col and is_done(m.get(col)):
                continue
        rows.append(row)
    return pd.DataFrame(rows)

def get_breakdowns(genset_id=None, status=None):
    conn = get_conn()
    q = """
        SELECT b.*, g.genset_sr, g.customer_name, g.mobile as g_mobile
        FROM breakdowns b LEFT JOIN gensets g ON b.genset_id = g.id WHERE 1=1
    """
    params = []
    if genset_id:
        q += " AND b.genset_id=?"; params.append(genset_id)
    if status:
        q += " AND b.status=?"; params.append(status)
    q += " ORDER BY b.complaint_date DESC"
    df = pd.read_sql_query(q, conn, params=params)
    conn.close()
    return df

def save_file(uploaded, prefix):
    if not uploaded:
        return None
    ext = Path(uploaded.name).suffix
    fname = f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
    with open(os.path.join(UPLOAD_DIR, fname), "wb") as f:
        f.write(uploaded.getbuffer())
    return fname

def show_report(filename, label="Report"):
    if not filename:
        st.caption(f"{label}: Not uploaded")
        return
    path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(path):
        st.caption(f"{label}: {filename} (missing)")
        return
    st.write(f"**{label}:** `{filename}`")
    with open(path, "rb") as f:
        data = f.read()
    st.download_button(f"⬇️ Download {label}", data=data, file_name=filename,
                       mime=mimetypes.guess_type(filename)[0] or "application/octet-stream",
                       key=f"dl_{filename}_{label}")
    if filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
        st.image(path, caption=label, use_container_width=True)

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Dashboard")
    return output.getvalue()

def do_backup():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = os.path.join(BACKUP_DIR, f"bhola_power_backup_{ts}.db")
    shutil.copy2(DB_PATH, dest)
    return dest

# ============================================================
# SIDEBAR
# ============================================================
def sidebar():
    with st.sidebar:
        st.markdown("### ⚡ BPS")
        st.caption("Tata Motors Genset Dealer")
        st.caption(f"👤 {st.session_state.user.get('full_name') or st.session_state.user['username']}")
        st.divider()
        menu = st.radio("Menu", [
            "📊 Dashboard",
            "🔌 Genset Master",
            "📝 Enter Commissioning / PMC",
            "🛠️ Breakdown Entry",
            "📅 Pending Reports",
            "📜 Genset History",
            "📥 Export Reports",
            "💾 Backup",
            "⚙️ Settings"
        ], label_visibility="collapsed")
        st.divider()
        if st.button("Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.rerun()
        return menu

def page_header(title, sub=None):
    st.markdown(f"""
    <div class="bps-header">
        <h1>{title}</h1>
        <p>{sub or "BHOLA POWER SOLUTION · Tata Motors Genset Authorized Dealer"}</p>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# PAGES (same logic as before)
# ============================================================
def page_dashboard():
    page_header("📊 Genset Service Dashboard")
    c1, c2, c3, c4 = st.columns([2, 1.5, 1.5, 1])
    with c1:
        search = st.text_input("🔍 Search (SR / Customer / Mobile / Model / CPCB)", placeholder="Type...")
    with c2:
        district = st.text_input("District")
    with c3:
        pmc_filter = st.selectbox("Pending only", ["All", "Commissioning", "1st PMC", "2nd PMC", "3rd PMC", "4th PMC"])
    with c4:
        st.write(""); st.write("")
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()

    filt = None if pmc_filter == "All" else pmc_filter
    df = get_dashboard_df(search or None, district or None, filt)

    m1, m2, m3, m4, m5 = st.columns(5)
    total = len(get_gensets())
    m1.metric("Total Gensets", total)
    m2.metric("1st PMC Pending", len(get_dashboard_df(pmc_filter="1st PMC")))
    m3.metric("2nd PMC Pending", len(get_dashboard_df(pmc_filter="2nd PMC")))
    m4.metric("3rd PMC Pending", len(get_dashboard_df(pmc_filter="3rd PMC")))
    m5.metric("4th PMC Pending", len(get_dashboard_df(pmc_filter="4th PMC")))

    st.divider()
    if df.empty:
        st.info("No gensets found.")
        return
    display_cols = [c for c in df.columns if c != "_id"]
    st.dataframe(df[display_cols], use_container_width=True, hide_index=True, height=400)
    st.caption(f"Showing **{len(df)}** records")

    options = {f"{r['Genset SR']} | {r['Customer Name']} | {r['1st PMC']}": r["_id"] for _, r in df.iterrows()}
    selected = st.selectbox("Select Genset for details", list(options.keys()))
    if selected:
        show_genset_detail(options[selected])

def show_genset_detail(gid):
    g = get_genset(gid)
    m = get_matrix(gid)
    if not g:
        return
    st.divider()
    st.subheader(f"🔎 {g.get('genset_sr')} — {g.get('customer_name')}")
    c1, c2, c3, c4 = st.columns(4)
    c1.write(f"**Mobile:** {g.get('mobile')}")
    c2.write(f"**Contact:** {g.get('contact_person')}")
    c3.write(f"**District:** {g.get('district')}")
    c4.write(f"**Rating / Model:** {g.get('kva')} / {g.get('model')}")
    st.write(f"**Address:** {g.get('address')}")

    st.markdown("#### 🟢 Commissioning")
    if is_done(m.get("comm_status")):
        st.success("Status: **DONE**")
        d1, d2, d3, d4 = st.columns(4)
        d1.write(f"**Complaint No:** {m.get('comm_complain_no') or '—'}")
        d2.write(f"**Date:** {m.get('comm_date') or '—'}")
        d3.write(f"**Resolve Date:** {m.get('comm_resolve_date') or '—'}")
        d4.write(f"**Running Hrs:** {m.get('comm_running_hrs') or '—'}")
        show_report(m.get("comm_report"), "Commissioning Report")
    else:
        st.warning("Status: **PENDING**")

    for label, prefix in [("1st PMC", "first"), ("2nd PMC", "second"), ("3rd PMC", "third"), ("4th PMC", "fourth")]:
        st.markdown(f"#### 🔧 {label}")
        if is_done(m.get(f"{prefix}_status")):
            st.success("Status: **DONE**")
            p1, p2, p3, p4 = st.columns(4)
            p1.write(f"**Complaint No:** {m.get(f'{prefix}_complain_no') or '—'}")
            p2.write(f"**Date:** {m.get(f'{prefix}_date') or '—'}")
            p3.write(f"**Running Hrs:** {m.get(f'{prefix}_running_hrs') or '—'}")
            p4.write(f"**Resolve Date:** {m.get(f'{prefix}_resolve_date') or '—'}")
            show_report(m.get(f"{prefix}_report"), f"{label} Report")
        else:
            st.warning("Status: **PENDING**")

def page_genset_master():
    page_header("🔌 Genset Master")
    search = st.text_input("🔍 Search", key="gm_s")
    df = get_gensets(search or None)
    tab1, tab2 = st.tabs(["📋 All Gensets", "➕ Add New Genset"])
    with tab1:
        if df.empty:
            st.info("No gensets.")
        else:
            st.caption(f"Total: {len(df)}")
            for _, row in df.iterrows():
                with st.expander(f"**{row.get('genset_sr')}** | {row.get('customer_name')} | {row.get('kva')} | {row.get('model')}"):
                    c1, c2, c3 = st.columns(3)
                    c1.write(f"**Mobile:** {row.get('mobile')}")
                    c1.write(f"**Contact:** {row.get('contact_person')}")
                    c2.write(f"**District:** {row.get('district')}")
                    c2.write(f"**Engine:** {row.get('engine_no')}")
                    c3.write(f"**Address:** {row.get('address')}")
                    c3.write(f"**Commissioning:** {row.get('commissioning_date')}")
                    e1, e2, _ = st.columns([1, 1, 4])
                    if e1.button("✏️ Edit", key=f"eg_{row['id']}"):
                        st.session_state.edit_g_id = int(row["id"]); st.rerun()
                    if e2.button("🗑️ Delete", key=f"dg_{row['id']}"):
                        conn = get_conn()
                        conn.execute("DELETE FROM service_matrix WHERE genset_id=?", (int(row["id"]),))
                        conn.execute("DELETE FROM gensets WHERE id=?", (int(row["id"]),))
                        conn.commit(); conn.close()
                        st.success("Deleted"); st.rerun()
        if st.session_state.get("edit_g_id"):
            g = get_genset(st.session_state.edit_g_id)
            if g:
                st.divider()
                st.subheader(f"Edit: {g.get('genset_sr')}")
                with st.form("edit_g"):
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        genset_sr = st.text_input("Genset SR *", value=g.get("genset_sr") or "")
                        customer_name = st.text_input("Customer *", value=g.get("customer_name") or "")
                        contact_person = st.text_input("Contact", value=g.get("contact_person") or "")
                        mobile = st.text_input("Mobile", value=g.get("mobile") or "")
                    with c2:
                        model = st.text_input("Model / CPCB Type", value=g.get("model") or "")
                        kva = st.text_input("Rating", value=g.get("kva") or "")
                        engine_no = st.text_input("Engine No", value=g.get("engine_no") or "")
                        alternator_no = st.text_input("Alternator No", value=g.get("alternator_no") or "")
                    with c3:
                        address = st.text_area("Address", value=g.get("address") or "", height=70)
                        district = st.text_input("District", value=g.get("district") or "")
                        commissioning_date = st.text_input("Commissioning Date", value=g.get("commissioning_date") or "")
                        initial_hours = st.text_input("Initial Hours", value=g.get("initial_hours") or "")
                    remarks = st.text_area("Remarks", value=g.get("commissioning_remarks") or "")
                    b1, b2 = st.columns(2)
                    if b1.form_submit_button("💾 Update", type="primary"):
                        conn = get_conn()
                        conn.execute("""UPDATE gensets SET genset_sr=?, customer_name=?, address=?, district=?,
                            contact_person=?, mobile=?, kva=?, model=?, engine_no=?, alternator_no=?,
                            commissioning_date=?, initial_hours=?, commissioning_remarks=? WHERE id=?""",
                            (genset_sr, customer_name, address, district, contact_person, mobile,
                             kva, model, engine_no, alternator_no, commissioning_date, initial_hours, remarks, g["id"]))
                        conn.commit(); conn.close()
                        st.session_state.edit_g_id = None
                        st.success("Updated"); st.rerun()
                    if b2.form_submit_button("❌ Cancel"):
                        st.session_state.edit_g_id = None; st.rerun()
    with tab2:
        with st.form("add_g", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                genset_sr = st.text_input("Genset SR *")
                customer_name = st.text_input("Customer Name *")
                contact_person = st.text_input("Contact Person")
                mobile = st.text_input("Mobile")
            with c2:
                model = st.text_input("Model / CPCB (II or IV+)")
                kva = st.text_input("Genset Rating")
                engine_no = st.text_input("Engine No")
                alternator_no = st.text_input("Alternator No")
            with c3:
                address = st.text_area("Address", height=70)
                district = st.text_input("District")
                commissioning_date = st.date_input("Commissioning Date", value=date.today())
                initial_hours = st.text_input("Initial Hours", value="0")
            remarks = st.text_area("Remarks")
            if st.form_submit_button("💾 Save Genset", type="primary"):
                if genset_sr.strip() and customer_name.strip():
                    conn = get_conn()
                    cur = conn.execute("""INSERT INTO gensets
                        (genset_sr, customer_name, address, district, contact_person, mobile,
                         kva, model, engine_no, alternator_no, commissioning_date, initial_hours, commissioning_remarks)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (genset_sr.strip(), customer_name.strip(), address, district, contact_person,
                         mobile, kva, model, engine_no, alternator_no, commissioning_date.isoformat(), initial_hours, remarks))
                    gid = cur.lastrowid
                    conn.execute("INSERT INTO service_matrix (genset_id) VALUES (?)", (gid,))
                    conn.commit(); conn.close()
                    st.success(f"Genset **{genset_sr}** saved!")
                    st.rerun()
                else:
                    st.error("Genset SR and Customer Name required")

def page_enter_pmc():
    page_header("📝 Enter Commissioning / PMC")
    gensets = get_gensets()
    if gensets.empty:
        st.warning("Pehle Genset add karein.")
        return
    opts = {f"{r['genset_sr']} | {r['customer_name']} | {r['district']}": int(r["id"]) for _, r in gensets.iterrows()}
    selected = st.selectbox("Select Genset", list(opts.keys()))
    gid = opts[selected]
    ensure_matrix(gid)
    g = get_genset(gid)
    m = get_matrix(gid)
    st.info(f"Editing: **{g.get('genset_sr')}** — {g.get('customer_name')}")

    with st.form("pmc_form"):
        st.markdown("### 🟢 Commissioning")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            comm_complain_no = st.text_input("Complaint No", value=m.get("comm_complain_no") or "")
        with c2:
            comm_date = st.text_input("Complaint Date", value=m.get("comm_date") or "")
        with c3:
            comm_resolve_date = st.text_input("Resolve Date", value=m.get("comm_resolve_date") or "")
        with c4:
            comm_running_hrs = st.text_input("Running Hours", value=m.get("comm_running_hrs") or "")
        opts_s = ["", "Pending", "Completed", "Done", "Closed"]
        cur = m.get("comm_status") or ""
        idx = opts_s.index(cur) if cur in opts_s else 0
        comm_status = st.selectbox("Commissioning Status", opts_s, index=idx)
        comm_report = st.file_uploader("Upload Commissioning Report", type=["pdf", "png", "jpg", "jpeg"])
        if m.get("comm_report"):
            st.caption(f"Current: {m.get('comm_report')}")

        service_fields = {}
        for label, prefix in [("1st PMC", "first"), ("2nd PMC", "second"), ("3rd PMC", "third"), ("4th PMC", "fourth")]:
            st.markdown(f"### 🔧 {label}")
            r1, r2, r3, r4 = st.columns(4)
            with r1:
                due_h = st.text_input("Due Hours ±50", value=m.get(f"{prefix}_due_hours") or "", key=f"{prefix}_dh")
            with r2:
                due_m = st.text_input("Due Months ±1", value=m.get(f"{prefix}_due_months") or "", key=f"{prefix}_dm")
            with r3:
                cno = st.text_input("Complaint No", value=m.get(f"{prefix}_complain_no") or "", key=f"{prefix}_cn")
            with r4:
                sdate = st.text_input("Date", value=m.get(f"{prefix}_date") or "", key=f"{prefix}_dt")
            r5, r6, r7 = st.columns(3)
            with r5:
                run_h = st.text_input("Running Hours", value=m.get(f"{prefix}_running_hrs") or "", key=f"{prefix}_rh")
            with r6:
                cur_s = m.get(f"{prefix}_status") or ""
                idx_s = opts_s.index(cur_s) if cur_s in opts_s else 0
                status = st.selectbox("Status", opts_s, index=idx_s, key=f"{prefix}_st")
            with r7:
                res_d = st.text_input("Resolve Date", value=m.get(f"{prefix}_resolve_date") or "", key=f"{prefix}_rd")
            up = st.file_uploader(f"Upload {label} Report", type=["pdf", "png", "jpg", "jpeg"], key=f"{prefix}_up")
            if m.get(f"{prefix}_report"):
                st.caption(f"Current: {m.get(f'{prefix}_report')}")
            service_fields[prefix] = dict(due_hours=due_h, due_months=due_m, complain_no=cno, date=sdate,
                                          running_hrs=run_h, status=status, resolve_date=res_d, upload=up)

        if st.form_submit_button("💾 Save All + Reports", type="primary", use_container_width=True):
            new_comm = m.get("comm_report")
            if comm_report:
                new_comm = save_file(comm_report, f"comm_{gid}")
            reports = {}
            for p in ["first", "second", "third", "fourth"]:
                reports[p] = m.get(f"{p}_report")
                if service_fields[p]["upload"]:
                    reports[p] = save_file(service_fields[p]["upload"], f"{p}_{gid}")
            conn = get_conn()
            conn.execute("""UPDATE service_matrix SET
                comm_complain_no=?, comm_date=?, comm_status=?, comm_resolve_date=?, comm_running_hrs=?, comm_report=?,
                first_due_hours=?, first_due_months=?, first_complain_no=?, first_date=?,
                first_running_hrs=?, first_status=?, first_resolve_date=?, first_report=?,
                second_due_hours=?, second_due_months=?, second_complain_no=?, second_date=?,
                second_running_hrs=?, second_status=?, second_resolve_date=?, second_report=?,
                third_due_hours=?, third_due_months=?, third_complain_no=?, third_date=?,
                third_running_hrs=?, third_status=?, third_resolve_date=?, third_report=?,
                fourth_due_hours=?, fourth_due_months=?, fourth_complain_no=?, fourth_date=?,
                fourth_running_hrs=?, fourth_status=?, fourth_resolve_date=?, fourth_report=?, updated_at=?
                WHERE genset_id=?""", (
                comm_complain_no, comm_date, comm_status, comm_resolve_date, comm_running_hrs, new_comm,
                service_fields["first"]["due_hours"], service_fields["first"]["due_months"],
                service_fields["first"]["complain_no"], service_fields["first"]["date"],
                service_fields["first"]["running_hrs"], service_fields["first"]["status"],
                service_fields["first"]["resolve_date"], reports["first"],
                service_fields["second"]["due_hours"], service_fields["second"]["due_months"],
                service_fields["second"]["complain_no"], service_fields["second"]["date"],
                service_fields["second"]["running_hrs"], service_fields["second"]["status"],
                service_fields["second"]["resolve_date"], reports["second"],
                service_fields["third"]["due_hours"], service_fields["third"]["due_months"],
                service_fields["third"]["complain_no"], service_fields["third"]["date"],
                service_fields["third"]["running_hrs"], service_fields["third"]["status"],
                service_fields["third"]["resolve_date"], reports["third"],
                service_fields["fourth"]["due_hours"], service_fields["fourth"]["due_months"],
                service_fields["fourth"]["complain_no"], service_fields["fourth"]["date"],
                service_fields["fourth"]["running_hrs"], service_fields["fourth"]["status"],
                service_fields["fourth"]["resolve_date"], reports["fourth"],
                datetime.now().isoformat(), gid))
            if comm_date:
                conn.execute("UPDATE gensets SET commissioning_date=? WHERE id=?", (comm_date, gid))
            conn.commit(); conn.close()
            st.success("✅ Saved!")
            st.rerun()

def page_breakdown():
    page_header("🛠️ Breakdown Entry")
    tab1, tab2 = st.tabs(["📋 All", "➕ New"])
    with tab1:
        filt = st.selectbox("Filter", ["All", "Open", "Closed"])
        df = get_breakdowns(status=None if filt == "All" else filt)
        if df.empty:
            st.info("No records")
        else:
            for _, row in df.iterrows():
                icon = "🔴" if row.get("status") == "Open" else "🟢"
                with st.expander(f"{icon} {row.get('complaint_no')} | {row.get('genset_sr')} | {row.get('customer_name')}"):
                    st.write(f"**Problem:** {row.get('problem')}")
                    st.write(f"**Action:** {row.get('action_taken')}")
                    st.write(f"**Tech:** {row.get('technician')} | **Status:** {row.get('status')}")
                    show_report(row.get("report_file"), "Report")
                    e1, e2, _ = st.columns([1, 1, 4])
                    if e1.button("✏️ Edit", key=f"eb_{row['id']}"):
                        st.session_state.edit_bd = int(row["id"]); st.rerun()
                    if e2.button("🗑️ Delete", key=f"db_{row['id']}"):
                        conn = get_conn()
                        conn.execute("DELETE FROM breakdowns WHERE id=?", (int(row["id"]),))
                        conn.commit(); conn.close(); st.rerun()
        if st.session_state.get("edit_bd"):
            conn = get_conn()
            b = dict(conn.execute("SELECT * FROM breakdowns WHERE id=?", (st.session_state.edit_bd,)).fetchone())
            conn.close()
            st.divider()
            with st.form("edit_bd"):
                problem = st.text_area("Problem", value=b.get("problem") or "")
                action = st.text_area("Action", value=b.get("action_taken") or "")
                tech = st.text_input("Technician", value=b.get("technician") or "")
                status = st.selectbox("Status", ["Open", "Closed"], index=0 if b.get("status") == "Open" else 1)
                new_r = st.file_uploader("Report", type=["pdf", "png", "jpg", "jpeg"])
                if st.form_submit_button("Save"):
                    closed = date.today().isoformat() if status == "Closed" else b.get("closed_date")
                    rfile = b.get("report_file")
                    if new_r:
                        rfile = save_file(new_r, f"bd_{b['id']}")
                    conn = get_conn()
                    conn.execute("UPDATE breakdowns SET problem=?, action_taken=?, technician=?, status=?, closed_date=?, report_file=? WHERE id=?",
                                 (problem, action, tech, status, closed, rfile, b["id"]))
                    conn.commit(); conn.close()
                    st.session_state.edit_bd = None; st.rerun()
    with tab2:
        gensets = get_gensets()
        if gensets.empty:
            st.warning("Add gensets first"); return
        opts = {f"{r['genset_sr']} | {r['customer_name']}": int(r["id"]) for _, r in gensets.iterrows()}
        sel = st.selectbox("Genset", list(opts.keys()))
        gid = opts[sel]
        g = get_genset(gid)
        with st.form("new_bd", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                cno = st.text_input("Complaint No *", value=f"CMP-{datetime.now().strftime('%Y%m%d-%H%M')}")
                cdate = st.date_input("Date", value=date.today())
                cby = st.text_input("By", value=g.get("contact_person") or "")
                mob = st.text_input("Mobile", value=g.get("mobile") or "")
            with c2:
                tech = st.text_input("Technician")
                status = st.selectbox("Status", ["Open", "Closed"])
            problem = st.text_area("Problem *")
            action = st.text_area("Action Taken")
            report = st.file_uploader("Report", type=["pdf", "png", "jpg", "jpeg"])
            if st.form_submit_button("💾 Save", type="primary"):
                if problem.strip() and cno.strip():
                    rname = save_file(report, f"bd_{gid}")
                    closed = date.today().isoformat() if status == "Closed" else None
                    conn = get_conn()
                    conn.execute("""INSERT INTO breakdowns
                        (genset_id, complaint_no, complaint_date, complaint_by, mobile, problem, action_taken, technician, status, closed_date, report_file)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                        (gid, cno, cdate.isoformat(), cby, mob, problem, action, tech, status, closed, rname))
                    conn.commit(); conn.close()
                    st.success("Saved!"); st.rerun()
                else:
                    st.error("Complaint No and Problem required")

def page_pending():
    page_header("📅 Pending Reports")
    choice = st.selectbox("Stage", ["Commissioning", "1st PMC", "2nd PMC", "3rd PMC", "4th PMC"])
    key_map = {"Commissioning": "comm_status", "1st PMC": "first_status", "2nd PMC": "second_status",
               "3rd PMC": "third_status", "4th PMC": "fourth_status"}
    col = key_map[choice]
    conn = get_conn()
    df = pd.read_sql_query(f"""
        SELECT g.genset_sr, g.customer_name, g.mobile, g.district, g.kva, g.model, g.address
        FROM gensets g LEFT JOIN service_matrix m ON g.id = m.genset_id
        WHERE m.{col} IS NULL OR m.{col} = '' OR LOWER(m.{col}) NOT IN ('completed','done','closed','resolved','ok')
        ORDER BY g.customer_name
    """, conn)
    conn.close()
    st.subheader(f"🔴 {choice} — Pending ({len(df)})")
    if df.empty:
        st.success(f"All **{choice}** completed!")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)

def page_history():
    page_header("📜 Genset History")
    gensets = get_gensets()
    if gensets.empty:
        st.info("No gensets"); return
    opts = {f"{r['genset_sr']} | {r['customer_name']}": int(r["id"]) for _, r in gensets.iterrows()}
    sel = st.selectbox("Genset SR", list(opts.keys()))
    show_genset_detail(opts[sel])
    st.divider()
    st.subheader("Breakdown History")
    bd = get_breakdowns(genset_id=opts[sel])
    if not bd.empty:
        for _, row in bd.iterrows():
            with st.expander(f"{row.get('complaint_no')} | {row.get('complaint_date')} | {row.get('status')}"):
                st.write(f"**Problem:** {row.get('problem')}")
                show_report(row.get("report_file"), "Report")
    else:
        st.info("No breakdowns")

def page_export():
    page_header("📥 Export Reports")
    df = get_dashboard_df()
    if df.empty:
        st.info("No data"); return
    export_df = df.drop(columns=["_id"], errors="ignore")
    st.dataframe(export_df.head(15), use_container_width=True, hide_index=True)
    try:
        excel_data = to_excel(export_df)
        st.download_button("⬇️ Download Dashboard Excel", data=excel_data,
                           file_name=f"BPS_Dashboard_{date.today().isoformat()}.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary")
    except Exception as e:
        csv = export_df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download CSV", data=csv, file_name="BPS_Dashboard.csv", mime="text/csv")
        st.caption(f"Excel ke liye: pip install openpyxl ({e})")

def page_backup():
    page_header("💾 Database Backup")
    st.write("Backup se aapka data safe rehta hai. Import se pehle hamesha backup lein.")
    if st.button("💾 Create Backup Now", type="primary", use_container_width=True):
        path = do_backup()
        st.success(f"Backup ban gaya: `{path}`")
        with open(path, "rb") as f:
            st.download_button("⬇️ Download Backup File", data=f.read(),
                               file_name=os.path.basename(path), mime="application/octet-stream")
    st.divider()
    st.subheader("Previous Backups")
    backups = sorted(Path(BACKUP_DIR).glob("bhola_power_backup_*.db"), reverse=True)
    if not backups:
        st.info("Abhi koi backup nahi.")
    else:
        for b in backups[:20]:
            st.write(f"📁 `{b.name}`  ({b.stat().st_size // 1024} KB)")

def page_settings():
    page_header("⚙️ Settings — User ID / Password")
    st.subheader("Password Badlein")
    with st.form("chg_pw"):
        old = st.text_input("Current Password", type="password")
        new = st.text_input("New Password", type="password")
        conf = st.text_input("Confirm New Password", type="password")
        if st.form_submit_button("Update Password", type="primary"):
            if not login_user(st.session_state.user["username"], old):
                st.error("Current password galat hai")
            elif new != conf or len(new) < 6:
                st.error("New password match nahi / kam se kam 6 character")
            else:
                conn = get_conn()
                conn.execute("UPDATE users SET password_hash=? WHERE id=?",
                             (hash_pw(new), st.session_state.user["id"]))
                conn.commit(); conn.close()
                st.success("Password change ho gaya!")

    st.divider()
    st.subheader("Naya User ID banayein (optional)")
    with st.form("new_user"):
        nu = st.text_input("New User ID")
        nn = st.text_input("Full Name")
        np = st.text_input("Password", type="password")
        if st.form_submit_button("Create User"):
            if not nu.strip() or len(np) < 6:
                st.error("User ID aur password (6+) zaroori")
            else:
                try:
                    conn = get_conn()
                    conn.execute("INSERT INTO users (username, password_hash, full_name) VALUES (?,?,?)",
                                 (nu.strip(), hash_pw(np), nn.strip() or nu.strip()))
                    conn.commit(); conn.close()
                    st.success(f"User **{nu}** ban gaya")
                except sqlite3.IntegrityError:
                    st.error("Ye User ID pehle se hai")

    st.divider()
    st.write(f"**Database:** `{DB_PATH}`")
    st.write(f"**Backups folder:** `{BACKUP_DIR}/`")
    st.warning("bhola_power.db delete mat karein. Backup zaroor lete rahein.")
    st.caption("BPS · Tata Motors Genset Authorized Dealer · Bhola Power Solution")

# ============================================================
# MAIN
# ============================================================
def main():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.user = None
    if not st.session_state.logged_in:
        login_page()
        return
    menu = sidebar()
    if menu == "📊 Dashboard":
        page_dashboard()
    elif menu == "🔌 Genset Master":
        page_genset_master()
    elif menu == "📝 Enter Commissioning / PMC":
        page_enter_pmc()
    elif menu == "🛠️ Breakdown Entry":
        page_breakdown()
    elif menu == "📅 Pending Reports":
        page_pending()
    elif menu == "📜 Genset History":
        page_history()
    elif menu == "📥 Export Reports":
        page_export()
    elif menu == "💾 Backup":
        page_backup()
    elif menu == "⚙️ Settings":
        page_settings()

if __name__ == "__main__":
    main()
