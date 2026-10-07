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


# Configuración de la página
st.set_page_config(
    page_title="Sistema POS & Analytics - Frappés",
    page_icon="🥤",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Estilos CSS
st.markdown(
    """
    <style>
    .stApp { max-width: 100%; padding: 0.8rem; }
    div[data-testid="stMetricValue"] { font-size: 1.8rem; font-weight: 700; }
    </style>
""",
    unsafe_allow_html=True,
)

# Encabezado
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

# 1. REGISTRAR VENTA
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
            v["id"] for v in st.session_state.ventas if isinstance(v, dict) and "id" in v
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
                        (v for v in st.session_state.ventas if v.get("id") == id_a_eliminar),
                        None,
                    )
                    if venta_target:
                        if venta_target.get("estado") == "Completada":
                            for item in venta_target.get("detalles", []):
                                if item["producto"] in st.session_state.inventario:
                                    st.session_state.inventario[item["producto"]][
                                        "stock"
                                    ] += item.get("cantidad", 0)

                        st.session_state.ventas = [
                            v for v in st.session_state.ventas if v.get("id") != id_a_eliminar
                        ]
                        guardar_datos()
                        st.success(f"Venta #{id_a_eliminar} eliminada correctamente.")
                        st.rerun()
    else:
        st.info("No hay registro de ventas en el sistema.")

# 2. INVENTARIO Y STOCK
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

# 3. DASHBOARD Y ANALÍTICA
elif opcion == "📊 Panel de control e indicadores clave de rendimiento (KPI)":
    st.header("📊 Executive BI Dashboard & Analytics")

    col_top1, col_top2 = st.columns([4, 1])
    with col_top2:
        if st.button("⚠️ Resetear BD (Limpiar)", help="Usa esto si tus datos antiguos dañan la vista"):
            st.session_state.ventas = []
            st.session_state.contador_pedido = 1
            guardar_datos()
            st.rerun()

    ventas_validas = [
        v for v in st.session_state.ventas
        if isinstance(v, dict) and v.get("estado") == "Completada" and "detalles" in v
    ]

    if not ventas_validas:
        st.info("💡 No hay ventas registradas aún.")
    else:
        df = pd.DataFrame(ventas_validas)
        detalles_list = []
        for v in ventas_validas:
            for item in v.get("detalles", []):
                detalles_list.append({
                    "ID_Pedido": v.get("id", 0),
                    "Hora_Entera": f"{str(v.get('hora', '00:00')).split(':')[0]}:00",
                    "Metodo_Pago": v.get("pago", "Efectivo"),
                    "Producto": item.get("producto", "Desconocido"),
                    "Cantidad": item.get("cantidad", 1),
                    "Ingreso_Total": item.get("subtotal", 0.0),
                    "Costo_Total": item.get("costo_total", 0.0),
                    "Ganancia_Neta": item.get("subtotal", 0.0) - item.get("costo_total", 0.0),
                })

        df_detalles = pd.DataFrame(detalles_list)

        tot_pedidos = len(df)
        tot_ventas = df["total_venta"].sum() if "total_venta" in df else 0.0
        tot_costo = df["costo_total"].sum() if "costo_total" in df else 0.0
        ganancia_total = df["ganancia_neta"].sum() if "ganancia_neta" in df else 0.0

        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("📦 Total Pedidos", f"{tot_pedidos}")
        kpi2.metric("💰 Ventas Totales", f"Bs. {tot_ventas:.2f}")
        kpi3.metric("📉 Costos Totales", f"Bs. {tot_costo:.2f}")
        kpi4.metric("🚀 Ganancia Neta", f"Bs. {ganancia_total:.2f}")

        st.markdown("---")

        col_g1, col_g2 = st.columns([3, 2])

        with col_g1:
            st.subheader("📈 Ventas por Hora")
            df_horas = df_detalles.groupby("Hora_Entera")["Ingreso_Total"].sum().reset_index()
            fig_bar_hora = px.bar(df_horas, x="Hora_Entera", y="Ingreso_Total", title="Ingresos por Hora")
            st.plotly_chart(fig_bar_hora, use_container_width=True)

        with col_g2:
            st.subheader("💳 Métodos de Pago")
            df_pago = df_detalles.groupby("Metodo_Pago")["Ingreso_Total"].sum().reset_index()
            fig_pie_pago = px.pie(df_pago, values="Ingreso_Total", names="Metodo_Pago", title="Distribución de Pagos")
            st.plotly_chart(fig_pie_pago, use_container_width=True)
