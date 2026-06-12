import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Análisis de Inventario JMW - Productos CATMAN", layout="wide")

st.title("📊 Análisis de Inventario JMW - Productos CATMAN")
st.markdown("---")

# Subir archivo
archivo = st.file_uploader("📂 Sube tu archivo Consolidado_Inventario_Catman.xlsx", type=["xlsx"])

if archivo is None:
    st.info("Esperando archivo Excel...")
    st.stop()

# Cargar datos
df = pd.read_excel(archivo, sheet_name='1_Consolidado_Total')

# Limpiar datos
df['Dias de Inventario'] = pd.to_numeric(df['Dias de Inventario'], errors='coerce')
df['Stock Actual'] = pd.to_numeric(df['Stock Actual'], errors='coerce')
df['PROVEEDOR'] = df['PROVEEDOR'].fillna('Sin Proveedor').astype(str).str.strip()
df['nombre'] = df['nombre'].fillna('Sin Tienda').astype(str).str.strip()
df['nombre'] = df['nombre'].str.replace("Farmacia ", "").str.replace("FARMACIA ", "").str.strip()
df['Producto'] = df['Producto'].fillna('Producto Desconocido').astype(str).str.strip()
df['serial'] = df['serial'].fillna('Sin Serial').astype(str).str.strip()

# Categorías
categorias = []
for dias in df['Dias de Inventario']:
    if pd.isna(dias):
        categorias.append('Sin Categoría')
    elif dias < 7:
        categorias.append('🔴 CRÍTICO (<7 días)')
    elif dias < 30:
        categorias.append('🟡 BAJO (7-29 días)')
    elif dias < 60:
        categorias.append('🟢 NORMAL (30-59 días)')
    else:
        categorias.append('⚫ EXCESO (≥60 días)')
df['Categoria_Dias'] = categorias

df = df[df['Producto'].str.strip() != '']

# Sidebar
st.sidebar.header("🔍 Filtros")
tiendas = ['📌 Todas'] + sorted(df['nombre'].unique().tolist())
proveedores = ['📌 Todos'] + sorted(df['PROVEEDOR'].unique().tolist())
categorias_lista = ['📌 Todas', '🔴 CRÍTICO (<7 días)', '🟡 BAJO (7-29 días)', '🟢 NORMAL (30-59 días)', '⚫ EXCESO (≥60 días)']

tienda_sel = st.sidebar.selectbox("🏪 Tienda", tiendas)
proveedor_sel = st.sidebar.selectbox("🏭 Proveedor", proveedores)
categoria_sel = st.sidebar.selectbox("📊 Categoría", categorias_lista)

# Filtrar
df_filtrado = df.copy()
if tienda_sel != '📌 Todas':
    df_filtrado = df_filtrado[df_filtrado['nombre'] == tienda_sel]
if proveedor_sel != '📌 Todos':
    df_filtrado = df_filtrado[df_filtrado['PROVEEDOR'] == proveedor_sel]
if categoria_sel != '📌 Todas':
    df_filtrado = df_filtrado[df_filtrado['Categoria_Dias'] == categoria_sel]

# KPIs
col1, col2, col3, col4 = st.columns(4)
col1.metric("📦 Productos", df_filtrado['Producto'].nunique())
col2.metric("🏪 Tiendas", df_filtrado['nombre'].nunique())
col3.metric("📊 Stock Total", f"{int(df_filtrado['Stock Actual'].sum()):,}")
col4.metric("⏱️ Días Promedio", f"{df_filtrado['Dias de Inventario'].mean():.1f}")

st.markdown("---")

# Críticos
st.subheader("⚠️ Productos Críticos (<7 días)")
criticos = df_filtrado[df_filtrado['Dias de Inventario'] < 7]
if not criticos.empty:
    st.warning(f"{len(criticos)} productos críticos")
    st.dataframe(criticos[['nombre', 'serial', 'Producto', 'Stock Actual', 'Dias de Inventario']].head(20))
else:
    st.success("✅ No hay productos críticos")

st.markdown("---")

# Gráficos
if not df_filtrado.empty:
    dist = df_filtrado['Categoria_Dias'].value_counts().reset_index()
    dist.columns = ['Categoría', 'Cantidad']
    dist['Porcentaje'] = (dist['Cantidad'] / dist['Cantidad'].sum() * 100).round(1)
    dist['Texto'] = dist['Cantidad'].astype(str) + ' (' + dist['Porcentaje'].astype(str) + '%)'
    
    color_map = {
        '🔴 CRÍTICO (<7 días)': '#dc3545',
        '🟡 BAJO (7-29 días)': '#fd7e14',
        '🟢 NORMAL (30-59 días)': '#28a745',
        '⚫ EXCESO (≥60 días)': '#6c757d'
    }
    
    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(dist, x='Categoría', y='Cantidad', text='Texto', color='Categoría', color_discrete_map=color_map, height=450)
        fig.update_traces(textposition='outside')
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.pie(dist, values='Cantidad', names='Categoría', color='Categoría', color_discrete_map=color_map, hole=0.3, height=450)
        fig.update_traces(textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Stock por categoría
    stock_cat = df_filtrado.groupby('Categoria_Dias')['Stock Actual'].sum().reset_index()
    stock_cat['Porcentaje'] = (stock_cat['Stock Actual'] / stock_cat['Stock Actual'].sum() * 100).round(1)
    stock_cat['Texto'] = stock_cat['Stock Actual'].apply(lambda x: f"{int(x):,}") + ' (' + stock_cat['Porcentaje'].astype(str) + '%)'
    fig = px.bar(stock_cat, x='Categoria_Dias', y='Stock Actual', text='Texto', color='Categoria_Dias', color_discrete_map=color_map, height=450)
    fig.update_traces(textposition='outside')
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Tabla detalle
    st.subheader("📋 Detalle de Productos")
    orden = st.selectbox("Ordenar por", ["Días (menor a mayor)", "Días (mayor a menor)", "Stock (mayor a menor)"])
    top = st.number_input("Mostrar top N", 10, 200, 50)
    
    tabla = df_filtrado[['nombre', 'serial', 'Producto', 'Stock Actual', 'Dias de Inventario', 'Categoria_Dias']].copy()
    tabla.columns = ['Tienda', 'SKU', 'Producto', 'Stock', 'Días', 'Categoría']
    
    if orden == "Días (menor a mayor)":
        tabla = tabla.nsmallest(top, 'Días')
    elif orden == "Días (mayor a menor)":
        tabla = tabla.nlargest(top, 'Días')
    else:
        tabla = tabla.nlargest(top, 'Stock')
    
    st.dataframe(tabla, use_container_width=True)
    
    csv = tabla.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Descargar CSV", csv, "inventario.csv", "text/csv")
    
    # Ranking tiendas
    if tienda_sel == '📌 Todas':
        st.markdown("---")
        st.subheader("🏪 Ranking de Tiendas")
        
        stock_tienda = df.groupby('nombre')['Stock Actual'].sum().reset_index().sort_values('Stock Actual', ascending=False)
        stock_tienda['Ranking'] = range(1, len(stock_tienda)+1)
        stock_tienda['Porcentaje'] = (stock_tienda['Stock Actual'] / stock_tienda['Stock Actual'].sum() * 100).round(1)
        stock_tienda['Texto'] = stock_tienda['Stock Actual'].apply(lambda x: f"{int(x):,}") + ' (' + stock_tienda['Porcentaje'].astype(str) + '%)'
        
        fig = px.bar(stock_tienda.head(10), x='nombre', y='Stock Actual', text='Texto', color='Stock Actual', color_continuous_scale='Blues', height=500)
        fig.update_traces(textposition='outside')
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
        
        # Ranking críticos
        criticos_tienda = df[df['Dias de Inventario'] < 7].groupby('nombre').size().reset_index(name='Críticos')
        todas = pd.DataFrame({'nombre': df['nombre'].unique()})
        criticos_tienda = todas.merge(criticos_tienda, on='nombre', how='left').fillna(0)
        criticos_tienda = criticos_tienda.sort_values('Críticos', ascending=False).head(10)
        criticos_tienda['Porcentaje'] = (criticos_tienda['Críticos'] / criticos_tienda['Críticos'].sum() * 100).round(1) if criticos_tienda['Críticos'].sum() > 0 else 0
        criticos_tienda['Texto'] = criticos_tienda['Críticos'].astype(int).astype(str) + ' (' + criticos_tienda['Porcentaje'].astype(str) + '%)'
        
        fig2 = px.bar(criticos_tienda, x='nombre', y='Críticos', text='Texto', color='Críticos', color_continuous_scale='Reds', height=500)
        fig2.update_traces(textposition='outside')
        fig2.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig2, use_container_width=True)

st.success("✅ Dashboard listo")
