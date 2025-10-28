import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import json

# -----------------------------
# CONFIG
# -----------------------------
st.set_page_config(page_title="AI Chat - Service Profiling", layout="wide")

# -----------------------------
# LOGIN / LOGOUT STATE
# -----------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "chat_state" not in st.session_state:
    st.session_state.chat_state = {"step": 0, "inputs": {}}

VALID_USERS = {"emp001": "123", "admin": "123"}

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

def weighted_score(E,C,D,wE,wC,wD): return round(wE*E + wC*C + wD*D,2)
def max_dom(E,C,D): return round(max(E,C,D),2)
def cvss_score(E,C,D): return round(((C+D)/2 + E)/2,2)

def visualize_profile_position(score, title="Service Profile"):
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
    for (s,e,l),c in zip(bands,colors): ax.axvspan(s,e,color=c,alpha=0.8)
    models=list(scores.keys()); vals=list(scores.values())
    y=np.arange(len(models))
    ax.barh(y,vals,height=0.4,color="#2563eb")
    for i,v in enumerate(vals): ax.text(v+0.05,i,f"{v}",va="center")
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
        if emp in VALID_USERS and VALID_USERS[emp]==pwd:
            st.session_state.logged_in=True
            st.session_state.employee_id=emp
            st.session_state.chat_state={"step":0,"inputs":{}}
            st.success("✅ Login successful")
            st.rerun()
        else:
            st.error("❌ Invalid credentials")
    st.stop()

# -----------------------------
# CHAT INTERFACE
# -----------------------------
st.markdown(f"""
<div style='display:flex;justify-content:space-between;align-items:center;'>
  <h3>🤖 AI Chat Assistant — Service Profiling</h3>
  <form action='#' style='margin:0;'>
    <button style='background:#2563eb;color:white;border:none;padding:5px 12px;border-radius:6px;font-size:0.8rem;' 
      onclick="window.location.reload();">Logout</button>
  </form>
</div>
""", unsafe_allow_html=True)
st.divider()

chat_state = st.session_state.chat_state

questions = [
    "What is the service name?",
    "Describe the service briefly.",
    "Business Criticality (1=Mission Critical ... 5=Non Critical)?",
    "Data Classification (1=Highly Restricted ... 5=Public)?",
    "Reachability (0–2)?",
    "Operational Availability (0–1)?",
    "Privilege Threshold (0–1)?",
    "Interaction Dependency (0–1)?"
]

# show past chat
for i in range(chat_state["step"]):
    st.chat_message("assistant").markdown(questions[i])
    st.chat_message("user").markdown(str(chat_state["inputs"].get(i, "")))

if chat_state["step"] < len(questions):
    prompt = questions[chat_state["step"]]
    st.chat_message("assistant").markdown(prompt)
    user_inp = st.chat_input("Your answer here...")
    if user_inp:
        chat_state["inputs"][chat_state["step"]] = user_inp
        chat_state["step"] += 1
        st.rerun()
else:
    # process final output
    inputs = chat_state["inputs"]
    try:
        service_name = inputs[0]
        desc = inputs[1]
        bc = int(inputs[2]); dc = int(inputs[3])
        r = float(inputs[4]); o = float(inputs[5]); p = float(inputs[6]); i = float(inputs[7])
    except Exception as e:
        st.error(f"Input parsing error: {e}")
        st.stop()

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

    col1,col2=st.columns(2)
    with col1: visualize_profile_position(w_score)
    with col2: visualize_three_scores(results)

    if st.button("🔄 Restart Chat"):
        st.session_state.chat_state={"step":0,"inputs":{}}
        st.rerun()
