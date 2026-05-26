import streamlit as st
import base64
from parser import parse_protocol

st.set_page_config(layout="wide")

# ---------- STYLING ----------
def inject_css():
    st.markdown(
        """
        <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;800&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">

        <style>
        :root {
            --jj-red: #CA001B;
            --ink: #1A1614;
            --ink-soft: #4A4441;
            --ink-mute: #8A847F;
            --paper: #FBF8F4;
            --rule: #D9D3CA;
        }

        .stApp {
            background:
                radial-gradient(circle at 10% 10%, rgba(202,0,27,0.04), transparent 40%),
                var(--paper);
        }

        html, body, [class*="css"], .stMarkdown {
            font-family: 'DM Sans', sans-serif;
            color: var(--ink);
        }

        h1, h2, h3 {
            font-family: 'Playfair Display', serif !important;
        }

        [data-testid="stFileUploader"] section {
            background: #fff;
            border: 1.5px dashed var(--rule);
            border-radius: 8px;
        }

        .stButton > button {
            border-radius: 6px;
            border: 1px solid var(--rule);
        }

        .stButton > button:hover {
            background: var(--jj-red);
            color: white;
        }

        textarea {
            border-radius: 6px !important;
            border: 1px solid var(--rule) !important;
        }

        textarea:focus {
            border-color: var(--jj-red) !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

inject_css()

# ---------- LOGO ----------
def get_base64_of_bin_file(bin_file):
    with open(bin_file, "rb") as f:
        return base64.b64encode(f.read()).decode()

logo_base64 = get_base64_of_bin_file("jjlogo.png")

st.markdown(
    f"""
    <div style="display: flex; justify-content: center;">
        <img src="data:image/png;base64,{logo_base64}" width="250">
    </div>
    """,
    unsafe_allow_html=True
)

# ---------- TITLE ----------
st.markdown(
    """
    <h1 style='text-align: center; font-size: 45px; font-weight: bold;'>
        ATTRITION SQL AGENT
    </h1>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <h3 style='text-align: center; color: grey;'>
        Clinical Protocol → Attrition → Cohort
    </h3>
    """,
    unsafe_allow_html=True
)

st.markdown("---")

# ---------- FILE UPLOAD ----------
st.markdown("## 📂 Upload Clinical Protocol")

file = st.file_uploader("Upload Protocol (.docx)", type=["docx"])

st.markdown("---")

# ---------- HELPERS ----------
def _load_parsed_into_state(file):
    inc_steps, exc_steps, _attrition, data_sources = parse_protocol(file)

    st.session_state["file_name"] = file.name
    st.session_state["data_sources"] = data_sources
    st.session_state["inc_steps"] = list(inc_steps)
    st.session_state["exc_steps"] = list(exc_steps)
    st.session_state["inc_steps_original"] = list(inc_steps)
    st.session_state["exc_steps_original"] = list(exc_steps)


def render_editable_steps(section_key: str, label: str):
    steps = st.session_state[section_key]

    if not steps:
        st.info(f"No {label.lower()} steps. Use ➕ Add step below.")

    for i, step in enumerate(steps):
        row = st.columns([10, 1])

        new_val = row[0].text_area(
            label=f"Step {i + 1}",
            value=step,
            key=f"{section_key}_text_{i}",
            height=70,
            label_visibility="collapsed",
        )

        if new_val != step:
            steps[i] = new_val

        if row[1].button("🗑", key=f"{section_key}_del_{i}"):
            steps.pop(i)
            st.rerun()

    if st.button(f"➕ Add {label} step", key=f"{section_key}_add"):
        steps.append("")
        st.rerun()


def build_attrition(inc_steps, exc_steps):
    attrition = []
    step_no = 1

    for s in inc_steps:
        s = s.strip()
        if s:
            attrition.append((step_no, "inclusion", s))
            step_no += 1

    for s in exc_steps:
        s = s.strip()
        if s:
            attrition.append((step_no, "exclusion", s))
            step_no += 1

    return attrition


# ---------- MAIN ----------
if file:

    if st.session_state.get("file_name") != file.name:
        _load_parsed_into_state(file)

    data_sources = st.session_state["data_sources"]

    st.markdown("## Data Source")

    if data_sources:
        for ds in data_sources:
            st.success(ds)
    else:
        st.warning("No Data Source Detected")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Inclusion Criteria")
        render_editable_steps("inc_steps", "Inclusion")

    with col2:
        st.markdown("### Exclusion Criteria")
        render_editable_steps("exc_steps", "Exclusion")

    reset_col, _ = st.columns([2, 8])
    with reset_col:
        if st.button("🔄 Reset to parsed values"):
            st.session_state["inc_steps"] = list(st.session_state["inc_steps_original"])
            st.session_state["exc_steps"] = list(st.session_state["exc_steps_original"])
            st.rerun()

    st.markdown("---")
    st.markdown("## Attrition Steps")

    attrition = build_attrition(
        st.session_state["inc_steps"],
        st.session_state["exc_steps"],
    )

    if not attrition:
        st.warning("No attrition steps yet.")
    else:
        for step_no, step_type, desc in attrition:
            st.write(f"**Step {step_no}** ({step_type}): {desc}")

    st.session_state["attrition_final"] = attrition

    st.markdown("---")

    st.markdown(
        """
        <h1 style='text-align: center; font-size: 45px; font-weight: bold;'>
            ATTRITION (SQL) w/ QC's
        </h1>
        """,
        unsafe_allow_html=True
    )
