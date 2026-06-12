import streamlit as st
import pandas as pd
import subprocess
import sys

# INSTALAR PLOTLY MANUALMENTE
try:
    import plotly.express as px
    import plotly.graph_objects as go
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "plotly"])
    import plotly.express as px
    import plotly.graph_objects as go

st.set_page_config(page_title="Análisis de Inventario JMW - Productos CATMAN", layout="wide")

st.title("📊 Análisis de Inventario JMW - Productos CATMAN")
st.markdown("---")

archivo = st.file_uploader("📂 Sube tu archivo Consolidado_Inventario_Catman.xlsx", type=["xlsx"])

if archivo is None:
    st.info("Esperando archivo Excel...")
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
def categoria(dias):
    if pd.isna(dias):
        return 'Sin Categoría'
    elif dias < 7:
        return '🔴 CRÍTICO (<7 días)'
    elif dias < 30:
        return '🟡 BAJO (7-29 días)'
    elif dias < 60:
        return '🟢 NORMAL (30-59 días)'
    else:
        return '⚫ EXCESO (≥60 días)'

df['Categoria_Dias'] = df['Dias de Inventario'].apply(categoria)

# Sidebar
st.sidebar.header("🔍 Filtros")
tiendas = ['📌 Todas'] + sorted(df['nombre'].unique().tolist())
proveedores = ['📌 Todos'] + sorted(df['PROVEEDOR'].unique().tolist())
categorias = ['📌 Todas', '🔴 CRÍTICO (<7 días)', '🟡 BAJO (7-29 días)', '🟢 NORMAL (30-59 días)', '⚫ EXCESO (≥60 días)']

tienda_sel = st.sidebar.selectbox("Tienda", tiendas)
proveedor_sel = st.sidebar.selectbox("Proveedor", proveedores)
categoria_sel = st.sidebar.selectbox("Categoría", categorias)

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
col1.metric("Productos", df_filtrado['Producto'].nunique())
col2.metric("Tiendas", df_filtrado['nombre'].nunique())
col3.metric("Stock Total", f"{int(df_filtrado['Stock Actual'].sum()):,}")
col4.metric("Días Promedio", f"{df_filtrado['Dias de Inventario'].mean():.1f}")

st.markdown("---")

# Productos críticos
st.subheader("⚠️ Productos Críticos (<7 días)")
criticos = df_filtrado[df_filtrado['Dias de Inventario'] < 7]
if not criticos.empty:
    st.warning(f"{len(criticos)} productos críticos")
    st.dataframe(criticos[['nombre', 'serial', 'Producto', 'Stock Actual', 'Dias de Inventario']].head(20))
else:
    st.success("No hay productos críticos")

st.success("✅ Sube tu archivo Excel para comenzar")
