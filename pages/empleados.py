import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# CONFIGURACIÓN DE LA PÁGINA Y ESTILO
# ==========================================
st.set_page_config(
    page_title="Dashboard de Empleados",
    page_icon="👔",
    layout="wide"
)

st.markdown("---")

st.markdown("**Creador de la página empleados:** ANCE ARIO")

st.markdown("""
<style>
    .main {
        background: linear-gradient(140deg, #0f172a 0%, #1e293b 100%);
    }
    div[data-testid="metric-container"] {
        background: rgba(30, 41, 59, 0.5);
        border-radius: 12px;
        padding: 20px;
        border: 1px solid rgba(148, 163, 184, 0.3);
        margin: 10px;
    }
    .box {
        background: rgba(30, 41, 59, 0.4);
        padding: 20px;
        border-radius: 12px;
        border: 1px solid rgba(148, 163, 184, 0.3);
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# DATOS SIMULADOS (FUNCIONALES)
# ==========================================
np.random.seed(42)

sucursales = ["Central", "Norte", "Sur", "Este", "Oeste"]
turnos = ["Mañana", "Tarde", "Noche"]
estados = ["Activo", "Vacaciones", "Suspendido", "Retirado"]

empleados = {
    "id_empleado": range(1, 41),
    "empleado": [f"Empleado {i}" for i in range(1, 41)],
    "nombre_sucursal": np.random.choice(sucursales, 40),
    "nombre_turno": np.random.choice(turnos, 40),
    "fecha_inicio_contrato": pd.date_range("2022-01-01", periods=40, freq="30D"),
    "fecha_fin_contrato": pd.date_range("2023-06-01", periods=40, freq="40D"),
    "nombre_estado": np.random.choice(estados, 40),
}

df = pd.DataFrame(empleados)
df["duracion_contrato"] = (df["fecha_fin_contrato"] - df["fecha_inicio_contrato"]).dt.days

# ==========================================
# SIDEBAR DE FILTROS
# ==========================================
st.sidebar.title("⚙️ Filtros de Empleados")

fil_sucursal = st.sidebar.multiselect("Sucursal", sucursales, sucursales)
fil_turno = st.sidebar.multiselect("Turno", turnos, turnos)
fil_estado = st.sidebar.multiselect("Estado Laboral", estados, estados)

df_filtered = df[
    (df["nombre_sucursal"].isin(fil_sucursal)) &
    (df["nombre_turno"].isin(fil_turno)) &
    (df["nombre_estado"].isin(fil_estado))
]

# ==========================================
# TÍTULO
# ==========================================
st.title("👔 Dashboard de Empleados – Tienda Deportiva")

# ==========================================
# KPIs
# ==========================================
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("👥 Total empleados", len(df_filtered))

with col2:
    st.metric("✔️ Activos", df_filtered[df_filtered["nombre_estado"] == "Activo"].shape[0])

with col3:
    st.metric("⏳ Duración promedio (días)", round(df_filtered["duracion_contrato"].mean(), 2))

with col4:
    st.metric("🏢 Sucursales con personal", df_filtered["nombre_sucursal"].nunique())

st.markdown("---")

# ==========================================
# GRÁFICO — EMPLEADOS POR SUCURSAL
# ==========================================
st.subheader("🏢 Distribución de Empleados por Sucursal")

suc_count = df_filtered["nombre_sucursal"].value_counts()

fig_suc = px.bar(
    suc_count,
    x=suc_count.index,
    y=suc_count.values,
    title="Empleados por Sucursal",
    color=suc_count.values,
    color_continuous_scale="Blues"
)
st.plotly_chart(fig_suc, use_container_width=True)

# ==========================================
# GRÁFICO — ESTADO LABORAL
# ==========================================
st.subheader("🧩 Estado Laboral del Personal")

estado_count = df_filtered["nombre_estado"].value_counts()

fig_estado = px.pie(
    names=estado_count.index,
    values=estado_count.values,
    title="Distribución de Estados Laborales",
    color_discrete_sequence=px.colors.sequential.Teal
)
st.plotly_chart(fig_estado, use_container_width=True)

# ==========================================
# GRÁFICO — DURACIÓN DEL CONTRATO
# ==========================================
st.subheader("⏱ Duración de Contratos por Empleado")

fig_duracion = px.line(
    df_filtered.sort_values("duracion_contrato"),
    x="empleado",
    y="duracion_contrato",
    markers=True,
    title="Duración de Contrato (días)"
)
st.plotly_chart(fig_duracion, use_container_width=True)

# ==========================================
# TABLA DETALLADA
# ==========================================
st.subheader("📋 Lista Detallada de Empleados")

busqueda = st.text_input("🔎 Buscar empleado")

df_show = df_filtered.copy()
if busqueda:
    df_show = df_show[df_show["empleado"].str.contains(busqueda, case=False)]

st.dataframe(df_show, use_container_width=True, height=350)

# ==========================================
# RESÚMENES
# ==========================================
st.markdown("---")
st.subheader("⭐ Resúmenes Generales")

col_a, col_b, col_c = st.columns(3)

with col_a:
    st.write("🏢 **Top Sucursales**")
    st.write(df_filtered["nombre_sucursal"].value_counts().head(3))

with col_b:
    st.write("🧩 **Estados más comunes**")
    st.write(df_filtered["nombre_estado"].value_counts().head(3))

with col_c:
    st.write("🕒 **Turnos más frecuentes**")
    st.write(df_filtered["nombre_turno"].value_counts().head(3))

# ==========================================
# FOOTER
# ==========================================
st.markdown("---")
st.markdown("""
<div style='text-align:center; padding:15px; color:#94a3b8;'>
    <h4 style='color:#10b981;'>👔 Dashboard de Empleados</h4>
    <p>Desarrollado con Streamlit y Plotly</p>
</div>
""", unsafe_allow_html=True)