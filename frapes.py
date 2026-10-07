import json
import os
import zoneinfo
from datetime import datetime
import pandas as pd
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
    .cat-box {
        background-color: #161b22;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #30363d;
        margin-bottom: 10px;
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
                        "ganancia_item": (info_prod["precio"] - info_prod["costo"])
                        * cant,
                        "categoria": info_prod.get("categoria", "Frappés"),
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

        subtotal_venta = sum(item["subtotal"] for item in st.session_state.carrito)
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
