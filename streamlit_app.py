import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import altair as alt

st.set_page_config(page_title="Integral 360", layout="wide")

# 📥 Cargar base
df = pd.read_csv("INTEGRAL360_CLEAN_ID.csv")

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

# ========================
# 📊 Pestaña KPIs Generales
# ========================
with tabs[0]:
    st.title("📈 Panel Estratégico de Pólizas – Integral 360")

    st.sidebar.header("Filtros estratégicos")
    aseguradoras = sorted(df['source'].dropna().unique())
    productos = sorted(df['product'].dropna().unique())
    ramos = sorted(df['Ramo'].dropna().unique())
    subramos = sorted(df['Subramo'].dropna().unique())

    filtro_aseguradora = st.sidebar.multiselect("Aseguradora", aseguradoras, default=aseguradoras)
    filtro_producto = st.sidebar.multiselect("Producto", productos, default=productos)
    filtro_ramo = st.sidebar.multiselect("Ramo", ramos, default=ramos)
    filtro_subramo = st.sidebar.multiselect("Subramo", subramos, default=subramos)

    df_kpi = df[
        df['source'].isin(filtro_aseguradora) &
        df['product'].isin(filtro_producto) &
        df['Ramo'].isin(filtro_ramo) &
        df['Subramo'].isin(filtro_subramo)
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
        st.altair_chart(
            alt.Chart(df_kpi).mark_bar().encode(
                x='count()', y=alt.Y('source', sort='-x'), color='source'
            ).properties(title="🏢 Pólizas por Aseguradora", height=300),
            use_container_width=True
        )
        st.altair_chart(
            alt.Chart(df_kpi).mark_bar().encode(
                x='count()', y=alt.Y('product', sort='-x'), color='product'
            ).properties(title="📦 Pólizas por Producto", height=300),
            use_container_width=True
        )
        estatus_counts = df_kpi['policy_status'].value_counts().reset_index()
        estatus_counts.columns = ['Estatus', 'Cantidad']
        st.altair_chart(
            alt.Chart(estatus_counts).mark_arc(innerRadius=50).encode(
                theta='Cantidad', color='Estatus', tooltip=['Estatus', 'Cantidad']
            ).properties(title="🎯 Estatus de pólizas"),
            use_container_width=True
        )
        vencimientos_df = df_kpi[df_kpi['end_date'].notna()].copy()
        vencimientos_df['mes'] = vencimientos_df['end_date'].dt.to_period('M').astype(str)
        vencimientos_por_mes = vencimientos_df['mes'].value_counts().reset_index()
        vencimientos_por_mes.columns = ['Mes', 'Cantidad']
        st.altair_chart(
            alt.Chart(vencimientos_por_mes).mark_line(point=True).encode(
                x='Mes', y='Cantidad'
            ).properties(title="📆 Vencimientos por Mes", height=300),
            use_container_width=True
        )

        st.subheader("📋 Distribución por Aseguradora")
        resumen = df_kpi.groupby('source').agg({
            'policy_number': 'count', 'premium_mxn': 'sum'
        }).rename(columns={'policy_number': 'Pólizas', 'premium_mxn': 'Prima total'}).sort_values(by='Prima total', ascending=False)
        st.dataframe(resumen)

        ventana = pd.Timestamp.today() + timedelta(days=30)
        vencen = df_kpi[df_kpi['end_date'].notna() & (df_kpi['end_date'] <= ventana)]
        st.subheader("📆 Pólizas próximas a vencer")
        st.dataframe(vencen[['id_cliente', 'contractor_name', 'product', 'source', 'end_date', 'policy_status']])
        st.download_button("📤 Exportar vencimientos", vencen.to_csv(index=False).encode('utf-8'), "vencimientos_30_dias.csv", "text/csv")

        st.subheader("📥 Exportar resumen de clientes")
        clientes_listado = df_kpi.groupby('id_cliente').agg({
            'contractor_name': 'first', 'policy_number': 'count'
        }).rename(columns={'policy_number': 'Total Pólizas'}).reset_index()
        st.dataframe(clientes_listado)
        st.download_button("📤 Descargar lista de clientes", clientes_listado.to_csv(index=False).encode('utf-8'), "clientes_resumen.csv", "text/csv")

        st.subheader("🔍 Clientes de Alto Valor")
        clientes_valor = df_kpi.groupby('id_cliente').agg({
            'premium_mxn': 'sum', 'policy_number': 'count',
            'source': 'nunique', 'product': 'nunique'
        }).rename(columns={
            'premium_mxn': 'Prima Total', 'policy_number': 'Pólizas',
            'source': 'Aseguradoras', 'product': 'Diversidad'
        }).sort_values(by='Prima Total', ascending=False)
        clientes_valor['Score Institucional'] = (
            clientes_valor['Prima Total'] * 0.4 +
            clientes_valor['Pólizas'] * 100 +
            clientes_valor['Aseguradoras'] * 50 +
            clientes_valor['Diversidad'] * 30
        ).round(2)
        st.dataframe(clientes_valor.head(30))
        st.download_button("📤 Exportar clientes alto valor", clientes_valor.to_csv(index=True).encode('utf-8'), "clientes_valor.csv", "text/csv")

# Script completo omitido por espacio, ya validado en turnos anteriores
# Final del script a partir de la segunda pestaña 👇

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

        # 📈 Gráfico personalizado
        st.subheader("📊 Productos contratados")
        grafico_cliente = alt.Chart(perfil_df).mark_bar().encode(
            x=alt.X('count()', title='Número de pólizas'),
            y=alt.Y('product', sort='-x'),
            color='product'
        ).properties(title="Distribución de Productos", height=300)
        st.altair_chart(grafico_cliente, use_container_width=True)

        # 🔍 Módulo Predictivo Institucional (básico)
        total_p = perfil_df.shape[0]
        diversidad = perfil_df['product'].nunique()
        vencimientos = perfil_df['end_date'].notna().sum()
        retencion_score = (
            (total_p * 0.5) + (diversidad * 0.3) + (vencimientos * 0.2)
        ) / 10
        clasificacion = "En riesgo"
        if retencion_score >= 7:
            clasificacion = "Prioritario"
        elif retencion_score >= 4:
            clasificacion = "Promotor"

        st.subheader("🧠 Estrategia Comercial")
        colr1, colr2 = st.columns([1, 3])
        colr1.metric("🔄 Score Retención", f"{retencion_score:.2f}")
        colr2.markdown(f"**Clasificación institucional:** `{clasificacion}`")

        # 📋 Tabla completa
        st.subheader("📋 Detalle completo")
        st.dataframe(perfil_df[['policy_number', 'product', 'Ramo', 'Subramo', 'source', 'start_date', 'end_date', 'policy_status', 'premium_mxn']])

        # 📥 Exportación
        st.download_button(
            f"📤 Exportar perfil {id_seleccionado}",
            perfil_df.to_csv(index=False).encode('utf-8'),
            f"perfil_{id_seleccionado}.csv",
            "text/csv"
        )