import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# Configuración de la página
st.set_page_config(
    page_title="Dashboard inventario",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado mejorado
st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    }
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 50px;
        font-weight: bold;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.3);
    }
    div[data-testid="metric-container"] {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(148, 163, 184, 0.2);
    }
    .chart-container {
        background: rgba(30, 41, 59, 0.5);
        border-radius: 15px;
        padding: 20px;
        border: 1px solid rgba(148, 163, 184, 0.2);
        margin-bottom: 20px;
    }
    .info-card {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        border-radius: 10px;
        padding: 15px;
        border-left: 4px solid #10b981;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

# Generar datos más detallados
@st.cache_data
def generate_inventory_data():
    marcas = ['Nike', 'Adidas', 'Puma', 'Reebok', 'Under Armour', 'New Balance']
    categorias = ['Polera deportiva', 'Pantalón fitness', 'Short', 'Zapatillas running', 'Sudadera', 'Leggins']
    estados = ['Disponible', 'Agotado', 'Descontinuado']
    proveedores = ['Aivee', 'Dazzlesphere', 'Quatz', 'Dynazzy', 'Oyoba', 'Omba']
    
    productos = []
    for i in range(50):
        producto = {
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
        }
        productos.append(producto)
    
    return pd.DataFrame(productos)

# Datos del sistema
df_productos = generate_inventory_data()

# Header con logo y título
col_h1, col_h2, col_h3 = st.columns([1, 2, 1])
with col_h2:
    st.markdown("""
        <div style='text-align: center; padding: 20px;'>
            <h1 style='color: white; font-size: 3em; margin: 0;'>🏪 INVENTARIO</h1>
            <p style='color: #10b981; font-size: 1.2em; margin: 5px 0;'>Sistema de Gestión Integral</p>
            <p style='color: #94a3b8; margin: 0;'>Tienda de Ropa Deportiva</p>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Sidebar mejorado con solución para los filtros
# Sidebar mejorado con filtros sin opciones "todas" o "ninguna"
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/warehouse.png", width=80)
    st.title("⚙ INVENTARIO Control")
    st.markdown("---")
    
    st.subheader("🔍 Filtros")
    
    # Listas únicas
    marcas_disponibles = sorted(df_productos['Marca'].unique().tolist())
    categorias_disponibles = sorted(df_productos['Categoría'].unique().tolist())
    estados_disponibles = sorted(df_productos['Estado'].unique().tolist())
    
    # Inicializar session_state si no existe
    if 'marcas_selected' not in st.session_state:
        st.session_state.marcas_selected = []
    if 'categorias_selected' not in st.session_state:
        st.session_state.categorias_selected = []
    if 'estados_selected' not in st.session_state:
        st.session_state.estados_selected = []

    # Multiselects sin "todas" o "ninguna"
    selected_marca = st.multiselect(
        "Seleccionar Marcas",
        options=marcas_disponibles,
        default=st.session_state.marcas_selected,
        key='marca_multiselect'
    )
    
    st.markdown("---")
    
    selected_categoria = st.multiselect(
        "Seleccionar Categorías",
        options=categorias_disponibles,
        default=st.session_state.categorias_selected,
        key='categoria_multiselect'
    )
    
    st.markdown("---")
    
    selected_estado = st.multiselect(
        "Seleccionar Estados",
        options=estados_disponibles,
        default=st.session_state.estados_selected,
        key='estado_multiselect'
    )
    
    st.markdown("---")
    
    date_range = st.date_input(
        "Rango de Fechas",
        value=(datetime.now() - timedelta(days=365), datetime.now()),
        max_value=datetime.now()
    )
    
    st.markdown("---")
    
    # Control de gráficos
    st.subheader("📊 Visualizaciones")
    show_provider = st.checkbox("🏢 Por Proveedor", value=False)
    show_timeline = st.checkbox("📅 Línea de Tiempo", value=False)
    
    st.markdown("---")
    st.info(f"✅ Gráficos activos: {sum([ show_provider, show_timeline])}/6")


# Aplicar filtros - Manejar listas vacías
if len(selected_marca) == 0:
    selected_marca = marcas_disponibles
if len(selected_categoria) == 0:
    selected_categoria = categorias_disponibles
if len(selected_estado) == 0:
    selected_estado = estados_disponibles

df_filtered = df_productos[
    (df_productos['Marca'].isin(selected_marca)) &
    (df_productos['Categoría'].isin(selected_categoria)) &
    (df_productos['Estado'].isin(selected_estado))
]

# Información del sistema
col_info1, col_info2 = st.columns([2, 1])

with col_info1:
    st.markdown(f"""
        <div class='info-card'>
            <h4 style='color: white; margin: 0;'>📅 Fecha del Sistema</h4>
            <p style='color: #10b981; font-size: 1.5em; margin: 5px 0;'>{datetime.now().strftime('%d de %B, %Y - %H:%M')}</p>
            <p style='color: #94a3b8; margin: 0;'>Última actualización: Hace 2 minutos</p>
        </div>
    """, unsafe_allow_html=True)

with col_info2:
    st.markdown(f"""
        <div class='info-card'>
            <h4 style='color: white; margin: 0;'>🔢 Registros</h4>
            <p style='color: #3b82f6; font-size: 1.5em; margin: 5px 0;'>{len(df_filtered)} productos</p>
            <p style='color: #94a3b8; margin: 0;'>Filtrados de {len(df_productos)} totales</p>
        </div>
    """, unsafe_allow_html=True)

# Métricas principales
st.markdown("### 📊 Métricas Principales")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    total_productos = len(df_filtered)
    st.metric(
        label="📦 Total Productos",
        value=total_productos,
        delta=f"{len(df_filtered[df_filtered['Estado'] == 'Disponible'])} disponibles"
    )

with col2:
    stock_total = df_filtered['Stock Actual'].sum()
    st.metric(
        label="📊 Stock Total",
        value=f"{stock_total:,}",
        delta=f"{len(df_filtered[df_filtered['Stock Actual'] < df_filtered['Stock Mínimo']])} bajo mínimo"
    )

with col3:
    precio_promedio = df_filtered['Precio'].mean()
    st.metric(
        label="💵 Precio Promedio",
        value=f"Bs. {precio_promedio:.2f}",
        delta=f"Min: Bs. {df_filtered['Precio'].min():.2f}"
    )

with col4:
    total_valor = (df_filtered['Precio'] * df_filtered['Stock Actual']).sum()
    st.metric(
        label="💰 Valor Inventario",
        value=f"Bs. {total_valor:,.2f}",
        delta="Actualizado"
    )

with col5:
    proveedores_activos = df_filtered['Proveedor'].nunique()
    st.metric(
        label="🏢 Proveedores",
        value=proveedores_activos,
        delta=f"{df_filtered['Marca'].nunique()} marcas"
    )

st.markdown("---")

# Sección de gráficos
st.markdown("### 📈 Análisis Visual")

# Botones para mostrar/ocultar gráficos
col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)

with col_btn1:
    if 'show_stock_chart' not in st.session_state:
        st.session_state.show_stock_chart = False
    if st.button("📊 STOCK POR MARCA", use_container_width=True):
        st.session_state.show_stock_chart = not st.session_state.show_stock_chart

with col_btn2:
    if 'show_status_chart' not in st.session_state:
        st.session_state.show_status_chart = False
    if st.button("🥧 ESTADO PRODUCTO", use_container_width=True):
        st.session_state.show_status_chart = not st.session_state.show_status_chart

with col_btn3:
    if 'show_price_chart' not in st.session_state:
        st.session_state.show_price_chart = False
    if st.button("💰 RANGO DE PRECIOS", use_container_width=True):
        st.session_state.show_price_chart = not st.session_state.show_price_chart

with col_btn4:
    if 'show_movement_chart' not in st.session_state:
        st.session_state.show_movement_chart = False
    if st.button("📈 MOVIMIENTOS", use_container_width=True):
        st.session_state.show_movement_chart = not st.session_state.show_movement_chart

st.markdown("---")

# Layout para gráficos
col_left, col_right = st.columns(2)

# Gráfico 1: Stock por Marca
if st.session_state.show_stock_chart:
    with col_left:
        with st.container():
            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
            st.markdown("#### 📊 Stock Actual por Marca")
            
            stock_by_marca = df_filtered.groupby('Marca').agg({
                'Stock Actual': 'sum',
                'Stock Mínimo': 'sum',
                'Stock Máximo': 'sum'
            }).reset_index()
            
            fig_stock = go.Figure()
            fig_stock.add_trace(go.Bar(name='Stock Actual', x=stock_by_marca['Marca'], 
                                       y=stock_by_marca['Stock Actual'], marker_color='#10b981'))
            fig_stock.add_trace(go.Bar(name='Stock Mínimo', x=stock_by_marca['Marca'], 
                                       y=stock_by_marca['Stock Mínimo'], marker_color='#f59e0b'))
            fig_stock.add_trace(go.Bar(name='Stock Máximo', x=stock_by_marca['Marca'], 
                                       y=stock_by_marca['Stock Máximo'], marker_color='#3b82f6'))
            
            fig_stock.update_layout(
                barmode='group', plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'), height=400, 
                xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='rgba(148, 163, 184, 0.1)')
            )
            st.plotly_chart(fig_stock, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

# Gráfico 2: Estado de Productos
if st.session_state.show_status_chart:
    with col_right:
        with st.container():
            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
            st.markdown("#### 🥧 Distribución por Estado")
            
            status_counts = df_filtered['Estado'].value_counts()
            colors = {'Disponible': '#10b981', 'Agotado': '#ef4444', 'Descontinuado': '#f59e0b'}
            
            fig_status = go.Figure(data=[go.Pie(
                labels=status_counts.index,
                values=status_counts.values,
                marker=dict(colors=[colors[x] for x in status_counts.index]),
                hole=0.4,
                textinfo='label+percent+value',
                textfont=dict(size=12, color='white')
            )])
            
            fig_status.update_layout(
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'), height=400, showlegend=True
            )
            st.plotly_chart(fig_status, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

# Gráfico 3: Rangos de Precios
if st.session_state.show_price_chart:
    with col_left:
        with st.container():
            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
            st.markdown("#### 💰 Análisis de Precios por Categoría")
            
            price_by_cat = df_filtered.groupby('Categoría')['Precio'].agg(['min', 'mean', 'max']).reset_index()
            
            fig_price = go.Figure()
            fig_price.add_trace(go.Bar(name='Mínimo', x=price_by_cat['Categoría'], 
                                       y=price_by_cat['min'], marker_color='#ef4444'))
            fig_price.add_trace(go.Bar(name='Promedio', x=price_by_cat['Categoría'], 
                                       y=price_by_cat['mean'], marker_color='#10b981'))
            fig_price.add_trace(go.Bar(name='Máximo', x=price_by_cat['Categoría'], 
                                       y=price_by_cat['max'], marker_color='#3b82f6'))
            
            fig_price.update_layout(
                barmode='group', plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'), height=400,
                xaxis=dict(showgrid=False, tickangle=-15), 
                yaxis=dict(showgrid=True, gridcolor='rgba(148, 163, 184, 0.1)', title='Precio (Bs.)')
            )
            st.plotly_chart(fig_price, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

# Gráfico 4: Movimientos
if st.session_state.show_movement_chart:
    with col_right:
        with st.container():
            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
            st.markdown("#### 📈 Tendencia de Movimientos")
            
            meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun']
            entradas = [145, 187, 203, 168, 195, 221]
            salidas = [98, 134, 156, 142, 178, 189]
            
            fig_movement = go.Figure()
            fig_movement.add_trace(go.Scatter(x=meses, y=entradas, mode='lines+markers',
                                             name='Entradas', line=dict(color='#10b981', width=3),
                                             marker=dict(size=10)))
            fig_movement.add_trace(go.Scatter(x=meses, y=salidas, mode='lines+markers',
                                             name='Salidas', line=dict(color='#ef4444', width=3),
                                             marker=dict(size=10)))
            
            fig_movement.update_layout(
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'), height=400,
                xaxis=dict(showgrid=False), 
                yaxis=dict(showgrid=True, gridcolor='rgba(148, 163, 184, 0.1)', title='Unidades')
            )
            st.plotly_chart(fig_movement, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

# Gráfico 5: Por Proveedor
if show_provider:
    with col_left:
        with st.container():
            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
            st.markdown("#### 🏢 Productos por Proveedor")
            
            provider_counts = df_filtered['Proveedor'].value_counts().head(10)
            
            fig_provider = px.bar(x=provider_counts.values, y=provider_counts.index, 
                                 orientation='h', color=provider_counts.values,
                                 color_continuous_scale='Viridis')
            
            fig_provider.update_layout(
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'), height=400, showlegend=False,
                xaxis=dict(title='Cantidad de Productos'),
                yaxis=dict(title='')
            )
            st.plotly_chart(fig_provider, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

# Gráfico 6: Timeline
if show_timeline:
    with col_right:
        with st.container():
            st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
            st.markdown("#### 📅 Línea de Tiempo de Ingresos")
            
            df_filtered['Fecha Ingreso'] = pd.to_datetime(df_filtered['Fecha Ingreso'])
            timeline_data = df_filtered.groupby(df_filtered['Fecha Ingreso'].dt.to_period('M')).size()
            timeline_data.index = timeline_data.index.to_timestamp()
            
            fig_timeline = go.Figure()
            fig_timeline.add_trace(go.Scatter(
                x=timeline_data.index, y=timeline_data.values,
                mode='lines+markers', fill='tozeroy',
                line=dict(color='#8b5cf6', width=2),
                marker=dict(size=8, color='#8b5cf6')
            ))
            
            fig_timeline.update_layout(
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='white'), height=400,
                xaxis=dict(showgrid=False, title='Fecha'),
                yaxis=dict(showgrid=True, gridcolor='rgba(148, 163, 184, 0.1)', title='Productos')
            )
            st.plotly_chart(fig_timeline, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")

# Tabla detallada de productos
st.markdown("### 📋 Lista Detallada de Productos")

# Búsqueda y filtros adicionales
col_search1, col_search2, col_search3 = st.columns([2, 1, 1])

with col_search1:
    search_term = st.text_input("🔍 Buscar producto", placeholder="ID, nombre, marca...")

with col_search2:
    sort_by = st.selectbox("Ordenar por", ["ID", "Nombre", "Precio", "Stock Actual", "Marca"])

with col_search3:
    sort_order = st.radio("Orden", ["Ascendente", "Descendente"], horizontal=True)

# Aplicar búsqueda
if search_term:
    df_display = df_filtered[
        df_filtered['ID'].str.contains(search_term, case=False) |
        df_filtered['Nombre'].str.contains(search_term, case=False) |
        df_filtered['Marca'].str.contains(search_term, case=False)
    ]
else:
    df_display = df_filtered

# Ordenar
df_display = df_display.sort_values(
    by=sort_by, 
    ascending=(sort_order == "Ascendente")
)

# Mostrar tabla con estilo
st.dataframe(
    df_display.style.background_gradient(subset=['Precio'], cmap='RdYlGn')
                   .background_gradient(subset=['Stock Actual'], cmap='Blues'),
    use_container_width=True,
    height=400
)

# Resumen por marca
st.markdown("---")
st.markdown("### 🏷 Resumen por Marca")

col_brand1, col_brand2, col_brand3 = st.columns(3)

with col_brand1:
    st.markdown("#### Top 3 Marcas - Stock")
    top_stock = df_filtered.groupby('Marca')['Stock Actual'].sum().sort_values(ascending=False).head(3)
    for i, (marca, stock) in enumerate(top_stock.items(), 1):
        st.markdown(f"{i}. {marca}: {stock:,} unidades")

with col_brand2:
    st.markdown("#### Top 3 Marcas - Valor")
    df_filtered_copy = df_filtered.copy()
    df_filtered_copy['Valor'] = df_filtered_copy['Precio'] * df_filtered_copy['Stock Actual']
    top_valor = df_filtered_copy.groupby('Marca')['Valor'].sum().sort_values(ascending=False).head(3)
    for i, (marca, valor) in enumerate(top_valor.items(), 1):
        st.markdown(f"{i}. {marca}: Bs. {valor:,.2f}")

with col_brand3:
    st.markdown("#### Top 3 Marcas - Productos")
    top_productos = df_filtered['Marca'].value_counts().head(3)
    for i, (marca, count) in enumerate(top_productos.items(), 1):
        st.markdown(f"{i}. {marca}: {count} productos")

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #64748b; padding: 30px;'>
        <h3 style='color: #10b981;'>🏪 INVENTARIO</h3>
        <p>Sistema de Gestión Integral de Inventario</p>
        <p>Tienda de Ropa Deportiva</p>
        <p style='font-size: 0.9em; margin-top: 10px;'>
            Desarrollado con ❤ y hecho por cielo sanchez usando Streamlit y Plotly<br>
        </p>
    </div>
""", unsafe_allow_html=True)