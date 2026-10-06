from datetime import datetime
import json
import os
import zoneinfo
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Zona Horaria Bolivia
ZONA_BOLIVIA = zoneinfo.ZoneInfo("America/La_Paz")


def obtener_hora_bo():
    return datetime.now(ZONA_BOLIVIA)


# ---------------------------------------------------------
# CONFIGURACIÓN DE LA PÁGINA (Optimizado Móvil + Tema Dark Pro)
# ---------------------------------------------------------
st.set_page_config(
    page_title="Sistema POS & Analytics - Frappés",
    page_icon="🥤",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Estilos CSS y Reloj en Vivo Ajustado a Bolivia
st.markdown(
    """
    <style>
    .stApp {
        max-width: 100%;
        padding: 0.8rem;
    }
    .reloj-container {
        background: linear-gradient(135deg, #1e1b4b 0%, #311b92 100%);
        color: #ffffff;
        padding: 12px 20px;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.3);
        border: 1px solid rgba(255,255,255,0.1);
    }
    .reloj-hora {
        font-size: 2.2rem;
        font-weight: 800;
        color: #00e676;
        letter-spacing: 2px;
        font-family: 'Courier New', monospace;
    }
    .reloj-fecha {
        font-size: 1rem;
        color: #cbd5e1;
        text-transform: capitalize;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: 700;
    }
    .js-plotly-plot .plotly .main-svg {
        user-select: none;
    }
    </style>

    <div class="reloj-container">
        <div class="reloj-fecha" id="fecha-live">Cargando fecha de Bolivia...</div>
        <div class="reloj-hora" id="reloj-live">00:00:00</div>
        <div style="font-size: 0.75rem; color: #94a3b8; margin-top:2px;">Hora Oficial de Bolivia (GMT-4)</div>
    </div>

    <script>
    function actualizarRelojBO() {
        const opciones = { timeZone: 'America/La_Paz', hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' };
        const opcionesFecha = { timeZone: 'America/La_Paz', weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
        
        const ahora = new Date();
        const horaStr = ahora.toLocaleTimeString('es-BO', opciones);
        const fechaStr = ahora.toLocaleDateString('es-BO', opcionesFecha);
        
        document.getElementById('reloj-live').textContent = horaStr;
        document.getElementById('fecha-live').textContent = fechaStr.charAt(0).toUpperCase() + fechaStr.slice(1);
    }
    setInterval(actualizarRelojBO, 1000);
    actualizarRelojBO();
    </script>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# PERSISTENCIA LOCAL Y DATOS INICIALES
# ---------------------------------------------------------
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
    st.session_state.inventario = data["inventario"]
    st.session_state.ventas = data["ventas"]
    st.session_state.contador_pedido = data["contador_pedido"]
    st.session_state.carrito = []
    st.session_state.datos_cargados = True

PLOTLY_CONFIG = {"staticPlot": True, "responsive": True}

# ---------------------------------------------------------
# NAVEGACIÓN
# ---------------------------------------------------------
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
        if cat_seleccionada == "Todas" or v["categoria"] == cat_seleccionada
    }

    col_prod1, col_prod2, col_prod3 = st.columns([2, 1, 1])

    with col_prod1:
        prod_nom = st.selectbox("Producto:", list(items_filtrados.keys()))

    info_prod = st.session_state.inventario[prod_nom]

    with col_prod2:
        st.caption(f"Stock: **{info_prod['stock']}**")
        st.caption(f"Precio: **Bs. {info_prod['precio']:.2f}**")

    with col_prod3:
        cant = st.number_input(
            "Cantidad:", min_value=1, max_value=max(1, info_prod["stock"]), value=1
        )

    if st.button("➕ Agregar al Carrito", use_container_width=True):
        if info_prod["stock"] < cant:
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
                    "categoria": info_prod["categoria"],
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
                    ahora_bo = obtener_hora_bo()
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
                        "notas": notas_pedido if notas_pedido else "Sin especificación",
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

    # REGISTRO Y TICKET
    st.markdown("---")
    st.subheader("📋 Ventas Recientes & Tickets")

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

        id_ver = st.number_input(
            "Ver Ticket de Pedido N°:",
            min_value=1,
            max_value=len(st.session_state.ventas),
            value=len(st.session_state.ventas),
        )

        venta_sel = next(
            (v for v in st.session_state.ventas if v["id"] == id_ver), None
        )

        if venta_sel:
            st.markdown("### 📄 Ticket Oficial de Pedido")

            items_str = "\n".join([
                f"  • {i['producto']} (x{i['cantidad']}) -> Bs. {i['subtotal']:.2f}"
                for i in venta_sel["detalles"]
            ])

            ticket_text = f"""
==================================================
        🥤 SISTEMA POS FRAPPÉS BOLIVIA 🥤        
==================================================
N° Pedido:     #{venta_sel['id']}
Fecha/Hora:    {venta_sel['fecha']} - {venta_sel['hora']} (BOT)
--------------------------------------------------
Cliente:       {venta_sel['cliente']}
Modalidad:     {venta_sel['servicio']}
Método Pago:   {venta_sel.get('pago', 'N/A')}
Notas:         {venta_sel.get('notas', 'Sin especificación')}
Estado:        {venta_sel['estado']}
--------------------------------------------------
DETALLE PRODUCTOS:
{items_str}
--------------------------------------------------
TOTAL COBRADO:        Bs. {venta_sel['total_venta']:.2f}
COSTO PRODUCCIÓN:     Bs. {venta_sel['costo_total']:.2f}
GANANCIA NETA:        Bs. {venta_sel['ganancia_neta']:.2f}
==================================================
            """
            st.code(ticket_text, language="text")

            col_a1, col_a2 = st.columns(2)
            with col_a1:
                if venta_sel["estado"] == "Completada":
                    if st.button("🚫 Anular Venta (Devolver Stock)"):
                        venta_sel["estado"] = "Anulada"
                        for item in venta_sel["detalles"]:
                            if item["producto"] in st.session_state.inventario:
                                st.session_state.inventario[item["producto"]][
                                    "stock"
                                ] += item["cantidad"]
                        guardar_datos()
                        st.success(f"Venta #{id_ver} Anulada.")
                        st.rerun()

            with col_a2:
                if st.button("❌ Eliminar Venta Definitivamente"):
                    if venta_sel["estado"] == "Completada":
                        for item in venta_sel["detalles"]:
                            if item["producto"] in st.session_state.inventario:
                                st.session_state.inventario[item["producto"]][
                                    "stock"
                                ] += item["cantidad"]
                    st.session_state.ventas = [
                        v for v in st.session_state.ventas if v["id"] != id_ver
                    ]
                    guardar_datos()
                    st.success(f"Venta #{id_ver} Eliminada.")
                    st.rer
