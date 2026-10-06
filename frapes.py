import json
import os
from datetime import datetime
import pandas as pd
import plotly.express as px
import streamlit as st

# ---------------------------------------------------------
# CONFIGURACIÓN DE LA PÁGINA (Optimizado para Celulares)
# ---------------------------------------------------------
st.set_page_config(
    page_title="Sistema POS - Frappés",
    page_icon="🥤",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Estilos CSS para evitar distorsiones en gráficos y adaptar a pantallas móviles
st.markdown(
    """
    <style>
    .stApp {
        max-width: 100%;
        padding: 1rem;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem;
    }
    .js-plotly-plot .plotly .main-svg {
        user-select: none;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# GESTIÓN DE DATOS Y PERSISTENCIA LOCAL (Funciona sin internet)
# ---------------------------------------------------------
DATA_FILE = "sistema_datos.json"

DEFAULT_INVENTORY = {
    "Frappé Clásico Café": {
        "precio": 35.0,
        "costo": 12.0,
        "stock": 50,
        "categoria": "Frappés",
    },
    "Frappé Oreo": {
        "precio": 40.0,
        "costo": 15.0,
        "stock": 40,
        "categoria": "Frappés",
    },
    "Frappé Caramel Macchiato": {
        "precio": 42.0,
        "costo": 16.0,
        "stock": 30,
        "categoria": "Frappés",
    },
    "Frappé Matcha": {
        "precio": 45.0,
        "costo": 18.0,
        "stock": 25,
        "categoria": "Frappés",
    },
    "Bobas de Tapioca": {
        "precio": 8.0,
        "costo": 2.5,
        "stock": 100,
        "categoria": "Extras",
    },
    "Bobas Explosivas Frutilla": {
        "precio": 10.0,
        "costo": 3.0,
        "stock": 80,
        "categoria": "Extras",
    },
    "Chantilly Extra": {
        "precio": 5.0,
        "costo": 1.5,
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

# Configuración del gráfico Plotly para móviles (estático al deslizar)
PLOTLY_CONFIG = {
    "staticPlot": True,  # Inmoviliza el gráfico al deslizar la pantalla en teléfonos
    "responsive": True,
}

# ---------------------------------------------------------
# MENÚ NAVEGACIÓN Y SIDEBAR
# ---------------------------------------------------------
st.sidebar.title("🥤 Menú Principal")
opcion = st.sidebar.radio(
    "Selecciona una opción:",
    ["🛒 Registrar Venta", "📦 Inventario & Stock", "📊 Dashboard & KPIs"],
)

# ---------------------------------------------------------
# 1. MÓDULO REGISTRAR VENTA
# ---------------------------------------------------------
if opcion == "🛒 Registrar Venta":
    st.header("🛒 Registrar Nueva Venta")

    col_cli1, col_cli2 = st.columns([2, 1])
    with col_cli1:
        nombre_cliente = st.text_input(
            "Nombre del Cliente:", placeholder="Ej: Juan Pérez"
        )
    with col_cli2:
        tipo_servicio = st.selectbox(
            "Tipo de Pedido:", ["Para Llevar", "Para Comer Aquí"]
        )

    st.markdown("---")
    st.subheader("Seleccionar Productos")

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
        st.caption(f"Precio: **${info_prod['precio']:.2f}**")

    with col_prod3:
        cant = st.number_input(
            "Cantidad:", min_value=1, max_value=max(1, info_prod["stock"]), value=1
        )

    if st.button("➕ Agregar al Carrito", use_container_width=True):
        if info_prod["stock"] < cant:
            st.error("❌ No hay suficiente stock disponible.")
        else:
            st.session_state.carrito.append(
                {
                    "producto": prod_nom,
                    "cantidad": cant,
                    "precio": info_prod["precio"],
                    "costo": info_prod["costo"],
                    "subtotal": info_prod["precio"] * cant,
                    "costo_total": info_prod["costo"] * cant,
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

        st.markdown(f"### **Total a Pagar: ${subtotal_venta:.2f}**")

        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("✅ Confirmar y Registrar Venta", use_container_width=True):
                if not nombre_cliente.strip():
                    st.warning("⚠️ Ingresa el nombre del cliente.")
                else:
                    ahora = datetime.now()
                    id_pedido = st.session_state.contador_pedido

                    # Descontar stock
                    for item in st.session_state.carrito:
                        st.session_state.inventario[item["producto"]][
                            "stock"
                        ] -= item["cantidad"]

                    venta_reg = {
                        "id": id_pedido,
                        "fecha": ahora.strftime("%Y-%m-%d"),
                        "hora": ahora.strftime("%H:%M:%S"),
                        "cliente": nombre_cliente,
                        "servicio": tipo_servicio,
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

    # ---------------------------------------------------------
    # HISTORIAL DE VENTAS Y TICKET / ANULACIÓN
    # ---------------------------------------------------------
    st.markdown("---")
    st.subheader("📋 Registro de Ventas Recientes & Tickets")

    if st.session_state.ventas:
        df_ventas_hist = pd.DataFrame(st.session_state.ventas)
        st.dataframe(
            df_ventas_hist[[
                "id",
                "fecha",
                "hora",
                "cliente",
                "servicio",
                "total_venta",
                "estado",
            ]],
            use_container_width=True,
        )

        id_ver = st.number_input(
            "Número de Pedido para Ticket / Modificar:",
            min_value=1,
            max_value=len(st.session_state.ventas),
            value=len(st.session_state.ventas),
        )

        venta_sel = next(
            (v for v in st.session_state.ventas if v["id"] == id_ver), None
        )

        if venta_sel:
            st.markdown("### 📄 Detalles del Ticket")
            st.text(f"""
========================================
         SISTEMA DE FRAPPÉS POS        
========================================
N° Pedido: #{venta_sel['id']}
Fecha: {venta_sel['fecha']} | Hora: {venta_sel['hora']}
Cliente: {venta_sel['cliente']}
Modalidad: {venta_sel['servicio']}
Estado: {venta_sel['estado']}
----------------------------------------
DETALLE:
""" + "\n".join([f"- {i['producto']} x{i['cantidad']} = ${i['subtotal']:.2f}" for i in venta_sel['detalles']]) + f"""
----------------------------------------
TOTAL VENTA: ${venta_sel['total_venta']:.2f}
========================================
            """)

            col_a1, col_a2 = st.columns(2)
            with col_a1:
                if venta_sel["estado"] == "Completada":
                    if st.button("🚫 Anular Venta (Reintegrar Stock)"):
                        venta_sel["estado"] = "Anulada"
                        for item in venta_sel["detalles"]:
                            if item["producto"] in st.session_state.inventario:
                                st.session_state.inventario[item["producto"]][
                                    "stock"
                                ] += item["cantidad"]
                        guardar_datos()
                        st.success(f"Venta #{id_ver} Anulada Correctamente.")
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
                    st.success(f"Venta #{id_ver} Eliminada del Registro.")
                    st.rerun()
    else:
        st.info("No hay ventas registradas hoy.")

# ---------------------------------------------------------
# 2. MÓDULO INVENTARIO Y STOCK
# ---------------------------------------------------------
elif opcion == "📦 Inventario & Stock":
    st.header("📦 Control de Inventario & Stock")

    inv_list = [
        {"Producto": k, **v} for k, v in st.session_state.inventario.items()
    ]
    df_inv = pd.DataFrame(inv_list)

    st.dataframe(
        df_inv[["Producto", "categoria", "precio", "costo", "stock"]],
        use_container_width=True,
    )

    st.markdown("---")
    st.subheader("✏️ Actualizar Stock o Registrar Nuevo Producto")

    tab1, tab2 = st.tabs(["Actualizar Stock Existent", "Agregar Nuevo Producto"])

    with tab1:
        prod_edit = st.selectbox(
            "Seleccionar Producto a Modificar:",
            list(st.session_state.inventario.keys()),
        )
        nuevo_stock = st.number_input(
            "Nuevo Stock Total:",
            min_value=0,
            value=st.session_state.inventario[prod_edit]["stock"],
        )
        if st.button("Actualizar Stock"):
            st.session_state.inventario[prod_edit]["stock"] = nuevo_stock
            guardar_datos()
            st.success("Stock actualizado correctamente.")
            st.rerun()

    with tab2:
        nuevo_nom = st.text_input("Nombre del Producto:")
        nueva_cat = st.selectbox("Categoría:", ["Frappés", "Extras"])
        nuevo_p = st.number_input("Precio de Venta ($):", min_value=0.0, value=30.0)
        nuevo_c = st.number_input("Costo de Producción ($):", min_value=0.0, value=10.0)
        nuevo_s = st.number_input("Stock Inicial:", min_value=0, value=50)

        if st.button("Guardar Producto"):
            if nuevo_nom:
                st.session_state.inventario[nuevo_nom] = {
                    "precio": nuevo_p,
                    "costo": nuevo_c,
                    "stock": nuevo_s,
                    "categoria": nueva_cat,
                }
                guardar_datos()
                st.success("Producto registrado exitosamente.")
                st.rerun()

# ---------------------------------------------------------
# 3. MÓDULO DASHBOARD & KPIS
# ---------------------------------------------------------
elif opcion == "📊 Dashboard & KPIs":
    st.header("📊 Dashboard Financiero y Estadísticas")

    ventas_validas = [
        v for v in st.session_state.ventas if v.get("estado") == "Completada"
    ]

    if not ventas_validas:
        st.info("Aún no hay ventas registradas para generar métricas.")
    else:
        df = pd.DataFrame(ventas_validas)

        # KPIs Principales
        tot_ventas = df["total_venta"].sum()
        tot_costo = df["costo_total"].sum()
        ganancia_neta = df["ganancia_neta"].sum()
        cant_pedidos = len(df)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Ingresos Totales", f"${tot_ventas:.2f}")
        col2.metric("Costo Producción", f"${tot_costo:.2f}")
        col3.metric(
            "Ganancia Neta",
            f"${ganancia_neta:.2f}",
            delta=f"{(ganancia_neta/tot_ventas*100) if tot_ventas > 0 else 0:.1f}% Margen",
        )
        col4.metric("N° Pedidos", cant_pedidos)

        st.markdown("---")

        # Preparación de datos para gráficos
        detalles_list = []
        for v in ventas_validas:
            for item in v["detalles"]:
                detalles_list.append({
                    "Fecha": v["fecha"],
                    "Hora": v["hora"],
                    "Producto": item["producto"],
                    "Categoria": item["categoria"],
                    "Cantidad": item["cantidad"],
                    "Subtotal": item["subtotal"],
                    "CostoTotal": item["costo_total"],
                    "Ganancia": item["subtotal"] - item["costo_total"],
                    "Servicio": v["servicio"],
                })

        df_detalles = pd.DataFrame(detalles_list)

        # Gráficos Dinámicos e Inmóviles al Touch
        col_g1, col_g2 = st.columns(2)

        with col_g1:
            st.subheader("🥤 Productos Más Vendidos")
            df_prod = (
                df_detalles.groupby("Producto")["Cantidad"]
                .sum()
                .reset_index()
                .sort_values(by="Cantidad", ascending=True)
            )
            fig_prod = px.bar(
                df_prod,
                x="Cantidad",
                y="Producto",
                orientation="h",
                title="Unidades Vendidas por Producto",
                color="Cantidad",
                color_continuous_scale="Viridis",
            )
            st.plotly_chart(
                fig_prod, use_container_width=True, config=PLOTLY_CONFIG
            )

        with col_g2:
            st.subheader("🛍️ Modalidad de Pedido")
            df_serv = (
                df.groupby("servicio")["total_venta"].sum().reset_index()
            )
            fig_serv = px.pie(
                df_serv,
                names="servicio",
                values="total_venta",
                title="Ingresos: Para Llevar vs Comer Aquí",
                hole=0.4,
            )
            st.plotly_chart(
                fig_serv, use_container_width=True, config=PLOTLY_CONFIG
            )

        # Tablas Dinámicas
        st.markdown("---")
        st.subheader("📋 Tabla Dinámica de Detalles")

        st.dataframe(
            df_detalles[[
                "Fecha",
                "Hora",
                "Producto",
                "Categoria",
                "Cantidad",
                "Subtotal",
                "CostoTotal",
                "Ganancia",
                "Servicio",
            ]],
            use_container_width=True,
        )

        # Exportación a Excel
        st.markdown("---")
        st.subheader("📥 Exportar Registro Diario a Excel")

        @st.cache_data
        def convertir_excel(df_export):
            import io

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                df_export.to_excel(
                    writer, index=False, sheet_name="Registro_Diario"
                )
            return output.getvalue()

        excel_data = convertir_excel(df_detalles)

        st.download_button(
            label="📥 Descargar Excel Completo",
            data=excel_data,
            file_name=f"Ventas_Frappes_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )