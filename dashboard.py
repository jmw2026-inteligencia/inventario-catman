import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Análisis de Inventario JMW - Productos CATMAN", layout="wide")

st.title("📊 Análisis de Inventario JMW - Productos CATMAN")

archivo = st.file_uploader("📂 Sube tu archivo Consolidado_Inventario_Catman.xlsx", type=["xlsx"])

if archivo is None:
    st.warning("Esperando archivo Excel...")
    st.stop()

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
condiciones = [
    df['Dias de Inventario'] < 7,
    (df['Dias de Inventario'] >= 7) & (df['Dias de Inventario'] < 30),
    (df['Dias de Inventario'] >= 30) & (df['Dias de Inventario'] < 60),
    df['Dias de Inventario'] >= 60
]
categorias = ['🔴 CRÍTICO (<7 días)', '🟡 BAJO (7-29 días)', '🟢 NORMAL (30-59 días)', '⚫ EXCESO (≥60 días)']
df['Categoria_Dias'] = 'Sin Categoría'
for cond, cat in zip(condiciones, categorias):
    df.loc[cond, 'Categoria_Dias'] = cat

df = df[df['Producto'].str.strip() != '']

# Sidebar
st.sidebar.header("🔍 Filtros")
tiendas = ['Todas'] + sorted(df['nombre'].unique().tolist())
proveedores = ['Todos'] + sorted(df['PROVEEDOR'].unique().tolist())
categorias_lista = ['Todas'] + categorias

tienda_sel = st.sidebar.selectbox("Tienda", tiendas)
proveedor_sel = st.sidebar.selectbox("Proveedor", proveedores)
categoria_sel = st.sidebar.selectbox("Categoría", categorias_lista)

# Filtrar
df_filtrado = df.copy()
if tienda_sel != 'Todas':
    df_filtrado = df_filtrado[df_filtrado['nombre'] == tienda_sel]
if proveedor_sel != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['PROVEEDOR'] == proveedor_sel]
if categoria_sel != 'Todas':
    df_filtrado = df_filtrado[df_filtrado['Categoria_Dias'] == categoria_sel]

# KPIs
col1, col2, col3, col4 = st.columns(4)
col1.metric("📦 Productos", df_filtrado['Producto'].nunique())
col2.metric("🏪 Tiendas", df_filtrado['nombre'].nunique())
col3.metric("📊 Stock Total", f"{int(df_filtrado['Stock Actual'].sum()):,}")
col4.metric("⏱️ Días Promedio", f"{df_filtrado['Dias de Inventario'].mean():.1f}")

st.markdown("---")

# Productos críticos
st.subheader("⚠️ Productos Críticos (<7 días)")
criticos = df_filtrado[df_filtrado['Dias de Inventario'] < 7]
if not criticos.empty:
    st.warning(f"{len(criticos)} productos críticos")
    st.dataframe(criticos[['nombre', 'serial', 'Producto', 'Stock Actual', 'Dias de Inventario']].head(20))
else:
    st.success("No hay productos críticos")

st.markdown("---")

# Gráficos
if not df_filtrado.empty:
    distribucion = df_filtrado['Categoria_Dias'].value_counts().reset_index()
    distribucion.columns = ['Categoría', 'Cantidad']
    distribucion['Porcentaje'] = (distribucion['Cantidad'] / distribucion['Cantidad'].sum() * 100).round(1)
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.bar(distribucion, x='Categoría', y='Cantidad', text=distribucion['Cantidad'].astype(str) + ' (' + distribucion['Porcentaje'].astype(str) + '%)', height=400)
        fig.update_traces(textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.pie(distribucion, values='Cantidad', names='Categoría', hole=0.3, height=400)
        fig.update_traces(textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)

st.success("✅ Dashboard listo - Sube tu archivo Excel para comenzar")
