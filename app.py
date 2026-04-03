import streamlit as st
import openai
import json
import pandas as pd
import io

# --- KONFIGURACE ---
st.set_page_config(page_title="Professional English Master", layout="wide", page_icon="🏴󠁧󠁢󠁳󠁣󠁴󠁿")

# Načtení klíče ze Streamlit Secrets
try:
    client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception:
    st.error("⚠️ Chybí API klíč! Nastavte jej v Settings -> Secrets na Streamlit Cloudu.")

# --- GRAFIKA (Dark Mode proof) ---
st.markdown("""
    <style>
    .english-box, .scottish-box { 
        background-color: #ffffff; 
        color: #1a202c !important; 
        padding: 20px; 
        border-radius: 10px; 
        border: 1px solid #e2e8f0;
        margin-bottom: 15px;
    }
    .english-box *, .scottish-box * { color: #1a202c !important; }
    h3 { color: #1e3a8a; }
    </style>
""", unsafe_allow_html=True)

# --- MOZEK AI ---
def analyze_text(text):
    system_instruction = """Jsi profesionální učitel angličtiny. 
    Specializace: aktivní mluvená angličtina a skotská angličtina.
    Vrať JSON: original, correction (tučně chyby), meaning (en), grammar (en), stylistic (en/scot), translation (cz), phonetic (IPA), example (en)."""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": system_instruction}, {"role": "user", "content": text}],
        response_format={ "type": "json_object" }
    )
    return json.loads(response.choices[0].message.content)

# --- ROZHRANÍ ---
st.title("🏴󠁧󠁢󠁳󠁣󠁴󠁿 Professional English Master")

user_input = st.text_area("Zadejte text k analýze:", placeholder="I didn't saw him...", height=100)

if user_input:
    with st.spinner('Učitel přemýšlí...'):
        try:
            res = analyze_text(user_input)
            
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("✅ Correction")
                st.success(res['correction'])
            with c2:
                st.subheader("🇨🇿 Překlad")
                st.info(res['translation'])

            st.subheader("🧠 Grammar & Meaning")
            st.markdown(f"<div class='english-box'><b>Meaning:</b> {res['meaning']}<br><br><b>Grammar:</b> {res['grammar']}</div>", unsafe_allow_html=True)

            st.subheader("🏴󠁧󠁢󠁳󠁣󠁴󠁿 Stylistic & Scottish Corner")
            st.markdown(f"<div class='scottish-box'>{res['stylistic']}</div>", unsafe_allow_html=True)

            # ANKI EXPORT
            st.divider()
            csv_data = [[res['original'], res['phonetic'], "", res['meaning'], res['translation'], res['example'], "NEW"]]
            df = pd.DataFrame(csv_data)
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False, header=False, sep=";")
            
            st.download_button("📥 Stáhnout pro Anki (CSV)", csv_buffer.getvalue(), "anki_export.csv", "text/csv")
            
        except Exception as e:
            st.error(f"Chyba: {e}")
