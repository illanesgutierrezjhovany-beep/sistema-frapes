from datetime import datetime
import io
import json
import os
import zoneinfo
import pandas as pd
import openpyxl
from openpyxl.chart import BarChart, DoughnutChart, LineChart, PieChart, Reference, ScatterChart, Series
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Configuración de zona horaria de Bolivia (BOT - GMT-4)
ZONA_BOLIVIA = zoneinfo.ZoneInfo("America/La_Paz")


def obtener_hora_bo():
    return datetime.now(ZONA_BOLIVIA)


# Configuración de la página Streamlit
st.set_page_config(
    page_title="Sistema POS & Executive Analytics - Frappés",
    page_icon="🥤",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Estilos CSS Personalizados
st.markdown(
    """
    <style>
    .stApp {
        background-color: #0d1117;
        color: #f0f6fc;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 800 !important;
        color: #00f2fe !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# Encabezado con hora oficial de Bolivia
ahora_bo = obtener_hora_bo()
fecha_bo_str = ahora_bo.strftime("%A, %d de %B de %Y").capitalize()
hora_bo_str = ahora_bo.strftime("%H:%M:%S")

col_rel1, col_rel2 = st.columns([3, 1])
with col_rel1:
    st.title("🥤 Sistema POS & Analytics - Frappés")
with col_rel2:
    st.metric(
        label=f"🇧🇴 Bolivia ({fecha_bo_str})",
        value=hora_bo_str,
        delta="Hora Oficial (GMT-4)",
    )

st.markdown("---")

# Base de datos local JSON
DATA_FILE = "sistema_datos.json"

DEFAULT_INVENTORY = {
    "Frappé Clásico Café": {
        "precio": 20.0,
        "costo": 7.0,
        "stock": 50,
        "categoria": "Frappés",
    },
    "Frappé Oreo Deluxe": {
        "precio": 25.0,
        "costo": 9.0,
        "stock": 40,
        "categoria": "Frappés",
    },
    "Frappé Caramel Macchiato": {
        "precio": 24.0,
        "costo": 8.5,
        "stock": 30,
        "categoria": "Frappés",
    },
    "Frappé Matcha Premium": {
        "precio": 28.0,
        "costo": 10.0,
        "stock": 25,
        "categoria": "Frappés",
    },
    "Bobas de Tapioca": {
        "precio": 5.0,
        "costo": 1.5,
        "stock": 100,
        "categoria": "Extras",
    },
    "Bobas Explosivas Frutilla": {
        "precio": 6.0,
        "costo": 2.0,
        "stock": 80,
        "categoria": "Extras",
    },
    "Chantilly Extra": {
        "precio": 3.0,
        "costo": 1.0,
        "stock": 60,
        "categoria": "Extras",
    },
}


def cargar_datos():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"inventario": DEFAULT_INVENTORY, "ventas": [], "contador_pedido": 1}


def guardar_datos():
    data = {
        "inventario": st.session_state.inventario,
        "ventas": st.session_state.ventas,
        "contador_pedido": st.session_state.contador_pedido,
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


if "datos_cargados" not in st.session_state:
    data = cargar_datos()
    st.session_state.inventario = data.get("inventario", DEFAULT_INVENTORY)
    st.session_state.ventas = data.get("ventas", [])
    st.session_state.contador_pedido = data.get("contador_pedido", 1)
    st.session_state.carrito = []
    st.session_state.datos_cargados = True

# Menú lateral
st.sidebar.title("🥤 Menú Principal")
opcion = st.sidebar.radio(
    "Selecciona una opción:",
    [
        "🛒 Registrar Venta",
        "📦 Inventario y stock",
        "📊 Panel de control e indicadores clave de rendimiento (KPI)",
        "📥 Exportar Suite BI Nivel Inversión (.XLSX)",
    ],
)

# ---------------------------------------------------------
# 1. REGISTRAR VENTA
# ---------------------------------------------------------
if opcion == "🛒 Registrar Venta":
    st.header("🛒 Registro POS de Ventas")

    col_cli1, col_cli2, col_cli3 = st.columns([2, 1, 1])
    with col_cli1:
        nombre_cliente = st.text_input(
            "Nombre del Cliente:", placeholder="Ej: Maria Lopez"
        )
    with col_cli2:
        tipo_servicio = st.selectbox(
            "Modalidad:", ["Para Llevar", "Para Comer Aquí"]
        )
    with col_cli3:
        metodo_pago = st.selectbox(
            "Método de Pago:", ["Efectivo", "QR / Transferencia", "Tarjeta"]
        )

    notas_pedido = st.text_input(
        "Indicaciones Especiales / Barista:",
        placeholder="Ej: Poco hielo, extra crema...",
    )

    st.markdown("---")
    st.subheader("Añadir Productos")

    cat_seleccionada = st.radio(
        "Categoría:", ["Todas", "Frappés", "Extras"], horizontal=True
    )

    items_filtrados = {
        k: v
        for k, v in st.session_state.inventario.items()
        if cat_seleccionada == "Todas" or v.get("categoria") == cat_seleccionada
    }

    if items_filtrados:
        col_prod1, col_prod2, col_prod3 = st.columns([2, 1, 1])

        with col_prod1:
            prod_nom = st.selectbox("Producto:", list(items_filtrados.keys()))

        info_prod = st.session_state.inventario[prod_nom]

        with col_prod2:
            st.caption(f"Stock: **{info_prod.get('stock', 0)}**")
            st.caption(f"Precio: **Bs. {info_prod.get('precio', 0.0):.2f}**")

        with col_prod3:
            cant = st.number_input(
                "Cantidad:",
                min_value=1,
                max_value=max(1, info_prod.get("stock", 1)),
                value=1,
            )

        if st.button("➕ Agregar al Carrito", use_container_width=True):
            if info_prod.get("stock", 0) < cant:
                st.error("❌ Stock insuficiente.")
            else:
                st.session_state.carrito.append(
                    {
                        "producto": prod_nom,
                        "cantidad": cant,
                        "precio": info_prod["precio"],
                        "costo": info_prod["costo"],
                        "subtotal": info_prod["precio"] * cant,
                        "costo_total": info_prod["costo"] * cant,
                        "ganancia_item": (
                            info_prod["precio"] - info_prod["costo"]
                        )
                        * cant,
                        "categoria": info_prod.get("categoria", "General"),
                    }
                )
                st.success(f"Agregado: {prod_nom} (x{cant})")

    if st.session_state.carrito:
        st.markdown("---")
        st.subheader("🛒 Resumen del Carrito")

        df_cart = pd.DataFrame(st.session_state.carrito)
        st.dataframe(
            df_cart[["producto", "cantidad", "precio", "subtotal"]],
            use_container_width=True,
        )

        subtotal_venta = sum(
            item["subtotal"] for item in st.session_state.carrito
        )
        costo_venta = sum(item["costo_total"] for item in st.session_state.carrito)

        st.markdown(f"### **Total a Cobrar: Bs. {subtotal_venta:.2f}**")

        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("✅ Confirmar y Registrar Venta", use_container_width=True):
                if not nombre_cliente.strip():
                    st.warning("⚠️ Ingresa el nombre del cliente.")
                else:
                    id_pedido = st.session_state.contador_pedido

                    for item in st.session_state.carrito:
                        st.session_state.inventario[item["producto"]][
                            "stock"
                        ] -= item["cantidad"]

                    venta_reg = {
                        "id": id_pedido,
                        "fecha": ahora_bo.strftime("%Y-%m-%d"),
                        "hora": ahora_bo.strftime("%H:%M:%S"),
                        "cliente": nombre_cliente,
                        "servicio": tipo_servicio,
                        "pago": metodo_pago,
                        "notas": (
                            notas_pedido
                            if notas_pedido
                            else "Sin especificación"
                        ),
                        "detalles": st.session_state.carrito.copy(),
                        "total_venta": subtotal_venta,
                        "costo_total": costo_venta,
                        "ganancia_neta": subtotal_venta - costo_venta,
                        "estado": "Completada",
                    }

                    st.session_state.ventas.append(venta_reg)
                    st.session_state.contador_pedido += 1
                    st.session_state.carrito = []
                    guardar_datos()
                    st.success(f"🎉 Venta #{id_pedido} registrada exitosamente.")
                    st.rerun()

        with col_b2:
            if st.button("🗑️ Vaciar Carrito", use_container_width=True):
                st.session_state.carrito = []
                st.rerun()

    st.markdown("---")
    st.subheader("📋 Ventas Recientes & Gestión de Pedidos")

    if st.session_state.ventas:
        df_ventas_hist = pd.DataFrame(st.session_state.ventas)
        cols_deseadas = [
            "id",
            "fecha",
            "hora",
            "cliente",
            "servicio",
            "pago",
            "total_venta",
            "estado",
        ]
        cols_existentes = [
            c for c in cols_deseadas if c in df_ventas_hist.columns
        ]

        st.dataframe(df_ventas_hist[cols_existentes], use_container_width=True)

        ids_disponibles = [
            v["id"]
            for v in st.session_state.ventas
            if isinstance(v, dict) and "id" in v
        ]

        if ids_disponibles:
            col_del1, col_del2 = st.columns([2, 1])

            with col_del1:
                id_a_eliminar = st.selectbox(
                    "Selecciona el ID de la Venta a Eliminar:",
                    options=ids_disponibles,
                    index=len(ids_disponibles) - 1,
                )

            with col_del2:
                st.write("")
                st.write("")
                if st.button("🗑️ Eliminar Venta", use_container_width=True):
                    venta_target = next(
                        (
                            v
                            for v in st.session_state.ventas
                            if v.get("id") == id_a_eliminar
                        ),
                        None,
                    )
                    if venta_target:
                        if venta_target.get("estado") == "Completada":
                            for item in venta_target.get("detalles", []):
                                if item["producto"] in st.session_state.inventario:
                                    st.session_state.inventario[
                                        item["producto"]
                                    ]["stock"] += item.get("cantidad", 0)

                        st.session_state.ventas = [
                            v
                            for v in st.session_state.ventas
                            if v.get("id") != id_a_eliminar
                        ]
                        guardar_datos()
                        st.success(
                            f"Venta #{id_a_eliminar} eliminada correctamente."
                        )
                        st.rerun()
    else:
        st.info("No hay registro de ventas en el sistema.")

# ---------------------------------------------------------
# 2. INVENTARIO Y STOCK
# ---------------------------------------------------------
elif opcion == "📦 Inventario y stock":
    st.header("📦 Control y Gestión de Stock")

    inv_list = [
        {"Producto": k, **v} for k, v in st.session_state.inventario.items()
    ]
    df_inv = pd.DataFrame(inv_list)

    st.dataframe(
        df_inv[["Producto", "categoria", "precio", "costo", "stock"]],
        use_container_width=True,
    )

    st.markdown("---")
    st.subheader("✏️ Gestión de Productos")

    tab1, tab2 = st.tabs(["Ajustar Stock", "Agregar Producto Nuevo"])

    with tab1:
        prod_edit = st.selectbox(
            "Seleccionar Producto:", list(st.session_state.inventario.keys())
        )
        nuevo_stock = st.number_input(
            "Nuevo Stock Disponible:",
            min_value=0,
            value=st.session_state.inventario[prod_edit]["stock"],
        )
        if st.button("Guardar Stock"):
            st.session_state.inventario[prod_edit]["stock"] = nuevo_stock
            guardar_datos()
            st.success("Stock actualizado.")
            st.rerun()

    with tab2:
        nuevo_nom = st.text_input("Nombre del Producto:")
        nueva_cat = st.selectbox("Categoría:", ["Frappés", "Extras"])
        nuevo_p = st.number_input("Precio Venta (Bs.):", min_value=0.0, value=20.0)
        nuevo_c = st.number_input(
            "Costo Producción (Bs.):", min_value=0.0, value=7.0
        )
        nuevo_s = st.number_input("Stock Inicial:", min_value=0, value=50)

        if st.button("Crear Producto"):
            if nuevo_nom:
                st.session_state.inventario[nuevo_nom] = {
                    "precio": nuevo_p,
                    "costo": nuevo_c,
                    "stock": nuevo_s,
                    "categoria": nueva_cat,
                }
                guardar_datos()
                st.success("Producto creado con éxito.")
                st.rerun()

# ---------------------------------------------------------
# 3. DASHBOARD Y ANALÍTICA EXECUTIVE BI
# ---------------------------------------------------------
elif opcion == "📊 Panel de control e indicadores clave de rendimiento (KPI)":
    st.header("🚀 Executive Business Intelligence & Analytics Dashboard")

    col_top1, col_top2 = st.columns([4, 1])
    with col_top2:
        if st.button("⚠️ Resetear BD", help="Limpia la base de datos de ventas"):
            st.session_state.ventas = []
            st.session_state.contador_pedido = 1
            guardar_datos()
            st.rerun()

    ventas_validas = [
        v
        for v in st.session_state.ventas
        if isinstance(v, dict)
        and v.get("estado") == "Completada"
        and "detalles" in v
    ]

    if not ventas_validas:
        st.info(
            "💡 No hay ventas registradas aún. Ve a '🛒 Registrar Venta' para añadir pedidos."
        )
    else:
        df_pedidos = pd.DataFrame(ventas_validas)
        detalles_list = []
        for v in ventas_validas:
            for item in v.get("detalles", []):
                detalles_list.append(
                    {
                        "ID_Pedido": v.get("id", 0),
                        "Fecha": v.get("fecha", ""),
                        "Hora_Exacta": v.get("hora", "00:00:00"),
                        "Hora_Entera": f"{str(v.get('hora', '00:00')).split(':')[0]}:00",
                        "Cliente": v.get("cliente", "Anónimo"),
                        "Servicio": v.get("servicio", "Para Llevar"),
                        "Metodo_Pago": v.get("pago", "Efectivo"),
                        "Producto": item.get("producto", "Desconocido"),
                        "Categoria": item.get("categoria", "Frappés"),
                        "Cantidad": item.get("cantidad", 1),
                        "Precio_Unit": item.get("precio", 0.0),
                        "Costo_Unit": item.get("costo", 0.0),
                        "Ingreso_Total": item.get("subtotal", 0.0),
                        "Costo_Total": item.get("costo_total", 0.0),
                        "Ganancia_Neta": item.get("subtotal", 0.0)
                        - item.get("costo_total", 0.0),
                    }
                )

        df_detalles = pd.DataFrame(detalles_list)

        tot_pedidos = len(df_pedidos)
        tot_ventas = (
            df_pedidos["total_venta"].sum()
            if "total_venta" in df_pedidos
            else 0.0
        )
        tot_costo = (
            df_pedidos["costo_total"].sum()
            if "costo_total" in df_pedidos
            else 0.0
        )
        ganancia_total = (
            df_pedidos["ganancia_neta"].sum()
            if "ganancia_neta" in df_pedidos
            else 0.0
        )
        margen_prom = (
            (ganancia_total / tot_ventas * 100) if tot_ventas > 0 else 0
        )
        total_items = (
            df_detalles["Cantidad"].sum() if not df_detalles.empty else 0
        )

        k1, k2, k3, k4, k5, k6 = st.columns(6)
        k1.metric("📦 Pedidos", f"{tot_pedidos}")
        k2.metric("💰 Ventas", f"Bs. {tot_ventas:.2f}")
        k3.metric("📉 Costos", f"Bs. {tot_costo:.2f}")
        k4.metric("🚀 Ganancia", f"Bs. {ganancia_total:.2f}")
        k5.metric("📊 Margen", f"{margen_prom:.1f}%")
        k6.metric("🥤 Items", f"{total_items}")

        st.markdown("---")

        col_c1, col_c2 = st.columns([3, 2])

        with col_c1:
            st.subheader("📈 Tendencia de Ventas y Ganancias")
            df_linea = (
                df_detalles.groupby("ID_Pedido")[
                    ["Ingreso_Total", "Ganancia_Neta"]
                ]
                .sum()
                .reset_index()
            )

            fig_line = go.Figure()
            fig_line.add_trace(
                go.Scatter(
                    x=df_linea["ID_Pedido"],
                    y=df_linea["Ingreso_Total"],
                    mode="lines+markers",
                    name="Ingreso (Bs.)",
                    line=dict(color="#00f2fe", width=3),
                )
            )
            fig_line.add_trace(
                go.Scatter(
                    x=df_linea["ID_Pedido"],
                    y=df_linea["Ganancia_Neta"],
                    mode="lines+markers",
                    name="Ganancia (Bs.)",
                    line=dict(color="#00ff87", width=3, dash="dash"),
                )
            )
            fig_line.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#f0f6fc"),
                height=300,
                margin=dict(l=10, r=10, t=10, b=10),
                legend=dict(orientation="h", y=1.15),
                xaxis=dict(showgrid=False, title="N° Pedido"),
                yaxis=dict(showgrid=True, gridcolor="#21262d", title="Bs."),
            )
            st.plotly_chart(fig_line, use_container_width=True)

        with col_c2:
            st.subheader("💳 Métodos de Pago")
            df_pago = (
                df_detalles.groupby("Metodo_Pago")["Ingreso_Total"]
                .sum()
                .reset_index()
            )
            fig_donut = px.pie(
                df_pago,
                values="Ingreso_Total",
                names="Metodo_Pago",
                hole=0.5,
                color_discrete_sequence=["#a855f7", "#00f2fe", "#ff007f"],
            )
            fig_donut.update_traces(textinfo="percent+label")
            fig_donut.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#f0f6fc"),
                height=300,
                margin=dict(l=10, r=10, t=10, b=10),
                showlegend=False,
            )
            st.plotly_chart(fig_donut, use_container_width=True)

        st.markdown("---")

        col_c3, col_c4 = st.columns([3, 2])

        with col_c3:
            st.subheader("📊 Ingresos vs Costos por Producto")
            df_prod = (
                df_detalles.groupby("Producto")[
                    ["Ingreso_Total", "Costo_Total"]
                ]
                .sum()
                .reset_index()
            )

            fig_bar_prod = go.Figure()
            fig_bar_prod.add_trace(
                go.Bar(
                    x=df_prod["Producto"],
                    y=df_prod["Ingreso_Total"],
                    name="Ingreso",
                    marker_color="#00f2fe",
                )
            )
            fig_bar_prod.add_trace(
                go.Bar(
                    x=df_prod["Producto"],
                    y=df_prod["Costo_Total"],
                    name="Costo",
                    marker_color="#ff4757",
                )
            )
            fig_bar_prod.update_layout(
                barmode="group",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#f0f6fc"),
                height=300,
                margin=dict(l=10, r=10, t=10, b=10),
                legend=dict(orientation="h", y=1.15),
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor="#21262d"),
            )
            st.plotly_chart(fig_bar_prod, use_container_width=True)

        with col_c4:
            st.subheader("⏰ Ventas por Horas")
            df_hora = (
                df_detalles.groupby("Hora_Entera")["Ingreso_Total"]
                .sum()
                .reset_index()
            )

            fig_hora = px.bar(
                df_hora,
                x="Hora_Entera",
                y="Ingreso_Total",
                text="Ingreso_Total",
                color_discrete_sequence=["#ff007f"],
            )
            fig_hora.update_traces(
                texttemplate="Bs. %{text:.0f}", textposition="outside"
            )
            fig_hora.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#f0f6fc"),
                height=300,
                margin=dict(l=10, r=10, t=10, b=10),
                xaxis=dict(showgrid=False, title="Hora"),
                yaxis=dict(showgrid=True, gridcolor="#21262d", title="Bs."),
            )
            st.plotly_chart(fig_hora, use_container_width=True)

# ---------------------------------------------------------
# 4. EXPORTAR SUITE BI EXECUTIVE ULTRAMEGA DE INVERSIÓN
# ---------------------------------------------------------
elif opcion == "📥 Exportar Suite BI Nivel Inversión (.XLSX)":
    st.header("📥 Central de Inteligencia de Negocios & Dashboard BI (.XLSX)")
    st.write(
        "Genera un libro interactivo multi-pestaña nivel **Inversión Corporativa**: incluye Dashboard Maestro BI con paneles laterales en vivo, tarjetas KPI ejecutivas, análisis de ROI, tendencias por horario y 5 gráficos estratégicos incrustados."
    )

    ventas_validas = [
        v
        for v in st.session_state.ventas
        if isinstance(v, dict) and v.get("estado") == "Completada"
    ]

    if not ventas_validas:
        st.info(
            "💡 Registra al menos una venta para poder generar la Suite de Inteligencia de Negocios."
        )
    else:
        detalles_list = []
        for v in ventas_validas:
            for item in v.get("detalles", []):
                hora_str = str(v.get("hora", "00:00"))
                hora_entera = f"{hora_str.split(':')[0]}:00"
                detalles_list.append(
                    {
                        "ID_Pedido": v.get("id"),
                        "Fecha": v.get("fecha"),
                        "Hora": v.get("hora"),
                        "Hora_Entera": hora_entera,
                        "Cliente": v.get("cliente"),
                        "Modalidad": v.get("servicio"),
                        "Metodo_Pago": v.get("pago"),
                        "Producto": item.get("producto"),
                        "Categoria": item.get("categoria"),
                        "Cantidad": item.get("cantidad"),
                        "Precio_Unitario": item.get("precio"),
                        "Costo_Unitario": item.get("costo"),
                        "Ingreso_Total": item.get("subtotal"),
                        "Costo_Total": item.get("costo_total"),
                        "Ganancia_Neta": item.get("ganancia_item"),
                    }
                )

        df_detalles = pd.DataFrame(detalles_list)

        # Tablas Agrupadas Corporativas
        df_res_diario = (
            df_detalles.groupby("Fecha", as_index=False)
            .agg(
                Total_Pedidos=("ID_Pedido", "nunique"),
                Unidades_Vendidas=("Cantidad", "sum"),
                Ingresos_Totales=("Ingreso_Total", "sum"),
                Costos_Totales=("Costo_Total", "sum"),
                Utilidad_Neta=("Ganancia_Neta", "sum"),
            )
        )
        df_res_diario["Margen_%"] = (df_res_diario["Utilidad_Neta"] / df_res_diario["Ingresos_Totales"]).fillna(0)

        df_res_prod = (
            df_detalles.groupby(["Producto", "Categoria"], as_index=False)
            .agg(
                Cantidad_Total=("Cantidad", "sum"),
                Ingresos_Totales=("Ingreso_Total", "sum"),
                Costos_Totales=("Costo_Total", "sum"),
                Ganancia_Neta=("Ganancia_Neta", "sum"),
            )
        )
        df_res_prod["Margen_%"] = (df_res_prod["Ganancia_Neta"] / df_res_prod["Ingresos_Totales"]).fillna(0)
        
        tot_ing_global = df_res_prod["Ingresos_Totales"].sum()
        df_res_prod["%_Participacion"] = (df_res_prod["Ingresos_Totales"] / tot_ing_global).fillna(0) if tot_ing_global > 0 else 0

        df_res_roi = df_res_prod[["Producto", "Categoria", "Ingresos_Totales", "Costos_Totales", "Ganancia_Neta", "Margen_%"]].copy()
        df_res_roi["ROI_%"] = (df_res_roi["Ganancia_Neta"] / df_res_roi["Costos_Totales"]).fillna(0)

        df_res_pedidos = (
            df_detalles.groupby(
                ["ID_Pedido", "Fecha", "Hora", "Cliente", "Modalidad", "Metodo_Pago"],
                as_index=False,
            )
            .agg(
                Items_Totales=("Cantidad", "sum"),
                Ingreso_Pedido=("Ingreso_Total", "sum"),
                Costo_Pedido=("Costo_Total", "sum"),
                Ganancia_Pedido=("Ganancia_Neta", "sum"),
            )
        )

        df_res_pagos = (
            df_detalles.groupby("Metodo_Pago", as_index=False)
            .agg(
                Transacciones=("ID_Pedido", "nunique"),
                Recaudacion=("Ingreso_Total", "sum"),
            )
        )

        df_res_cat = (
            df_detalles.groupby("Categoria", as_index=False)
            .agg(
                Unidades=("Cantidad", "sum"),
                Ingresos=("Ingreso_Total", "sum")
            )
        )

        df_res_hora = (
            df_detalles.groupby("Hora_Entera", as_index=False)
            .agg(
                Pedidos=("ID_Pedido", "nunique"),
                Ingresos=("Ingreso_Total", "sum")
            )
        )

        st.success("✅ Modelo BI Corporativo cargado e integrado.")

        if st.button("🚀 Generar Suite BI Corporativa Nivel Inversión", use_container_width=True):
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                # 1. Escribir todas las hojas analíticas
                df_res_diario.to_excel(writer, sheet_name="Reporte del Día", index=False)
                df_res_prod.to_excel(writer, sheet_name="Rendimiento Productos", index=False)
                df_res_roi.to_excel(writer, sheet_name="Análisis Margen & ROI", index=False)
                df_res_cat.to_excel(writer, sheet_name="Ventas Categoria", index=False)
                df_res_hora.to_excel(writer, sheet_name="Tendencia Horaria", index=False)
                df_res_pagos.to_excel(writer, sheet_name="Flujo por Pago", index=False)
                df_res_pedidos.to_excel(writer, sheet_name="Auditoria de Pedidos", index=False)
                df_detalles.to_excel(writer, sheet_name="Transacciones Maestro", index=False)

                workbook = writer.book

                # Estilizador Corporativo Premium
                def aplicar_estilo_corporativo(ws, df, titulo_hoja):
                    ws.views.sheetView[0].showGridLines = True
                    fill_title = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid")
                    fill_header = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
                    fill_zebra = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
                    
                    font_title = Font(name="Calibri", size=15, bold=True, color="FFFFFF")
                    font_header = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
                    font_normal = Font(name="Calibri", size=11, color="0F172A")
                    
                    border_grid = Border(
                        left=Side(style='thin', color='E2E8F0'),
                        right=Side(style='thin', color='E2E8F0'),
                        top=Side(style='thin', color='E2E8F0'),
                        bottom=Side(style='thin', color='E2E8F0')
                    )

                    ws.insert_rows(1, 2)
                    max_col = len(df.columns)
                    max_col_letter = get_column_letter(max_col)
                    
                    ws.merge_cells(f"A1:{max_col_letter}1")
                    c_title = ws["A1"]
                    c_title.value = f"💼 {titulo_hoja.upper()} - SUITE DE INVERSIÓN"
                    c_title.font = font_title
                    c_title.fill = fill_title
                    c_title.alignment = Alignment(horizontal="center", vertical="center")
                    ws.row_dimensions[1].height = 38

                    ws.row_dimensions[3].height = 24
                    for col_num in range(1, max_col + 1):
                        cell = ws.cell(row=3, column=col_num)
                        cell.font = font_header
                        cell.fill = fill_header
                        cell.alignment = Alignment(horizontal="center", vertical="center")

                    for row_num in range(4, len(df) + 4):
                        ws.row_dimensions[row_num].height = 20
                        is_even = (row_num % 2 == 0)
                        for col_num in range(1, max_col + 1):
                            cell = ws.cell(row=row_num, column=col_num)
                            cell.font = font_normal
                            cell.border = border_grid
                            if is_even:
                                cell.fill = fill_zebra
                            
                            col_name = df.columns[col_num-1]
                            if "Margen" in col_name or "%" in col_name or "ROI" in col_name or "Participacion" in col_name:
                                cell.number_format = '0.00%'
                            elif "Ingreso" in col_name or "Costo" in col_name or "Ganancia" in col_name or "Utilidad" in col_name or "Recaudacion" in col_name:
                                cell.number_format = '#,##0.00'
                            elif "Unidades" in col_name or "Cantidad" in col_name or "Pedidos" in col_name or "Transacciones" in col_name:
                                cell.number_format = '#,##0'

                    for col in ws.columns:
                        max_len = 0
                        col_letter = get_column_letter(col[0].column)
                        for cell in col:
                            if cell.row > 2 and cell.value is not None:
                                max_len = max(max_len, len(str(cell.value)))
                        ws.column_dimensions[col_letter].width = max(max_len + 4, 15)

                aplicar_estilo_corporativo(workbook["Reporte del Día"], df_res_diario, "Consolidado Diario de Operaciones")
                aplicar_estilo_corporativo(workbook["Rendimiento Productos"], df_res_prod, "Rendimiento y Margen por Producto")
                aplicar_estilo_corporativo(workbook["Análisis Margen & ROI"], df_res_roi, "Análisis Financiero de ROI")
                aplicar_estilo_corporativo(workbook["Ventas Categoria"], df_res_cat, "Ingresos por Categoría")
                aplicar_estilo_corporativo(workbook["Tendencia Horaria"], df_res_hora, "Análisis de Ventas por Hora")
                aplicar_estilo_corporativo(workbook["Flujo por Pago"], df_res_pagos, "Flujo Financiero por Método de Pago")
                aplicar_estilo_corporativo(workbook["Auditoria de Pedidos"], df_res_pedidos, "Auditoría de Transacciones")
                aplicar_estilo_corporativo(workbook["Transacciones Maestro"], df_detalles, "Base de Datos Maestro POS")

                # ========================================================
                # CREACIÓN DEL DASHBOARD MAESTRO BI (HOJA PRINCIPAL DE EXCEL)
                # ========================================================
                ws_dash = workbook.create_sheet(title="Dashboard Maestro BI", index=0)
                ws_dash.views.sheetView[0].showGridLines = True

                fill_dash_header = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid")
                fill_card_header = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
                fill_card_body = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
                
                border_thin = Border(
                    left=Side(style='thin', color='CBD5E1'),
                    right=Side(style='thin', color='CBD5E1'),
                    top=Side(style='thin', color='CBD5E1'),
                    bottom=Side(style='thin', color='CBD5E1')
                )

                # Banner Principal del Dashboard
                ws_dash.merge_cells("B2:Q2")
                cell_title = ws_dash["B2"]
                cell_title.value = "📊 EXECUTIVE BUSINESS INTELLIGENCE DASHBOARD - FRAPPÉS"
                cell_title.font = Font(name="Calibri", size=18, bold=True, color="FFFFFF")
                cell_title.fill = fill_dash_header
                cell_title.alignment = Alignment(horizontal="center", vertical="center")
                ws_dash.row_dimensions[2].height = 45

                # 6 Tarjetas KPI Ejecutivas con Fórmulas
                kpis = [
                    ("INGRESOS TOTALES (Bs.)", f"=SUM('Transacciones Maestro'!M4:M{len(df_detalles)+3})", "B", "C", "#,##0.00"),
                    ("COSTOS OPERATIVOS (Bs.)", f"=SUM('Transacciones Maestro'!N4:N{len(df_detalles)+3})", "D", "E", "#,##0.00"),
                    ("UTILIDAD NETA (Bs.)", f"=SUM('Transacciones Maestro'!O4:O{len(df_detalles)+3})", "F", "G", "#,##0.00"),
                    ("MARGEN GLOBAL (%)", f"=IF(B5=0,0,F5/B5)", "H", "I", "0.00%"),
                    ("TOTAL TRANSACCIONES", f"=COUNTA('Auditoria de Pedidos'!A4:A{len(df_res_pedidos)+3})", "J", "K", "#,##0"),
                    ("UNIDADES VENDIDAS", f"=SUM('Transacciones Maestro'!J4:J{len(df_detalles)+3})", "L", "M", "#,##0"),
                ]

                row_kpi_lbl = 4
                row_kpi_val = 5
                ws_dash.row_dimensions[row_kpi_lbl].height = 20
                ws_dash.row_dimensions[row_kpi_val].height = 32

                for label, formula, c1, c2, num_fmt in kpis:
                    ws_dash.merge_cells(f"{c1}{row_kpi_lbl}:{c2}{row_kpi_lbl}")
                    ws_dash.merge_cells(f"{c1}{row_kpi_val}:{c2}{row_kpi_val}")
                    
                    c_lbl = ws_dash[f"{c1}{row_kpi_lbl}"]
                    c_lbl.value = label
                    c_lbl.font = Font(name="Calibri", size=9, bold=True, color="FFFFFF")
                    c_lbl.fill = fill_card_header
                    c_lbl.alignment = Alignment(horizontal="center", vertical="center")

                    c_val = ws_dash[f"{c1}{row_kpi_val}"]
                    c_val.value = formula
                    c_val.font = Font(name="Calibri", size=14, bold=True, color="0F172A")
                    c_val.fill = fill_card_body
                    c_val.alignment = Alignment(horizontal="center", vertical="center")
                    c_val.number_format = num_fmt

                # Panel Lateral de Desglose en Vivo (Side Data Table)
                ws_dash["B8"] = "📌 RESUMEN DE RENDIMIENTO DE PRODUCTOS"
                ws_dash["B8"].font = Font(name="Calibri", size=11, bold=True, color="0F172A")

                headers_side = ["Producto", "Categoría", "Cant. Vendida", "Ingreso (Bs.)", "Margen %", "% Part."]
                for col_idx, h in enumerate(headers_side, start=2):
                    cell = ws_dash.cell(row=9, column=col_idx)
                    cell.value = h
                    cell.font = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
                    cell.fill = fill_card_header
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                ws_dash.row_dimensions[9].height = 22

                for r_idx, row_data in df_res_prod.iterrows():
                    r_num = 10 + r_idx
                    ws_dash.row_dimensions[r_num].height = 18
                    ws_dash.cell(row=r_num, column=2, value=row_data["Producto"]).font = Font(name="Calibri", size=10)
                    ws_dash.cell(row=r_num, column=3, value=row_data["Categoria"]).font = Font(name="Calibri", size=10)
                    
                    c_cant = ws_dash.cell(row=r_num, column=4, value=row_data["Cantidad_Total"])
                    c_cant.font = Font(name="Calibri", size=10)
                    c_cant.number_format = "#,##0"

                    c_ing = ws_dash.cell(row=r_num, column=5, value=row_data["Ingresos_Totales"])
                    c_ing.font = Font(name="Calibri", size=10)
                    c_ing.number_format = "#,##0.00"

                    c_mar = ws_dash.cell(row=r_num, column=6, value=row_data["Margen_%"])
                    c_mar.font = Font(name="Calibri", size=10)
                    c_mar.number_format = "0.00%"

                    c_part = ws_dash.cell(row=r_num, column=7, value=row_data["%_Participacion"])
                    c_part.font = Font(name="Calibri", size=10)
                    c_part.number_format = "0.00%"

                    for col in range(2, 8):
                        ws_dash.cell(row=r_num, column=col).border = border_thin

                # --------------------------------------------------
                # INCRUSTAR 5 GRÁFICOS PROFESIONALES DE EXCEL
                # --------------------------------------------------
                ws_prod = workbook["Rendimiento Productos"]
                ws_pagos = workbook["Flujo por Pago"]
                ws_pedidos = workbook["Auditoria de Pedidos"]
                ws_cat = workbook["Ventas Categoria"]
                ws_hora = workbook["Tendencia Horaria"]

                # 1. Gráfico de Barras Doble (Ingresos y Costos)
                chart_bar = BarChart()
                chart_bar.type = "col"
                chart_bar.style = 10
                chart_bar.title = "Ingresos vs Costos por Producto (Bs.)"
                chart_bar.y_axis.title = "Bolivianos (Bs.)"
                data_bar = Reference(ws_prod, min_col=4, min_row=3, max_col=5, max_row=len(df_res_prod)+3)
                cats_bar = Reference(ws_prod, min_col=1, min_row=4, max_row=len(df_res_prod)+3)
                chart_bar.add_data(data_bar, titles_from_data=True)
                chart_bar.set_categories(cats_bar)
                chart_bar.width = 16
                chart_bar.height = 10
                ws_dash.add_chart(chart_bar, "I8")

                # 2. Gráfico de Anillo (Recaudación por Método de Pago)
                chart_donut = DoughnutChart()
                chart_donut.title = "Recaudación por Método de Pago"
                data_donut = Reference(ws_pagos, min_col=3, min_row=3, max_row=len(df_res_pagos)+3)
                cats_donut = Reference(ws_pagos, min_col=1, min_row=4, max_row=len(df_res_pagos)+3)
                chart_donut.add_data(data_donut, titles_from_data=True)
                chart_donut.set_categories(cats_donut)
                chart_donut.width = 12
                chart_donut.height = 10
                ws_dash.add_chart(chart_donut, "N8")

                # 3. Gráfico de Torta / Pie (Participación por Categoría)
                chart_pie = PieChart()
                chart_pie.title = "Distribución por Categoría"
                data_pie = Reference(ws_cat, min_col=3, min_row=3, max_row=len(df_res_cat)+3)
                cats_pie = Reference(ws_cat, min_col=1, min_row=4, max_row=len(df_res_cat)+3)
                chart_pie.add_data(data_pie, titles_from_data=True)
                chart_pie.set_categories(cats_pie)
                chart_pie.width = 12
                chart_pie.height = 10
                ws_dash.add_chart(chart_pie, "B25")

                # 4. Gráfico de Líneas (Curva de Ventas e Horas Pico)
                chart_line = LineChart()
                chart_line.title = "Curva de Ventas e Horas Pico (Bs.)"
                chart_line.style = 13
                chart_line.y_axis.title = "Ingresos (Bs.)"
                data_line = Reference(ws_hora, min_col=3, min_row=3, max_row=len(df_res_hora)+3)
                cats_line = Reference(ws_hora, min_col=1, min_row=4, max_row=len(df_res_hora)+3)
                chart_line.add_data(data_line, titles_from_data=True)
                chart_line.set_categories(cats_line)
                chart_line.width = 16
                chart_line.height = 10
                ws_dash.add_chart(chart_line, "H25")

                # 5. Gráfico de Dispersión (Relación Costo vs Ingreso por Pedido)
                chart_scatter = ScatterChart()
                chart_scatter.title = "Relación Costo vs Ingreso por Pedido"
                chart_scatter.style = 2
                chart_scatter.y_axis.title = "Ingreso Total (Bs.)"
                chart_scatter.x_axis.title = "Costo del Pedido (Bs.)"
                xvalues = Reference(ws_pedidos, min_col=9, min_row=4, max_row=len(df_res_pedidos)+3)
                yvalues = Reference(ws_pedidos, min_col=8, min_row=4, max_row=len(df_res_pedidos)+3)
                series_scatter = Series(yvalues, xvalues, title_from_data=False)
                chart_scatter.series.append(series_scatter)
                chart_scatter.width = 13
                chart_scatter.height = 10
                ws_dash.add_chart(chart_scatter, "N25")

                # Autoajuste de anchos de columna en el Dashboard
                for col in ws_dash.columns:
                    max_len = 0
                    col_letter = get_column_letter(col[0].column)
                    for cell in col:
                        if cell.row > 2 and cell.value is not None:
                            max_len = max(max_len, len(str(cell.value)))
                    ws_dash.column_dimensions[col_letter].width = max(max_len + 4, 15)

            excel_data = output.getvalue()

            st.download_button(
                label="⬇️ Descargar Suite BI Nivel Inversión Completa (.XLSX)",
                data=excel_data,
                file_name=f"Suite_BI_Inversion_Frappes_{ahora_bo.strftime('%Y-%m-%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

        st.markdown("---")
        st.subheader("👁️ Vista Previa del Reporte Gerencial")
        tab_v1, tab_v2, tab_v3 = st.tabs(
            ["Reporte del Día", "Análisis ROI & Margen", "Tendencia Horaria"]
        )
        with tab_v1:
            st.dataframe(df_res_diario, use_container_width=True)
        with tab_v2:
            st.dataframe(df_res_roi, use_container_width=True)
        with tab_v3:
            st.dataframe(df_res_hora, use_container_width=True)
