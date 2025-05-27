import streamlit as st
import pandas as pd
from fpdf import FPDF
import io
import requests
import sqlite3

# --- Dark Theme CSS + Responsive Layout + Logo + Heading with Animation ---
st.markdown("""
    <style>
        .stApp {
            background-color: #1e1e1e;
            color: #ffffff;
            padding: 20px;
        }
        h1, h2 {
            color: #00c2ff;
            text-align: center;
            animation: fadeInDown 1.2s ease-in-out;
        }
        .stButton>button {
            background-color: #00c2ff;
            color: black;
            font-weight: bold;
            border-radius: 8px;
        }
        .stSelectbox, .stNumberInput, .stTextInput {
            color: black !important;
        }
        @media (max-width: 600px) {
            .stButton>button {
                width: 100%;
            }
        }
        .logo {
            display: block;
            margin-left: auto;
            margin-right: auto;
            width: 100px;
            border-radius: 50%;
            animation: fadeIn 2s ease-in-out;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: scale(0.8); }
            to { opacity: 1; transform: scale(1); }
        }
        @keyframes fadeInDown {
            from { opacity: 0; transform: translateY(-20px); }
            to { opacity: 1; transform: translateY(0); }
        }
    </style>
""", unsafe_allow_html=True)

# --- Logo + Title ---
st.image("https://i.imgur.com/ZF6s192.png", use_container_width=False, width=100, caption="SooBi's Converter")
st.title("🔄 SooBi's Smart Unit Converter")
st.markdown("""
<h2>✨ Simple | Fast | Intelligent</h2>
<p style='text-align: center; animation: fadeIn 1.5s;'>“Har Unit Ka Perfect Answer — Bas Ek Click Mein!”</p>
""", unsafe_allow_html=True)

# --- Conversion Category Selection ---
conversion_category = st.selectbox("Select Conversion Category", ["Length", "Weight", "Temperature", "Currency"])
units = {
    "Length": ["Meters", "Kilometers", "Centimeters"],
    "Weight": ["Kilograms", "Grams", "Pounds"],
    "Temperature": ["Celsius", "Fahrenheit"],
    "Currency": ["USD", "EUR", "INR", "GBP"]
}

from_unit = st.selectbox("From Unit", units[conversion_category])
to_unit = st.selectbox("To Unit", units[conversion_category])
value = st.number_input("Enter Value", step=0.1)

# --- Conversion Logic ---
def convert_units(category, from_u, to_u, val):
    if category == "Length":
        factors = {"Meters": 1, "Kilometers": 1000, "Centimeters": 0.01}
        return val * (factors[from_u] / factors[to_u])

    elif category == "Weight":
        factors = {"Kilograms": 1, "Grams": 0.001, "Pounds": 0.453592}
        return val * (factors[from_u] / factors[to_u])

    elif category == "Temperature":
        if from_u == "Celsius" and to_u == "Fahrenheit":
            return (val * 9/5) + 32
        elif from_u == "Fahrenheit" and to_u == "Celsius":
            return (val - 32) * 5/9
        else:
            return val

    elif category == "Currency":
        api_url = f"https://api.exchangerate-api.com/v4/latest/{from_u}"
        response = requests.get(api_url)
        data = response.json()
        rate = data["rates"].get(to_u)
        if rate:
            return val * rate
        else:
            st.error(f"Conversion rate from {from_u} to {to_u} not available.")
            return None

# --- Session History Setup ---
if "history" not in st.session_state:
    st.session_state.history = []

# --- Database Setup (SQLite) ---
def create_db():
    conn = sqlite3.connect('conversion_history.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS history
                 (category TEXT, from_unit TEXT, to_unit TEXT, input_value REAL, result_value REAL)''')
    conn.commit()
    conn.close()

def save_to_db(category, from_u, to_u, input_val, result_val):
    conn = sqlite3.connect('conversion_history.db')
    c = conn.cursor()
    c.execute("INSERT INTO history (category, from_unit, to_unit, input_value, result_value) VALUES (?, ?, ?, ?, ?)",
              (category, from_u, to_u, input_val, result_val))
    conn.commit()
    conn.close()

# --- Perform conversion ---
if st.button("Convert"):
    if from_unit == to_unit:
        st.warning("Select different units for conversion.")
    else:
        result = convert_units(conversion_category, from_unit, to_unit, value)
        if result is not None:
            st.success(f"{value} {from_unit} = {round(result, 4)} {to_unit}")
            st.session_state.history.append({
                "Category": conversion_category,
                "From": from_unit,
                "To": to_unit,
                "Input": value,
                "Result": round(result, 4)
            })
            save_to_db(conversion_category, from_unit, to_unit, value, round(result, 4))

# --- Show Conversion History ---
if st.session_state.history:
    st.subheader("📜 Conversion History")
    df = pd.DataFrame(st.session_state.history)
    st.dataframe(df)

    excel_file = io.BytesIO()
    with pd.ExcelWriter(excel_file, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='History')
    st.download_button(
        label="📥 Download Excel",
        data=excel_file.getvalue(),
        file_name='conversion_history.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Conversion History", ln=True, align="C")
    for row in st.session_state.history:
        pdf.cell(200, 10, txt=f"{row['Input']} {row['From']} = {row['Result']} {row['To']} ({row['Category']})", ln=True)
    pdf_output = pdf.output(dest='S').encode('latin1')

    st.download_button(
        label="📄 Download PDF",
        data=pdf_output,
        file_name="conversion_history.pdf",
        mime="application/pdf"
    )

# --- Notifications ---
st.info("Use the app to convert units or currencies! 💸")

# --- Initialize DB on App Start ---
create_db()
