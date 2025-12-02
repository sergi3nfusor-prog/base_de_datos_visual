import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from sqlalchemy import create_engine, text

# ============================================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================================
st.set_page_config(
    page_title="Dashboard de Ventas - Tienda Deportiva",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Asegúrate de tener pymysql instalado si usas este URI
DEFAULT_DB_URI = "mysql+pymysql://root:root@localhost:3306/TiendaDeportiva"

# ============================================================
# FUNCIÓN DE CONEXIÓN
# ============================================================
def get_engine(db_uri):
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
    engine = create_engine(db_uri)

    query = """
        SELECT 
            v.id_venta,
            v.fecha_venta,
            v.monto_total,
            v.impuesto,
            v.descuento_aplicado,
            (v.monto_total - v.descuento_aplicado) AS monto_neto,

            -- CLIENTE
            c.id_cliente,
            CONCAT(COALESCE(c.nombre,''), ' ', COALESCE(c.apellido_paterno,''), ' ', COALESCE(c.apellido_materno,'')) AS nombre_cliente,
            c.ci,

            -- FACTURA
            f.id_factura,
            f.numero_factura,
            f.total AS total_factura,

            -- DETALLE
            dv.id_detalle_venta,
            dv.id_producto AS dv_id_producto,
            dv.cantidad,
            dv.precio_unitario,
            dv.subtotal,
            dv.fecha_pedido,

            -- PRODUCTO
            p.id_producto,
            p.nombre_producto,
            p.marca,
            p.material,
            p.talla,
            p.precio AS precio_producto,

            -- MÉTODO DE PAGO
            CASE
                WHEN qr.id_qr IS NOT NULL THEN 'QR'
                WHEN tar.id_tarjeta IS NOT NULL THEN 'TARJETA'
                WHEN ef.id_efectivo IS NOT NULL THEN 'EFECTIVO'
                ELSE 'SIN_REGISTRO'
            END AS tipo_pago

        FROM venta v
        LEFT JOIN cliente c ON c.id_cliente = v.id_cliente
        LEFT JOIN factura f ON f.id_factura = v.id_factura
        LEFT JOIN pago pg ON pg.id_pago = v.id_pago
        LEFT JOIN qr ON qr.id_pago = pg.id_pago
        LEFT JOIN tarjeta tar ON tar.id_pago = pg.id_pago
        LEFT JOIN efectivo ef ON ef.id_pago = pg.id_pago
        LEFT JOIN detalle_venta dv ON dv.id_venta = v.id_venta
        LEFT JOIN producto p ON p.id_producto = dv.id_producto;
    """

    try:
        df = pd.read_sql(query, engine)
    except Exception as e:
        st.error(f"❌ Error ejecutando la consulta SQL:\n{e}")
        return pd.DataFrame()

    # Conversión de fechas
    df["fecha_venta"] = pd.to_datetime(df.get("fecha_venta"), errors="coerce")
    df["fecha_pedido"] = pd.to_datetime(df.get("fecha_pedido"), errors="coerce")

    # Limpieza y conversión numérica segura
    for col in ["monto_total", "descuento_aplicado", "monto_neto", "impuesto", "precio_unitario", "subtotal", "precio_producto"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    # Recalcular monto_neto si hay inconsistencias
    if "monto_total" in df.columns and "descuento_aplicado" in df.columns:
        df["monto_neto"] = df["monto_total"] - df["descuento_aplicado"]
    else:
        df["monto_neto"] = df.get("monto_neto", pd.Series(0.0, index=df.index))

    # Derivados temporales
    df["anio"] = df["fecha_venta"].dt.year
    df["mes"] = df["fecha_venta"].dt.month
    df["mes_anio"] = df["fecha_venta"].dt.to_period("M").astype(str)

    df["tipo_pago"] = df["tipo_pago"].fillna("SIN_REGISTRO")
    df["nombre_producto"] = df["nombre_producto"].fillna("SIN_PRODUCTO")

    return df

# ============================================================
# FUNCIÓN DE FILTRADO
# ============================================================
def filtrar(df, fechas, productos, marcas, pagos):
    # fechas: lista o tupla [fi, ff]
    try:
        fi, ff = fechas
    except Exception:
        # si el usuario seleccionó una sola fecha, la duplicamos
        fi = ff = fechas

    # Aseguramos que son objetos date
    if hasattr(fi, "to_pydatetime"):
        fi = fi
    if hasattr(ff, "to_pydatetime"):
        ff = ff

    # Filtrado por rango inclusive
    mask_fecha = df["fecha_venta"].dt.date.between(pd.to_datetime(fi).date(), pd.to_datetime(ff).date())
    df = df[mask_fecha]

    if productos:
        df = df[df["nombre_producto"].isin(productos)]


