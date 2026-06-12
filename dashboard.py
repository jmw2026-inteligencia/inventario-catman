# dashboard_streamlit.py - VERSIÓN FINAL FUNCIONAL
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# Configuración de la página
st.set_page_config(
    page_title="Análisis de Inventario JMW - Productos CATMAN",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título principal
st.title("📊 Análisis de Inventario JMW - Productos CATMAN")
st.markdown("---")

def limpiar_nombre_tienda(nombre):
    """Limpia el nombre de la tienda - versión simple sin errores"""
    if pd.isna(nombre):
        return "Sin Nombre"
    nombre = str(nombre)
    # Reemplazar "Farmacia " por vacío
    nombre = nombre.replace("Farmacia ", "").replace("FARMACIA ", "").replace("farmacia ", "")
    nombre = nombre.replace("Farmacia", "").replace("FARMACIA", "").replace("farmacia", "")
    # Limpiar espacios
    nombre = nombre.strip()
    if not nombre or nombre == '':
        return "Tienda"
    return nombre

@st.cache_data
def cargar_datos():
    """Carga los datos del Excel generado"""
    archivo = 'Consolidado_Inventario_Catman.xlsx'
    if os.path.exists(archivo):
        try:
            df = pd.read_excel(archivo, sheet_name='1_Consolidado_Total')
            
            # Limpiar y preparar datos
            df['Dias de Inventario'] = pd.to_numeric(df['Dias de Inventario'], errors='coerce')
            df['Stock Actual'] = pd.to_numeric(df['Stock Actual'], errors='coerce')
            
            df['PROVEEDOR'] = df['PROVEEDOR'].fillna('Sin Proveedor')
            df['PROVEEDOR'] = df['PROVEEDOR'].astype(str).str.strip()
            
            # LIMPIAR NOMBRES DE TIENDAS
            df['nombre_original'] = df['nombre'].fillna('Sin Tienda')
            df['nombre_original'] = df['nombre_original'].astype(str).str.strip()
            df['nombre'] = df['nombre_original'].apply(limpiar_nombre_tienda)
            
            df['Producto'] = df['Producto'].fillna('Producto Desconocido')
            df['Producto'] = df['Producto'].astype(str).str.strip()
            df['serial'] = df['serial'].fillna('Sin Serial')
            df['serial'] = df['serial'].astype(str).str.strip()
            
            # Crear categorías (ordenadas correctamente)
            condiciones = [
                df['Dias de Inventario'] < 7,
                (df['Dias de Inventario'] >= 7) & (df['Dias de Inventario'] < 30),
                (df['Dias de Inventario'] >= 30) & (df['Dias de Inventario'] < 60),
                df['Dias de Inventario'] >= 60
            ]
            categorias = ['🔴 CRÍTICO (<7 días)', 
                          '🟡 BAJO (7-29 días)', 
                          '🟢 NORMAL (30-59 días)', 
                          '⚫ EXCESO (≥60 días)']
            
            df['Categoria_Dias'] = 'Sin Categoría'
            for cond, cat in zip(condiciones, categorias):
                df.loc[cond, 'Categoria_Dias'] = cat
            
            df = df[df['Producto'].str.strip() != '']
            df = df[df['Producto'] != 'Producto Desconocido']
            
            return df
        except Exception as e:
            st.error(f"Error al cargar datos: {str(e)}")
            return None
    else:
        st.error("No se encontró el archivo Consolidado_Inventario_Catman.xlsx")
        st.info("Ejecuta primero el script principal para generar el archivo")
        return None

def main():
    # Cargar datos
    df = cargar_datos()
    
    if df is None or df.empty:
        st.warning("⚠️ No se pudieron cargar los datos. Verifica que el archivo Excel exista y tenga datos.")
        return
    
    # Sidebar con filtros
    st.sidebar.header("🔍 Filtros Interactivos")
    st.sidebar.markdown("---")
    
    # Obtener valores únicos
    tiendas_unicas = sorted(df['nombre'].unique().tolist())
    proveedores_unicos = sorted([p for p in df['PROVEEDOR'].unique().tolist() if p and p != 'Sin Proveedor'])
    
    # Orden correcto de categorías
    orden_categorias = ['🔴 CRÍTICO (<7 días)', 
                        '🟡 BAJO (7-29 días)', 
                        '🟢 NORMAL (30-59 días)', 
                        '⚫ EXCESO (≥60 días)']
    categorias_unicas = [c for c in orden_categorias if c in df['Categoria_Dias'].unique()]
    
    # Filtros
    tienda_seleccionada = st.sidebar.selectbox("🏪 Seleccionar Tienda", ['📌 Todas las Tiendas'] + tiendas_unicas)
    proveedor_seleccionado = st.sidebar.selectbox("🏭 Seleccionar Proveedor", ['📌 Todos'] + proveedores_unicos)
    categoria_seleccionada = st.sidebar.selectbox("📊 Seleccionar Categoría", ['📌 Todas'] + categorias_unicas)
    
    # Aplicar filtros
    df_filtrado = df.copy()
    
    if tienda_seleccionada != '📌 Todas las Tiendas':
        df_filtrado = df_filtrado[df_filtrado['nombre'] == tienda_seleccionada]
    
    if proveedor_seleccionado != '📌 Todos':
        df_filtrado = df_filtrado[df_filtrado['PROVEEDOR'] == proveedor_seleccionado]
    
    if categoria_seleccionada != '📌 Todas':
        df_filtrado = df_filtrado[df_filtrado['Categoria_Dias'] == categoria_seleccionada]
    
    # Mostrar filtros activos
    filtros_activos = []
    if tienda_seleccionada != '📌 Todas las Tiendas':
        filtros_activos.append(f'Tienda: **{tienda_seleccionada}**')
    if proveedor_seleccionado != '📌 Todos':
        filtros_activos.append(f'Proveedor: **{proveedor_seleccionado}**')
    if categoria_seleccionada != '📌 Todas':
        filtros_activos.append(f'Categoría: **{categoria_seleccionada}**')
    
    if filtros_activos:
        st.info(f"🔍 **Filtros activos:** {', '.join(filtros_activos)}")
    
    # ==================== KPI CARDS ====================
    st.subheader("📈 Indicadores Clave")
    col1, col2, col3, col4 = st.columns(4)
    
    total_productos = df_filtrado['Producto'].nunique()
    total_tiendas = df_filtrado['nombre'].nunique()
    stock_total = int(df_filtrado['Stock Actual'].sum())
    dias_promedio = df_filtrado['Dias de Inventario'].mean()
    
    with col1:
        st.metric("📦 Total Productos", f"{total_productos:,}")
    with col2:
        st.metric("🏪 Total Tiendas", f"{total_tiendas:,}")
    with col3:
        st.metric("📊 Stock Total", f"{stock_total:,}")
    with col4:
        if pd.notna(dias_promedio):
            st.metric("⏱️ Días Promedio", f"{dias_promedio:.1f} días")
    
    st.markdown("---")
    
    # ==================== PRODUCTOS CRÍTICOS ====================
    st.subheader("⚠️ Productos con Inventario Crítico (Menos de 7 días)")
    
    productos_criticos = df_filtrado[df_filtrado['Dias de Inventario'] < 7].copy()
    
    if not productos_criticos.empty:
        st.warning(f"🔴 Se encontraron {len(productos_criticos)} productos con menos de 7 días")
        
        df_criticos = productos_criticos[['nombre', 'serial', 'Producto', 'PROVEEDOR', 'Stock Actual', 'Dias de Inventario']].copy()
        df_criticos.columns = ['Tienda', 'SKU', 'Producto', 'Proveedor', 'Stock', 'Días']
        df_criticos = df_criticos.sort_values('Días')
        
        st.dataframe(df_criticos.head(20), use_container_width=True)
        if len(df_criticos) > 20:
            st.info(f"Mostrando 20 de {len(df_criticos)} productos")
    else:
        st.success("✅ No hay productos críticos")
    
    st.markdown("---")
    
    # ==================== GRÁFICOS PRINCIPALES ====================
    if not df_filtrado.empty:
        distribucion = df_filtrado['Categoria_Dias'].value_counts().reset_index()
        distribucion.columns = ['Categoría', 'Cantidad']
        distribucion['Categoria'] = pd.Categorical(distribucion['Categoría'], categories=orden_categorias, ordered=True)
        distribucion = distribucion.sort_values('Categoria')
        
        total = distribucion['Cantidad'].sum()
        if total > 0:
            distribucion['Porcentaje'] = (distribucion['Cantidad'] / total * 100).round(1)
            distribucion['Texto'] = distribucion['Cantidad'].astype(str) + ' (' + distribucion['Porcentaje'].astype(str) + '%)'
            
            color_map = {
                '🔴 CRÍTICO (<7 días)': '#dc3545',
                '🟡 BAJO (7-29 días)': '#fd7e14',
                '🟢 NORMAL (30-59 días)': '#28a745',
                '⚫ EXCESO (≥60 días)': '#6c757d'
            }
            
            # Gráfico de barras
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📊 Distribución por Categoría")
                fig = px.bar(distribucion, x='Categoría', y='Cantidad', text='Texto',
                             color='Categoría', color_discrete_map=color_map, height=450)
                fig.update_traces(textposition='outside')
                fig.update_layout(showlegend=False, xaxis_title="Categoría", yaxis_title="Número de Productos")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.subheader("📈 Distribución Porcentual")
                fig_pie = px.pie(distribucion, values='Cantidad', names='Categoría',
                                 color='Categoría', color_discrete_map=color_map, hole=0.3, height=450)
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_pie, use_container_width=True)
            
            st.markdown("---")
            
            # Stock por categoría
            st.subheader("💰 Stock por Categoría")
            stock_categoria = df_filtrado.groupby('Categoria_Dias')['Stock Actual'].sum().reset_index()
            stock_categoria.columns = ['Categoría', 'Stock']
            stock_categoria['Categoria'] = pd.Categorical(stock_categoria['Categoría'], categories=orden_categorias, ordered=True)
            stock_categoria = stock_categoria.sort_values('Categoria')
            
            total_stock = stock_categoria['Stock'].sum()
            if total_stock > 0:
                stock_categoria['Porcentaje'] = (stock_categoria['Stock'] / total_stock * 100).round(1)
                stock_categoria['Texto'] = stock_categoria['Stock'].apply(lambda x: f"{int(x):,}") + ' (' + stock_categoria['Porcentaje'].astype(str) + '%)'
                
                fig_stock = px.bar(stock_categoria, x='Categoría', y='Stock', text='Texto',
                                   color='Categoría', color_discrete_map=color_map, height=450)
                fig_stock.update_traces(textposition='outside')
                fig_stock.update_layout(showlegend=False, xaxis_title="Categoría", yaxis_title="Stock Total")
                st.plotly_chart(fig_stock, use_container_width=True)
            
            st.markdown("---")
            
            # Tabla de productos
            st.subheader("📋 Detalle de Productos")
            col1, col2 = st.columns(2)
            with col1:
                ordenar_por = st.selectbox("Ordenar por:", ["Días (menor a mayor)", "Días (mayor a menor)", "Stock (mayor a menor)"])
            with col2:
                mostrar_top = st.number_input("Mostrar top N", min_value=10, max_value=200, value=50)
            
            df_tabla = df_filtrado[['nombre', 'serial', 'PROVEEDOR', 'Producto', 'Stock Actual', 'Dias de Inventario', 'Categoria_Dias']].copy()
            df_tabla.columns = ['Tienda', 'SKU', 'Proveedor', 'Producto', 'Stock', 'Días', 'Categoría']
            
            if ordenar_por == "Días (menor a mayor)":
                df_tabla = df_tabla.nsmallest(mostrar_top, 'Días')
            elif ordenar_por == "Días (mayor a menor)":
                df_tabla = df_tabla.nlargest(mostrar_top, 'Días')
            else:
                df_tabla = df_tabla.nlargest(mostrar_top, 'Stock')
            
            st.dataframe(df_tabla, use_container_width=True, height=400)
            
            csv = df_tabla.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Descargar CSV", data=csv, file_name="inventario_filtrado.csv", mime="text/csv")
            
            # ==================== GRÁFICOS DE TIENDAS ====================
            if tienda_seleccionada == '📌 Todas las Tiendas':
                st.markdown("---")
                st.subheader("🏪 Análisis de Tiendas")
                
                # Ranking de Stock
                with st.expander("📊 Ranking de Tiendas por Stock Total", expanded=True):
                    stock_por_tienda = df.groupby('nombre')['Stock Actual'].sum().reset_index()
                    stock_por_tienda = stock_por_tienda.sort_values('Stock Actual', ascending=False)
                    stock_por_tienda['Stock Actual'] = stock_por_tienda['Stock Actual'].astype(int)
                    stock_por_tienda['Ranking'] = range(1, len(stock_por_tienda) + 1)
                    stock_por_tienda['Porcentaje'] = (stock_por_tienda['Stock Actual'] / stock_por_tienda['Stock Actual'].sum() * 100).round(1)
                    stock_por_tienda['Texto'] = stock_por_tienda['Stock Actual'].apply(lambda x: f"{x:,}") + ' (' + stock_por_tienda['Porcentaje'].astype(str) + '%)'
                    
                    fig = px.bar(stock_por_tienda, x='nombre', y='Stock Actual', text='Texto',
                                 color='Stock Actual', color_continuous_scale='Blues', height=500)
                    fig.update_traces(textposition='outside')
                    fig.update_layout(xaxis_tickangle=-45, xaxis_title="Tienda", yaxis_title="Stock Total")
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.dataframe(stock_por_tienda[['Ranking', 'nombre', 'Stock Actual', 'Porcentaje']], use_container_width=True)
                
                # Ranking de Críticos
                with st.expander("⚠️ Ranking de Tiendas por Productos Críticos", expanded=True):
                    criticos_por_tienda = df[df['Dias de Inventario'] < 7].groupby('nombre').size().reset_index(name='Críticos')
                    todas_tiendas = pd.DataFrame({'nombre': tiendas_unicas})
                    criticos_por_tienda = todas_tiendas.merge(criticos_por_tienda, on='nombre', how='left').fillna(0)
                    criticos_por_tienda['Críticos'] = criticos_por_tienda['Críticos'].astype(int)
                    criticos_por_tienda = criticos_por_tienda.sort_values('Críticos', ascending=False)
                    criticos_por_tienda['Ranking'] = range(1, len(criticos_por_tienda) + 1)
                    
                    total_criticos = criticos_por_tienda['Críticos'].sum()
                    if total_criticos > 0:
                        criticos_por_tienda['Porcentaje'] = (criticos_por_tienda['Críticos'] / total_criticos * 100).round(1)
                        criticos_por_tienda['Texto'] = criticos_por_tienda['Críticos'].astype(str) + ' (' + criticos_por_tienda['Porcentaje'].astype(str) + '%)'
                    else:
                        criticos_por_tienda['Texto'] = criticos_por_tienda['Críticos'].astype(str)
                    
                    fig = px.bar(criticos_por_tienda, x='nombre', y='Críticos', text='Texto',
                                 color='Críticos', color_continuous_scale='Reds', height=500)
                    fig.update_traces(textposition='outside')
                    fig.update_layout(xaxis_tickangle=-45, xaxis_title="Tienda", yaxis_title="Productos Críticos")
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.dataframe(criticos_por_tienda[['Ranking', 'nombre', 'Críticos', 'Porcentaje']], use_container_width=True)
    
    else:
        st.warning("⚠️ No hay datos con los filtros seleccionados")
    
    st.markdown("---")
    st.markdown("*Dashboard desarrollado para JMW - Productos CATMAN*")

if __name__ == "__main__":
    main()