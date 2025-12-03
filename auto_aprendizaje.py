import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine

# CONFIGURACIÓN
st.set_page_config(page_title="Dashboard de Ventas", layout="wide")

# 🔄 NUEVA CONEXIÓN QUE ME PEDISTE
DB_URL = "mysql+pymysql://sql5809887:XSjyzGzKg8@sql5.freesqldatabase.com:3306/sql5809887"
engine = create_engine(DB_URL)

# FUNCIÓN DE CARGA DE DATOS
@st.cache_data
def load_data():
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
        LEFT JOIN factura f 
            ON v.id_factura = f.id_factura

        LEFT JOIN detalle_factura df 
            ON df.id_factura = f.id_factura

        LEFT JOIN pago pg 
            ON v.id_pago = pg.id_pago

        LEFT JOIN qr 
            ON pg.id_pago = qr.id_pago

        LEFT JOIN efectivo ef 
            ON pg.id_pago = ef.id_pago

        LEFT JOIN tarjeta t 
            ON pg.id_pago = t.id_pago;
    """

    df = pd.read_sql(consulta, engine)

    df["fecha_venta"] = pd.to_datetime(df["fecha_venta"])
    df["mes"] = df["fecha_venta"].dt.to_period("M").astype(str)

    return df


# CARGAR DATOS
df = load_data()

# FILTROS
st.sidebar.header("Filtros")

# 📅 RANGO FECHAS
fecha_min = df["fecha_venta"].min()
fecha_max = df["fecha_venta"].max()

rango_fechas = st.sidebar.date_input(
    "Rango de Fechas (Calendario)",
    value=(fecha_min, fecha_max),
    min_value=fecha_min,
    max_value=fecha_max
)

fecha_inicio, fecha_fin = rango_fechas

df = df[
    (df["fecha_venta"] >= pd.to_datetime(fecha_inicio)) &
    (df["fecha_venta"] <= pd.to_datetime(fecha_fin))
]

# 📆 MESES
meses_disp = sorted(df["mes"].unique())
meses_sel = st.sidebar.multiselect("Filtrar por Mes", meses_disp, default=meses_disp)

# 🎽 PRODUCTOS
productos_disp = sorted(df["nombre_producto"].dropna().unique())
productos_sel = st.sidebar.multiselect("Productos", productos_disp, default=productos_disp)

# 💳 MÉTODO PAGO
metodos_disp = sorted(df["metodo_pago"].dropna().unique())
metodos_sel = st.sidebar.multiselect("Método de Pago", metodos_disp, default=metodos_disp)

# 🪪 TARJETA
tarjetas_disp = sorted(df["tipo_tarjeta"].dropna().unique())
tarjetas_sel = st.sidebar.multiselect("Tipo de Tarjeta", tarjetas_disp, default=tarjetas_disp)

# APLICAR FILTROS
df_filtrado = df[
    df["mes"].isin(meses_sel) &
    df["nombre_producto"].isin(productos_sel) &
    df["metodo_pago"].isin(metodos_sel)
]

if tarjetas_sel:
    df_filtrado = df_filtrado[
        (df_filtrado["tipo_tarjeta"].isin(tarjetas_sel)) |
        (df_filtrado["tipo_tarjeta"].isna())
    ]

# TÍTULO
st.title("📊 Dashboard de Ventas - Tienda Deportiva")

# KPIs
st.subheader("📌 Indicadores")

c1, c2, c3, c4 = st.columns(4)

c1.metric("Ventas Totales", f"{df_filtrado['monto_neto'].sum():,.2f} Bs")
c2.metric("Total de Ventas", len(df_filtrado))
c3.metric("Ticket Promedio", f"{df_filtrado['monto_neto'].mean():,.2f} Bs" if len(df_filtrado) else "0.00 Bs")

top_prod = (
    df_filtrado.groupby("nombre_producto")["subtotal"]
    .sum()
    .sort_values(ascending=False)
    .index[0]
    if not df_filtrado.empty else "N/A"
)
c4.metric("Producto Más Vendido", top_prod)

# 🔹 Ventas por Mes
with st.expander("📄 Ventas por Mes"):
    tabla_mes = df_filtrado.groupby("mes")["monto_neto"].sum().reset_index()
    st.dataframe(tabla_mes, use_container_width=True)

    fig_mes = px.bar(tabla_mes, x="mes", y="monto_neto", title="Ventas por Mes")
    st.plotly_chart(fig_mes, use_container_width=True)

# 🔹 Top Productos
with st.expander("🏆 Top 10 Productos Más Vendidos"):
    top_productos = (
        df_filtrado.groupby("nombre_producto")["subtotal"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
        .head(10)
    )

    fig_top = px.bar(top_productos, x="nombre_producto", y="subtotal", title="Top 10 Productos")
    st.plotly_chart(fig_top, use_container_width=True)

# 🔹 Métodos de Pago
with st.expander("💳 Distribución de Métodos de Pago"):
    tabla_pago = df_filtrado.groupby("metodo_pago")["monto_neto"].sum().reset_index()

    fig_pago = px.pie(tabla_pago, names="metodo_pago", values="monto_neto", title="Métodos de Pago")
    st.plotly_chart(fig_pago, use_container_width=True)

# 🔹 Dashboard por Tipo de Tarjeta
with st.expander("💳 Ventas por Tipo de Tarjeta"):
    df_tarjeta = df_filtrado[df_filtrado["tipo_tarjeta"].notna()]

    if not df_tarjeta.empty:
        tabla_tarjeta = df_tarjeta.groupby("tipo_tarjeta")["monto_neto"].sum().reset_index()

        fig_tarjeta = px.bar(tabla_tarjeta, x="tipo_tarjeta", y="monto_neto", title="Ventas por Tipo de Tarjeta")
        st.plotly_chart(fig_tarjeta, use_container_width=True)
    else:
        st.info("No hay ventas pagadas con tarjeta en el filtro seleccionado.")

# 🔹 Ventas por Producto a lo Largo del Tiempo
with st.expander("📦 Ventas por Producto a lo Largo del Tiempo"):
    detalle_prod = (
        df_filtrado.groupby(["mes", "nombre_producto"])["subtotal"]
        .sum()
        .reset_index()
    )

    fig_detalle = px.line(detalle_prod, x="mes", y="subtotal", color="nombre_producto",
                          title="Tendencia de Ventas por Producto")
    st.plotly_chart(fig_detalle, use_container_width=True)
