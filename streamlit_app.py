import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import altair as alt

# 🧭 Configuración inicial
st.set_page_config(page_title="Integral 360", layout="wide")

# 🛡️ Encabezado institucional con columnas
col_logo, col_titulo = st.columns([1, 5])
with col_logo:
    try:
        st.image("logo_integral360.png", width=100)
    except:
        st.warning("No se encontró logo_integral360.png")

with col_titulo:
    st.markdown("## 🛡️ Plataforma Integral 360 – Visualización Estratégica")

col_cliente, _ = st.columns([1, 5])
with col_cliente:
    try:
        st.image("logo_cliente.png", caption="Marca institucional del cliente", width=100)
    except:
        st.info("Puede agregar logo_cliente.png para personalizar el dashboard")

# 📂 Carga automática del archivo local
try:
    df = pd.read_csv("INTEGRAL360_CLEAN_ID.csv")
except FileNotFoundError:
    st.error("⛔ No se encontró el archivo INTEGRAL360_CLEAN_ID.csv en la carpeta del proyecto.")
    st.stop()

# 🧹 Conversión segura de fechas
for col in ['start_date', 'end_date', 'birth_date']:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors='coerce')

# 🔖 Normalización tipográfica
for campo in ['Ramo', 'Subramo', 'product']:
    if campo in df.columns:
        df[campo] = df[campo].astype(str).str.strip().str.upper()

# 🧭 Homologación de nomenclaturas
mapa_ramos = {
    'AUTO': 'AUTOS', 'AUTOS PARTICULAR': 'AUTOS', 'CAMIONES': 'AUTOS',
    'BENEFICIOS': 'BENEFICIOS', 'DAÑOS': 'DAÑOS', 'GMM': 'GMM', 'HOGAR': 'HOGAR',
    'PMM': 'PMM', 'SALUD': 'SALUD', 'VDA': 'VIDA', 'VIDA': 'VIDA'
}
mapa_subramos = {
    'ACCIDENTES': 'ACCIDENTES', 'AUTOS PARTICULAR': 'AUTOS', 'CAMIONES': 'AUTOS',
    'GMM INDIVIDUAL / FAMILIA': 'GMM', 'GERENTE GENERAL': 'GERENCIA',
    'RC': 'RESPONSABILIDAD CIVIL', 'RESPONSABILIDAD CIVIL': 'RESPONSABILIDAD CIVIL',
    'HOGAR': 'HOGAR', 'YAYA': 'YAYA', 'EDUCATIVO': 'EDUCATIVO',
    'EMPRESARIAL': 'EMPRESARIAL', 'SALUD': 'SALUD', 'VIDA': 'VIDA'
}
df['Ramo'] = df['Ramo'].replace(mapa_ramos)
df['Subramo'] = df['Subramo'].replace(mapa_subramos)

# 🧭 Tabs
tabs = st.tabs(["📊 KPIs Generales", "🗂️ Perfil por Cliente"])

# ========================
# 📊 Pestaña KPIs Generales
# ========================
with tabs[0]:
    st.header("📈 Panel Estratégico de Pólizas")

    filtros = {
        "Aseguradora": sorted(df['source'].dropna().unique()),
        "Producto": sorted(df['product'].dropna().unique()),
        "Ramo": sorted(df['Ramo'].dropna().unique()),
        "Subramo": sorted(df['Subramo'].dropna().unique())
    }

    seleccion = {
        clave: st.sidebar.multiselect(clave, valores, default=valores)
        for clave, valores in filtros.items()
    }

    df_kpi = df[
        df['source'].isin(seleccion['Aseguradora']) &
        df['product'].isin(seleccion['Producto']) &
        df['Ramo'].isin(seleccion['Ramo']) &
        df['Subramo'].isin(seleccion['Subramo'])
    ]

    if df_kpi.empty:
        st.warning("⚠️ No se encontraron pólizas con los filtros aplicados.")
    else:
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("📄 Pólizas", f"{df_kpi['policy_number'].nunique():,}")
        col2.metric("👥 Clientes", f"{df_kpi['id_cliente'].nunique():,}")
        col3.metric("🏢 Aseguradoras", f"{df_kpi['source'].nunique():,}")
        col4.metric("🧾 Productos", f"{df_kpi['product'].nunique():,}")
        col5.metric("💰 Prima total MXN", f"${df_kpi['premium_mxn'].sum():,.2f}")

        st.subheader("📊 Distribución del Portafolio")
        graf1 = alt.Chart(df_kpi).mark_bar().encode(x='count()', y='source', color='source').properties(height=300)
        graf2 = alt.Chart(df_kpi).mark_bar().encode(x='count()', y='product', color='product').properties(height=300)
        st.altair_chart(graf1, use_container_width=True)
        st.altair_chart(graf2, use_container_width=True)

        estatus_counts = df_kpi['policy_status'].value_counts().reset_index()
        estatus_counts.columns = ['Estatus', 'Cantidad']
        st.subheader("🎯 Estatus de pólizas")
        st.altair_chart(
            alt.Chart(estatus_counts).mark_arc(innerRadius=50).encode(
                theta='Cantidad', color='Estatus', tooltip=['Estatus', 'Cantidad']
            ), use_container_width=True
        )

        vencimientos_df = df_kpi[df_kpi['end_date'].notna()].copy()
        vencimientos_df['mes'] = vencimientos_df['end_date'].dt.to_period('M').astype(str)
        resumen_mes = vencimientos_df['mes'].value_counts().reset_index()
        resumen_mes.columns = ['Mes', 'Cantidad']
        st.subheader("📆 Vencimientos por Mes")
        st.altair_chart(
            alt.Chart(resumen_mes).mark_line(point=True).encode(x='Mes', y='Cantidad'),
            use_container_width=True
        )

        st.subheader("📥 Exportar Información")
        ventana = pd.Timestamp.today() + timedelta(days=30)
        vencen = df_kpi[df_kpi['end_date'].notna() & (df_kpi['end_date'] <= ventana)]
        st.download_button("📤 Exportar vencimientos", vencen.to_csv(index=False).encode('utf-8'), "vencimientos_30_dias.csv", "text/csv")

        clientes_listado = df_kpi.groupby('id_cliente').agg({
            'contractor_name': 'first', 'policy_number': 'count'
        }).rename(columns={'policy_number': 'Total Pólizas'}).reset_index()
        st.download_button("📤 Descargar clientes", clientes_listado.to_csv(index=False).encode('utf-8'), "clientes_resumen.csv", "text/csv")

        clientes_valor = df_kpi.groupby('id_cliente').agg({
            'premium_mxn': 'sum', 'policy_number': 'count',
            'source': 'nunique', 'product': 'nunique'
        }).rename(columns={
            'premium_mxn': 'Prima Total', 'policy_number': 'Pólizas',
            'source': 'Aseguradoras', 'product': 'Diversidad'
        })
        clientes_valor['Score Institucional'] = (
            clientes_valor['Prima Total'] * 0.4 +
            clientes_valor['Pólizas'] * 100 +
            clientes_valor['Aseguradoras'] * 50 +
            clientes_valor['Diversidad'] * 30
        ).round(2)
        st.subheader("🔍 Clientes de Alto Valor")
        st.dataframe(clientes_valor.head(30))
        st.download_button("📤 Exportar alto valor", clientes_valor.to_csv(index=True).encode('utf-8'), "clientes_valor.csv", "text/csv")

# ========================
# 🗂️ Pestaña Perfil por Cliente
# ========================
with tabs[1]:
    st.title("🧑‍💼 Perfil por Cliente – Integral 360")

    id_seleccionado = st.selectbox("Seleccionar cliente (ID)", sorted(df['id_cliente'].dropna().unique()))
    perfil_df = df[df['id_cliente'] == id_seleccionado]

    if perfil_df.empty:
        st.warning("⚠️ No se encontraron pólizas asociadas.")
    else:
        nombre = perfil_df['contractor_name'].dropna().iloc[0]
        st.markdown(f"### 👤 Contratante: `{nombre}`")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("📄 Pólizas", f"{perfil_df.shape[0]}")
        col2.metric("🏢 Aseguradoras", f"{perfil_df['source'].nunique()}")
        col3.metric("🧾 Productos", f"{perfil_df['product'].nunique()}")
        col4.metric("💰 Prima total MXN", f"${perfil_df['premium_mxn'].sum():,.2f}")

# 📊 Gráfico de productos contratados
st.subheader("📊 Productos contratados")
grafico_cliente = alt.Chart(perfil_df).mark_bar().encode(
    x=alt.X('count()', title='Número de pólizas'),
    y=alt.Y('product', sort='-x'),
    color='product'
).properties(title="Distribución de Productos", height=300)
st.altair_chart(grafico_cliente, use_container_width=True)

# 🔍 Módulo Predictivo Institucional
total_p = perfil_df.shape[0]
diversidad = perfil_df['product'].nunique()
vencimientos = perfil_df['end_date'].notna().sum()
retencion_score = ((total_p * 0.5) + (diversidad * 0.3) + (vencimientos * 0.2)) / 10
clasificacion = "En riesgo"
if retencion_score >= 7:
    clasificacion = "Prioritario"
elif retencion_score >= 4:
    clasificacion = "Promotor"

st.subheader("🧠 Estrategia Comercial")
colr1, colr2 = st.columns([1, 3])
colr1.metric("🔄 Score Retención", f"{retencion_score:.2f}")
colr2.markdown(f"**Clasificación institucional:** `{clasificacion}`")

# 📋 Detalle completo
st.subheader("📋 Detalle completo")
st.dataframe(perfil_df[['policy_number', 'product', 'Ramo', 'Subramo', 'source', 'start_date', 'end_date', 'policy_status', 'premium_mxn']])

# 📥 Exportación
st.download_button(
    f"📤 Exportar perfil {id_seleccionado}",
    perfil_df.to_csv(index=False).encode('utf-8'),
    f"perfil_{id_seleccionado}.csv",
    "text/csv"
)
       