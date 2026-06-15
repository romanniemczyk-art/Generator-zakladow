import streamlit as st
import sqlite3
import itertools
import os
import math
import json

# ============================================================
#  BRAMKARZ (SECURITY GATE)
# ============================================================
def check_complexity(n, k, t):
    try:
        combinations = math.comb(n, k)
        difficulty_factor = (t / k) * 10
        return combinations * difficulty_factor
    except:
        return float('inf')

# ============================================================
#  BAZA PAMIĘCI (CACHE)
# ============================================================
def get_db_connection():
    conn = sqlite3.connect("beta_systemy.db")
    curr = conn.cursor()
    curr.execute("CREATE TABLE IF NOT EXISTS cache (klucz TEXT PRIMARY KEY, wyniki TEXT)")
    conn.commit()
    return conn

def pobierz_surowy_system(v, k, t, max_pct, min_norma):
    klucz = f"{v}_{k}_{t}_{max_pct}_{min_norma}"
    conn = get_db_connection()
    curr = conn.cursor()
    row = curr.execute("SELECT wyniki FROM cache WHERE klucz = ?", (klucz,)).fetchone()
    conn.close()
    if row:
        return json.loads(row[0])
    return None

def zapisz_surowy_system(v, k, t, max_pct, min_norma, wyniki):
    klucz = f"{v}_{k}_{t}_{max_pct}_{min_norma}"
    conn = get_db_connection()
    curr = conn.cursor()
    curr.execute("INSERT OR REPLACE INTO cache VALUES (?, ?)", (klucz, json.dumps(wyniki)))
    conn.commit()
    conn.close()

# ============================================================
#  SYSTEM JĘZYKÓW & STYL
# ============================================================
if "lang" not in st.session_state:
    st.session_state.lang = "PL"

def T(pl, en):
    return pl if st.session_state.lang == "PL" else en

st.set_page_config(page_title="Maria System - β-Universal PRO", layout="centered")

st.markdown("""
<style>
    :root { color-scheme: dark; }
    body { background-color: #0E1117; }
    h1, h2, h3 { color: #4CAF50 !important; }
    .stButton>button { 
        background-color: #4CAF50 !important; color: white !important; 
        border-radius: 8px !important; width: 100%; height: 50px; font-weight: bold; border: none;
    }
    hr { border: none; border-top: 2px solid #00ffcc !important; margin: 20px 0; }
    .stSlider label, .stSlider div { color: #ffffff !important; }
    .stSlider [data-baseweb="slider"] > div:first-child { background: transparent !important; }
    .stSlider [data-baseweb="slider"] > div > div:first-child { background-color: #ffffff !important; }
    .stSlider [data-baseweb="slider"] [role="slider"] { background-color: #ffffff !important; border: 2px solid #ffffff !important; }
    .ticket-line { 
        font-family: 'Courier New', monospace; font-size: 22px; color: #FFFF00 !important; 
        background-color: #262730; padding: 8px 15px; margin-bottom: 8px; border-radius: 10px;
        border-left: 5px solid #FFFF00; font-weight: bold;
    }
    .ticket-number { color: #4CAF50; font-weight: bold; margin-right: 15px; font-size: 16px; }
    .status-bar { padding: 5px 15px; background: #262730; border-radius: 20px; border-left: 5px solid #00ffcc; font-family: 'Courier New', monospace; font-size: 14px; color: #ffffff; margin-top: 10px; }
    .status-value { color: #4CAF50; font-weight: bold; }
    .stTooltipIcon svg { fill: #ff9800 !important; color: #ff9800 !important; }
    .norm-row { background-color: #262730; color: #ffffff; padding: 10px 15px; margin: 5px 0; border-left: 5px solid #FFFF00; font-size: 16px; }
</style>
""", unsafe_allow_html=True)

# LOGIKA KALKULATORA
def kalkulator_norm(n, k, t):
    wyniki = []
    for trafienia in range(t, k + 1):
        norma = math.comb(trafienia, t)
        wyniki.append((trafienia, norma))
    return wyniki

# NAGŁÓWEK
title_col, lang_col = st.columns([6, 1])
with title_col: st.title(T("🏗️ Maria System - β-Universal PRO", "🏗️ Maria System - β-Universal PRO"))
with lang_col:
    if st.button("PL/EN"): st.session_state.lang = "EN" if st.session_state.lang == "PL" else "PL"

st.markdown("---")
st.header(T("⚙️ Konfiguracja systemu", "⚙️ System configuration"))
c1, c2, c3 = st.columns(3)
with c1: v_pula = st.number_input(T("🎲 Pula (n)", "🎲 Pool (n)"), min_value=1, value=1, help=T("Całkowita pula liczb dostępnych w systemie (n).", "Total range of numbers available in the pool (n)."))
with c2: k_zaklad = st.number_input(T("🔢 Zakład (k)", "🔢 Ticket (k)"), min_value=1, value=1, help=T("Liczba liczb w jednym zakładzie (k).", "Number of balls per ticket (k)."))
with c3: t_gwar = st.number_input(T("🎯 Gwarancja (t)", "🎯 Guarantee (t)"), min_value=1, value=1, help=T("Stopień gwarancji systemu (t) – trafienie minimum t w każdym kuponie.", "System guarantee degree (t) – ensure at least t matches per ticket."))

# TRYB AUTO
if st.session_state.get("tryb_auto"):
    st.markdown(f"### 🧮 {T('KALKULATOR NORM SYSTEMOWYCH', 'SYSTEM NORM CALCULATOR')}")
    for traf, norma in reversed(kalkulator_norm(v_pula, k_zaklad, t_gwar)):
        st.markdown(f'<div class="norm-row">{T("Gwarancja", "Guarantee")} <b>{t_gwar}</b> {T("przy trafieniu", "at hit")} <b>{traf}</b> {T("z", "from")} <b>{v_pula}</b> | {T("Sugerowana Norma", "Suggested Norm")}: <b>{norma}</b></div>', unsafe_allow_html=True)
    if st.button(T("ZAMKNIJ", "CLOSE")):
        st.session_state.tryb_auto = False
        st.rerun()
    st.stop()

# FILTRY
st.subheader(T("🛡️ Filtry optymalizacji pokrycia", "🛡️ Coverage optimization filters"))
c4, c5a, c5b = st.columns([3, 2, 1])
with c4: limit_procent = st.slider(T("📊 Współczynnik pokrycia (%)", "📊 Coverage ratio (%)"), 0.0, 100.0, 1.0, step=1.0, help=T("Określa pożądany procentowy stopień pokrycia.", "Specifies the desired coverage ratio."))
with c5a: limit_norma = st.number_input(T("🛑 Minimalna wymagana Norma", "🛑 Minimum required Norm"), min_value=1, value=1, help=T("Minimalna liczba unikalnych układów gwarantowanych.", "Minimum number of unique guaranteed combinations."))
with c5b:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("AUTO", help=T("Otwórz kalkulator norm", "Open norm calculator")):
        st.session_state.tryb_auto = True
        st.rerun()

st.header(T("✍️ Twoje liczby", "✍️ Your numbers"))
user_numbers_raw = st.text_area(T("Wpisz swoje liczby", "Enter numbers"), help=T("Wpisz własny zestaw liczb.", "Enter your custom numbers."))
st.markdown("---")

# ============================================================
#  SILNIK — WERSJA ITERACYJNA (BEZPIECZNA DLA RAM)
# ============================================================
def build_system(v, k, t, max_pct, min_norma):
    conn = sqlite3.connect(":memory:")
    curr = conn.cursor()
    curr.execute("CREATE TABLE cele (kombinacja TEXT PRIMARY KEY)")
    cele_gen = (",".join(map(str, c)) for c in itertools.combinations(range(1, v + 1), t))
    curr.executemany("INSERT INTO cele (kombinacja) VALUES (?)", ((c,) for c in cele_gen))
    conn.commit()

    total_to_cover = curr.execute("SELECT COUNT(*) FROM cele").fetchone()[0]
    covered_count = 0
    wybrane_zaklady = []
    
    progress_bar = st.progress(0)
    stat_placeholder = st.empty()
    max_in_ticket = math.comb(k, t)

    for norma in range(max_in_ticket, 0, -1):
        if norma < min_norma:
            st.warning(f"{T('Zatrzymano: Osiągnięto normę', 'Stopped: Reached norm')} {norma+1}. {T('Następna norma to', 'Next norm is')} {norma}.")
            break
        for ticket in itertools.combinations(range(1, v + 1), k):
            sub_combos = [",".join(map(str, c)) for c in itertools.combinations(ticket, t)]
            placeholders = ",".join(["?"] * len(sub_combos))
            if curr.execute(f"SELECT COUNT(*) FROM cele WHERE kombinacja IN ({placeholders})", sub_combos).fetchone()[0] >= norma:
                wybrane_zaklady.append(ticket)
                curr.execute(f"DELETE FROM cele WHERE kombinacja IN ({placeholders})", sub_combos)
                covered_count += curr.rowcount
                conn.commit()
                procent = (covered_count / total_to_cover) * 100
                progress_bar.progress(min(procent / 100.0, 1.0))
                stat_placeholder.text(f"Norma: {norma} | Postęp: {procent:.2f}% | Zostało: {total_to_cover - covered_count} | Bilety: {len(wybrane_zaklady)}")
                if procent >= max_pct:
                    st.warning(f"{T('Zatrzymano: Osiągnięto limit postępu', 'Stopped: Progress limit reached')} {max_pct:.2f}%.")
                    conn.close(); return wybrane_zaklady
    conn.close(); return wybrane_zaklady

# WYNIKI
if st.button(T("🚀 GENERUJ SYSTEM", "🚀 GENERATE SYSTEM")):
    # 1. BRAMKARZ: Sprawdź złożoność
    HARD_LIMIT = 50_000_000
    score = check_complexity(v_pula, k_zaklad, t_gwar)
    
    if score > HARD_LIMIT:
        st.error(f"❌ {T('System przekracza dopuszczalną złożoność obliczeniową (Score: ', 'System exceeds maximum computational complexity (Score: ')}{score:.0f}). {T('Zmniejsz pulę lub dostosuj parametry.', 'Please reduce the pool or adjust parameters.')}")
    else:
        # 2. Sprawdź bazę (Cache)
        res = pobierz_surowy_system(v_pula, k_zaklad, t_gwar, limit_procent, limit_norma)
        
        if res is not None:
            st.info(f"Znaleziono bilety: {len(res)}")
        else:
            # 3. Brak w bazie - miel silnik
            res = build_system(v_pula, k_zaklad, t_gwar, limit_procent, limit_norma)
            # 4. Zapisz surowy wynik do bazy
            zapisz_surowy_system(v_pula, k_zaklad, t_gwar, limit_procent, limit_norma, res)
        
        # 5. Mapowanie liczb
        if user_numbers_raw:
            try:
                u_list = [int(x) for x in user_numbers_raw.replace(",", " ").split()]
                if len(u_list) >= v_pula:
                    mapping = {i+1: u_list[i] for i in range(v_pula)}
                    res = [tuple(sorted([mapping[n] for n in t])) for t in res]
            except: st.error("Błąd mapowania!")
        st.session_state.last_res = res

if "last_res" in st.session_state:
    for i, t in enumerate(st.session_state.last_res, 1):
        formatted = " ".join(f"{x:02d}" for x in t)
        st.markdown(f'<div class="ticket-line"><span class="ticket-number">{i:03d}:</span> {formatted}</div>', unsafe_allow_html=True)
    st.download_button(label=T("📥 Pobierz system (TXT)", "📥 Download system (TXT)"), data="\n".join([" ".join(f"{x:02d}" for x in t) for t in st.session_state.last_res]), file_name="maria_system.txt", mime="text/plain")

# OSTRZEŻENIE I STOPKA
st.markdown(f"""
<div style="background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%); border-left: 5px solid #ffd600; padding: 15px; border-radius: 0 10px 10px 0; font-size: 14px; color:#ecf0f1; margin: 30px 0; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
    <strong>⚠️ {T('Informacja:', 'Note:')}</strong> {T('System służy do celów analitycznych i statystycznych. Nie stanowi porady inwestycyjnej ani gwarancji wyników. Gry losowe wiążą się z ryzykiem.', 'The system is for analytical and statistical purposes only. It does not constitute investment advice or a guarantee of results. Games of chance involve risk.')}
</div>
""", unsafe_allow_html=True)
st.markdown("---")
st.markdown(f"<div style='text-align:center; color:#00ffcc;'>© 2026 Maria System | {T('Wszelkie prawa zastrzeżone', 'All rights reserved')}</div>", unsafe_allow_html=True)
