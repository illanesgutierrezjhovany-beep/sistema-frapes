from datetime import datetime
import json
import os
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

# Reloj en tiempo real y estilos
st.markdown(
    """
    <style>
    .stApp {
        max-width: 100%;
        padding: 0.8rem;
    }
    .reloj-container {
        background-color: #1f2937;
        color: #ffffff;
        padding: 10px 15px;
        border-radius: 10px;
        text-align: center;
        font-family: monospace;
        margin-bottom: 15px;
        box-shadow: 0px 4px 6px rgba(0,0,0,0.1);
    }
    .reloj-hora {
        font-size: 1.8rem;
        font-weight: bold;
        color: #10b981;
    }
    .reloj-fecha {
        font-size: 0.9rem;
        color: #9ca3af;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.6rem;
    }
    .js-plotly-plot .plotly .main-svg {
        user-select: none;
    }
    </style>

    <div class="reloj-container">
        <div class="reloj-fecha" id="fecha-live">Cargando fecha...</div>
        <div class="reloj-hora" id="reloj-live">00:00:00</div>
    </div>

    <script>
    function actualizarReloj() {
        const ahora = new Date();
        const opcionesFecha = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
        const fechaStr = ahora.toLocaleDateString('es-ES', opcionesFecha);
        const horaStr = ahora.toLocaleTimeString('es-ES');
        
        document.getElementById('reloj-live').textContent = horaStr;
        document.getElementById('fecha-live').textContent = fechaStr.charAt(0).toUpperCase() + fechaStr.slice(1);
    }
    setInterval(actualizarReloj, 1000);
    actualizarReloj();
    </script>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# GESTIÓN DE DATOS Y PERSISTENCIA LOCAL
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

PLOTLY_CONFIG = {"staticPlot": True, "responsive": True}

# ---------------------------------------------------------
# MENÚ NAVEGACIÓN
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
# 1. MÓDULO REGISTRAR VENTA
# ---------------------------------------------------------
if opcion == "🛒 Registrar Venta":
    st.header("🛒 Registrar Nueva Venta")

    col_cli1, col_cli2, col_cli3 = st.columns([2, 1, 1])
    with col_cli1:
        nombre_cliente = st.text_input(
            "Nombre del Cliente:", placeholder="Ej: Juan Pérez"
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
        "Notas / Indicaciones del Pedido:",
        placeholder="Ej: Sin crema chantilly, extra frío...",
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

        st.markdown(f"### **Total a Pagar: ${subtotal_venta:.2f}**")

        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("✅ Confirmar y Registrar Venta", use_container_width=True):
                if not nombre_cliente.strip():
                    st.warning("⚠️ Ingresa el nombre del cliente.")
                else:
                    ahora = datetime.now()
                    id_pedido = st.session_state.contador_pedido

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
                        "pago": metodo_pago,
                        "notas": notas_pedido if notas_pedido else "Ninguna",
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

    # HISTORIAL DE VENTAS
    st.markdown("---")
    st.subheader("📋 Registro de Ventas Recientes & Tickets")

    if st.session_state.ventas:
        df_ventas_hist = pd.DataFrame(st.session_state.ventas)

        # Seleccionar únicamente columnas existentes para evitar errores
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
            "Ingresa N° de Pedido para Ver Ticket / Acciones:",
            min_value=1,
            max_value=len(st.session_state.ventas),
            value=len(st.session_state.ventas),
        )

        venta_sel = next(
            (v for v in st.session_state.ventas if v["id"] == id_ver), None
        )

        if venta_sel:
            st.markdown("### 📄 Ticket Detallado del Pedido")

            items_str = "\n".join([
                f"  • {i['producto']} (x{i['cantidad']}) -> ${i['subtotal']:.2f} [Costo: ${i['costo_total']:.2f}]"
                for i in venta_sel["detalles"]
            ])

            ticket_text = f"""
==================================================
           🥤 SISTEMA POS FRAPPÉS 🥤           
==================================================
N° Pedido: #{venta_sel['id']}
Fecha Registro: {venta_sel['fecha']}
Hora Exacta:   {venta_sel['hora']}
--------------------------------------------------
Cliente:       {venta_sel['cliente']}
Modalidad:     {venta_sel['servicio']}
Método Pago:   {venta_sel.get('pago', 'N/A')}
Notas:         {venta_sel.get('notas', 'Ninguna')}
Estado Venta:  {venta_sel['estado']}
--------------------------------------------------
DETALLE DE PRODUCTOS:
{items_str}
--------------------------------------------------
SUBTOTAL:             ${venta_sel['total_venta']:.2f}
COSTO PRODUCCIÓN:     ${venta_sel['costo_total']:.2f}
GANANCIA NETA:        ${venta_sel['ganancia_neta']:.2f}
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
                    st.rerun()
    else:
        st.info("Aún no hay ventas registradas.")

# ---------------------------------------------------------
# 2. MÓDULO INVENTARIO Y STOCK
# ---------------------------------------------------------
elif opcion == "📦 Inventario y stock":
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
        nuevo_nom = st.text_input("Nombre:")
        nueva_cat = st.selectbox("Categoría:", ["Frappés", "Extras"])
        nuevo_p = st.number_input("Precio ($):", min_value=0.0, value=30.0)
        nuevo_c = st.number_input("Costo ($):", min_value=0.0, value=10.0)
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
                st.success("Producto creado.")
                st.rerun()

# ---------------------------------------------------------
# 3. MÓDULO DASHBOARD & KPIS
# ---------------------------------------------------------
elif (
    opcion == "📊 Panel de control e indicadores clave de rendimiento (KPI)"
):
    st.header("📊 Dashboard Financiero y Estadísticas")

    ventas_validas = [
        v for v in st.session_state.ventas if v.get("estado") == "Completada"
    ]

    if not ventas_validas:
        st.info("Aún no hay ventas registradas para generar reportes.")
    else:
        df = pd.DataFrame(ventas_validas)

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

        detalles_list = []
        for v in ventas_validas:
            for item in v["detalles"]:
                detalles_list.append({
                    "ID_Pedido": v["id"],
                    "Fecha": v["fecha"],
                    "Hora_Exacta": v["hora"],
                    "Cliente": v["cliente"],
                    "Servicio": v["servicio"],
                    "Metodo_Pago": v.get("pago", "No Registrado"),
                    "Notas": v.get("notas", "Ninguna"),
                    "Producto": item["producto"],
                    "Categoria": item["categoria"],
                    "Cantidad": item["cantidad"],
                    "Precio_Unit": item["precio"],
                    "Costo_Unit": item["costo"],
                    "Subtotal_Venta": item["subtotal"],
                    "Costo_Total": item["costo_total"],
                    "Ganancia_Item": item["subtotal"] - item["costo_total"],
                })

        df_detalles = pd.DataFrame(detalles_list)

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
            st.subheader("💳 Ventas por Método de Pago")
            if "pago" in df.columns:
                df_pago = (
                    df.groupby("pago")["total_venta"].sum().reset_index()
                )
                fig_pago = px.pie(
                    df_pago,
                    names="pago",
                    values="total_venta",
                    title="Ingresos por Forma de Pago",
                    hole=0.4,
                )
                st.plotly_chart(
                    fig_pago, use_container_width=True, config=PLOTLY_CONFIG
                )
            else:
                st.info("Sin registros de métodos de pago aún.")

        st.markdown("---")
        st.subheader("📋 Tabla Dinámica con Información Detallada")

        st.dataframe(df_detalles, use_container_width=True)

        st.markdown("---")
        st.subheader("📥 Exportar Informe Diario Completo a Excel")

        @st.cache_data
        def convertir_excel(df_export):
            import io

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                df_export.to_excel(
                    writer, index=False, sheet_name="Detalle_Completo"
                )
            return output.getvalue()

        excel_data = convertir_excel(df_detalles)

        st.download_button(
            label="📥 Descargar Reporte Excel",
            data=excel_data,
            file_name=f"Reporte_Detallado_Frappes_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
