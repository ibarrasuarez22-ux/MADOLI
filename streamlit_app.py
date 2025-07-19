import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import altair as alt

# 🧭 Configuración inicial de la app
st.set_page_config(page_title="Integral 360", layout="wide")

# 🛡️ Encabezado institucional
try:
    st.image("logo_integral360.png", width=200)
except:
    st.warning("No se encontró logo_integral360.png")

st.markdown("## 🛡️ Plataforma Integral 360 – Visualización Estratégica")

try:
    st.image("logo_cliente.png", caption="Marca institucional del cliente")
except:
    st.info("Puede agregar logo_cliente.png para personalizar el dashboard")

# 📂 Cargar base institucional desde archivo
archivo_csv = st.file_uploader("📥 Cargar base institucional (.csv)", type=["csv"])
if archivo_csv:
    df = pd.read_csv(archivo_csv)
else:
    st.stop()

# 🧹 Conversión segura de fechas
for col in ['start_date', 'end_date', 'birth_date']:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors='coerce')

# 🔖 Normalización tipográfica
for campo in ['Ramo', 'Subramo', 'product']:
    if campo in df.columns:
        df[campo] = df[campo].astype(str).str.strip().str.upper().fillna('SIN DEFINIR')

# 🧭 Diccionarios institucionales actualizados
mapa_ramos = {
    'AUTO': 'AUTOS', 'AUTOS PARTICULAR': 'AUTOS', 'CAMIONES': 'AUTOS', 'AUTOS': 'AUTOS',
    'BENEFICIOS': 'BENEFICIOS', 'DAÑOS': 'DAÑOS', 'GMM': 'GMM', 'HOGAR': 'HOGAR',
    'PMM': 'PMM', 'SALUD': 'SALUD', 'VDA': 'VIDA', 'VIDA': 'VIDA'
}
mapa_subramos = {
    'ACCIDENTES INDIVIDUALES': 'ACCIDENTES', 'ACCIDENTES': 'ACCIDENTES',
    'AUTO': 'AUTOS', 'AUTOS PARTICULAR': 'AUTOS', 'CAMIONES': 'AUTOS', 'AUTOS': 'AUTOS',
    'GMM INDIVIDUAL / FAMILIA': 'GMM', 'GMM': 'GMM',
    'GERENTE GENERAL': 'GERENCIA',
    'RC': 'RESPONSABILIDAD CIVIL', 'RESPONSABILIDAD CIVIL': 'RESPONSABILIDAD CIVIL',
    'HOGAR': 'HOGAR', 'YAYA': 'YAYA',
    'EDUCATIVO': 'EDUCATIVO', 'EMPRESARIAL': 'EMPRESARIAL',
    'SALUD': 'SALUD', 'VIDA': 'VIDA'
}
df['Ramo'] = df['Ramo'].replace(mapa_ramos)
df['Subramo'] = df['Subramo'].replace(mapa_subramos)

# 🧭 Tabs
tabs = st.tabs(["📊 KPIs Generales", "🗂️ Perfil por Cliente"])

# El resto del código permanece igual a su versión validada previamente (ya es funcional y robusto)