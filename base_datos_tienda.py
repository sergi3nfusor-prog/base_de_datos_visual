import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from sqlalchemy import create_engine, text

# ============================================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================================
#hola
st.set_page_config(
    page_title="Dashboard Tienda Deportiva",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Cadena de conexión por defecto
DEFAULT_DB_URI = "mysql+pymysql://sql5809887:XSjyzGzKg8@sql5.freesqldatabase.com:3306/sql5809887"

# ============================================================
# FUNCIÓN DE CONEXIÓN
# ============================================================
def get_engine(db_uri):
    """Crea un engine SQLAlchemy sin cachearlo."""
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
def load_data(db_uri):
    """Carga datos desde la base de datos y los procesa."""
    engine = create_engine(db_uri)

    query = """
        SELECT 
            v.id_venta,
            v.fecha_venta,
            v.monto_total,
            v.impuesto,
            v.descuento_aplicado,
            v.precio_momento,
            (v.monto_total - v.descuento_aplicado) AS monto_neto,

            -- Producto
            p.id_producto,
            p.nombre_producto,
            p.marca,
            p.precio,
            p.material,
            p.talla,
            p.temporada,
            p.estado AS estado_producto,

            -- Categoría
            cat.nombre_categoria,
            cat.descripcion AS descripcion_categoria,

            -- Cliente
            c.id_cliente,
            CONCAT(c.nombre, ' ', c.apellido_paterno, ' ', c.apellido_materno) AS nombre_cliente,
            c.genero,
            c.ci,

            -- Dirección del cliente
            dc.ciudad AS ciudad_cliente,
            dc.pais AS pais_cliente,

            -- Empleado
            e.id_empleado,
            CONCAT(e.nombre, ' ', e.apellido_paterno, ' ', e.apellido_materno) AS nombre_empleado,

            -- Sucursal
            s.nombre_sucursal,
            s.ciudad AS ciudad_sucursal,
            s.pais AS pais_sucursal,

            -- Factura
            f.numero_factura,
            f.nit,
            f.razon_social,

            -- Tipo de pago
            CASE 
                WHEN qr.id_qr IS NOT NULL THEN 'QR'
                WHEN t.id_tarjeta IS NOT NULL THEN 'TARJETA'
                WHEN ef.id_efectivo IS NOT NULL THEN 'EFECTIVO'
                ELSE 'SIN_REGISTRO'
            END AS tipo_pago,

            -- Promoción
            prom.tipo AS tipo_promocion,
            prom.valor AS valor_promocion,
            prom.nombre_promocion,

            -- Proveedor
            prov.nombre_proveedor,
            prov.tipo_proveedor

        FROM venta v
        LEFT JOIN producto p ON p.id_venta = v.id_venta
        LEFT JOIN categoria cat ON cat.id_producto = p.id_producto
        LEFT JOIN cliente c ON c.id_cliente = v.id_cliente
        LEFT JOIN direccion_cliente dc ON dc.id_cliente = c.id_cliente
        LEFT JOIN empleado e ON e.id_empleado = v.id_empleado
        LEFT JOIN empleado_sucursal es ON es.id_empleado = e.id_empleado
        LEFT JOIN sucursal s ON s.id_sucursal = es.id_sucursal
        LEFT JOIN factura f ON f.id_factura = v.id_factura
        LEFT JOIN pago pg ON pg.id_pago = v.id_pago
        LEFT JOIN qr ON qr.id_pago = pg.id_pago
        LEFT JOIN tarjeta t ON t.id_pago = pg.id_pago
        LEFT JOIN efectivo ef ON ef.id_pago = pg.id_pago
        LEFT JOIN promocion prom ON prom.id_venta = v.id_venta
        LEFT JOIN proveedor prov ON prov.id_proveedor = p.id_proveedor
        WHERE v.fecha_venta IS NOT NULL;
    """

    df = pd.read_sql(query, engine)

    # Conversión de tipos
    df['fecha_venta'] = pd.to_datetime(df['fecha_venta'])
    df['descuento_aplicado'] = df['descuento_aplicado'].fillna(0).astype(float)
    df['monto_total'] = df['monto_total'].astype(float)
    df['monto_neto'] = df['monto_total'] - df['descuento_aplicado']

    # Columnas derivadas de fecha
    df['anio'] = df['fecha_venta'].dt.year
    df['mes'] = df['fecha_venta'].dt.month
    df['dia'] = df['fecha_venta'].dt.day
    df['mes_anio'] = df['fecha_venta'].dt.to_period('M').astype(str)
    df['trimestre'] = df['fecha_venta'].dt.quarter
    df['dia_semana'] = df['fecha_venta'].dt.day_name()

    # Limpieza básica de texto / nulos
    df['ciudad_cliente'] = df['ciudad_cliente'].fillna('Sin ciudad')
    df['ciudad_sucursal'] = df['ciudad_sucursal'].fillna('Sin sucursal')
    df['tipo_pago'] = df['tipo_pago'].fillna('SIN_REGISTRO')
    df['marca'] = df['marca'].fillna('Sin marca')
    df['nombre_categoria'] = df['nombre_categoria'].fillna('Sin categoría')

    return df

# ============================================================
# FUNCIONES DE FILTRADO
# ============================================================
def filtrar(df, fechas, productos, ciudades, marcas, categorias, tipo_pago):
    """Filtra el DataFrame según los criterios seleccionados."""
    if isinstance(fechas, (list, tuple)):
        if len(fechas) == 2:
            fi, ff = fechas
        elif len(fechas) == 1:
            fi = ff = fechas[0]
        else:
            fi = ff = df['fecha_venta'].min().date()
    else:
        fi = ff = fechas
    
    df = df[df['fecha_venta'].dt.date.between(fi, ff)]

    if productos:
        df = df[df['nombre_producto'].isin(productos)]
    if ciudades:
        df = df[df['ciudad_cliente'].isin(ciudades)]
    if marcas:
        df = df[df['marca'].isin(marcas)]
    if categorias:
        df = df[df['nombre_categoria'].isin(categorias)]
    if tipo_pago:
        df = df[df['tipo_pago'].isin(tipo_pago)]
    
    return df

# ============================================================
# INTERFAZ PRINCIPAL
# ============================================================

st.title("⚽ Dashboard Tienda Deportiva")

# ============================================================
# Sidebar – Configuración de conexión
# ============================================================

db_uri = DEFAULT_DB_URI
engine = get_engine(db_uri)

if engine is None:
    st.stop()

# ============================================================
# Cargar datos
# ============================================================
df = load_data(db_uri)

if df.empty:
    st.warning("⚠️ No se pudo cargar la información de ventas.")
    st.stop()

# ============================================================
# FILTROS EN SIDEBAR
# ============================================================
st.sidebar.header("🔍 Filtros")

fecha_min = df['fecha_venta'].min().date()
fecha_max = df['fecha_venta'].max().date()

fechas = st.sidebar.date_input(
    "📅 Rango de fechas", 
    [fecha_min, fecha_max], 
    min_value=fecha_min, 
    max_value=fecha_max
)

productos = st.sidebar.multiselect(
    "🏃 Productos", 
    df['nombre_producto'].dropna().unique().tolist()
)

ciudades = st.sidebar.multiselect(
    "🌆 Ciudades (Cliente)", 
    df['ciudad_cliente'].unique().tolist()
)

marcas = st.sidebar.multiselect(
    "🏷️ Marcas", 
    df['marca'].unique().tolist()
)

categorias = st.sidebar.multiselect(
    "📂 Categorías", 
    df['nombre_categoria'].unique().tolist()
)

tipo_pago = st.sidebar.multiselect(
    "💳 Tipo de Pago", 
    df['tipo_pago'].unique().tolist()
)

# Aplicar filtros
df_filtrado = filtrar(df, fechas, productos, ciudades, marcas, categorias, tipo_pago)

if df_filtrado.empty:
    st.warning("⚠️ No se encontraron resultados con los filtros aplicados.")
    st.stop()

# ============================================================
# INDICADORES PRINCIPALES (KPIs)
# ============================================================
st.subheader("📊 Indicadores Clave")

k1, k2, k3, k4 = st.columns(4)

total_ventas = df_filtrado['monto_neto'].sum()
num_ventas = len(df_filtrado)
venta_promedio = df_filtrado['monto_neto'].mean()

if not df_filtrado.empty:
    prod_top = (
        df_filtrado
        .groupby('nombre_producto')['monto_neto']
        .sum()
        .sort_values(ascending=False)
        .index[0]
    )
else:
    prod_top = "N/A"

k1.metric("💰 Total Ventas", f"${total_ventas:,.2f}")
k2.metric("🛒 Número de Ventas", f"{num_ventas:,}")
k3.metric("📈 Venta Promedio", f"${venta_promedio:,.2f}")
k4.metric("🏆 Producto Top", prod_top)

st.divider()

# ============================================================
# TABLA DE DATOS FILTRADOS
# ============================================================
with st.expander("📋 Ver Datos Filtrados"):
    st.dataframe(df_filtrado, use_container_width=True)
    
    csv = df_filtrado.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Descargar CSV",
        data=csv,
        file_name="ventas_tienda_deportiva.csv",
        mime="text/csv"
    )

st.divider()

# ============================================================
# VISUALIZACIONES POR TABS
# ============================================================
st.subheader("📊 Visualizaciones")

tab_tiempo, tab_productos, tab_clientes, tab_geograf, tab_pago = st.tabs([
    "⏰ Tiempo",
    "🏃 Productos",
    "👥 Clientes",
    "🗺️ Geografía",
    "💳 Métodos de Pago"
])

# ============================================================
# TAB: TIEMPO
# ============================================================
with tab_tiempo:
    st.subheader("📅 Análisis Temporal")
    
    col_t1, col_t2 = st.columns(2)
    
    with col_t1:
        st.markdown("### 📈 Evolución de Ventas")
        df_ts = (
            df_filtrado
            .groupby('fecha_venta', as_index=False)['monto_neto']
            .sum()
            .sort_values('fecha_venta')
        )
        
        fig = px.line(
            df_ts, 
            x='fecha_venta', 
            y='monto_neto',
            title='Ventas Diarias',
            labels={'monto_neto': 'Monto Neto', 'fecha_venta': 'Fecha'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col_t2:
        st.markdown("### 📊 Ventas por Mes")
        df_mes = (
            df_filtrado
            .groupby('mes_anio', as_index=False)['monto_neto']
            .sum()
            .sort_values('mes_anio')
        )
        
        fig = px.bar(
            df_mes,
            x='mes_anio',
            y='monto_neto',
            title='Ventas Mensuales',
            labels={'monto_neto': 'Monto Neto', 'mes_anio': 'Mes-Año'}
        )
        st.plotly_chart(fig, use_container_width=True)

# ============================================================
# TAB: PRODUCTOS
# ============================================================
with tab_productos:
    st.subheader("🏃 Análisis de Productos")
    
    col_p1, col_p2 = st.columns(2)
    
    with col_p1:
        st.markdown("### 🏆 Top 10 Productos")
        df_prod = (
            df_filtrado
            .groupby('nombre_producto', as_index=False)['monto_neto']
            .sum()
            .sort_values('monto_neto', ascending=False)
            .head(10)
        )
        
        fig = px.bar(
            df_prod,
            x='monto_neto',
            y='nombre_producto',
            orientation='h',
            title='Top 10 Productos por Ventas',
            labels={'monto_neto': 'Ventas Netas', 'nombre_producto': 'Producto'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col_p2:
        st.markdown("### 🏷️ Ventas por Marca")
        df_marca = (
            df_filtrado
            .groupby('marca', as_index=False)['monto_neto']
            .sum()
            .sort_values('monto_neto', ascending=False)
        )
        
        fig = px.pie(
            df_marca,
            values='monto_neto',
            names='marca',
            title='Distribución por Marca'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Categorías
    st.markdown("### 📂 Ventas por Categoría")
    df_cat = (
        df_filtrado
        .groupby('nombre_categoria', as_index=False)['monto_neto']
        .sum()
        .sort_values('monto_neto', ascending=False)
    )
    
    fig = px.bar(
        df_cat,
        x='nombre_categoria',
        y='monto_neto',
        title='Ventas por Categoría',
        labels={'monto_neto': 'Ventas Netas', 'nombre_categoria': 'Categoría'}
    )
    st.plotly_chart(fig, use_container_width=True)

# ============================================================
# TAB: CLIENTES
# ============================================================
with tab_clientes:
    st.subheader("👥 Análisis de Clientes")
    
    col_c1, col_c2 = st.columns(2)
    
    with col_c1:
        st.markdown("### 🌟 Top 10 Clientes")
        df_clientes = (
            df_filtrado
            .groupby('nombre_cliente', as_index=False)['monto_neto']
            .sum()
            .sort_values('monto_neto', ascending=False)
            .head(10)
        )
        
        fig = px.bar(
            df_clientes,
            x='monto_neto',
            y='nombre_cliente',
            orientation='h',
            title='Top 10 Clientes por Compras',
            labels={'monto_neto': 'Total Comprado', 'nombre_cliente': 'Cliente'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col_c2:
        st.markdown("### 👤 Ventas por Género")
        df_genero = (
            df_filtrado
            .groupby('genero', as_index=False)['monto_neto']
            .sum()
        )
        
        fig = px.pie(
            df_genero,
            values='monto_neto',
            names='genero',
            title='Distribución por Género'
        )
        st.plotly_chart(fig, use_container_width=True)

# ============================================================
# TAB: GEOGRAFÍA
# ============================================================
with tab_geograf:
    st.subheader("🗺️ Análisis Geográfico")
    
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        st.markdown("### 🌆 Ventas por Ciudad (Cliente)")
        df_city = (
            df_filtrado
            .groupby('ciudad_cliente', as_index=False)['monto_neto']
            .sum()
            .sort_values('monto_neto', ascending=False)
            .head(10)
        )
        
        fig = px.bar(
            df_city,
            x='ciudad_cliente',
            y='monto_neto',
            title='Top 10 Ciudades por Ventas',
            labels={'monto_neto': 'Ventas Netas', 'ciudad_cliente': 'Ciudad'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col_g2:
        st.markdown("### 🏬 Ventas por Sucursal")
        df_sucursal = (
            df_filtrado
            .groupby('nombre_sucursal', as_index=False)['monto_neto']
            .sum()
            .sort_values('monto_neto', ascending=False)
        )
        
        fig = px.bar(
            df_sucursal,
            x='nombre_sucursal',
            y='monto_neto',
            title='Ventas por Sucursal',
            labels={'monto_neto': 'Ventas Netas', 'nombre_sucursal': 'Sucursal'}
        )
        st.plotly_chart(fig, use_container_width=True)

# ============================================================
# TAB: MÉTODOS DE PAGO
# ============================================================
with tab_pago:
    st.subheader("💳 Análisis de Métodos de Pago")
    
    col_mp1, col_mp2 = st.columns(2)
    
    with col_mp1:
        st.markdown("### 💰 Distribución por Tipo de Pago")
        df_pago = (
            df_filtrado
            .groupby('tipo_pago', as_index=False)['monto_neto']
            .sum()
            .sort_values('monto_neto', ascending=False)
        )
        
        fig = px.pie(
            df_pago,
            values='monto_neto',
            names='tipo_pago',
            title='Ventas por Tipo de Pago'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col_mp2:
        st.markdown("### 📊 Evolución Mensual por Tipo de Pago")
        df_pago_mes = (
            df_filtrado
            .groupby(['mes_anio', 'tipo_pago'], as_index=False)['monto_neto']
            .sum()
            .sort_values('mes_anio')
        )
        
        fig = px.bar(
            df_pago_mes,
            x='mes_anio',
            y='monto_neto',
            color='tipo_pago',
            barmode='group',
            title='Ventas Mensuales por Tipo de Pago',
            labels={'monto_neto': 'Ventas Netas', 'mes_anio': 'Mes-Año'}
        )
        st.plotly_chart(fig, use_container_width=True)

# ============================================================
# PIE DE PÁGINA
# ============================================================
st.divider()
st.caption("🏫 UNIVALLE - BASES DE DATOS I 2025 | Dashboard Tienda Deportiva")