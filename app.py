# ============================
# app.py (Setup)
# ============================
import streamlit as st

# ----------------------------------------
# Page config
# ----------------------------------------
st.set_page_config(page_title="Savings Monopoly — Setup", layout="centered")
st.title("💰 Savings Monopoly — Setup")

# ----------------------------------------
# Initialize facilitator settings (defaults)
# Only runs once — never overwrites on every render
# ----------------------------------------
if "facilitator_settings" not in st.session_state:
    st.session_state.facilitator_settings = {
        "goal": 5000,
        "income": 2000,
        "rounds": 10,
        "fixed_costs": 1000,
        "ef_cap": 3000,
    }

fs = st.session_state.facilitator_settings

# ----------------------------------------
# Facilitator Setup (sidebar)
# FIX: Use widget keys so sidebar inputs own their state.
# Session state is only updated when values actually change,
# not on every render — prevents the infinite rerun loop.
# ----------------------------------------
st.sidebar.header("Facilitator Settings")

if "fs_goal" not in st.session_state:
    st.session_state["fs_goal"] = fs["goal"]
if "fs_income" not in st.session_state:
    st.session_state["fs_income"] = fs["income"]
if "fs_fixed_costs" not in st.session_state:
    st.session_state["fs_fixed_costs"] = fs["fixed_costs"]
if "fs_rounds" not in st.session_state:
    st.session_state["fs_rounds"] = fs["rounds"]
if "fs_ef_cap" not in st.session_state:
    # FIX: don't use `or default_cap` — that silently replaces a valid 0
    st.session_state["fs_ef_cap"] = fs.get("ef_cap", fs["fixed_costs"] * 3)

st.sidebar.number_input("Savings goal (SAR)",             min_value=0,   step=100, key="fs_goal")
st.sidebar.number_input("Monthly income (SAR)",           min_value=0,   step=100, key="fs_income")
st.sidebar.number_input("Fixed monthly costs / NEEDS (SAR)", min_value=0, step=50, key="fs_fixed_costs")
st.sidebar.number_input("Number of rounds (months)",      min_value=1,   step=1,   key="fs_rounds")
st.sidebar.number_input("Emergency fund cap (SAR)",       min_value=0,   step=100, key="fs_ef_cap")

# Read current sidebar values
goal        = st.session_state["fs_goal"]
income      = st.session_state["fs_income"]
fixed_costs = st.session_state["fs_fixed_costs"]
rounds      = st.session_state["fs_rounds"]
ef_cap      = st.session_state["fs_ef_cap"]

# Sync to facilitator_settings dict (only updates the dict, no rerun triggered)
st.session_state.facilitator_settings = {
    "goal": goal,
    "income": income,
    "rounds": rounds,
    "fixed_costs": fixed_costs,
    "ef_cap": ef_cap,
}

# ----------------------------------------
# Sidebar validation warnings
# ----------------------------------------
if income <= fixed_costs:
    st.sidebar.warning("⚠️ Fixed costs equal or exceed income — players will have no budget to allocate.")
if goal <= 0:
    st.sidebar.warning("⚠️ Savings goal should be greater than 0.")
if rounds < 1:
    st.sidebar.warning("⚠️ Rounds must be at least 1.")

# ----------------------------------------
# Player Creation Form
# ----------------------------------------
st.header("Create Player")

# CORNER CASE: available budget could be 0 or negative
available = max(0, income - fixed_costs)
st.markdown(f"**Available monthly budget:** SAR {available:,}")

if available == 0:
    st.warning("⚠️ No budget available to allocate. Adjust income or fixed costs in the sidebar.")

with st.form("create_player_form"):
    team = st.text_input("Team Name")
    name = st.text_input("Player Name")
    desc = st.text_input("Savings Goal Description")

    c1, c2, c3 = st.columns(3)
    with c1:
        wants = st.number_input(
            "Wants (SAR)",
            min_value=0, max_value=max(1, available),
            step=50,
            value=min(available // 3, available),
        )
    with c2:
        ef = st.number_input(
            "Emergency Fund (SAR)",
            min_value=0, max_value=max(1, available),
            step=50,
            value=min(available // 3, available),
        )
    with c3:
        # Default savings = whatever is left after wants and ef defaults
        default_savings = max(0, available - (available // 3) - (available // 3))
        savings = st.number_input(
            "Savings Goal (SAR)",
            min_value=0, max_value=max(1, available),
            step=50,
            value=default_savings,
        )

    submitted = st.form_submit_button("Create Player")

    if submitted:
        has_error = False

        if not team.strip():
            st.error("Please enter a team name.")
            has_error = True
        if not name.strip():
            st.error("Please enter a player name.")
            has_error = True
        if not desc.strip():
            st.error("Please enter a savings goal description.")
            has_error = True
        if available == 0:
            st.error("Cannot create a player with zero available budget. Adjust settings in the sidebar.")
            has_error = True
        if wants + ef + savings != available:
            st.error(
                f"Wants + Emergency Fund + Savings must equal the available budget "
                f"(SAR {available:,}). Currently: SAR {wants + ef + savings:,}."
            )
            has_error = True

        if not has_error:
            # FIX: Reset all game-related session state so a new game starts clean.
            # Prevents stale card history or game state carrying over from a previous session.
            for key in ["used_card_titles", "life_cards"]:
                if key in st.session_state:
                    del st.session_state[key]

            st.session_state.player = {
                "team":          team.strip(),
                "name":          name.strip(),
                "goal_desc":     desc.strip(),
                "income":        income,
                "fixed_costs":   fixed_costs,
                "allocation":    {"wants": wants, "ef": ef, "savings": savings},
                "rounds_played": 0,
                "savings":       0,
                "ef_balance":    0,
                "ef_cap":        ef_cap,
                "emotion":       5,
                "time":          5,
                "decision_log":  [],
                "current_card":  None,
                "choice_made":   False,
            }

            st.success(f"✅ Player {name.strip()} created! Redirecting to game…")

            # FIX: Wrap switch_page in try/except — if it fails, show a clear error
            # instead of an unhandled 500.
            try:
                st.switch_page("pages/game.py")
            except Exception as e:
                st.error(
                    f"Could not redirect to the game page automatically. "
                    f"Please navigate there manually. (Error: {e})"
                )

st.markdown("---")
st.caption("Each round your allocated EF and Savings amounts are added before drawing a life card.")
