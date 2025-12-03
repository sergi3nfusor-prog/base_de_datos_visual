# app.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta

# ------------------------
# CONFIG GENERAL (1 sola vez)
# ------------------------
st.set_page_config(page_title="Dashboard General - Tienda Deportiva", layout="wide")
st.markdown("""<style> .reportview-container .main { padding: 1rem 1rem 3rem 1rem; } </style>""", unsafe_allow_html=True)

# ------------------------
# CONSTANTES / CONEXIÓN
# ------------------------
DB_URL = "mysql+pymysql://sql5809887:XSjyzGzKg8@sql5.freesqldatabase.com:3306/sql5809887"

def get_engine(db_uri=DB_URL):
    try:
        engine = create_engine(db_uri)
        # quick test
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return engine
    except Exception as e:
        st.sidebar.error("⚠️ No se pudo conectar a la base de datos. Muchas funciones que requieren BD estarán deshabilitadas.")
        st.sidebar.caption(f"Detalles: {str(e)[:200]}")
        return None

engine = get_engine()

# ------------------------
# FUNCIONES ÚTILES
# ------------------------
@st.cache_data
def read_sql(query: str):
    if engine is None:
        return pd.DataFrame()
    return pd.read_sql(query, engine)

# ------------------------
# PÁGINAS (cada función renderiza una página)
# ------------------------

# ---------- Página 1: Ventas ----------
def render_ventas():
    st.title("📊 Dashboard de Ventas - Tienda Deportiva")

    if engine is None:
        st.warning("La conexión a DB no está disponible. Esta página necesita acceso a la base de datos.")
        return

    @st.cache_data
    def load_sales():
        consulta = """
            SELECT 
                v.id_venta,
                v.fecha_venta,
                v.monto_total,
                v.descuento_aplicado,
                (v.monto_total - v.descuento_aplicado) AS monto_neto,
                df.descripcion_producto AS nombre_producto,
                df.cantidad,
                df.monto_total AS subtotal,
                NULL AS marca,
                NULL AS material,
                CASE
                    WHEN qr.id_qr IS NOT NULL THEN 'QR'
                    WHEN ef.id_efectivo IS NOT NULL THEN 'Efectivo'
                    WHEN t.id_tarjeta IS NOT NULL THEN CONCAT('Tarjeta - ', t.tipo_tarjeta)
                    ELSE 'Sin Registro'
                END AS metodo_pago,
                t.tipo_tarjeta
            FROM venta v
            LEFT JOIN factura f ON v.id_factura = f.id_factura
            LEFT JOIN detalle_factura df ON df.id_factura = f.id_factura
            LEFT JOIN pago pg ON v.id_pago = pg.id_pago
            LEFT JOIN qr ON pg.id_pago = qr.id_pago
            LEFT JOIN efectivo ef ON pg.id_pago = ef.id_pago
            LEFT JOIN tarjeta t ON pg.id_pago = t.id_pago;
        """
        df = pd.read_sql(consulta, engine)
        if not df.empty:
            df["fecha_venta"] = pd.to_datetime(df["fecha_venta"], errors='coerce')
            df["mes"] = df["fecha_venta"].dt.to_period("M").astype(str)
        return df

    df = load_sales()
    if df.empty:
        st.info("No hay datos de ventas disponibles para mostrar.")
        return

    # SIDEBAR filtros (compartidos con otras páginas: usamos prefijos)
    st.sidebar.header("Filtros · Ventas")
    fecha_min = df["fecha_venta"].min()
    fecha_max = df["fecha_venta"].max()
    rango_fechas = st.sidebar.date_input("Rango de Fechas (Ventas)", value=(fecha_min, fecha_max), min_value=fecha_min, max_value=fecha_max)
    fecha_inicio, fecha_fin = rango_fechas
    meses_disp = sorted(df["mes"].dropna().unique().tolist())
    meses_sel = st.sidebar.multiselect("Meses (Ventas)", meses_disp, default=meses_disp)
    productos_disp = sorted(df["nombre_producto"].dropna().unique().tolist())
    productos_sel = st.sidebar.multiselect("Productos (Ventas)", productos_disp, default=productos_disp)
    metodos_disp = sorted(df["metodo_pago"].dropna().unique().tolist())
    metodos_sel = st.sidebar.multiselect("Método Pago (Ventas)", metodos_disp, default=metodos_disp)
    tarjetas_disp = sorted(df["tipo_tarjeta"].dropna().unique().tolist()) if "tipo_tarjeta" in df.columns else []
    tarjetas_sel = st.sidebar.multiselect("Tipo Tarjeta (Ventas)", tarjetas_disp, default=tarjetas_disp)

    # aplicar filtros
    df_f = df[
        (df["fecha_venta"] >= pd.to_datetime(fecha_inicio)) &
        (df["fecha_venta"] <= pd.to_datetime(fecha_fin))
    ]
    df_f = df_f[df_f["mes"].isin(meses_sel) & df_f["nombre_producto"].isin(productos_sel) & df_f["metodo_pago"].isin(metodos_sel)]
    if tarjetas_sel:
        df_f = df_f[(df_f["tipo_tarjeta"].isin(tarjetas_sel)) | (df_f["tipo_tarjeta"].isna())]

    # KPIs
    st.subheader("📌 Indicadores")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ventas Totales", f"{df_f['monto_neto'].sum():,.2f} Bs")
    c2.metric("Total de Ventas", len(df_f))
    c3.metric("Ticket Promedio", f"{df_f['monto_neto'].mean():,.2f} Bs" if len(df_f) else "0.00 Bs")
    top_prod = (df_f.groupby("nombre_producto")["subtotal"].sum().sort_values(ascending=False).index[0]) if not df_f.empty else "N/A"
    c4.metric("Producto Más Vendido", top_prod)

    # Gráficos (organizados en expanders)
    with st.expander("📄 Ventas por Mes"):
        tabla_mes = df_f.groupby("mes")["monto_neto"].sum().reset_index()
        st.dataframe(tabla_mes, use_container_width=True)
        fig_mes = px.bar(tabla_mes, x="mes", y="monto_neto", title="Ventas por Mes")
        st.plotly_chart(fig_mes, use_container_width=True)

    with st.expander("🏆 Top 10 Productos Más Vendidos"):
        top_productos = df_f.groupby("nombre_producto")["subtotal"].sum().sort_values(ascending=False).reset_index().head(10)
        fig_top = px.bar(top_productos, x="nombre_producto", y="subtotal", title="Top 10 Productos")
        st.plotly_chart(fig_top, use_container_width=True)

    with st.expander("💳 Métodos de Pago"):
        tabla_pago = df_f.groupby("metodo_pago")["monto_neto"].sum().reset_index()
        fig_pago = px.pie(tabla_pago, names="metodo_pago", values="monto_neto", title="Métodos de Pago")
        st.plotly_chart(fig_pago, use_container_width=True)

    with st.expander("📦 Ventas por Producto a lo Largo del Tiempo"):
        detalle_prod = df_f.groupby(["mes", "nombre_producto"])["subtotal"].sum().reset_index()
        if detalle_prod.empty:
            st.info("No hay detalle por producto en el periodo seleccionado.")
        else:
            fig_detalle = px.line(detalle_prod, x="mes", y="subtotal", color="nombre_producto", title="Tendencia de Ventas por Producto")
            st.plotly_chart(fig_detalle, use_container_width=True)


# ---------- Página 2: Inventario ----------
def render_inventario():
    st.title("🏪 INVENTARIO - Tienda Deportiva")

    # CSS local (preserva tu estilo)
    st.markdown("""
        <style>
        .chart-container { background: rgba(30,41,59,0.5); border-radius:12px; padding:12px; }
        .info-card { background: linear-gradient(135deg,#1e293b 0%,#334155 100%); border-radius:10px; padding:12px; color:white;}
        </style>
    """, unsafe_allow_html=True)

    @st.cache_data
    def generate_inventory_data():
        marcas = ['Nike', 'Adidas', 'Puma', 'Reebok', 'Under Armour', 'New Balance']
        categorias = ['Polera deportiva', 'Pantalón fitness', 'Short', 'Zapatillas running', 'Sudadera', 'Leggins']
        estados = ['Disponible', 'Agotado', 'Descontinuado']
        proveedores = ['Aivee', 'Dazzlesphere', 'Quatz', 'Dynazzy', 'Oyoba', 'Omba']
        productos = []
        for i in range(50):
            productos.append({
                'ID': f'PROD{i+1:03d}',
                'Nombre': f'{np.random.choice(categorias)} {np.random.choice(marcas)}',
                'Marca': np.random.choice(marcas),
                'Categoría': np.random.choice(categorias),
                'Precio': round(np.random.uniform(50, 700), 2),
                'Stock Actual': np.random.randint(0, 500),
                'Stock Mínimo': np.random.randint(10, 200),
                'Stock Máximo': np.random.randint(300, 800),
                'Estado': np.random.choice(estados, p=[0.44, 0.30, 0.26]),
                'Proveedor': np.random.choice(proveedores),
                'Fecha Ingreso': (datetime.now() - timedelta(days=np.random.randint(0, 365))).strftime('%Y-%m-%d'),
                'Última Venta': (datetime.now() - timedelta(days=np.random.randint(0, 90))).strftime('%Y-%m-%d')
            })
        return pd.DataFrame(productos)

    df_productos = generate_inventory_data()

    # Sidebar filtros inventario
    st.sidebar.header("Filtros · Inventario")
    marcas_disponibles = sorted(df_productos['Marca'].unique().tolist())
    categorias_disponibles = sorted(df_productos['Categoría'].unique().tolist())
    estados_disponibles = sorted(df_productos['Estado'].unique().tolist())

    selected_marca = st.sidebar.multiselect("Marcas", options=marcas_disponibles, default=marcas_disponibles)
    selected_categoria = st.sidebar.multiselect("Categorías", options=categorias_disponibles, default=categorias_disponibles)
    selected_estado = st.sidebar.multiselect("Estados", options=estados_disponibles, default=estados_disponibles)

    df_filtered = df_productos[
        (df_productos['Marca'].isin(selected_marca)) &
        (df_productos['Categoría'].isin(selected_categoria)) &
        (df_productos['Estado'].isin(selected_estado))
    ]

    # Indicadores
    st.subheader("📊 Métricas Principales")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("📦 Total Productos", len(df_filtered))
    col2.metric("📊 Stock Total", f"{df_filtered['Stock Actual'].sum():,}")
    col3.metric("💵 Precio Promedio", f"Bs. {df_filtered['Precio'].mean():.2f}")
    col4.metric("💰 Valor Inventario", f"Bs. {(df_filtered['Precio'] * df_filtered['Stock Actual']).sum():,.2f}")
    col5.metric("🏢 Proveedores", df_filtered['Proveedor'].nunique())

    st.markdown("---")
    st.markdown("### 📈 Análisis Visual")

    left, right = st.columns(2)
    with left:
        if st.checkbox("Mostrar: Stock por Marca", value=True):
            stock_by_marca = df_filtered.groupby('Marca')['Stock Actual'].sum().reset_index()
            fig_stock = px.bar(stock_by_marca, x='Marca', y='Stock Actual', title='Stock por Marca')
            st.plotly_chart(fig_stock, use_container_width=True)
    with right:
        if st.checkbox("Mostrar: Estado de Productos", value=True):
            status_counts = df_filtered['Estado'].value_counts()
            fig_status = go.Figure(data=[go.Pie(labels=status_counts.index, values=status_counts.values, hole=0.4)])
            st.plotly_chart(fig_status, use_container_width=True)

    st.markdown("---")
    st.markdown("### 📋 Lista Detallada")
    search_term = st.text_input("🔍 Buscar producto (ID, Nombre, Marca)")
    if search_term:
        df_display = df_filtered[df_filtered['ID'].str.contains(search_term, case=False) |
                                 df_filtered['Nombre'].str.contains(search_term, case=False) |
                                 df_filtered['Marca'].str.contains(search_term, case=False)]
    else:
        df_display = df_filtered.copy()

    st.dataframe(df_display, use_container_width=True, height=350)


# ---------- Página 3: Clientes ----------
def render_clientes():
    st.title("📊 Dashboard de Clientes - Tienda Deportiva")

    if engine is None:
        st.warning("La conexión a DB no está disponible. Esta página requiere base de datos.")
        return

    @st.cache_data(ttl=600)
    def load_client_data():
        query = """
            SELECT 
                cl.id_cliente,
                CONCAT(cl.nombre, ' ', cl.apellido_paterno, ' ', cl.apellido_materno) AS nombre_completo,
                cl.genero,
                dc.pais,
                dc.ciudad,
                cr.fecha_registro,
                hm.fecha_inicio AS membresia_inicio,
                hm.fecha_expiracion AS membresia_expiracion,
                em.estado AS estado_membresia,
                pf.puntos_acumulados,
                pf.nivel AS nivel_fidelizacion,
                pf.fecha_ultima_compra,
                cf.monto AS monto_cliente_frecuente,
                v.monto_total AS monto_venta,
                v.fecha_venta,
                v.descuento_aplicado
            FROM cliente cl
            LEFT JOIN direccion_cliente dc ON dc.id_cliente = cl.id_cliente
            LEFT JOIN cliente_registrado cr ON cr.id_cliente = cl.id_cliente
            LEFT JOIN historial_membresia hm ON hm.id_cliente_registrado = cr.id_cliente_registrado
            LEFT JOIN estado_membresia em ON em.id_historial_membresia = hm.id_historial_membresia
            LEFT JOIN programa_fidelizacion pf ON pf.id_cliente = cl.id_cliente
            LEFT JOIN cliente_frecuente cf ON cf.id_cliente = cl.id_cliente
            LEFT JOIN venta v ON v.id_cliente = cl.id_cliente
        """
        dfc = pd.read_sql(query, engine)
        # conversiones
        for col in ['fecha_registro','fecha_ultima_compra','fecha_venta','membresia_inicio','membresia_expiracion']:
            if col in dfc.columns:
                dfc[col] = pd.to_datetime(dfc[col], errors='coerce')
        numeric_cols = ['puntos_acumulados','monto_venta','monto_cliente_frecuente','descuento_aplicado']
        for c in numeric_cols:
            if c in dfc.columns:
                dfc[c] = pd.to_numeric(dfc[c], errors='coerce').fillna(0)
        # fillna basicos
        for c in ['ciudad','pais','genero','estado_membresia','nivel_fidelizacion']:
            if c in dfc.columns:
                dfc[c] = dfc[c].fillna(f'Sin {c}')
        return dfc

    df = load_client_data()
    if df.empty:
        st.info("No hay datos de clientes para mostrar.")
        return

    # filtros
    st.sidebar.header("Filtros · Clientes")
    ciudades = st.sidebar.multiselect("Ciudades", sorted(df['ciudad'].dropna().unique().tolist()), default=None)
    generos = st.sidebar.multiselect("Géneros", sorted(df['genero'].dropna().unique().tolist()), default=None)
    niveles = st.sidebar.multiselect("Niveles Fidelización", sorted(df['nivel_fidelizacion'].dropna().unique().tolist()), default=None)
    estados = st.sidebar.multiselect("Estados Membresía", sorted(df['estado_membresia'].dropna().unique().tolist()), default=None)

    fecha_min = df['fecha_registro'].min()
    fecha_max = df['fecha_registro'].max()
    if pd.notna(fecha_min) and pd.notna(fecha_max):
        fecha_inicio = st.sidebar.date_input("Desde (Clientes)", value=fecha_min.date(), min_value=fecha_min.date(), max_value=fecha_max.date())
        fecha_fin = st.sidebar.date_input("Hasta (Clientes)", value=fecha_max.date(), min_value=fecha_min.date(), max_value=fecha_max.date())
    else:
        fecha_inicio = fecha_fin = None

    df_filtrado = df.copy()
    if ciudades:
        df_filtrado = df_filtrado[df_filtrado['ciudad'].isin(ciudades)]
    if generos:
        df_filtrado = df_filtrado[df_filtrado['genero'].isin(generos)]
    if niveles:
        df_filtrado = df_filtrado[df_filtrado['nivel_fidelizacion'].isin(niveles)]
    if estados:
        df_filtrado = df_filtrado[df_filtrado['estado_membresia'].isin(estados)]
    if fecha_inicio and fecha_fin:
        df_filtrado = df_filtrado[(df_filtrado['fecha_registro'] >= pd.to_datetime(fecha_inicio)) & (df_filtrado['fecha_registro'] <= pd.to_datetime(fecha_fin))]

    if df_filtrado.empty:
        st.warning("⚠️ No se encontraron resultados con los filtros aplicados.")
        return

    # KPIs
    st.subheader("📈 INDICADORES CLAVE")
    col1, col2, col3, col4 = st.columns(4)
    total_clientes = df_filtrado['id_cliente'].nunique()
    clientes_activos = df_filtrado[df_filtrado['estado_membresia']=='Activa']['id_cliente'].nunique() if 'estado_membresia' in df_filtrado.columns else 0
    promedio_puntos = df_filtrado.groupby('id_cliente')['puntos_acumulados'].first().mean() if 'puntos_acumulados' in df_filtrado.columns else 0
    total_ventas = df_filtrado['monto_venta'].sum() if 'monto_venta' in df_filtrado.columns else 0
    col1.metric("Total Clientes", f"{total_clientes:,}")
    col2.metric("Membresías Activas", f"{clientes_activos:,}")
    col3.metric("Promedio Puntos", f"{promedio_puntos:,.0f}")
    col4.metric("Total Ventas", f"${total_ventas:,.2f}")

    st.divider()
    st.subheader("🎨 Visualizaciones")
    show_graph1 = st.checkbox("📊 Distribución por Ciudad", value=True)
    show_graph2 = st.checkbox("🎯 Niveles de Fidelización", value=True)
    show_graph3 = st.checkbox("👥 Clientes por Género", value=True)
    show_graph4 = st.checkbox("📅 Registro Mensual", value=True)

    col_a, col_b = st.columns(2)
    if show_graph1:
        clientes_ciudad = df_filtrado.groupby('ciudad')['id_cliente'].nunique().reset_index().sort_values('id_cliente', ascending=False).head(10)
        fig1 = px.bar(clientes_ciudad, x='id_cliente', y='ciudad', orientation='h', labels={'id_cliente':'Cantidad','ciudad':'Ciudad'}, title='Top Ciudades')
        st.plotly_chart(fig1, use_container_width=True)
    if show_graph2:
        niveles_fid = df_filtrado.groupby('nivel_fidelizacion')['id_cliente'].nunique().reset_index()
        fig2 = px.pie(niveles_fid, values='id_cliente', names='nivel_fidelizacion', title='Clientes por Nivel')
        st.plotly_chart(fig2, use_container_width=True)
    if show_graph3:
        genero_dist = df_filtrado.groupby('genero')['id_cliente'].nunique().reset_index()
        fig3 = px.bar(genero_dist, x='genero', y='id_cliente', title='Clientes por Género')
        st.plotly_chart(fig3, use_container_width=True)
    if show_graph4:
        df_registros = df_filtrado[df_filtrado['fecha_registro'].notna()].copy()
        df_registros['mes_anio'] = df_registros['fecha_registro'].dt.to_period('M').astype(str)
        registros_mes = df_registros.groupby('mes_anio')['id_cliente'].nunique().reset_index().sort_values('mes_anio')
        fig4 = px.line(registros_mes, x='mes_anio', y='id_cliente', title='Registros Mensuales', markers=True)
        st.plotly_chart(fig4, use_container_width=True)

    st.divider()
    st.subheader("📋 Tablas")
    if st.checkbox("Mostrar: Top Clientes"):
        top_clientes = df_filtrado.groupby(['id_cliente','nombre_completo','ciudad']).agg({'monto_venta':'count','puntos_acumulados':'first'}).reset_index().sort_values('monto_venta', ascending=False).head(10)
        st.dataframe(top_clientes, use_container_width=True)

    if st.checkbox("Descargar datos filtrados"):
        csv = df_filtrado.to_csv(index=False).encode('utf-8')
        st.download_button(label="📥 Descargar CSV clientes", data=csv, file_name=f"clientes_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")


# ---------- Página 4: Empleados ----------
def render_empleados():
    st.title("👔 Dashboard de Empleados – Tienda Deportiva")

    # datos simulados (tu código original)
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
    df_emp = pd.DataFrame(empleados)
    df_emp["duracion_contrato"] = (df_emp["fecha_fin_contrato"] - df_emp["fecha_inicio_contrato"]).dt.days

    # sidebar filtros empleados
    st.sidebar.header("Filtros · Empleados")
    fil_sucursal = st.sidebar.multiselect("Sucursal (Empleados)", sucursales, default=sucursales)
    fil_turno = st.sidebar.multiselect("Turno (Empleados)", turnos, default=turnos)
    fil_estado = st.sidebar.multiselect("Estado (Empleados)", estados, default=estados)

    df_filtered = df_emp[
        (df_emp["nombre_sucursal"].isin(fil_sucursal)) &
        (df_emp["nombre_turno"].isin(fil_turno)) &
        (df_emp["nombre_estado"].isin(fil_estado))
    ]

    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("👥 Total empleados", len(df_filtered))
    col2.metric("✔️ Activos", df_filtered[df_filtered["nombre_estado"] == "Activo"].shape[0])
    col3.metric("⏳ Duración promedio (días)", round(df_filtered["duracion_contrato"].mean(), 2))
    col4.metric("🏢 Sucursales con personal", df_filtered["nombre_sucursal"].nunique())

    st.markdown("---")
    st.subheader("🏢 Distribución de Empleados por Sucursal")
    suc_count = df_filtered["nombre_sucursal"].value_counts().reset_index()
    suc_count.columns = ['Sucursal', 'Cantidad']
    fig_suc = px.bar(suc_count, x='Sucursal', y='Cantidad', title="Empleados por Sucursal")
    st.plotly_chart(fig_suc, use_container_width=True)

    st.subheader("🧩 Estado Laboral del Personal")
    estado_count = df_filtered["nombre_estado"].value_counts().reset_index()
    estado_count.columns = ['Estado', 'Cantidad']
    fig_estado = px.pie(estado_count, names='Estado', values='Cantidad', title="Distribución de Estados Laborales")
    st.plotly_chart(fig_estado, use_container_width=True)

    st.subheader("📋 Lista Detallada")
    busqueda = st.text_input("🔎 Buscar empleado")
    df_show = df_filtered.copy()
    if busqueda:
        df_show = df_show[df_show["empleado"].str.contains(busqueda, case=False)]
    st.dataframe(df_show, use_container_width=True, height=350)

# ------------------------
# NAVEGACIÓN: menú lateral
# ------------------------
st.sidebar.title("Navegación")
page = st.sidebar.radio("Ir a", ("Ventas", "Inventario", "Clientes", "Empleados"))

if page == "Ventas":
    render_ventas()
elif page == "Inventario":
    render_inventario()
elif page == "Clientes":
    render_clientes()
elif page == "Empleados":
    render_empleados()

# ------------------------
# FOOTER COMÚN
# ------------------------
st.markdown("---")
st.markdown("<div style='text-align:center; color:#94a3b8;'>Tienda Deportiva — Dashboards integrados · Desarrollado con Streamlit & Plotly</div>", unsafe_allow_html=True)
# ---------- Página 4: Empleados ----------
def render_empleados():

    st.title("👔 Dashboard de Empleados – Tienda Deportiva")

    # ==========================================
    # ESTILO (reutilizado del dashboard original)
    # ==========================================
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
    # DATOS SIMULADOS (exacto a tu código)
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
    # SIDEBAR — filtros
    # ==========================================
    st.sidebar.header("Filtros · Empleados")

    fil_sucursal = st.sidebar.multiselect("Sucursal", sucursales, sucursales)
    fil_turno = st.sidebar.multiselect("Turno", turnos, turnos)
    fil_estado = st.sidebar.multiselect("Estado Laboral", estados, estados)

    df_filtered = df[
        (df["nombre_sucursal"].isin(fil_sucursal)) &
        (df["nombre_turno"].isin(fil_turno)) &
        (df["nombre_estado"].isin(fil_estado))
    ]

    # ==========================================
    # KPIs
    # ==========================================
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("👥 Total empleados", len(df_filtered))
    col2.metric("✔️ Activos", df_filtered[df_filtered["nombre_estado"] == "Activo"].shape[0])
    col3.metric("⏳ Duración promedio (días)", round(df_filtered["duracion_contrato"].mean(), 2))
    col4.metric("🏢 Sucursales con personal", df_filtered["nombre_sucursal"].nunique())

    st.markdown("---")

    # ==========================================
    # Gráficos
    # ==========================================
    # Empleados por sucursal
    st.subheader("🏢 Distribución de Empleados por Sucursal")
    suc_count = df_filtered["nombre_sucursal"].value_counts()
    fig_suc = px.bar(suc_count, x=suc_count.index, y=suc_count.values, title="Empleados por Sucursal")
    st.plotly_chart(fig_suc, use_container_width=True)

    # Estado laboral
    st.subheader("🧩 Estado Laboral del Personal")
    estado_count = df_filtered["nombre_estado"].value_counts()
    fig_estado = px.pie(names=estado_count.index, values=estado_count.values, title="Estados Laborales")
    st.plotly_chart(fig_estado, use_container_width=True)

    # Duración contrato
    st.subheader("⏱ Duración del Contrato")
    fig_duracion = px.line(df_filtered.sort_values("duracion_contrato"),
                           x="empleado", y="duracion_contrato", markers=True)
    st.plotly_chart(fig_duracion, use_container_width=True)

    # ==========================================
    # Tabla
    # ==========================================
    st.subheader("📋 Lista Detallada de Empleados")

    busqueda = st.text_input("🔎 Buscar empleado")
    df_show = df_filtered.copy()
    if busqueda:
        df_show = df_show[df_show["empleado"].str.contains(busqueda, case=False)]

    st.dataframe(df_show, height=350, use_container_width=True)
