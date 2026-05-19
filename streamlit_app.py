import streamlit as st
import random
import base64

# ============================================================
# PARAMETRY WYDAJNOŚCI
# ============================================================
SIMULATIONS = 50000

# ============================================================
# SYSTEM JĘZYKÓW PL / EN
# ============================================================
if "lang" not in st.session_state:
    st.session_state.lang = "PL"

def T(pl, en):
    return pl if st.session_state.lang == "PL" else en

# ============================================================
# STYL GRAFICZNY
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
.ticket-line { font-family: monospace; font-size: 20px; color: #ffd600; margin-bottom: 6px; }
.ticket-number { color: #1a73e8; font-weight: 700; padding-right: 25px; }
hr { border: none; border-top: 2px solid #00ffcc !important; margin: 20px 0; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# TYTUŁ + PRZYCISKI JĘZYKA
# ============================================================
title_col, lang_col = st.columns([6, 2])
with title_col:
    st.title(T("🎛️ Generator Liczb", "🎛️ Number Generator"))  

with lang_col:
    bcol1, bcol2 = st.columns(2)
    with bcol1:
        if st.button("PL", key="lang_pl_btn"): 
            st.session_state.lang = "PL"
            st.rerun()
    with bcol2:
        if st.button("EN", key="lang_en_btn"): 
            st.session_state.lang = "EN"
            st.rerun()

st.markdown("---")

# ============================================================
# PARAMETRY GRY
# ============================================================
st.header(T("⚙️ Parametry gry", "⚙️ Game parameters"))
col1, col2, col3 = st.columns(3)

with col1:
    k = st.number_input(T("🔢 Liczby w zakładzie (k)", "🔢 Numbers per ticket (k)"), 1, 200, 1,
                        help=T("Liczba liczb wybieranych na pojedynczy kupon.", "Number of numbers selected for a single ticket."))
with col2:
    m = st.number_input(T("🎰 Liczby w losowaniu (m)", "🎰 Drawn numbers (m)"), 1, 200, 1,
                        help=T("Całkowita liczba liczb wyłanianych w oficjalnym losowaniu.", "Total number of balls drawn in the official lottery draw."))
with col3:
    n = st.number_input(T("🎲 Pula liczb (n)", "🎲 Range of numbers (n)"), 1, 200, 1,
                        help=T("Całkowity zakres liczb dostępnych w maszynie losującej.", "Total range of numbers available in the draw machine."))

col_s1, col_s2 = st.columns(2)
with col_s1:
    strength = st.slider(T("💪 Startowa siła (%)", "💪 Start strength (%)"), 0, 100, 1,
                         help=T("Bazowy poziom dopasowania do rozkładu historycznego.", "Base level of alignment with historical distribution."))
with col_s2:
    max_strength_limit = st.slider(T("🛡️ Limit jakości (%)", "🛡️ Quality limit (%)"), 0, 100, 1,
                                   help=T("Maksymalny próg siły, do którego system będzie dążył w poszukiwaniu optymalnych kombinacji.", "Maximum strength threshold the system will reach for optimal combinations."))

num_tickets = st.number_input(T("📄 Ile zakładów wygenerować", "📄 Number of tickets to generate"), 1, 1000, 1,
                              help=T("Liczba finalnych kombinacji do wygenerowania.", "Number of final combinations to be generated."))

st.markdown("---")

# ============================================================
# FILTRY
# ============================================================
st.header(T("🧩 Filtry", "🧩 Filters"))
max_common = st.number_input(T("🔁 Maksymalna liczba wspólnych liczb", "🔁 Max shared numbers"), 0, 200, 1,
                             help=T("Ogranicza powtarzalność tych samych liczb między wygenerowanymi kuponami.", "Limits the repetition of the same numbers across generated tickets."))
eliminate_even_odd = st.toggle(T("⚖️ Eliminuj sam parzyste/nieparzyste", "⚖️ No all-even/odd"), False,
                               help=T("Odrzuca kupony o zerowej wariancji parzystości (np. same parzyste).", "Discards tickets with zero parity variance (e.g., all even)."))
max_block_length = st.number_input(T("📏 Max długość bloku", "📏 Max consecutive block"), 0, 200, 1,
                                   help=T("Ogranicza liczbę kolejnych liczb występujących po sobie w zakładzie.", "Limits the number of consecutive numbers appearing in a ticket."))
max_blocks = st.number_input(T("🧱 Max liczba bloków", "🧱 Max blocks"), 0, 200, 1,
                             help=T("Ogranicza liczbę odseparowanych serii kolejnych liczb na kuponie.", "Limits the number of separated sequences of consecutive numbers on a ticket."))

st.markdown("---")

# ============================================================
# FUNKCJE SILNIKA (Z OPTYMALIZACJĄ CACHE)
# ============================================================
@st.cache_data(show_spinner=False)
def run_monte_carlo_simulation(sim_count, m_val, n_val):
    pos_count = [[0] * (n_val + 1) for _ in range(m_val)]
    for _ in range(sim_count):
        full_draw = sorted(random.sample(range(1, n_val + 1), m_val))
        for i, val in enumerate(full_draw): 
            pos_count[i][val] += 1
    return pos_count

def count_blocks(ticket):
    blocks = []
    curr = 1
    for i in range(len(ticket) - 1):
        if ticket[i+1] == ticket[i] + 1: 
            curr += 1
        else:
            if curr > 1: 
                blocks.append(curr)
            curr = 1
    if curr > 1: 
        blocks.append(curr)
    return blocks

def generate_single_ticket(ranges, k_val, tickets_so_far, max_c, no_eo, mbl, mb):
    attempts = 0
    while attempts < 10000:
        attempts += 1
        ticket = []
        if len(ranges) < k_val:
            return None
        chosen_positions = random.sample(range(len(ranges)), k_val)
        for pos in chosen_positions:
            inner_attempts = 0
            while inner_attempts < 30:
                x = random.choice(ranges[pos])
                if x not in ticket:
                    ticket.append(x)
                    break
                inner_attempts += 1
        if len(ticket) < k_val: 
            continue
        ticket.sort()
        if max_c >= 0 and any(len(set(ticket) & set(old)) > max_c for old in tickets_so_far): 
            continue
        if no_eo:
            evens = sum(1 for x in ticket if x % 2 == 0)
            if evens == 0 or evens == k_val: 
                continue
        blks = count_blocks(ticket)
        if mb > 0 and len(blks) > mb: 
            continue
        if mbl > 0 and any(b > mbl for b in blks): 
            continue
        return tuple(ticket)
    return None

# ============================================================
# LOGIKA GENEROWANIA
# ============================================================
if "results" not in st.session_state:
    st.session_state.results = None

if st.button(T("🚀 Generuj", "🚀 Generate")):
    if k > n or k > m or m > n:
        st.error(T("Błąd: Parametry muszą spełniać warunek k <= m <= n", "Error: Parameters must satisfy k <= m <= n"))
    else:
        with st.spinner(T("Trwa symulacja i dobieranie liczb...", "Running simulation and selecting numbers...")):
            pos_count = run_monte_carlo_simulation(SIMULATIONS, m, n)
            tickets = []
            curr_str = strength
            limit = max_strength_limit
            last_ranges = []

            while len(tickets) < num_tickets and curr_str <= limit:
                curr_ranges = []
                for i in range(m):
                    hist = pos_count[i]
                    total_at_pos = sum(hist)
                    if total_at_pos == 0:
                        curr_ranges.append(list(range(1, n + 1)))
                        continue
                    target = total_at_pos * (curr_str / 100.0)
                    vals = sorted([(v, hist[v]) for v in range(1, n + 1) if hist[v] > 0], key=lambda x: x[1], reverse=True)
                    run, sel = 0, []
                    for v, c in vals:
                        sel.append(v)
                        run += c
                        if run >= target: 
                            break
                    curr_ranges.append(sel if sel else list(range(1, n + 1)))
                last_ranges = curr_ranges
                needed = num_tickets - len(tickets)
                for _ in range(needed):
                    t = generate_single_ticket(curr_ranges, k, tickets, max_common, eliminate_even_odd, max_block_length, max_blocks)
                    if t:
                        tickets.append(t)
                    else:
                        break
                if len(tickets) < num_tickets:
                    curr_str += 1 
                else:
                    break
            st.session_state.results = {"tickets": tickets, "ranges": last_ranges, "final_str": min(curr_str, limit)}

# ============================================================
# WYNIKI
# ============================================================
if st.session_state.results:
    res = st.session_state.results
    st.header(T("🎯 Wyniki", "🎯 Results"))

    with st.expander(T("🔧 Wyliczone zakresy pozycyjne", "🔧 Calculated positional ranges")):
        st.write(T("Zakresy (listy wartości) wyznaczone na podstawie m-pozycji w losowaniu.", "Ranges (value lists) determined based on m-positions in draw."))
        for i, val_list in enumerate(res["ranges"], 1):
            if not val_list:
                txt_pl = f"Pozycja {i}: brak danych"
                txt_en = f"Position {i}: no data"
            else:
                mn = min(val_list)
                mx = max(val_list)
                txt_pl = f"Pozycja {i}: {mn} – {mx}"
                txt_en = f"Position {i}: {mn} – {mx}"
            st.write(T(txt_pl, txt_en))
    
    if not res["tickets"]:
        st.warning(T("Brak wyników. Spróbuj złagodzić filtry lub zwiększyć Limit jakości.", "No results. Try relaxing filters or increasing Quality limit."))
    else:
        st.success(T(f"Wygenerowano {len(res['tickets'])} zakładów (Osiągnięta siła: {res['final_str']}%).", f"Generated {len(res['tickets'])} tickets (Strength: {res['final_str']}%)."))
        for i, t in enumerate(res["tickets"], 1):
            nums = "  ".join(f"{x:02d}" for x in t)
            st.markdown(f'<div class="ticket-line"><span class="ticket-number">{i:02d}:</span> {nums}</div>', unsafe_allow_html=True)

        st.markdown("---")
        col_csv, col_txt = st.columns(2)
        csv_data = "\n".join([";".join(map(str, t)) for t in res["tickets"]])
        txt_data = "\n".join([" ".join(f"{x:02d}" for x in t) for t in res["tickets"]])
        col_csv.download_button(T("📥 Pobierz CSV", "📥 Download CSV"), csv_data, "tickets.csv", "text/csv", use_container_width=True)
        col_txt.download_button(T("📄 Zapisz jako TXT", "📄 Save as TXT"), txt_data, "tickets.txt", "text/plain", use_container_width=True)

# ============================================================
# NOWOCZESNE OSTRZEŻENIE (DISCLAIMER)
# ============================================================
st.markdown(f"""
<div style="
    background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
    border-left: 5px solid #ffd600;
    padding: 15px;
    border-radius: 0 10px 10px 0;
    font-size: 14px;
    color: #ecf0f1;
    margin: 30px 0;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
">
    <strong>⚠️ {T('Informacja:', 'Note:')}</strong> {T(
        'Generator ma charakter demonstracyjny i analityczny. Nie stanowi porady inwestycyjnej ani prognozy wyników. Hazard wiąże się z ryzykiem.',
        'This generator is for demonstration and analysis only. It does not constitute investment advice or result prediction. Gambling involves risk.'
    )}
</div>
""", unsafe_allow_html=True)

# ============================================================
# STOPKA
# ============================================================
st.markdown("---")
footer_html = f"""
<div style='text-align:center; font-size:14px; color:#555; line-height:1.6;'>
    <strong style='color:#00ffcc;'>© Maria System</strong><br>
    {T('Wszelkie prawa zastrzeżone.', 'All rights reserved.')}<br>
    <div style='margin-top:10px; color:#777; font-size:13px;'>
        {T('Zaprojektowane przez Roman Niemczyk', 'Designed by Roman Niemczyk')}
    </div>
</div>
"""
st.markdown(footer_html, unsafe_allow_html=True)
