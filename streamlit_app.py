import streamlit as st
import random
import base64

SIMULATIONS = 500000



# ============================================================
#  SYSTEM JĘZYKÓW PL / EN
# ============================================================

if "lang" not in st.session_state:
    st.session_state.lang = "EN"   # domyślnie angielski

def T(pl, en):
    return pl if st.session_state.lang == "PL" else en


# ============================================================
#  STYL GRAFICZNY – jasny, elegancki, minimalistyczny
# ============================================================

st.markdown("""
<style>
:root {
    color-scheme: light;
}
html, body, [class*="css"] {
    font-family: 'Segoe UI', sans-serif;
}
body {
    background-color: #f2f2f7 !important;
}
h1, h2, h3 {
    color: #4CAF50 !important;
    font-weight: 600 !important;
}
.stButton>button {
    background-color: #4CAF50 !important;
    color: white !important;
    border-radius: 8px !important;
    padding: 8px 16px !important;
    font-size: 14px !important;
    border: none !important;
}
.stButton>button:hover {
    background-color: #45a049 !important;
}

/* Wyniki – linia zakładu */
.ticket-line {
    font-family: monospace;
    font-size: 20px;
    color: #ffd600;
    margin-bottom: 6px;
}
.ticket-number {
    color: #1a73e8;
    font-weight: 700;
    padding-right: 25px;
}

/* Tooltip – pomarańczowy tekst */
div[data-baseweb="tooltip"] * {
    color: #ff9800 !important;
}

/* Pomarańczowa ikona ? — nowy Streamlit */
button[aria-label="Tooltip"] svg {
    fill: #ff9800 !important;
    color: #ff9800 !important;
    width: 18px !important;
    height: 18px !important;
}

/* Pomarańczowa ikona ? — stary Streamlit */
.stTooltipIcon svg {
    fill: #ff9800 !important;
    color: #ff9800 !important;
}

/* Seledynowe linie poziome */
hr {
    border: none;
    border-top: 2px solid #00ffcc !important;
    margin: 20px 0;
}
</style>
""", unsafe_allow_html=True)


# ============================================================
#  TYTUŁ + PRZYCISKI JĘZYKA
# ============================================================

title_col, lang_col = st.columns([6, 2])

with title_col:
    st.title(T("🎛️ Generator Liczb", "🎛️ Number Generator"))

with lang_col:
    bcol1, bcol2 = st.columns(2)
    with bcol1:
        if st.button("PL", key="lang_pl_btn"):
            st.session_state.lang = "PL"
    with bcol2:
        if st.button("EN", key="lang_en_btn"):
            st.session_state.lang = "EN"

st.markdown("---")


# ============================================================
#  PARAMETRY GRY – STARTOWE = 1
# ============================================================

st.header(T("⚙️ Parametry gry", "⚙️ Game parameters"))

col1, col2 = st.columns(2)

with col1:
    k = st.number_input(
        T("🔢 Ile liczb w zakładzie (k)", "🔢 Numbers per ticket (k)"),
        min_value=1,
        max_value=200,
        value=1,
        help=T(
            "Liczba liczb, które mają znaleźć się na jednym kuponie (np. 6 w Lotto).",
            "Number of numbers placed on a single ticket (e.g., 6 in classic lotto)."
        )
    )

with col2:
    n = st.number_input(
        T("🎲 Z ilu liczb losujemy (n)", "🎲 Range of numbers (n)"),
        min_value=1,
        max_value=200,
        value=1,
        help=T(
            "Zakres liczb, z którego wybierane są liczby do kuponów (1 do n).",
            "Range of numbers from which tickets are generated (1 to n)."
        )
    )

strength = st.slider(
    T("💪 Siła zakresów (%)", "💪 Range strength (%)"),
    min_value=0,
    max_value=100,
    value=1,
    help=T(
        "Określa, jak mocno generator ma kierować się statystyką zamiast czystej losowości.",
        "Controls how strongly the generator relies on statistical patterns instead of pure randomness."
    )
)

num_tickets = st.number_input(
    T("📄 Ile zakładów wygenerować", "📄 Number of tickets to generate"),
    min_value=1,
    max_value=1000,
    value=1,
    help=T(
        "Liczba kuponów, które mają zostać wygenerowane w jednym przebiegu.",
        "Number of tickets to generate in a single run."
    )
)

st.markdown("---")


# ============================================================
#  FILTRY – STARTOWE = 1
# ============================================================

st.header(T("🧩 Filtry", "🧩 Filters"))

max_common = st.number_input(
    T("🔁 Maksymalna liczba wspólnych liczb na kuponach",
      "🔁 Maximum shared numbers across tickets"),
    min_value=0,
    max_value=200,
    value=1,
    help=T(
        "Ile liczb może powtarzać się pomiędzy wygenerowanymi kuponami.",
        "How many numbers may repeat across generated tickets."
    )
)

eliminate_even_odd = st.toggle(
    T(
        "⚖️ Eliminuj zakłady wyłącznie parzyste lub wyłącznie nieparzyste",
        "⚖️ Eliminate all-even or all-odd tickets"
    ),
    value=False,
    help=T(
        "Usuwa kupony składające się wyłącznie z liczb parzystych lub wyłącznie nieparzystych.",
        "Removes tickets containing only even or only odd numbers."
    )
)

max_block_length = st.number_input(
    T("📏 Maksymalna długość bloku kolejnych liczb",
      "📏 Maximum length of a consecutive block"),
    min_value=0,
    max_value=200,
    value=1,
    help=T(
        "Najdłuższy dopuszczalny ciąg kolejnych liczb (np. 3 oznacza, że 4 kolejne liczby są niedozwolone).",
        "Longest allowed sequence of consecutive numbers (e.g., 3 means 4 in a row is not allowed)."
    )
)

max_blocks = st.number_input(
    T("🧱 Maksymalna liczba bloków kolejnych liczb",
      "🧱 Maximum number of consecutive blocks"),
    min_value=0,
    max_value=200,
    value=1,
    help=T(
        "Maksymalna liczba oddzielnych bloków kolejnych liczb, które mogą pojawić się na kuponie.",
        "Maximum number of separate consecutive-number blocks allowed on a ticket."
    )
)

st.markdown("---")


# ============================================================
#  SILNIK OBLICZENIOWY – ZAKRESY POZYCYJNE
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
    current_length = 1
    for i in range(len(ticket) - 1):
        if ticket[i + 1] == ticket[i] + 1:
            current_length += 1
        else:
            if current_length > 1:
                blocks.append(current_length)
            current_length = 1
    if current_length > 1:
        blocks.append(current_length)
    return blocks


def generate_single_ticket(
    ranges,
    k,
    tickets_so_far,
    max_common,
    eliminate_even_odd_flag,
    max_block_length,
    max_blocks
):
    attempts = 0
    while attempts < 2000:
        attempts += 1
        ticket = []

        for (low, high) in ranges:
            inner_attempts = 0
            while inner_attempts < 50:
                x = random.randint(low, high)
                if x not in ticket:
                    ticket.append(x)
                    break
                inner_attempts += 1

        if len(ticket) < k:
            continue

        ticket.sort()

        if max_common > 0:
            if any(len(set(ticket) & set(old)) > max_common for old in tickets_so_far):
                continue

        if eliminate_even_odd_flag:
            even_count = sum(1 for x in ticket if x % 2 == 0)
            if even_count == 0 or even_count == k:
                continue

        blocks = count_blocks(ticket)
        if max_blocks > 0 and len(blocks) > max_blocks:
            continue
        if max_block_length > 0 and any(b > max_block_length for b in blocks):
            continue

        return tuple(ticket)

    return None


# ============================================================
#  LOGIKA GENEROWANIA I WYNIKI – PEŁNA WERSJA
# ============================================================

if "results" not in st.session_state:
    st.session_state.results = None

if st.button(T("🚀 Generuj", "🚀 Generate")):
    if k > n:
        st.error(T(
            "Błąd: k nie może być większe niż n.",
            "Error: k cannot be greater than n."
        ))
    else:
        with st.spinner(T(
            "Trwa symulacja i dobieranie liczb...",
            "Running simulation and selecting numbers..."
        )):
            ranges = compute_ranges(int(k), int(n), SIMULATIONS, int(strength))
            tickets = []
            for _ in range(int(num_tickets)):
                t = generate_single_ticket(
                    ranges,
                    int(k),
                    tickets,
                    int(max_common),
                    eliminate_even_odd,
                    int(max_block_length),
                    int(max_blocks)
                )
                if t:
                    tickets.append(t)

            st.session_state.results = {"tickets": tickets, "ranges": ranges}


if st.session_state.results:
    res = st.session_state.results

    st.header(T("🎯 Wyniki", "🎯 Results"))

    # Zakresy pozycyjne – widoczne w pełnej wersji
    with st.expander(T(
        "🔧 Wyliczone zakresy pozycyjne", 
        "🔧 Calculated positional ranges"
    )):
        st.markdown(f"""
        <p style="font-size:14px; color:#555;">
        {T(
            'Zakresy poniżej pokazują, z jakich przedziałów najczęściej wypadają liczby na poszczególnych pozycjach w zakładzie.',
            'The ranges below show from which intervals numbers most often appear in each ticket position.'
        )}
        <span style="color:#ff9800; cursor:help; font-size:16px;"
              title="{T(
                  'Zakres wyznaczony jest na podstawie symulacji – zawiera liczby, które łącznie dają określony procent wszystkich trafień na danej pozycji.',
                  'The range is based on simulation – it contains the numbers that jointly account for a chosen percentage of hits at a given position.'
              )}"> ❔</span>
        </p>
        """, unsafe_allow_html=True)

        for i, (low, high) in enumerate(res["ranges"], start=1):
            st.write(T(
                f"Pozycja {i}: od {low} do {high}",
                f"Position {i}: from {low} to {high}"
            ))

    if not res["tickets"]:
        st.warning(T(
            "Nie udało się wygenerować zakładów przy tych filtrach.",
            "No tickets could be generated with these filters."
        ))
    else:
        st.success(T(
            f"Pomyślnie wygenerowano {len(res['tickets'])} zakładów.",
            f"Successfully generated {len(res['tickets'])} tickets."
        ))

        for i, t in enumerate(res["tickets"], start=1):
            numbers = "  ".join(f"{x:02d}" for x in t)
            st.markdown(
                f"""
                <div class="ticket-line">
                    <span class="ticket-number">{i:02d}:</span>
                    {numbers}
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown("---")
        col_csv, col_txt = st.columns(2)

        with col_csv:
            csv_data = "\n".join([";".join(map(str, t)) for t in res["tickets"]])
            st.download_button(
                label=T("📥 Pobierz CSV (Excel)", "📥 Download CSV (Excel)"),
                data=csv_data,
                file_name="tickets.csv",
                mime="text/csv",
                use_container_width=True
            )

        with col_txt:
            txt_data = "\n".join([" ".join(map(str, t)) for t in res["tickets"]])
            st.download_button(
                label=T("📄 Zapisz jako TXT", "📄 Save as TXT"),
                data=txt_data,
                file_name="tickets.txt",
                mime="text/plain",
                use_container_width=True
            )


# ============================================================
#  OSTRZEŻENIE – NAD STOPKĄ
# ============================================================

st.markdown(
    f"""
    <div style="
        margin-top: 20px;
        margin-bottom: 10px;
        padding: 10px 14px;
        background-color: #ffcc80;
        color: #4a2c00;
        border-radius: 6px;
        font-size: 13px;
        line-height: 1.4;
    ">
        {T(
            'Generator ma charakter demonstracyjny – nie stanowi rekomendacji ani prognozy wyników.',
            'This generator is for demonstration purposes only – it does not constitute a recommendation or prediction of results.'
        )}
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
#  STOPKA Z LOGO + SELEDYNOWY „© Maria System”
# ============================================================

try:
    with open("logo5a.png", "rb") as f:
        logo_base64 = base64.b64encode(f.read()).decode()
except FileNotFoundError:
    logo_base64 = None

st.markdown("---")

if logo_base64:
    footer_pl = f"""
    <div style='text-align:center; font-size:14px; color:#555; line-height:1.4;'>
        <img src='data:image/png;base64,{logo_base64}' width='120' style='margin-bottom:6px;'><br>
        <strong style='color:#00ffcc;'>© Maria System</strong><br>
        Wszelkie prawa zastrzeżone. Kopiowanie lub rozpowszechnianie bez zgody autora jest zabronione.
    </div>
    """

    footer_en = f"""
    <div style='text-align:center; font-size:14px; color:#555; line-height:1.4;'>
        <img src='data:image/png;base64,{logo_base64}' width='120' style='margin-bottom:6px;'><br>
        <strong style='color:#00ffcc;'>© Maria System</strong><br>
        All rights reserved. Copying or distribution without author's consent is prohibited.
    </div>
    """
else:
    footer_pl = """
    <div style='text-align:center; font-size:14px; color:#555; line-height:1.4;'>
        <strong style='color:#00ffcc;'>© Maria System</strong><br>
        Wszelkie prawa zastrzeżone. Kopiowanie lub rozpowszechnianie bez zgody autora jest zabronione.
    </div>
    """
    footer_en = """
    <div style='text-align:center; font-size:14px; color:#555; line-height:1.4;'>
        <strong style='color:#00ffcc;'>© Maria System</strong><br>
        All rights reserved. Copying or distribution without author's consent is prohibited.
    </div>
    """

st.markdown(
    f"<div style='text-align:center; margin-top:10px; color:#777; font-size:13px;'>"
    f"{T('Zaprojektowane przez Roman Niemczyk', 'Designed by Roman Niemczyk')}"
    "</div>",
    unsafe_allow_html=True
)

st.markdown(
    footer_pl if st.session_state.lang == "PL" else footer_en,
    unsafe_allow_html=True
)

