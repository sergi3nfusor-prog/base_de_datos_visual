import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine, text
from datetime import datetime

# ============================================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================================
st.set_page_config(
    page_title="Dashboard de Clientes - Tienda Deportiva",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Cadena de conexión
DEFAULT_DB_URI = "mysql+pymysql://sql5809887:XSjyzGzKg8@sql5.freesqldatabase.com:3306/sql5809887"

# ============================================================
# FUNCIÓN DE CONEXIÓN
# ============================================================
def get_engine(db_uri):
    """Crea un engine SQLAlchemy."""
    try:
        engine = create_engine(db_uri)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return engine
    except Exception as e:
        st.error(f"❌ Error conectando a la base de datos:\n{e}")
        return None

# ============================================================
# CARGA DE DATOS
# ============================================================
@st.cache_data(ttl=600)
def load_client_data(db_uri):
    """Carga datos de clientes desde la base de datos."""
    engine = create_engine(db_uri)

    query = """
        SELECT 
            cl.id_cliente,
            CONCAT(cl.nombre, ' ', cl.apellido_paterno, ' ', cl.apellido_materno) AS nombre_completo,
            cl.nombre AS nombre_cliente,
            cl.apellido_paterno,
            cl.apellido_materno,
            cl.genero,
            cl.ci,
            
            -- Dirección del cliente
            dc.pais,
            dc.ciudad,
            dc.calle,
            dc.numero_de_provincia,
            
            -- Teléfono
            tc.numero_telefono,
            
            -- Información de registro
            cr.fecha_registro,
            
            -- Membresía
            hm.fecha_inicio AS membresia_inicio,
            hm.fecha_expiracion AS membresia_expiracion,
            em.estado AS estado_membresia,
            
            -- Programa de fidelización
            pf.puntos_acumulados,
            pf.nivel AS nivel_fidelizacion,
            pf.fecha_ultima_compra,
            pf.puntos_fidelizacion,
            
            -- Cliente frecuente
            cf.monto AS monto_cliente_frecuente,
            
            -- Ventas
            v.monto_total AS monto_venta,
            v.fecha_venta,
            v.descuento_aplicado,
            
            -- Producto comprado
            p.descripcion AS producto_descripcion,
            p.marca,
            p.precio AS precio_producto
            
        FROM cliente cl
        LEFT JOIN direccion_cliente dc ON dc.id_cliente = cl.id_cliente
        LEFT JOIN telefono_cliente tc ON tc.id_cliente = cl.id_cliente
        LEFT JOIN cliente_registrado cr ON cr.id_cliente = cl.id_cliente
        LEFT JOIN historial_membresia hm ON hm.id_cliente_registrado = cr.id_cliente_registrado
        LEFT JOIN estado_membresia em ON em.id_historial_membresia = hm.id_historial_membresia
        LEFT JOIN programa_fidelizacion pf ON pf.id_cliente = cl.id_cliente
        LEFT JOIN cliente_frecuente cf ON cf.id_cliente = cl.id_cliente
        LEFT JOIN venta v ON v.id_cliente = cl.id_cliente
        LEFT JOIN producto p ON p.id_venta = v.id_venta
    """

    df = pd.read_sql(query, engine)

    # Conversión de tipos
    df['fecha_registro'] = pd.to_datetime(df['fecha_registro'], errors='coerce')
    df['fecha_venta'] = pd.to_datetime(df['fecha_venta'], errors='coerce')
    df['fecha_ultima_compra'] = pd.to_datetime(df['fecha_ultima_compra'], errors='coerce')
    df['membresia_inicio'] = pd.to_datetime(df['membresia_inicio'], errors='coerce')
    df['membresia_expiracion'] = pd.to_datetime(df['membresia_expiracion'], errors='coerce')
    
    # Limpiar y convertir valores numéricos
    df['puntos_acumulados'] = pd.to_numeric(df['puntos_acumulados'], errors='coerce').fillna(0)
    df['puntos_fidelizacion'] = pd.to_numeric(df['puntos_fidelizacion'], errors='coerce').fillna(0)
    df['monto_venta'] = pd.to_numeric(df['monto_venta'], errors='coerce').fillna(0)
    df['monto_cliente_frecuente'] = pd.to_numeric(df['monto_cliente_frecuente'], errors='coerce').fillna(0)
    df['descuento_aplicado'] = pd.to_numeric(df['descuento_aplicado'], errors='coerce').fillna(0)
    
    # Limpieza básica
    df['ciudad'] = df['ciudad'].fillna('Sin ciudad')
    df['pais'] = df['pais'].fillna('Sin país')
    df['genero'] = df['genero'].fillna('No especificado')
    df['estado_membresia'] = df['estado_membresia'].fillna('Sin membresía')
    df['nivel_fidelizacion'] = df['nivel_fidelizacion'].fillna('Sin nivel')
    
    # Crear columnas derivadas
    df['anio_registro'] = df['fecha_registro'].dt.year
    df['mes_registro'] = df['fecha_registro'].dt.month
    
    return df

# ============================================================
# FUNCIONES DE FILTRADO
# ============================================================
def filtrar_datos(df, ciudades, generos, niveles, estados_membresia, fecha_inicio, fecha_fin):
    """Filtra el DataFrame según los criterios seleccionados."""
    df_filtered = df.copy()
    
    if ciudades:
        df_filtered = df_filtered[df_filtered['ciudad'].isin(ciudades)]
    if generos:
        df_filtered = df_filtered[df_filtered['genero'].isin(generos)]
    if niveles:
        df_filtered = df_filtered[df_filtered['nivel_fidelizacion'].isin(niveles)]
    if estados_membresia:
        df_filtered = df_filtered[df_filtered['estado_membresia'].isin(estados_membresia)]
    
    if fecha_inicio and fecha_fin:
        df_filtered = df_filtered[
            (df_filtered['fecha_registro'] >= pd.to_datetime(fecha_inicio)) &
            (df_filtered['fecha_registro'] <= pd.to_datetime(fecha_fin))
        ]
    
    return df_filtered

# ============================================================
# INTERFAZ PRINCIPAL
# ============================================================
st.title("📊 Dashboard de Clientes - Tienda Deportiva")
st.markdown("---")

st.markdown("**Creador de la página ventas:** MAMANI  KARLA")

# Verificar conexión
engine = get_engine(DEFAULT_DB_URI)
if engine is None:
    st.stop()

# Cargar datos
with st.spinner("Cargando datos de clientes..."):
    df = load_client_data(DEFAULT_DB_URI)

if df.empty:
    st.warning("No se pudo cargar la información de clientes.")
    st.stop()

# ============================================================
# SIDEBAR - FILTROS
# ============================================================
st.sidebar.header("🔍 FILTROS")

# Filtro por ciudad
ciudades_disponibles = sorted(df['ciudad'].unique().tolist())
ciudades_seleccionadas = st.sidebar.multiselect(
    "Ciudades",
    ciudades_disponibles,
    default=None
)

# Filtro por género
generos_disponibles = sorted(df['genero'].unique().tolist())
generos_seleccionados = st.sidebar.multiselect(
    "Género",
    generos_disponibles,
    default=None
)

# Filtro por nivel de fidelización
niveles_disponibles = sorted(df['nivel_fidelizacion'].unique().tolist())
niveles_seleccionados = st.sidebar.multiselect(
    "Nivel de Fidelización",
    niveles_disponibles,
    default=None
)

# Filtro por estado de membresía
estados_disponibles = sorted(df['estado_membresia'].unique().tolist())
estados_seleccionados = st.sidebar.multiselect(
    "Estado de Membresía",
    estados_disponibles,
    default=None
)

# Filtro por fecha de registro
st.sidebar.subheader("Fecha de Registro")
fecha_min = df['fecha_registro'].min()
fecha_max = df['fecha_registro'].max()

if pd.notna(fecha_min) and pd.notna(fecha_max):
    fecha_inicio = st.sidebar.date_input(
        "Desde",
        value=fecha_min.date(),
        min_value=fecha_min.date(),
        max_value=fecha_max.date()
    )
    fecha_fin = st.sidebar.date_input(
        "Hasta",
        value=fecha_max.date(),
        min_value=fecha_min.date(),
        max_value=fecha_max.date()
    )
else:
    fecha_inicio = None
    fecha_fin = None

# Aplicar filtros
df_filtrado = filtrar_datos(
    df,
    ciudades_seleccionadas,
    generos_seleccionados,
    niveles_seleccionados,
    estados_seleccionados,
    fecha_inicio,
    fecha_fin
)

if df_filtrado.empty:
    st.warning("⚠️ No se encontraron resultados con los filtros aplicados.")
    st.stop()

# ============================================================
# INDICADORES CLAVE (KPIs)
# ============================================================
st.subheader("📈 INDICADORES CLAVE")

col1, col2, col3, col4 = st.columns(4)

# Total de clientes
total_clientes = df_filtrado['id_cliente'].nunique()
col1.metric("Total Clientes", f"{total_clientes:,}")

# Clientes activos (con membresía activa)
clientes_activos = df_filtrado[df_filtrado['estado_membresia'] == 'Activa']['id_cliente'].nunique()
col2.metric("Membresías Activas", f"{clientes_activos:,}")

# Promedio de puntos de fidelización
promedio_puntos = df_filtrado.groupby('id_cliente')['puntos_acumulados'].first().mean()
col3.metric("Promedio Puntos", f"{promedio_puntos:,.0f}")

# Total ventas
total_ventas = df_filtrado['monto_venta'].sum()
col4.metric("Total Ventas", f"${total_ventas:,.2f}")

st.divider()

# ============================================================
# CONTROLES DE VISUALIZACIÓN
# ============================================================
st.subheader("🎨 Visualizaciones")

# Checkboxes para mostrar/ocultar gráficos
col_check1, col_check2, col_check3, col_check4 = st.columns(4)

show_graph1 = col_check1.checkbox("📊 Distribución por Ciudad", value=True)
show_graph2 = col_check2.checkbox("🎯 Niveles de Fidelización", value=True)
show_graph3 = col_check3.checkbox("👥 Clientes por Género", value=True)
show_graph4 = col_check4.checkbox("📅 Registro Mensual", value=True)

# ============================================================
# GRÁFICOS
# ============================================================
graph_col1, graph_col2 = st.columns(2)

# GRÁFICO 1: Distribución por Ciudad
if show_graph1:
    with graph_col1:
        st.markdown("### 📊 Distribución de Clientes por Ciudad")
        clientes_ciudad = df_filtrado.groupby('ciudad')['id_cliente'].nunique().reset_index()
        clientes_ciudad.columns = ['Ciudad', 'Cantidad']
        clientes_ciudad = clientes_ciudad.sort_values('Cantidad', ascending=False).head(10)
        
        fig1 = px.bar(
            clientes_ciudad,
            x='Cantidad',
            y='Ciudad',
            orientation='h',
            title='Top 10 Ciudades con Más Clientes',
            color='Cantidad',
            color_continuous_scale='Blues'
        )
        fig1.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig1, use_container_width=True)

# GRÁFICO 2: Niveles de Fidelización
if show_graph2:
    with graph_col2:
        st.markdown("### 🎯 Distribución por Nivel de Fidelización")
        niveles_fid = df_filtrado.groupby('nivel_fidelizacion')['id_cliente'].nunique().reset_index()
        niveles_fid.columns = ['Nivel', 'Cantidad']
        
        fig2 = px.pie(
            niveles_fid,
            values='Cantidad',
            names='Nivel',
            title='Clientes por Nivel de Fidelización',
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig2.update_traces(textposition='inside', textinfo='percent+label')
        fig2.update_layout(height=400)
        st.plotly_chart(fig2, use_container_width=True)

graph_col3, graph_col4 = st.columns(2)

# GRÁFICO 3: Distribución por Género
if show_graph3:
    with graph_col3:
        st.markdown("### 👥 Distribución de Clientes por Género")
        genero_dist = df_filtrado.groupby('genero')['id_cliente'].nunique().reset_index()
        genero_dist.columns = ['Género', 'Cantidad']
        
        fig3 = px.bar(
            genero_dist,
            x='Género',
            y='Cantidad',
            title='Clientes por Género',
            color='Género',
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig3.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig3, use_container_width=True)

# GRÁFICO 4: Registros por Mes
if show_graph4:
    with graph_col4:
        st.markdown("### 📅 Registros de Clientes por Mes")
        
        # Crear datos mensuales
        df_registros = df_filtrado[df_filtrado['fecha_registro'].notna()].copy()
        df_registros['mes_anio'] = df_registros['fecha_registro'].dt.to_period('M').astype(str)
        registros_mes = df_registros.groupby('mes_anio')['id_cliente'].nunique().reset_index()
        registros_mes.columns = ['Mes', 'Registros']
        registros_mes = registros_mes.sort_values('Mes')
        
        fig4 = px.line(
            registros_mes,
            x='Mes',
            y='Registros',
            title='Evolución de Registros Mensuales',
            markers=True
        )
        fig4.update_traces(line_color='#FF6B6B', line_width=3)
        fig4.update_layout(height=400)
        st.plotly_chart(fig4, use_container_width=True)

st.divider()

# ============================================================
# TABLAS
# ============================================================
st.subheader("📋 Tablas de Datos")

# Checkboxes para mostrar/ocultar tablas
col_table1, col_table2, col_table3, col_table4 = st.columns(4)

show_table1 = col_table1.checkbox("📝 Top Clientes", value=True)
show_table2 = col_table2.checkbox("💰 Mejores Compradores", value=True)
show_table3 = col_table3.checkbox("🏆 Puntos de Fidelización", value=True)
show_table4 = col_table4.checkbox("📊 Resumen por Ciudad", value=True)

# TABLA 1: Top Clientes con más compras
if show_table1:
    with st.expander("📝 TOP CLIENTES CON MÁS COMPRAS", expanded=True):
        top_clientes = df_filtrado.groupby(['id_cliente', 'nombre_completo', 'ciudad']).agg({
            'monto_venta': 'count',
            'puntos_acumulados': 'first'
        }).reset_index()
        top_clientes.columns = ['ID', 'Nombre', 'Ciudad', 'Num. Compras', 'Puntos']
        top_clientes = top_clientes.sort_values('Num. Compras', ascending=False).head(10)
        
        st.dataframe(
            top_clientes.style.format({
                'Puntos': '{:,.0f}',
                'Num. Compras': '{:,.0f}'
            }),
            use_container_width=True,
            hide_index=True
        )

# TABLA 2: Mejores compradores por monto
if show_table2:
    with st.expander("💰 MEJORES COMPRADORES POR MONTO", expanded=True):
        mejores_compradores = df_filtrado.groupby(['id_cliente', 'nombre_completo', 'nivel_fidelizacion']).agg({
            'monto_venta': 'sum',
            'descuento_aplicado': 'sum'
        }).reset_index()
        mejores_compradores.columns = ['ID', 'Nombre', 'Nivel', 'Total Compras', 'Descuentos']
        mejores_compradores = mejores_compradores.sort_values('Total Compras', ascending=False).head(10)
        
        st.dataframe(
            mejores_compradores.style.format({
                'Total Compras': '${:,.2f}',
                'Descuentos': '${:,.2f}'
            }),
            use_container_width=True,
            hide_index=True
        )

# TABLA 3: Ranking de puntos de fidelización
if show_table3:
    with st.expander("🏆 RANKING DE PUNTOS DE FIDELIZACIÓN", expanded=True):
        ranking_puntos = df_filtrado.groupby(['id_cliente', 'nombre_completo', 'nivel_fidelizacion']).agg({
            'puntos_acumulados': 'first',
            'puntos_fidelizacion': 'first',
            'fecha_ultima_compra': 'first'
        }).reset_index()
        ranking_puntos.columns = ['ID', 'Nombre', 'Nivel', 'Puntos Acum.', 'Puntos Fid.', 'Última Compra']
        ranking_puntos = ranking_puntos.sort_values('Puntos Acum.', ascending=False).head(15)
        
        st.dataframe(
            ranking_puntos.style.format({
                'Puntos Acum.': '{:,.0f}',
                'Puntos Fid.': '{:,.0f}',
                'Última Compra': lambda x: x.strftime('%Y-%m-%d') if pd.notna(x) else 'N/A'
            }),
            use_container_width=True,
            hide_index=True
        )

# TABLA 4: Resumen por ciudad
if show_table4:
    with st.expander("📊 RESUMEN POR CIUDAD", expanded=True):
        resumen_ciudad = df_filtrado.groupby('ciudad').agg({
            'id_cliente': 'nunique',
            'monto_venta': 'sum',
            'puntos_acumulados': 'mean'
        }).reset_index()
        resumen_ciudad.columns = ['Ciudad', 'Total Clientes', 'Ventas Totales', 'Puntos Promedio']
        resumen_ciudad = resumen_ciudad.sort_values('Total Clientes', ascending=False).head(15)
        
        st.dataframe(
            resumen_ciudad.style.format({
                'Total Clientes': '{:,.0f}',
                'Ventas Totales': '${:,.2f}',
                'Puntos Promedio': '{:,.0f}'
            }),
            use_container_width=True,
            hide_index=True
        )

# ============================================================
# DATOS COMPLETOS
# ============================================================
with st.expander("📊 VER TODOS LOS DATOS FILTRADOS"):
    # Seleccionar columnas relevantes
    columnas_mostrar = [
        'id_cliente', 'nombre_completo', 'genero', 'ciudad', 'pais',
        'fecha_registro', 'nivel_fidelizacion', 'puntos_acumulados',
        'estado_membresia', 'monto_venta'
    ]
    
    df_mostrar = df_filtrado[columnas_mostrar].drop_duplicates(subset=['id_cliente'])
    
    st.dataframe(df_mostrar, use_container_width=True)
    
    # Botón de descarga
    csv = df_mostrar.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Descargar datos en CSV",
        data=csv,
        file_name=f"clientes_tienda_deportiva_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

st.divider()
st.caption("🏃‍♂️ TIENDA DEPORTIVA - Dashboard de Clientes | UNIVALLE - BASES DE DATOS I 2025/II")