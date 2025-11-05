import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

# -----------------------------
# CONFIG
# -----------------------------
st.set_page_config(page_title="AI Chat - Service Profiling", layout="wide")

# -----------------------------
# LOGIN / SESSION
# -----------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

VALID_USERS = {"emp001": "123", "admin": "Adminprivilage@45786"}

# -----------------------------
# FUNCTIONS
# -----------------------------
def map_score_to_profile(score):
    if score < 1.5: return "P1"
    elif score < 2.0: return "P2"
    elif score < 3.0: return "P3"
    elif score < 4.0: return "P4"
    else: return "P5"

def compute_exposure(r, o, p, i):
    return round((0.5*r)+(0.17*o)+(0.17*p)+(0.16*i),2)

def weighted_score(E,C,D,wE,wC,wD): 
    return round(wE*E + wC*C + wD*D,2)

def max_dom(E,C,D): 
    return round(max(E,C,D),2)

def cvss_score(E,C,D): 
    return round(((C+D)/2 + E)/2,2)

def visualize_profile_position(score):
    fig, ax = plt.subplots(figsize=(9, 2))
    bands = [("P1",0,1.5),("P2",1.5,2),("P3",2,3),("P4",3,4),("P5",4,5)]
    colors = ["#fee6e6","#fee8cc","#fff5cc","#ecf7d9","#e4f7df"]
    for (p,s,e),c in zip(bands,colors):
        ax.axvspan(s,e,color=c,alpha=0.8)
        ax.text((s+e)/2,0.8,p,ha="center",va="center",fontsize=10,weight="bold")
    ax.axvline(score,color="blue",lw=3,ls="--")
    ax.set_xlim(0,5); ax.set_ylim(0,1)
    ax.set_yticks([]); ax.set_xlabel("Score (1–5)")
    st.pyplot(fig)

def visualize_three_scores(scores):
    fig, ax = plt.subplots(figsize=(9,3))
    bands = [(0,1.5,'P1'),(1.5,2,'P2'),(2,3,'P3'),(3,4,'P4'),(4,5,'P5')]
    colors = ["#f7d7d7","#fde2b6","#fff8b3","#e6f7cf","#dff4e2"]
    for (s,e,l),c in zip(bands,colors): 
        ax.axvspan(s,e,color=c,alpha=0.8)
    models=list(scores.keys()); vals=list(scores.values())
    y=np.arange(len(models))
    ax.barh(y,vals,height=0.4,color="#2563eb")
    for i,v in enumerate(vals): 
        ax.text(v+0.05,i,f"{v}",va="center")
    ax.set_yticks(y); ax.set_yticklabels(models)
    ax.set_xlim(0,5); ax.set_xlabel("Score (1–5)")
    st.pyplot(fig)

# -----------------------------
# LOGIN SCREEN
# -----------------------------
if not st.session_state.logged_in:
    st.markdown("<h2 style='text-align:center;'>🔐 Employee Login</h2>", unsafe_allow_html=True)
    emp = st.text_input("Employee ID")
    pwd = st.text_input("Password", type="password")
    if st.button("Login", use_container_width=True):
        if emp in VALID_USERS and VALID_USERS[emp] == pwd:
            st.session_state.logged_in = True
            st.session_state.employee_id = emp
            st.success("✅ Login successful")
            st.rerun()
        else:
            st.error("❌ Invalid credentials")
    st.stop()

# -----------------------------
# MAIN HEADER
# -----------------------------
st.markdown(f"""
<div style='display:flex;justify-content:space-between;align-items:center;'>
  <h3>🧭 Service Profiling Dashboard (Sidebar Mode)</h3>
  <div>
    <button style='background:#ef4444;color:white;border:none;padding:6px 12px;border-radius:6px;margin-right:8px;cursor:pointer;'
      onclick="window.location.reload();">Logout</button>
  </div>
</div>
""", unsafe_allow_html=True)
st.divider()

# -----------------------------
# SIDEBAR INPUTS
# -----------------------------
st.sidebar.header("⚙️ Service Parameters")

service_name = st.sidebar.text_input("Service Name")
desc = st.sidebar.text_area("Description")

bc = st.sidebar.selectbox(
    "Business Criticality",
    ["1 - Mission Critical", "2 - Highly Critical", "3 - Important", "4 - Low Impact", "5 - Non Critical"]
)
dc = st.sidebar.selectbox(
    "Data Classification",
    ["1 - Highly Restricted", "2 - Restricted", "3 - Internal", "4 - Confidential", "5 - Public"]
)
r = st.sidebar.slider("Reachability (0–2)", 0.0, 2.0, 1.0, 0.1)
o = st.sidebar.slider("Operational Availability (0–1)", 0.0, 1.0, 0.5, 0.1)
p = st.sidebar.slider("Privilege Threshold (0–1)", 0.0, 1.0, 0.5, 0.1)
i = st.sidebar.slider("Interaction Dependency (0–1)", 0.0, 1.0, 0.5, 0.1)

if st.sidebar.button("🔍 Compute Profile"):
    bc = int(bc.split(" - ")[0])
    dc = int(dc.split(" - ")[0])
    E = compute_exposure(r,o,p,i)
    w_score = weighted_score(E,bc,dc,0.4,0.3,0.3)
    m_score = max_dom(E,bc,dc)
    c_score = cvss_score(E,bc,dc)
    results = {"Weighted":w_score,"Max-Dominant":m_score,"CVSS-Inspired":c_score}

    st.success(f"✅ Computation complete for **{service_name}**")
    st.json({
        "Exposure":E,
        "Weighted":w_score,"MaxDominant":m_score,"CVSSInspired":c_score,
        "Profiles":{k:map_score_to_profile(v) for k,v in results.items()}
    })

    col1,col2 = st.columns(2)
    with col1: visualize_profile_position(w_score)
    with col2: visualize_three_scores(results)

# -----------------------------
# RESET BUTTON
# -----------------------------
if st.sidebar.button("🔄 Reset Inputs"):
    st.rerun()
