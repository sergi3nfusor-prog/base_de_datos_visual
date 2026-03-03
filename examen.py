import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, text

# ==============================================
# CONFIGURACIÓN DE LA PÁGINA
# ==============================================
st.set_page_config(
    page_title="Dashboard EcoRuta Mejorado",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================
# DATOS DE CONEXIÓN
# ==============================================
DB_USER = "sql3810834"
DB_PASSWORD = "AP4qVtc2sc"
DB_HOST = "sql3.freesqldatabase.com"
DB_NAME = "sql3810834"
DB_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

# ==============================================
# FUNCIÓN PARA CREAR ENGINE
# ==============================================
def get_engine(db_uri):
    try:
        engine = create_engine(db_uri)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        st.success("✅ Conectado a la base de datos correctamente")
        return engine
    except Exception as e:
        st.error(f"❌ Error conectando a la base de datos:\n{e}")
        return None

engine = get_engine(DB_URI)

# ==============================================
# FUNCIÓN PARA CARGAR DATOS
# ==============================================
@st.cache_data(ttl=600)
def load_data(db_uri):
    engine = create_engine(db_uri)
    query = """
        SELECT 
            v.id_visita,
            v.fecha_visita,
            v.cantidad_kg,
            v.estado AS estado_visita,
            r.nombre_ruta,
            r.tipo_material,
            r.frecuencia,
            b.nombre_barrio,
            b.distrito,
            rc.nombre_completo AS recolector
        FROM visitas v
        LEFT JOIN rutas r ON v.id_ruta = r.id_ruta
        LEFT JOIN barrios b ON r.id_barrio = b.id_barrio
        LEFT JOIN recolectores rc ON v.id_recolector = rc.id_recolector
        WHERE v.fecha_visita IS NOT NULL;
    """
    df = pd.read_sql(query, engine)
    df["fecha_visita"] = pd.to_datetime(df["fecha_visita"])
    df["cantidad_kg"] = df["cantidad_kg"].astype(float)
    return df

# ==============================================
# CARGAR DATOS Y MOSTRAR
# ==============================================
if engine:
    df = load_data(DB_URI)
    
    if df.empty:
        st.warning("No se encontraron registros en visitas")
    else:
        st.title("📊 Dashboard EcoRuta Mejorado")

        # ==============================================
        # FILTROS EN SIDEBAR
        # ==============================================
        st.sidebar.header("Filtros")

        barrios_disp = sorted(df["nombre_barrio"].unique())
        barrios_sel = st.sidebar.multiselect("Selecciona Barrio(s)", barrios_disp, default=barrios_disp)

        recolectores_disp = sorted(df["recolector"].dropna().unique())
        recolectores_sel = st.sidebar.multiselect("Selecciona Recolector(es)", recolectores_disp, default=recolectores_disp)

        estados_disp = sorted(df["estado_visita"].unique())
        estados_sel = st.sidebar.multiselect("Selecciona Estado de Visita", estados_disp, default=estados_disp)

        fecha_min = df["fecha_visita"].min()
        fecha_max = df["fecha_visita"].max()
        fecha_sel = st.sidebar.date_input("Rango de Fechas", [fecha_min, fecha_max], min_value=fecha_min, max_value=fecha_max)
        fecha_inicio, fecha_fin = fecha_sel

        # ==============================================
        # APLICAR FILTROS
        # ==============================================
        df_filtrado = df[
            (df["nombre_barrio"].isin(barrios_sel)) &
            (df["recolector"].isin(recolectores_sel)) &
            (df["estado_visita"].isin(estados_sel)) &
            (df["fecha_visita"] >= pd.to_datetime(fecha_inicio)) &
            (df["fecha_visita"] <= pd.to_datetime(fecha_fin))
        ]

        # ==============================================
        # KPIs
        # ==============================================
        st.subheader("📌 Indicadores")
        c1, c2, c3 = st.columns(3)
        c1.metric("Total kg recolectados", f"{df_filtrado['cantidad_kg'].sum():,.2f} kg")
        ruta_top = df_filtrado.groupby("nombre_ruta")["id_visita"].count().idxmax()
        c2.metric("Ruta más visitada", ruta_top)
        recolector_top = df_filtrado.groupby("recolector")["id_visita"].count().idxmax()
        c3.metric("Recolector más activo", recolector_top)

        # ==============================================
        # GRÁFICOS
        # ==============================================
        # Kg por barrio (colores según estado)
        df_barrio = df_filtrado.groupby(["nombre_barrio", "estado_visita"])["cantidad_kg"].sum().reset_index()
        fig1 = px.bar(
            df_barrio,
            x="nombre_barrio",
            y="cantidad_kg",
            color="estado_visita",
            title="Kg recolectados por Barrio",
            text_auto=True
        )
        st.plotly_chart(fig1, use_container_width=True)

        #  Kg por recolector (colores según estado)
        df_recolector = df_filtrado.groupby(["recolector", "estado_visita"])["cantidad_kg"].sum().reset_index()
        fig2 = px.bar(
            df_recolector,
            x="recolector",
            y="cantidad_kg",
            color="estado_visita",
            title="Kg recolectados por Recolector",
            text_auto=True
        )
        st.plotly_chart(fig2, use_container_width=True)

        #  Kg recolectados por fecha (colores según estado)
        df_fecha = df_filtrado.groupby(["fecha_visita", "estado_visita"])["cantidad_kg"].sum().reset_index()
        fig3 = px.line(
            df_fecha,
            x="fecha_visita",
            y="cantidad_kg",
            color="estado_visita",
            title="Kg recolectados por Fecha",
            markers=True
        )
        st.plotly_chart(fig3, use_container_width=True)

        # Kg recolectados por tipo de material
        df_material = df_filtrado.groupby(["tipo_material", "estado_visita"])["cantidad_kg"].sum().reset_index()
        fig4 = px.bar(
            df_material,
            x="tipo_material",
            y="cantidad_kg",
            color="estado_visita",
            title="Kg recolectados por Tipo de Material",
            text_auto=True
        )
        st.plotly_chart(fig4, use_container_width=True)

else:
    st.warning("No se pudo cargar la información porque no hay conexión a la base de datos.")
