# pages/game.py
import streamlit as st
import json
import random
import time

# -------------------------------------------------
# Helper functions
# -------------------------------------------------
def fmt(value):
    try:
        return f"SAR {int(value):,}"
    except Exception:
        return f"SAR {value}"

def emoji_bar(value, emoji, max_value=10):
    v = int(max(0, min(max_value, value)))
    return emoji * v + "▫️" * (max_value - v) + f" ({v}/{max_value})"

def draw_weighted_card(cards, round_number, total_rounds):
    if "used_card_titles" not in st.session_state:
        st.session_state.used_card_titles = []

    used = set(st.session_state.used_card_titles)
    available = [c for c in cards if c["title"] not in used]

    if not available:
        st.session_state.used_card_titles = []
        available = list(cards)

    progress = round_number / max(1, total_rounds)

    if progress < 0.3:
        weights = {"positive": 0.35, "neutral": 0.30, "negative_type_1": 0.25, "negative_type_2": 0.10}
    else:
        weights = {"positive": 0.20, "neutral": 0.20, "negative_type_1": 0.35, "negative_type_2": 0.25}

    pool = [c for c in available if c["type"] in weights and weights[c["type"]] > 0]
    if not pool:
        pool = available

    card_weights = [weights.get(c["type"], 0.1) for c in pool]
    chosen = random.choices(pool, weights=card_weights, k=1)[0]
    st.session_state.used_card_titles.append(chosen["title"])
    return chosen


# -------------------------------------------------
# Guards
# -------------------------------------------------
if "player" not in st.session_state or "facilitator_settings" not in st.session_state:
    st.warning("No player data found. Please start from the setup page.")
    st.stop()

p = st.session_state.player
fs = st.session_state.facilitator_settings
st.set_page_config(layout="wide")

# -------------------------------------------------
# Defaults
# -------------------------------------------------
p.setdefault("rounds_played", 0)
p.setdefault("savings", 0)
p.setdefault("emotion", 5)
p.setdefault("time", 5)
p.setdefault("decision_log", [])
p.setdefault("current_card", None)
p.setdefault("choice_made", False)
p.setdefault("income", fs.get("income", 2000))
p.setdefault("fixed_costs", fs.get("fixed_costs", 1000))
p.setdefault("ef_cap", 3000)
p.setdefault("ef_balance", 0)
p.setdefault("wants_balance", 0)
p.setdefault("allocation", {"savings": 0, "ef": 0, "wants": 0})

if "used_card_titles" not in st.session_state:
    st.session_state.used_card_titles = []

# CORNER CASE: remaining budget could be 0 or negative if admin misconfigured
# fixed_costs >= income. Clamp to 0 to avoid broken number_input (max < min).
remaining = max(0, int(p["income"] - p["fixed_costs"]))

# Initialise widget-owned allocation state once
if "alloc_sav" not in st.session_state:
    st.session_state["alloc_sav"] = int(p["allocation"]["savings"])
if "alloc_ef" not in st.session_state:
    st.session_state["alloc_ef"] = int(p["allocation"]["ef"])
if "alloc_w" not in st.session_state:
    st.session_state["alloc_w"] = int(p["allocation"]["wants"])

# Load cards once
if "life_cards" not in st.session_state:
    with open("data/life_cards.json", "r") as f:
        st.session_state.life_cards = json.load(f)

# CORNER CASE: card file is empty or malformed
if not st.session_state.life_cards:
    st.error("⚠️ No life cards found. Please check data/life_cards.json.")
    st.stop()

# -------------------------------------------------
# Style
# -------------------------------------------------
st.markdown(
    """
<style>
div.block-container {
  max-width: 1280px;
  padding-top: 3rem;
}
.header-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.5rem;
  padding-top: 0.5rem;
}
.header-title {
  font-size: 1.8rem;
  font-weight: 800;
  line-height: 1.25;
  margin: 0;
}
.rounds {
  text-align: right;
  font-size: 0.9rem;
}
.rounds progress {
  width: 180px;
  height: 8px;
  border-radius: 4px;
  accent-color: #1f6feb;
  display: block;
  margin-top: 0.4rem;
}
h4 { font-size: 1rem !important; font-weight: 700 !important; }
.section-title { font-size: 1.1rem; font-weight: 750; margin-top: 1rem; }
div[data-testid="column"] { padding-left: 0.5rem !important; padding-right: 0.5rem !important; }
div[data-testid="stNumberInput"] > div { width: 100% !important; }
div[data-testid="stNumberInput"] input { width: 100% !important; font-size: 0.9rem; }
.stProgress > div > div { height: 6px !important; border-radius: 3px !important; }
</style>
""",
    unsafe_allow_html=True,
)

# -------------------------------------------------
# Header
# -------------------------------------------------
rp = p["rounds_played"]
tr = fs.get("rounds", 10)
# CORNER CASE: tr could be 0 if admin sets rounds to 0
tr = max(1, tr)
pct_rounds = min(1.0, float(rp) / float(tr))

st.markdown(
    f"""
<div class="header-row">
  <div class="header-title">💰 Savings Monopoly</div>
  <div class="rounds">
    <div><b>Game Progress</b></div>
    <progress value="{pct_rounds}" max="1"></progress>
    <div>{rp}/{tr} rounds played</div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# -------------------------------------------------
# KPI ROW
# -------------------------------------------------
# CORNER CASE: remaining = 0 (fixed costs >= income) — show warning
if remaining == 0:
    st.warning("⚠️ Your fixed costs equal or exceed your income. No budget left to allocate.")

with st.container(border=True):
    c1, c2, c3, c4 = st.columns(4, gap="medium")

    with c1:
        st.markdown("#### 💰 Budget Overview")
        st.markdown(f"**Monthly Income:** {fmt(p['income'])}")
        st.markdown(f"**Fixed Costs:** {fmt(p['fixed_costs'])}")
        st.markdown(f"**Remaining:** {fmt(remaining)}")

    with c2:
        st.markdown("#### 🎯 Savings Goal")
        goal = max(1, fs.get("goal", 5000))  # CORNER CASE: avoid division by zero
        pct = p["savings"] / goal
        st.progress(min(1.0, pct))
        st.markdown(f"**{fmt(p['savings'])} / {fmt(goal)}** ({int(pct * 100)}%)")
        st.number_input(
            "Monthly allocation (Savings):",
            min_value=0, max_value=remaining,
            step=50, key="alloc_sav",
        )

    with c3:
        st.markdown("#### 🛟 Emergency Fund")
        st.markdown(f"**Balance:** {fmt(p['ef_balance'])}")
        st.caption(f"Cap: {fmt(p['ef_cap'])}")
        st.number_input(
            "Monthly allocation (EF):",
            min_value=0, max_value=remaining,
            step=50, key="alloc_ef",
        )

    with c4:
        st.markdown("#### 🎉 Wants Fund")
        st.markdown(f"**Balance:** {fmt(p['wants_balance'])}")
        st.caption("Cap: None")
        st.number_input(
            "Monthly allocation (Wants):",
            min_value=0, max_value=remaining,
            step=50, key="alloc_w",
        )

# Read allocation from widget-owned session state
alloc_sav = st.session_state["alloc_sav"]
alloc_ef  = st.session_state["alloc_ef"]
alloc_w   = st.session_state["alloc_w"]

# Sync to p so game logic can read them
p["allocation"]["savings"] = alloc_sav
p["allocation"]["ef"]      = alloc_ef
p["allocation"]["wants"]   = alloc_w

# -------------------------------------------------
# Allocation validation
# -------------------------------------------------
alloc_sum   = alloc_sav + alloc_ef + alloc_w
alloc_valid = (alloc_sum == remaining)

if not alloc_valid:
    diff      = alloc_sum - remaining
    direction = "over" if diff > 0 else "under"
    st.error(
        f"⚠️ Your monthly allocations add up to **{fmt(alloc_sum)}** "
        f"but your remaining budget is **{fmt(remaining)}** — "
        f"you are **{fmt(abs(diff))} {direction}**. "
        f"Please adjust before continuing."
    )

# -------------------------------------------------
# Game Logic
# -------------------------------------------------
def simulate_choice_and_validate(p, selected):
    s_delta         = selected.get("savings_delta", 0)
    ef_delta        = selected.get("ef_delta", 0)
    w_delta         = selected.get("wants_delta", 0)
    wellbeing_delta = selected.get("wellbeing", 0)
    # FIX: time field is already signed in card data (-1 = costs time, +1 = gains time)
    # was: new_time = p["time"] - time_cost → wrong sign
    # now: new_time = p["time"] + time_delta → correct
    time_delta = selected.get("time", 0)

    savings_after_alloc = p["savings"] + p["allocation"].get("savings", 0)
    ef_after_alloc      = min(p["ef_cap"], p["ef_balance"] + p["allocation"].get("ef", 0))
    wants_after_alloc   = p["wants_balance"] + p["allocation"].get("wants", 0)

    new_savings = savings_after_alloc + s_delta
    new_ef      = ef_after_alloc + ef_delta
    new_wants   = wants_after_alloc + w_delta

    if new_savings < 0:
        return False, "Not enough in your savings pot to cover this decision.", None
    if new_ef < 0:
        return False, "Not enough in your emergency fund to cover this decision.", None
    if new_wants < 0:
        return False, "Not enough in your wants fund to cover this decision.", None

    # CORNER CASE: ef_cap = 0 would make ef always 0 — handled by min() above
    # CORNER CASE: time goes below 0 — block the choice
    new_time = p["time"] + time_delta
    if new_time < 0:
        return False, "Not enough time/energy to take this action.", None

    new_emotion = p["emotion"] + wellbeing_delta
    if new_emotion < 0:
        return False, "This decision would push your wellbeing too low.", None

    # Silently cap both at 10 — never block for exceeding max
    new_emotion = min(10, new_emotion)
    new_time    = min(10, new_time)

    return True, "", {
        "savings":       new_savings,
        "ef_balance":    new_ef,
        "wants_balance": new_wants,
        "time":          new_time,
        "emotion":       new_emotion,
    }


def end_popup(msg, success=False):
    if success:
        st.success(msg)
    else:
        st.error(msg)
    if st.button("🔄 Restart Game"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()
    st.stop()


# -------------------------------------------------
# Game Round + Stats
# -------------------------------------------------
left, right = st.columns([2, 1], gap="large")

with left:
    st.markdown('<div class="section-title">🎴 Game Round</div>', unsafe_allow_html=True)

    # End conditions — check before anything else
    if p["emotion"] <= 0:
        end_popup("💥 You burned out! Game over.", success=False)

    if p["savings"] >= goal:
        end_popup("🎉 You reached your savings goal early! Great job.", success=True)

    if p["time"] <= 0:
        p["emotion"] = max(0, p["emotion"] - 2)
        p["time"] = 3
        st.session_state.player = p
        st.warning("⏳ You ran out of time. -2 wellbeing, time reset to 3.")

    if p["rounds_played"] >= tr:
        if p["savings"] >= goal:
            end_popup("🏆 The game ended — you achieved your goal! 🥳", success=True)
        else:
            end_popup(
                f"⏰ The game ended after {tr} rounds — goal not reached. Try again!",
                success=False,
            )

    draw_disabled = bool(
        p.get("current_card")
        or p["rounds_played"] >= tr
        or not alloc_valid
    )
    draw = st.button(
        "🎴 Draw Life Card",
        type="primary",
        disabled=draw_disabled,
        help="Fix your budget allocation above before drawing." if not alloc_valid else None,
    )

    if draw and not draw_disabled:
        p["current_card"] = draw_weighted_card(
            st.session_state.life_cards, p["rounds_played"], tr
        )
        p["choice_made"] = False
        st.session_state.player = p

    if not p.get("current_card"):
        st.caption("Draw a life card to start the month.")
    else:
        card = p["current_card"]
        st.subheader(card.get("title", "Life Event"))
        if card.get("description"):
            st.write(card["description"])

        options = card.get("options", [])

        # CORNER CASE: card has no options (malformed card data)
        if not options:
            st.error("⚠️ This card has no options. Skipping...")
            p["current_card"] = None
            st.session_state.player = p
            st.rerun()

        display_opts = [
            f"{opt['label']} → Savings: {opt.get('savings_delta', 0):+}, "
            f"EF: {opt.get('ef_delta', 0):+}, Wants: {opt.get('wants_delta', 0):+}, "
            f"Wellbeing: {opt.get('wellbeing', 0):+}, Time: {opt.get('time', 0):+}"
            for opt in options
        ]

        choice = st.radio("Choose an option:", display_opts, key="decision_choice")

        save_disabled = not alloc_valid
        if st.button(
            "💾 Save Decision",
            key="save_decision",
            disabled=save_disabled,
            help="Fix your budget allocation above before saving." if save_disabled else None,
        ):
            # CORNER CASE: choice somehow not in display_opts (shouldn't happen but guard it)
            if choice not in display_opts:
                st.error("Unexpected error selecting option. Please try again.")
                st.stop()

            selected = options[display_opts.index(choice)]
            ok, msg, new_state = simulate_choice_and_validate(p, selected)

            if not ok:
                st.warning(f"❗ {msg} Please choose a different option.")
                st.stop()
            else:
                p["savings"]       = new_state["savings"]
                p["ef_balance"]    = new_state["ef_balance"]
                p["wants_balance"] = new_state["wants_balance"]
                p["time"]          = new_state["time"]
                p["emotion"]       = new_state["emotion"]

                p["rounds_played"] += 1
                p["decision_log"].append(f"{card['title']} — {selected['label']}")
                p["choice_made"]  = True
                p["current_card"] = None

                st.session_state.player = p
                st.success("✅ Decision saved! Next round starting...")
                time.sleep(0.4)
                st.rerun()

with right:
    st.markdown('<div class="section-title">❤️⚡ Wellbeing / Time</div>', unsafe_allow_html=True)
    st.markdown(f"**Wellbeing:** {emoji_bar(p['emotion'], '❤️')}")
    st.markdown(f"**Time:** {emoji_bar(p['time'], '⚡')}")

# -------------------------------------------------
# Decision Log
# -------------------------------------------------
st.markdown("---")
st.subheader("🧾 Decision Log")
if p["decision_log"]:
    for i, d in enumerate(p["decision_log"], 1):
        st.write(f"**Round {i}:** {d}")
else:
    st.caption("No decisions yet.")