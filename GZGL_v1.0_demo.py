import streamlit as st
import random
import base64

SIMULATIONS = 5000

# ============================================================
#  SYSTEM JĘZYKÓW PL / EN
# ============================================================

if "lang" not in st.session_state:
    st.session_state.lang = "EN"

def T(pl, en):
    return pl if st.session_state.lang == "PL" else en

# ============================================================
#  STYL GRAFICZNY
# ============================================================

st.markdown("""
<style>
:root { color-scheme: light; }
html, body, [class*="css"] { font-family: 'Segoe UI', sans-serif; }
body { background-color: #f2f2f7 !important; }
h1, h2, h3 { color: #4CAF50 !important; font-weight: 600 !important; }
.stButton>button {
    background-color: #4CAF50 !important;
    color: white !important;
    border-radius: 8px !important;
    padding: 8px 16px !important;
    font-size: 14px !important;
    border: none !important;
}
.stButton>button:hover { background-color: #45a049 !important; }

.ticket-line { font-family: monospace; font-size: 20px; color: #ffd600; margin-bottom: 6px; }
.ticket-number { color: #1a73e8; font-weight: 700; padding-right: 25px; }

div[data-baseweb="tooltip"] * { color: #ff9800 !important; }
button[aria-label="Tooltip"] svg { fill: #ff9800 !important; color: #ff9800 !important; width: 18px !important; height: 18px !important; }
.stTooltipIcon svg { fill: #ff9800 !important; color: #ff9800 !important; }

hr { border: none; border-top: 2px solid #00ffcc !important; margin: 20px 0; }
</style>
""", unsafe_allow_html=True)

# ============================================================
#  TYTUŁ + JĘZYK
# ============================================================

title_col, lang_col = st.columns([6, 2])

with title_col:
    st.title(T("🎛️ Generator Zakładów", "🎛️ Ticket Generator"))

with lang_col:
    b1, b2 = st.columns(2)
    with b1:
        if st.button("PL", key="lang_pl_btn"):
            st.session_state.lang = "PL"
    with b2:
        if st.button("EN", key="lang_en_btn"):
            st.session_state.lang = "EN"

# Ostrzeżenie
st.markdown(f"""
<span style="font-weight:600; color:#d32f2f; font-size:16px;">
    {T("Ostrzeżenie!", "Warning!")}
</span>
<span 
    title="{T(
        'Generator ma charakter demonstracyjny. Wyniki nie stanowią prognozy ani rekomendacji.',
        'This generator is a demonstration tool. Results do not represent predictions or recommendations.'
    )}"
    style="cursor: help; font-size:18px; color:#ff9800; margin-left:6px;">
    ❗
</span>
""", unsafe_allow_html=True)

# ============================================================
#  PARAMETRY GRY
# ============================================================

SIMULATIONS = 100000

st.header(T("⚙️ Parametry gry", "⚙️ Game Parameters"))

col1, col2 = st.columns(2)
with col1:
    k = st.number_input(
        T("🔢 Ile liczb w zakładzie (k)", "🔢 Numbers per ticket (k)"),
        1, 200, 1,
        help=T("Ile liczb zawiera zakład.", "How many numbers each ticket contains.")
    )
with col2:
    n = st.number_input(
        T("🎲 Z ilu liczb losujemy (n)", "🎲 Range of numbers (n)"),
        1, 200, 1,
        help=T("Zakres liczb 1..n.", "Numbers are drawn from 1..n.")
    )

strength = st.slider(
    T("💪 Siła zakresów (%)", "💪 Range strength (%)"),
    0, 100, 1,
    help=T(
    "Ustala, jak bardzo dane statystyczne wpływają na dobór liczb.",
    "Sets how much statistical data influences number selection."
    )
)

num_tickets = st.number_input(
    T("📄 Ile zakładów wygenerować", "📄 Number of tickets"),
    1, 1000, 1,
    help=T("Demo ogranicza do 6 zakładów.", "Demo limits to 6 tickets.")
)

if num_tickets > 6:
    num_tickets = 6
    st.warning(T("Wersja demo: maksymalnie 6 zakładów.", "Demo version: max 6 tickets."))

st.markdown("---")

# ============================================================
#  FILTRY
# ============================================================

st.header(T("🧩 Filtry", "🧩 Filters"))

max_common = st.number_input(
    T("🔁 Wspólne liczby", "🔁 Common numbers limit"),
    0, 200, 1,
    help=T("Maksymalna liczba wspólnych liczb.", "Maximum shared numbers.")
)

eliminate_even_odd = st.checkbox(
    T("⚖️ Eliminacja samych parzystych/nieparzystych",
      "⚖️ Eliminate all-even or all-odd tickets"),
    value=False,
    help=T("Odrzuca zakłady 100% parzyste lub nieparzyste.", "Rejects all-even or all-odd tickets.")
)

max_block_length = st.number_input(
    T("📏 Maksymalna długość bloku", "📏 Max block length"),
    0, 200, 1,
    help=T("Najdłuższy dopuszczalny blok kolejnych liczb.", "Longest allowed consecutive block.")
)

max_blocks = st.number_input(
    T("🧱 Maksymalna liczba bloków", "🧱 Maximum number of blocks"),
    0, 200, 1,
    help=T("Maksymalna liczba bloków kolejnych liczb.", "Maximum number of consecutive blocks.")
)

st.markdown("---")

# ============================================================
#  SILNIK
# ============================================================

def compute_ranges(k, n, simulations, strength_percent):
    pos_count = [[0] * (n + 1) for _ in range(k)]
    for _ in range(simulations):
        try:
            draw = sorted(random.sample(range(1, n + 1), k))
            for i, val in enumerate(draw):
                pos_count[i][val] += 1
        except ValueError:
            break

    ranges = []
    for i in range(k):
        hist = pos_count[i]
        total = sum(hist)
        if strength_percent == 0 or total == 0:
            ranges.append((1, n))
            continue

        target = total * (strength_percent / 100.0)
        values = [(v, hist[v]) for v in range(1, n + 1) if hist[v] > 0]
        values.sort(key=lambda x: x[1], reverse=True)

        running = 0
        selected = []
        for v, c in values:
            selected.append(v)
            running += c
            if running >= target:
                break

        if not selected:
            ranges.append((1, n))
        else:
            ranges.append((min(selected), max(selected)))

    return ranges


def count_blocks(ticket):
    blocks = []
    current = 1
    for i in range(len(ticket) - 1):
        if ticket[i + 1] == ticket[i] + 1:
            current += 1
        else:
            if current > 1:
                blocks.append(current)
            current = 1
    if current > 1:
        blocks.append(current)
    return blocks


def generate_single_ticket(ranges, k, tickets_so_far, max_common, eliminate_even_odd_flag, max_block_length, max_blocks):
    attempts = 0
    while attempts < 2000:
        attempts += 1
        ticket = []
        for (low, high) in ranges:
            inner = 0
            while inner < 50:
                x = random.randint(low, high)
                if x not in ticket:
                    ticket.append(x)
                    break
                inner += 1

        if len(ticket) < k:
            continue

        ticket.sort()

        if any(len(set(ticket) & set(old)) > max_common for old in tickets_so_far):
            continue

        if eliminate_even_odd_flag:
            even_count = sum(1 for x in ticket if x % 2 == 0)
            if even_count == 0 or even_count == k:
                continue

        blocks = count_blocks(ticket)
        if len(blocks) > max_blocks:
            continue
        if any(b > max_block_length for b in blocks):
            continue

        return tuple(ticket)

    return None

# ============================================================
#  GENEROWANIE + WYNIKI
# ============================================================

if "results" not in st.session_state:
    st.session_state.results = None

if st.button(T("🚀 Generuj zakłady", "🚀 Generate tickets")):
    if k > n:
        st.error(T("Błąd: k > n.", "Error: k > n."))
    else:
        with st.spinner(T("Trwa symulacja...", "Running simulation...")):
            ranges = compute_ranges(int(k), int(n), SIMULATIONS, int(strength))
            tickets = []

            for _ in range(int(num_tickets)):
                t = generate_single_ticket(
                    ranges, int(k), tickets,
                    int(max_common), eliminate_even_odd,
                    int(max_block_length), int(max_blocks)
                )
                if t:
                    tickets.append(t)

            st.session_state.results = {"tickets": tickets, "ranges": ranges}

if st.session_state.results:
    res = st.session_state.results

    st.header(T("🎯 Wyniki", "🎯 Results"))

    with st.expander(
        T("🔧 Zobacz wyliczone zakresy pozycyjne", "🔧 View positional ranges")
    ):
        st.info(T("Zakresy ukryte w wersji demo.", "Ranges hidden in demo version."))

    if not res["tickets"]:
        st.warning(T("Nie udało się wygenerować zakładów.", "No tickets generated."))
    else:
        st.success(T(
            f"Wygenerowano {len(res['tickets'])} zakładów.",
            f"Generated {len(res['tickets'])} tickets."
        ))

        for i, t in enumerate(res["tickets"], start=1):
            numbers = "  ".join(f"{x:02d}" for x in t)
            st.markdown(
                f"<div class='ticket-line'><span class='ticket-number'>{i:02d}:</span>{numbers}</div>",
                unsafe_allow_html=True
            )

        st.markdown("---")

        col_csv, col_txt = st.columns(2)

        with col_csv:
            if st.button(T("📥 Pobierz CSV", "📥 Download CSV"), use_container_width=True):
                st.error(T("Tylko w pełnej wersji.", "Full version only."))

        with col_txt:
            if st.button(T("📄 Zapisz TXT", "📄 Save TXT"), use_container_width=True):
                st.error(T("Tylko w pełnej wersji.", "Full version only."))

# ============================================================
#  STOPKA
# ============================================================

try:
    with open("logo5a.png", "rb") as f:
        logo_base64 = base64.b64encode(f.read()).decode()
except FileNotFoundError:
    logo_base64 = None

st.markdown("---")

footer_pl = """
<div style='text-align:center; font-size:14px; color:#555; line-height:1.4;'>
    <strong style='color:#00ffcc;'>© Maria System</strong><br>
    Wszelkie prawa zastrzeżone. Kopiowanie lub rozpowszechnianie bez zgody autora jest zabronione.
</div>
"""

footer_en = """
<div style='text-align:center; font-size:14px; color:#555; line-height:1.4;'>
    <strong style='color:#00ffcc;'>© Maria System</strong><br>
    All rights reserved.Copying or distribution without author's consent is prohibited.
</div>
"""

st.markdown(
    f"<div style='text-align:center; margin-top:10px; color:#777; font-size:13px;'>"
    f"{T('Zaprojektowane przez Roman Niemczyk', 'Designed by Roman Niemczyk')}"
    "</div>",
    unsafe_allow_html=True
)

st.markdown(footer_pl if st.session_state.lang == "PL" else footer_en, unsafe_allow_html=True)