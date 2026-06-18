import streamlit as st
import itertools
import sqlite3
import json
import math
import gc

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
# BAZA DANYCH
# ============================================================
def get_db_connection():
    conn = sqlite3.connect('alfa_systemy.db')
    conn.execute("CREATE TABLE IF NOT EXISTS cache (klucz TEXT PRIMARY KEY, wyniki TEXT)")
    return conn

def pobierz_surowy_system(v, k, t):
    klucz = f"{v}_{k}_{t}"
    conn = get_db_connection()
    row = conn.execute("SELECT wyniki FROM cache WHERE klucz = ?", (klucz,)).fetchone()
    conn.close()
    if row:
        dane = json.loads(row[0])
        if isinstance(dane, dict):
            return dane.get("wyniki"), dane.get("status", "full")
        return dane, "full"
    return None, None

def zapisz_surowy_system(v, k, t, wyniki, status):
    klucz = f"{v}_{k}_{t}"
    conn = get_db_connection()
    dane_do_zapisu = {"wyniki": wyniki, "status": status}
    conn.execute("INSERT OR REPLACE INTO cache VALUES (?, ?)", (klucz, json.dumps(dane_do_zapisu)))
    conn.commit()
    conn.close()

# ============================================================
# SYSTEM JĘZYKÓW & KONFIGURACJA
# ============================================================
if "lang" not in st.session_state:
    st.session_state.lang = "PL"

def T(pl, en):
    return pl if st.session_state.lang == "PL" else en

st.set_page_config(page_title="Maria System - α-TCE PRO", layout="centered")

# TWÓJ LOOK + POPRAWKI BŁĘKITU
st.markdown("""
<style>
    :root { color-scheme: dark; }
    body { background-color: #0E1117; }
    h1, h2, h3 { color: #4CAF50 !important; }
    
    .stButton>button { 
        background-color: #4CAF50 !important; 
        color: white !important; 
        border-radius: 8px !important; 
        width: 100%; height: 50px; font-weight: bold; border: none;
    }
    hr { border: none; border-top: 2px solid #00ffcc !important; margin: 20px 0; }
    
    .ticket-line { 
        font-family: 'Courier New', monospace; font-size: 22px; 
        color: #FFFF00 !important; background-color: #262730; 
        padding: 10px 15px; margin-bottom: 8px; border-radius: 10px;
        border-left: 8px solid #FFFF00; font-weight: bold;
    }
    .ticket-number { color: #4CAF50; font-weight: bold; margin-right: 20px; font-size: 16px; }
    
    .footer { text-align: center; padding: 30px; color: #00ffcc; font-size: 13px; border-top: 1px solid #333; margin-top: 50px; opacity: 0.8; }
    
    .stNumberInput div div input { color: #ffffff !important; font-weight: bold !important; font-size: 20px !important; }

    div[data-baseweb="tag"] {
        background-color: #007bff !important;
        border: none !important;
    }
    
    .live-counter {
        color: #00a2ff;
        font-weight: bold;
        padding: 5px 0;
        margin-bottom: 2px;
    }
    .live-warning { color: #ff9900; }

    /* Kolor tooltipów */
    .stTooltipIcon svg { fill: #ff9800 !important; color: #ff9800 !important; }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------
# NAGŁÓWEK
# ------------------------------------------------

t_col, l_col = st.columns([5, 1])
with t_col:
    st.title(T("🏗️ Maria System - α-TCE PRO", "🏗️ Maria System - α-TCE PRO"))
with l_col:
    if st.button("PL/EN"):
        st.session_state.lang = "EN" if st.session_state.lang == "PL" else "PL"
        st.rerun()

st.markdown("---")

# ----------------------------------------------------
# PARAMETRY
# -----------------------------------------------------

st.header(T("⚙️ Konfiguracja systemu", "⚙️ System configuration"))
c1, c2, c3 = st.columns(3)
with c1:
    v_pula = st.number_input(T("🎲 Pula (n) (Max: 80)", "🎲 Pool (n) (Max: 80)"), min_value=1, max_value=80, value=1,
                             help=T("Całkowita liczba liczb w Twoim systemie (n).", "Total number of balls in your system (n)."))
with c2:
    k_zaklad = st.number_input(T("🔢 Zakład (k)", "🔢 Ticket (k)"), min_value=1, value=1,
                               help=T("Ile liczb zawiera jeden pojedynczy zakład (k).", "How many numbers per single ticket (k)."))
with c3:
    t_gwar = st.number_input(T("🎯 Gwarancja (t)", "🎯 Guarantee (t)"), min_value=1, value=1,
                             help=T("Poziom gwarancji systemu (t) – trafienie minimum t w każdym zakładzie.", "Guarantee level (t) – ensure at least t match in each ticket."))

# ---------------------------------------------------
# WALIDACJA WEJŚCIA
# ----------------------------------------------------

def validate_inputs(v, k, t):
    if t > k:
        return T("Błąd: Gwarancja (t) nie może być większa niż liczba liczb w zakładzie (k).", "Error: Guarantee (t) cannot be greater than numbers per ticket (k).")
    if k > v:
        return T("Błąd: Liczba liczb w zakładzie (k) nie może być większa niż Pula (n).", "Error: Numbers per ticket (k) cannot be greater than Pool (n).")
    return None

error_msg = validate_inputs(v_pula, k_zaklad, t_gwar)

st.header(T("✍️ Twoje liczby", "✍️ Your numbers"))

if "user_multiselect" in st.session_state:
    sel_count = len(st.session_state.user_multiselect)
    if sel_count > 0:
        if sel_count < v_pula:
            st.markdown(f'<div class="live-counter live-warning">⚠️ {T("Wybrano", "Selected")}: {sel_count} / {v_pula} ({T("Brakuje", "Missing")}: {v_pula - sel_count})</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="live-counter">💎 {T("Komplet wybrany", "Full set selected")}: {sel_count} / {v_pula}</div>', unsafe_allow_html=True)

user_list = st.multiselect(
    T("Wybierz liczby (puste = gra 1-n):", "Select numbers (empty = 1-n):"),
    options=list(range(1, 81)),
    max_selections=v_pula,
    key="user_multiselect",
    label_visibility="collapsed",
    help=T("Wybierz własne liczby. Pozostaw puste, aby system operował na standardowym zakresie 1-n.", "Select your own numbers. Leave empty to use standard 1-n range.")
)

st.markdown("---")

# ---------------------------------------------------
# SILNIK MARIA v15
# ----------------------------------------------------

def build_final_gear_system(v, k, t):
    wybrane_zaklady = []
    zapisane_sety = []
    
    counter_placeholder = st.empty()
    generator_trzonow = itertools.combinations(range(1, v + 1), t)

    for trzon in generator_trzonow:
        trzon_set = set(trzon)
        kolizja_trzonu = False
        for zapisany in zapisane_sety:
            if len(trzon_set.intersection(zapisany)) >= t:
                kolizja_trzonu = True
                break
        if kolizja_trzonu: 
            continue
            
        ile_potrzeba_ogon = k - t
        start_liczba = trzon[-1] + 1
        
        def buduj_sekwencyjnie(start, obecny_ogon):
            if len(obecny_ogon) == ile_potrzeba_ogon: 
                return obecny_ogon
                
            for kandydat in range(start, v + 1):
                sklad = list(trzon) + obecny_ogon + [kandydat]
                sklad_set = set(sklad)
                
                kolizja = False
                for zapisany in zapisane_sety:
                    if len(sklad_set.intersection(zapisany)) >= t:
                        kolizja = True
                        break
                        
                if not kolizja:
                    wynik = buduj_sekwencyjnie(kandydat + 1, obecny_ogon + [kandydat])
                    if wynik: 
                        return wynik
            return None

        znaleziony_ogon = buduj_sekwencyjnie(start_liczba, [])
        if znaleziony_ogon:
            pelny_kupon = tuple(sorted(list(trzon) + znaleziony_ogon))
            wybrane_zaklady.append(pelny_kupon)

            # --- BEZPIECZNIK ---
            if len(wybrane_zaklady) >= 500:
                return wybrane_zaklady, "ograniczony"
            # -------------------

            zapisane_sety.append(set(pelny_kupon))
            counter_placeholder.markdown(f"**{T('Znaleziono zakładów', 'Tickets found')}: {len(wybrane_zaklady)}**")
            
    return wybrane_zaklady, "full"

# ---------------------------------------------------
# LOGIKA URUCHOMIENIA
# ---------------------------------------------------

if st.button(T("🚀 GENERUJ SYSTEM", "🚀 GENERATE SYSTEM")):
    if error_msg:
        st.error(error_msg)
    else:
        # BRAMKARZ
        HARD_LIMIT = 10_000_000_000
        score = check_complexity(v_pula, k_zaklad, t_gwar)
        
        if score > HARD_LIMIT:
            st.error(f"❌ {T('System przekracza dopuszczalną złożoność obliczeniową (Score: ', 'System exceeds maximum computational complexity (Score: ')}{score:.0f}).")
        else:
            # BAZA DANYCH - ODCZYT
            res_base, status = pobierz_surowy_system(v_pula, k_zaklad, t_gwar)
            
            if res_base is None:
                # GENEROWANIE - ZAPIS
                res_base, status = build_final_gear_system(v_pula, k_zaklad, t_gwar)
                zapisz_surowy_system(v_pula, k_zaklad, t_gwar, res_base, status)

            # MAPOWANIE LICZB
            if len(user_list) == v_pula:
                mapping = {i+1: user_list[i] for i in range(v_pula)}
                res = [tuple(sorted([mapping[n] for n in b])) for b in res_base]
            else:
                res = res_base
            
            # WYŚWIETLANIE WYNIKÓW
            st.success(f"{T('Gotowe!', 'Done!')} {len(res)} {T('zakładów', 'tickets')}.")
            
            # OSTRZEŻENIE - wyświetla się tylko jeśli status jest 'ograniczony'
            if status == "ograniczony":
                st.warning(T("⚠️ System osiągnął optymalny limit zakładów. Zgodnie z zasadami odpowiedzialnej gry, ograniczyliśmy liczbę kuponów, aby ograniczyć koszt systemu.", 
                             "⚠️ Optimal limit of tickets reached. In accordance with responsible gaming principles, we have limited the number of tickets to manage system costs."))
            
            txt_data = "\n".join(" ".join(f"{x:02d}" for x in bilet) for bilet in res)
            
            for i, bilet in enumerate(res, 1):
                formatted = " ".join(f"{x:02d}" for x in bilet)
                st.markdown(f'<div class="ticket-line"><span class="ticket-number">{i:03d}:</span> {formatted}</div>', unsafe_allow_html=True)

            st.markdown("---")
            st.download_button(
                label=T("📥 Pobierz plik TXT", "📥 Download TXT file"),
                data=txt_data,
                file_name="maria_tce_system.txt",
                mime="text/plain"
            )
            
            # CZYŚCIMY PAMIĘĆ RAM
            del res
            del res_base
            del txt_data
            gc.collect()

# -----------------------------------------------------
# NOWOCZESNE OSTRZEŻENIE
# ------------------------------------------------------
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
        'System TCE PRO służy do celów analitycznych i matematycznych. Nie stanowi porady inwestycyjnej ani prognozy wyników. Hazard wiąże się z ryzykiem.',
        'The TCE PRO system is for analytical and mathematical purposes only. It does not constitute investment advice or result prediction. Gambling involves risk.'
    )}
</div>
""", unsafe_allow_html=True)

st.markdown("---")
st.markdown(f"<div style='text-align:center; color:#00ffcc;'>© 2026 Maria System | {T('Wszelkie prawa zastrzeżone', 'All rights reserved')}</div>", unsafe_allow_html=True)
