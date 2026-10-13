import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from io import BytesIO
import json
import os
import shutil

from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

# =========================================================
# FRAPPES POS - VERSION MEJORADA
# Persistencia Excel + copias de seguridad + dashboard profesional
# =========================================================

st.set_page_config(
    page_title="Frappés POS | Sistema Ejecutivo",
    page_icon="🥤",
    layout="wide",
    initial_sidebar_state="expanded"
)

TZ = ZoneInfo("America/La_Paz")
BASE_DIR = Path(__file__).resolve().parent
DB = BASE_DIR / "frappes_database.xlsx"
BACKUP_DIR = BASE_DIR / "copias_seguridad"
BACKUP_DIR.mkdir(exist_ok=True)

st.markdown("""
<style>
.stApp {
    background: #0b1220;
    color: #f1f5f9;
}
[data-testid="stMetric"] {
    background: linear-gradient(135deg, #172554, #164e63);
    border: 1px solid #334155;
    padding: 15px;
    border-radius: 14px;
}
[data-testid="stMetricLabel"] {
    color: #cbd5e1;
}
[data-testid="stMetricValue"] {
    color: #67e8f9;
    font-weight: 800;
}
h1, h2, h3 {
    color: #67e8f9;
}
.stButton > button {
    border-radius: 9px;
    font-weight: 700;
}
</style>
""", unsafe_allow_html=True)


def ahora():
    return datetime.now(TZ)


INVENTARIO_INICIAL = {
    "Frappé Clásico Café": {
        "categoria": "Frappés",
        "precio": 20.0,
        "costo": 7.0,
        "stock": 50
    },
    "Frappé Oreo Deluxe": {
        "categoria": "Frappés",
        "precio": 25.0,
        "costo": 9.0,
        "stock": 40
    },
    "Frappé Caramel Macchiato": {
        "categoria": "Frappés",
        "precio": 24.0,
        "costo": 8.5,
        "stock": 30
    },
    "Frappé Matcha Premium": {
        "categoria": "Frappés",
        "precio": 28.0,
        "costo": 10.0,
        "stock": 25
    },
    "Bobas de Tapioca": {
        "categoria": "Extras",
        "precio": 5.0,
        "costo": 1.5,
        "stock": 100
    },
    "Bobas Explosivas Frutilla": {
        "categoria": "Extras",
        "precio": 6.0,
        "costo": 2.0,
        "stock": 80
    },
    "Chantilly Extra": {
        "categoria": "Extras",
        "precio": 3.0,
        "costo": 1.0,
        "stock": 60
    },
}

COLUMNAS_VENTAS = [
    "ID", "Fecha", "Hora", "Cliente", "Modalidad",
    "Metodo_Pago", "Notas", "Total_Venta", "Costo_Total",
    "Ganancia_Neta", "Estado", "Detalles_JSON"
]

COLUMNAS_DETALLES = [
    "ID_Pedido", "Fecha", "Hora", "Cliente", "Modalidad",
    "Metodo_Pago", "Producto", "Categoria", "Cantidad",
    "Precio_Unitario", "Costo_Unitario", "Ingreso_Total",
    "Costo_Total", "Ganancia_Neta"
]


# =========================================================
# COPIAS DE SEGURIDAD
# =========================================================

def crear_respaldo():
    if DB.exists():
        sello = ahora().strftime("%Y%m%d_%H%M%S_%f")
        destino = BACKUP_DIR / f"frappes_database_{sello}.xlsx"
        shutil.copy2(DB, destino)

        copias = sorted(
            BACKUP_DIR.glob("frappes_database_*.xlsx"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        for vieja in copias[100:]:
            vieja.unlink(missing_ok=True)


# =========================================================
# CARGAR BASE DE DATOS
# =========================================================

def cargar_db():
    if not DB.exists():
        return {
            k: v.copy()
            for k, v in INVENTARIO_INICIAL.items()
        }, [], 1

    try:
        xls = pd.ExcelFile(DB)
        inventario = {}
        ventas = []

        if "Inventario" in xls.sheet_names:
            df = pd.read_excel(
                DB,
                sheet_name="Inventario"
            ).fillna(0)

            for _, r in df.iterrows():
                nombre = str(
                    r.get("Producto", "")
                ).strip()

                if nombre and nombre.lower() != "nan":
                    inventario[nombre] = {
                        "categoria": str(
                            r.get("Categoria", "Frappés")
                        ),
                        "precio": float(
                            r.get("Precio", 0)
                        ),
                        "costo": float(
                            r.get("Costo", 0)
                        ),
                        "stock": int(
                            float(r.get("Stock", 0))
                        )
                    }

        if "Ventas" in xls.sheet_names:
            df = pd.read_excel(
                DB,
                sheet_name="Ventas"
            )

            for _, r in df.iterrows():
                try:
                    raw = r.get("Detalles_JSON", "[]")
                    detalles = json.loads(
                        raw if isinstance(raw, str) else "[]"
                    )

                    ventas.append({
                        "id": int(r["ID"]),
                        "fecha": str(r["Fecha"])[:10],
                        "hora": str(r["Hora"]),
                        "cliente": str(r["Cliente"]),
                        "servicio": str(r["Modalidad"]),
                        "pago": str(r["Metodo_Pago"]),
                        "notas": str(r.get("Notas", "")),
                        "total_venta": float(r["Total_Venta"]),
                        "costo_total": float(r["Costo_Total"]),
                        "ganancia_neta": float(r["Ganancia_Neta"]),
                        "estado": str(r["Estado"]),
                        "detalles": detalles
                    })

                except (
                    ValueError,
                    TypeError,
                    KeyError,
                    json.JSONDecodeError
                ):
                    continue

        if not inventario:
            inventario = {
                k: v.copy()
                for k, v in INVENTARIO_INICIAL.items()
            }

        siguiente_id = max(
            [v["id"] for v in ventas] + [0]
        ) + 1

        return inventario, ventas, siguiente_id

    except Exception as e:
        st.error(
            f"No se pudo leer {DB.name}: {e}. "
            "Se intentará recuperar desde una copia de seguridad."
        )

        copias = sorted(
            BACKUP_DIR.glob("frappes_database_*.xlsx"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        for copia in copias:
            try:
                xls = pd.ExcelFile(copia)
                inv = {}
                ventas = []

                if "Inventario" in xls.sheet_names:
                    df_inv = pd.read_excel(
                        copia,
                        sheet_name="Inventario"
                    ).fillna(0)

                    for _, r in df_inv.iterrows():
                        nombre = str(
                            r.get("Producto", "")
                        ).strip()

                        if nombre and nombre.lower() != "nan":
                            inv[nombre] = {
                                "categoria": str(
                                    r.get("Categoria", "Frappés")
                                ),
                                "precio": float(
                                    r.get("Precio", 0)
                                ),
                                "costo": float(
                                    r.get("Costo", 0)
                                ),
                                "stock": int(
                                    float(r.get("Stock", 0))
                                )
                            }

                if "Ventas" in xls.sheet_names:
                    df_ventas = pd.read_excel(
                        copia,
                        sheet_name="Ventas"
                    )

                    for _, r in df_ventas.iterrows():
                        try:
                            raw = r.get("Detalles_JSON", "[]")
                            detalles = json.loads(
                                raw if isinstance(raw, str) else "[]"
                            )

                            ventas.append({
                                "id": int(r["ID"]),
                                "fecha": str(r["Fecha"])[:10],
                                "hora": str(r["Hora"]),
                                "cliente": str(r["Cliente"]),
                                "servicio": str(r["Modalidad"]),
                                "pago": str(r["Metodo_Pago"]),
                                "notas": str(r.get("Notas", "")),
                                "total_venta": float(r["Total_Venta"]),
                                "costo_total": float(r["Costo_Total"]),
                                "ganancia_neta": float(r["Ganancia_Neta"]),
                                "estado": str(r["Estado"]),
                                "detalles": detalles
                            })

                        except Exception:
                            continue

                st.warning(
                    f"Datos recuperados desde la copia: {copia.name}"
                )

                siguiente_id = max(
                    [v["id"] for v in ventas] + [0]
                ) + 1

                return (
                    inv or {
                        k: v.copy()
                        for k, v in INVENTARIO_INICIAL.items()
                    },
                    ventas,
                    siguiente_id
                )

            except Exception:
                continue

        st.error(
            "No se encontró una copia legible. "
            "No guardes datos nuevos hasta revisar el archivo dañado."
        )

        return {
            k: v.copy()
            for k, v in INVENTARIO_INICIAL.items()
        }, [], 1


# =========================================================
# GUARDAR BASE DE DATOS EXCEL
# =========================================================

def guardar_db():
    inv = st.session_state.inventario
    ventas = st.session_state.ventas

    df_inv = pd.DataFrame([
        {
            "Producto": nombre,
            "Categoria": producto["categoria"],
            "Precio": producto["precio"],
            "Costo": producto["costo"],
            "Stock": producto["stock"]
        }
        for nombre, producto in inv.items()
    ], columns=["Producto", "Categoria", "Precio", "Costo", "Stock"])

    filas_v = []
    filas_d = []

    for venta in ventas:
        filas_v.append({
            "ID": venta["id"],
            "Fecha": venta["fecha"],
            "Hora": venta["hora"],
            "Cliente": venta["cliente"],
            "Modalidad": venta["servicio"],
            "Metodo_Pago": venta["pago"],
            "Notas": venta.get("notas", ""),
            "Total_Venta": venta["total_venta"],
            "Costo_Total": venta["costo_total"],
            "Ganancia_Neta": venta["ganancia_neta"],
            "Estado": venta["estado"],
            "Detalles_JSON": json.dumps(
                venta["detalles"],
                ensure_ascii=False
            )
        })

        for item in venta.get("detalles", []):
            filas_d.append({
                "ID_Pedido": venta["id"],
                "Fecha": venta["fecha"],
                "Hora": venta["hora"],
                "Cliente": venta["cliente"],
                "Modalidad": venta["servicio"],
                "Metodo_Pago": venta["pago"],
                "Producto": item["producto"],
                "Categoria": item["categoria"],
                "Cantidad": item["cantidad"],
                "Precio_Unitario": item["precio"],
                "Costo_Unitario": item["costo"],
                "Ingreso_Total": item["subtotal"],
                "Costo_Total": item["costo_total"],
                "Ganancia_Neta": item["ganancia_item"]
            })

    df_v = pd.DataFrame(
        filas_v,
        columns=COLUMNAS_VENTAS
    )

    df_d = pd.DataFrame(
        filas_d,
        columns=COLUMNAS_DETALLES
    )

    temporal = DB.with_name("frappes_database_temp.xlsx")

    try:
        crear_respaldo()

        with pd.ExcelWriter(
            temporal,
            engine="openpyxl"
        ) as writer:
            df_inv.to_excel(
                writer,
                sheet_name="Inventario",
                index=False
            )

            df_v.to_excel(
                writer,
                sheet_name="Ventas",
                index=False
            )

            df_d.to_excel(
                writer,
                sheet_name="Detalle Ventas",
                index=False
            )

            for ws in writer.book.worksheets:
                ws.freeze_panes = "A2"
                ws.sheet_view.showGridLines = False
                ws.auto_filter.ref = ws.dimensions

                for celda in ws[1]:
                    celda.fill = PatternFill(
                        "solid",
                        fgColor="16324F"
                    )
                    celda.font = Font(
                        bold=True,
                        color="FFFFFF"
                    )
                    celda.alignment = Alignment(
                        horizontal="center",
                        vertical="center"
                    )

                for columna in ws.columns:
                    letra = get_column_letter(
                        columna[0].column
                    )

                    ancho = max(
                        [
                            len(str(c.value))
                            if c.value is not None
                            else 0
                            for c in columna
                        ] + [12]
                    )

                    ws.column_dimensions[letra].width = min(
                        max(ancho + 3, 14),
                        35
                    )

                if ws.max_row >= 2 and ws.max_column:
                    nombre_tabla = (
                        "Tabla"
                        + "".join(
                            ch for ch in ws.title
                            if ch.isalnum()
                        )[:20]
                    )

                    tabla = Table(
                        displayName=nombre_tabla,
                        ref=ws.dimensions
                    )

                    tabla.tableStyleInfo = TableStyleInfo(
                        name="TableStyleMedium2",
                        showRowStripes=True,
                        showColumnStripes=False
                    )

                    ws.add_table(tabla)

        os.replace(temporal, DB)

    except PermissionError:
        temporal.unlink(missing_ok=True)
        raise PermissionError(
            "Cierra frappes_database.xlsx en Excel y vuelve a guardar."
        )

    except Exception:
        temporal.unlink(missing_ok=True)
        raise


# =========================================================
# OBTENER DETALLE DE VENTAS COMPLETADAS
# =========================================================

def obtener_detalles():
    filas = []

    for venta in st.session_state.ventas:
        if venta.get("estado") != "Completada":
            continue

        for item in venta.get("detalles", []):
            filas.append({
                "ID_Pedido": venta["id"],
                "Fecha": venta["fecha"],
                "Hora": venta["hora"],
                "Hora_Entera": str(venta["hora"])[:2] + ":00",
                "Cliente": venta["cliente"],
                "Modalidad": venta["servicio"],
                "Metodo_Pago": venta["pago"],
                "Producto": item["producto"],
                "Categoria": item["categoria"],
                "Cantidad": item["cantidad"],
                "Precio_Unitario": item["precio"],
                "Costo_Unitario": item["costo"],
                "Ingreso_Total": item["subtotal"],
                "Costo_Total": item["costo_total"],
                "Ganancia_Neta": item["ganancia_item"]
            })

    return pd.DataFrame(
        filas,
        columns=[
            "ID_Pedido", "Fecha", "Hora", "Hora_Entera",
            "Cliente", "Modalidad", "Metodo_Pago",
            "Producto", "Categoria", "Cantidad",
            "Precio_Unitario", "Costo_Unitario",
            "Ingreso_Total", "Costo_Total", "Ganancia_Neta"
        ]
    )


# =========================================================
# ESTILO DE GRÁFICOS
# =========================================================

def estilo_figura(fig, x_title=None, y_title=None):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e2e8f0", size=12),
        margin=dict(l=35, r=25, t=65, b=55),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0
        ),
        hoverlabel=dict(
            bgcolor="#172554",
            font_color="white"
        ),
        xaxis_title=x_title,
        yaxis_title=y_title
    )

    fig.update_xaxes(
        showgrid=False,
        automargin=True,
        title_font=dict(size=13)
    )

    fig.update_yaxes(
        gridcolor="#334155",
        automargin=True,
        title_font=dict(size=13),
        zerolinecolor="#475569"
    )

    return fig


# =========================================================
# INICIALIZAR SESIÓN
# =========================================================

if "inicializado" not in st.session_state:
    inventario, ventas, siguiente = cargar_db()

    st.session_state.inventario = inventario
    st.session_state.ventas = ventas
    st.session_state.siguiente_id = siguiente
    st.session_state.carrito = []
    st.session_state.inicializado = True


fecha_hora = ahora()

st.title("🥤 FRAPPÉS POS")
st.caption(
    f"Sistema de punto de venta y analítica empresarial · "
    f"{fecha_hora:%d/%m/%Y %H:%M:%S} · Bolivia GMT-4"
)

st.sidebar.title("🥤 MENÚ PRINCIPAL")

menu = st.sidebar.radio(
    "Selecciona un módulo",
    [
        "🛒 Registrar venta",
        "📦 Inventario",
        "📊 Dashboard ejecutivo",
        "🗄️ Base de datos Excel",
        "📤 Exportar reporte BI"
    ]
)

st.sidebar.divider()
st.sidebar.caption("💾 Base de datos Excel + copias automáticas")
st.sidebar.code(str(DB))
st.sidebar.caption(f"Copias de seguridad: {BACKUP_DIR}")


# =========================================================
# 1. PUNTO DE VENTA
# =========================================================

if menu == "🛒 Registrar venta":
    st.header("🛒 Punto de venta")

    c1, c2, c3 = st.columns([2, 1, 1])

    cliente = c1.text_input("Nombre del cliente")
    modalidad = c2.selectbox(
        "Modalidad",
        ["Para Llevar", "Para Comer Aquí"]
    )
    metodo_pago = c3.selectbox(
        "Método de pago",
        ["Efectivo", "QR / Transferencia", "Tarjeta"]
    )

    notas = st.text_input("Notas de preparación")

    categoria = st.radio(
        "Categoría de productos",
        ["Todas", "Frappés", "Extras"],
        horizontal=True
    )

    productos = [
        nombre
        for nombre, producto in st.session_state.inventario.items()
        if categoria == "Todas"
        or producto["categoria"] == categoria
    ]

    if productos:
        c1, c2, c3 = st.columns([3, 1, 1])

        producto = c1.selectbox("Producto", productos)
        info = st.session_state.inventario[producto]

        c2.metric("Precio", f"Bs. {info['precio']:.2f}")
        c2.caption(f"Stock disponible: {info['stock']}")

        cantidad = c3.number_input(
            "Cantidad",
            min_value=1,
            max_value=max(1, int(info["stock"])),
            value=1,
            step=1,
            disabled=info["stock"] <= 0
        )

        if st.button(
            "➕ Añadir al carrito",
            use_container_width=True
        ):
            en_carrito = sum(
                item["cantidad"]
                for item in st.session_state.carrito
                if item["producto"] == producto
            )

            if info["stock"] <= 0:
                st.error("Este producto está agotado.")

            elif en_carrito + cantidad > info["stock"]:
                st.error("La cantidad supera el stock disponible.")

            else:
                st.session_state.carrito.append({
                    "producto": producto,
                    "categoria": info["categoria"],
                    "cantidad": int(cantidad),
                    "precio": info["precio"],
                    "costo": info["costo"],
                    "subtotal": info["precio"] * cantidad,
                    "costo_total": info["costo"] * cantidad,
                    "ganancia_item": (
                        info["precio"] - info["costo"]
                    ) * cantidad
                })

                st.rerun()

    if st.session_state.carrito:
        st.divider()
        st.subheader("🛒 Carrito de compra")

        st.dataframe(
            pd.DataFrame(st.session_state.carrito)[
                ["producto", "cantidad", "precio", "subtotal"]
            ],
            use_container_width=True,
            hide_index=True
        )

        total = sum(
            item["subtotal"]
            for item in st.session_state.carrito
        )

        costo_total = sum(
            item["costo_total"]
            for item in st.session_state.carrito
        )

        utilidad = total - costo_total

        a, b, c = st.columns(3)

        a.metric("💰 Total a cobrar", f"Bs. {total:.2f}")
        b.metric("📉 Costo estimado", f"Bs. {costo_total:.2f}")
        c.metric("💚 Utilidad estimada", f"Bs. {utilidad:.2f}")

        a, b = st.columns(2)

        if a.button(
            "✅ Confirmar venta",
            use_container_width=True
        ):
            if not cliente.strip():
                st.warning("Ingresa el nombre del cliente.")

            elif any(
                st.session_state.inventario[item["producto"]]["stock"]
                < item["cantidad"]
                for item in st.session_state.carrito
            ):
                st.error("Stock insuficiente para confirmar.")

            else:
                venta = {
                    "id": st.session_state.siguiente_id,
                    "fecha": fecha_hora.strftime("%Y-%m-%d"),
                    "hora": fecha_hora.strftime("%H:%M:%S"),
                    "cliente": cliente.strip(),
                    "servicio": modalidad,
                    "pago": metodo_pago,
                    "notas": notas or "Sin especificación",
                    "detalles": [
                        item.copy()
                        for item in st.session_state.carrito
                    ],
                    "total_venta": total,
                    "costo_total": costo_total,
                    "ganancia_neta": utilidad,
                    "estado": "Completada"
                }

                for item in st.session_state.carrito:
                    st.session_state.inventario[
                        item["producto"]
                    ]["stock"] -= item["cantidad"]

                st.session_state.ventas.append(venta)
                st.session_state.siguiente_id += 1

                try:
                    guardar_db()
                    st.session_state.carrito = []
                    st.success(
                        "Venta guardada en Excel y respaldo actualizado."
                    )
                    st.rerun()

                except Exception as e:
                    st.error(
                        f"La venta quedó en la sesión, pero no se pudo "
                        f"confirmar el guardado en disco: {e}. "
                        "No cierres la aplicación hasta resolverlo."
                    )

        if b.button(
            "🗑️ Vaciar carrito",
            use_container_width=True
        ):
            st.session_state.carrito = []
            st.rerun()

    st.divider()
    st.subheader("📋 Historial permanente de ventas")

    if st.session_state.ventas:
        hist = pd.DataFrame([
            {
                "ID": venta["id"],
                "Fecha": venta["fecha"],
                "Hora": venta["hora"],
                "Cliente": venta["cliente"],
                "Modalidad": venta["servicio"],
                "Pago": venta["pago"],
                "Total (Bs.)": venta["total_venta"],
                "Costo (Bs.)": venta["costo_total"],
                "Utilidad (Bs.)": venta["ganancia_neta"],
                "Estado": venta["estado"]
            }
            for venta in st.session_state.ventas
        ])

        st.dataframe(
            hist.sort_values("ID", ascending=False),
            use_container_width=True,
            hide_index=True
        )

        with st.expander("🗑️ Eliminar una venta (operación irreversible)"):
            ids = [
                venta["id"]
                for venta in st.session_state.ventas
            ]

            id_eliminar = st.selectbox(
                "Selecciona el pedido",
                ids
            )

            confirmar = st.checkbox(
                "Confirmo eliminar la venta y restituir el stock."
            )

            if st.button("Eliminar venta seleccionada"):
                if not confirmar:
                    st.warning("Confirma la operación primero.")

                else:
                    venta = next(
                        venta
                        for venta in st.session_state.ventas
                        if venta["id"] == id_eliminar
                    )

                    if venta["estado"] == "Completada":
                        for item in venta["detalles"]:
                            nombre = item["producto"]

                            if nombre in st.session_state.inventario:
                                st.session_state.inventario[
                                    nombre
                                ]["stock"] += item["cantidad"]

                    st.session_state.ventas = [
                        venta
                        for venta in st.session_state.ventas
                        if venta["id"] != id_eliminar
                    ]

                    try:
                        guardar_db()
                        st.success(
                            "Venta eliminada, stock restituido y cambios guardados."
                        )
                        st.rerun()

                    except Exception as e:
                        st.error(f"Error al guardar: {e}")

    else:
        st.info("Todavía no hay ventas registradas.")


# =========================================================
# 2. INVENTARIO
# =========================================================

elif menu == "📦 Inventario":
    st.header("📦 Control y gestión de inventario")

    df_inv = pd.DataFrame([
        {
            "Producto": nombre,
            "Categoría": producto["categoria"],
            "Precio (Bs.)": producto["precio"],
            "Costo (Bs.)": producto["costo"],
            "Stock": producto["stock"],
            "Utilidad por unidad": (
                producto["precio"] - producto["costo"]
            )
        }
        for nombre, producto in st.session_state.inventario.items()
    ])

    a, b, c = st.columns(3)

    a.metric("Productos", len(df_inv))
    b.metric(
        "Con stock bajo",
        int(((df_inv.Stock > 0) & (df_inv.Stock <= 5)).sum())
    )
    c.metric(
        "Agotados",
        int((df_inv.Stock == 0).sum())
    )

    st.dataframe(
        df_inv.style.format({
            "Precio (Bs.)": "Bs. {:.2f}",
            "Costo (Bs.)": "Bs. {:.2f}",
            "Utilidad por unidad": "Bs. {:.2f}"
        }),
        use_container_width=True,
        hide_index=True
    )

    tab1, tab2 = st.tabs([
        "✏️ Editar producto",
        "➕ Nuevo producto"
    ])

    with tab1:
        nombre = st.selectbox(
            "Producto a editar",
            list(st.session_state.inventario.keys())
        )

        producto = st.session_state.inventario[nombre]

        a, b, c = st.columns(3)

        nuevo_stock = a.number_input(
            "Stock disponible",
            min_value=0,
            value=int(producto["stock"]),
            step=1,
            key="stock_edit"
        )

        nuevo_precio = b.number_input(
            "Precio de venta (Bs.)",
            min_value=0.0,
            value=float(producto["precio"]),
            step=0.5,
            key="precio_edit"
        )

        nuevo_costo = c.number_input(
            "Costo (Bs.)",
            min_value=0.0,
            value=float(producto["costo"]),
            step=0.5,
            key="costo_edit"
        )

        nueva_categoria = st.selectbox(
            "Categoría",
            ["Frappés", "Extras"],
            index=0 if producto["categoria"] == "Frappés" else 1,
            key="categoria_edit"
        )

        if st.button("💾 Guardar modificaciones"):
            antes = producto.copy()

            producto.update({
                "stock": int(nuevo_stock),
                "precio": float(nuevo_precio),
                "costo": float(nuevo_costo),
                "categoria": nueva_categoria
            })

            try:
                guardar_db()
                st.success("Producto actualizado y guardado.")
                st.rerun()

            except Exception as e:
                producto.update(antes)
                st.error(f"Error al guardar: {e}")

    with tab2:
        nombre_nuevo = st.text_input("Nombre del nuevo producto")

        cat_nueva = st.selectbox(
            "Categoría",
            ["Frappés", "Extras"],
            key="categoria_nueva"
        )

        precio_nuevo = st.number_input(
            "Precio de venta",
            min_value=0.0,
            value=20.0,
            key="precio_nuevo"
        )

        costo_nuevo = st.number_input(
            "Costo de producción",
            min_value=0.0,
            value=7.0,
            key="costo_nuevo"
        )

        stock_nuevo = st.number_input(
            "Stock inicial",
            min_value=0,
            value=20,
            step=1,
            key="stock_nuevo"
        )

        if st.button("➕ Crear producto"):
            nombre_nuevo = nombre_nuevo.strip()

            if not nombre_nuevo:
                st.error("Escribe un nombre.")

            elif nombre_nuevo in st.session_state.inventario:
                st.error("El producto ya existe.")

            else:
                st.session_state.inventario[nombre_nuevo] = {
                    "categoria": cat_nueva,
                    "precio": float(precio_nuevo),
                    "costo": float(costo_nuevo),
                    "stock": int(stock_nuevo)
                }

                try:
                    guardar_db()
                    st.success("Producto creado y guardado.")
                    st.rerun()

                except Exception as e:
                    st.session_state.inventario.pop(
                        nombre_nuevo,
                        None
                    )
                    st.error(f"Error al guardar: {e}")


# =========================================================
# 3. DASHBOARD EJECUTIVO PROFESIONAL
# =========================================================

elif menu == "📊 Dashboard ejecutivo":
    st.header("📊 Dashboard ejecutivo de ventas")

    df = obtener_detalles()

    if df.empty:
        st.info(
            "Registra una venta para visualizar gráficos e indicadores."
        )

    else:
        fechas = sorted(
            df["Fecha"].dropna().astype(str).unique()
        )

        with st.expander(
            "🔎 Filtrar el dashboard por fechas",
            expanded=True
        ):
            seleccion = st.multiselect(
                "Fechas incluidas",
                fechas,
                default=fechas
            )

        df = df[df["Fecha"].isin(seleccion)] if seleccion else df.iloc[0:0]

        ids = set(df["ID_Pedido"].unique())

        ventas = [
            venta
            for venta in st.session_state.ventas
            if venta["estado"] == "Completada"
            and venta["id"] in ids
        ]

        ingresos = sum(
            venta["total_venta"]
            for venta in ventas
        )

        costos = sum(
            venta["costo_total"]
            for venta in ventas
        )

        utilidad = sum(
            venta["ganancia_neta"]
            for venta in ventas
        )

        unidades = int(df["Cantidad"].sum()) if not df.empty else 0
        margen = utilidad / ingresos if ingresos else 0

        k1, k2, k3, k4, k5, k6 = st.columns(6)

        k1.metric("🧾 Pedidos", len(ventas))
        k2.metric("💰 Ingresos", f"Bs. {ingresos:,.2f}")
        k3.metric("📉 Costos", f"Bs. {costos:,.2f}")
        k4.metric("💚 Utilidad neta", f"Bs. {utilidad:,.2f}")
        k5.metric("📈 Margen", f"{margen:.1%}")
        k6.metric("🥤 Unidades", unidades)

        if df.empty:
            st.warning("No hay ventas en las fechas seleccionadas.")

        else:
            st.divider()
            izquierda, derecha = st.columns(2)

            with izquierda:
                st.subheader(
                    "1. Ingresos, costos y utilidad por producto"
                )

                q = df.groupby(
                    "Producto",
                    as_index=False
                ).agg(
                    Ingresos=("Ingreso_Total", "sum"),
                    Costos=("Costo_Total", "sum"),
                    Utilidad=("Ganancia_Neta", "sum")
                )

                fig = go.Figure()

                for columna, color in [
                    ("Ingresos", "#22D3EE"),
                    ("Costos", "#FB7185"),
                    ("Utilidad", "#4ADE80")
                ]:
                    fig.add_bar(
                        x=q["Producto"],
                        y=q[columna],
                        name=columna,
                        marker_color=color,
                        text=q[columna].map(
                            lambda x: f"Bs. {x:,.2f}"
                        ),
                        textposition="outside",
                        cliponaxis=False
                    )

                fig.update_layout(
                    barmode="group",
                    xaxis_tickangle=-25,
                    legend_title_text="Indicador"
                )

                st.plotly_chart(
                    estilo_figura(
                        fig,
                        "Producto",
                        "Monto (Bs.)"
                    ),
                    use_container_width=True
                )

            with derecha:
                st.subheader("2. Ingresos y utilidad por pedido")

                q = df.groupby(
                    "ID_Pedido",
                    as_index=False
                ).agg(
                    Ingresos=("Ingreso_Total", "sum"),
                    Costos=("Costo_Total", "sum"),
                    Utilidad=("Ganancia_Neta", "sum")
                )

                fig = go.Figure()

                for columna, color in [
                    ("Ingresos", "#22D3EE"),
                    ("Costos", "#FB7185"),
                    ("Utilidad", "#4ADE80")
                ]:
                    fig.add_scatter(
                        x=q["ID_Pedido"],
                        y=q[columna],
                        name=columna,
                        mode="lines+markers+text",
                        text=q[columna].map(
                            lambda x: f"{x:.0f}"
                        ),
                        textposition="top center",
                        line=dict(width=3, color=color)
                    )

                st.plotly_chart(
                    estilo_figura(
                        fig,
                        "Número de pedido (ID)",
                        "Monto (Bs.)"
                    ),
                    use_container_width=True
                )

            st.divider()
            izquierda, derecha = st.columns(2)

            with izquierda:
                st.subheader("3. Unidades vendidas por producto")

                q = df.groupby(
                    "Producto",
                    as_index=False
                ).agg(
                    Unidades=("Cantidad", "sum")
                ).sort_values("Unidades")

                fig = px.bar(
                    q,
                    x="Unidades",
                    y="Producto",
                    orientation="h",
                    text="Unidades",
                    color="Unidades",
                    color_continuous_scale="Teal"
                )

                fig.update_traces(
                    textposition="outside",
                    cliponaxis=False
                )

                st.plotly_chart(
                    estilo_figura(
                        fig,
                        "Unidades vendidas",
                        "Producto"
                    ),
                    use_container_width=True
                )

            with derecha:
                st.subheader("4. Ingresos por método de pago")

                q = df.groupby(
                    "Metodo_Pago",
                    as_index=False
                ).agg(
                    Ingresos=("Ingreso_Total", "sum"),
                    Pedidos=("ID_Pedido", "nunique")
                )

                fig = px.pie(
                    q,
                    names="Metodo_Pago",
                    values="Ingresos",
                    hole=0.45,
                    color_discrete_sequence=[
                        "#A78BFA",
                        "#22D3EE",
                        "#FB7185"
                    ]
                )

                fig.update_traces(
                    textinfo="label+value+percent",
                    texttemplate=(
                        "%{label}<br>"
                        "Bs. %{value:.2f}<br>"
                        "%{percent}"
                    ),
                    hovertemplate=(
                        "%{label}<br>"
                        "Ingresos: Bs. %{value:.2f}<br>"
                        "Pedidos: %{customdata[0]}<extra></extra>"
                    ),
                    customdata=q[["Pedidos"]]
                )

                st.plotly_chart(
                    estilo_figura(
                        fig,
                        "Método de pago",
                        "Participación de ingresos"
                    ),
                    use_container_width=True
                )

            st.divider()
            izquierda, derecha = st.columns(2)

            with izquierda:
                st.subheader(
                    "5. Evolución diaria: ingresos, costos y utilidad"
                )

                q = df.groupby(
                    "Fecha",
                    as_index=False
                ).agg(
                    Ingresos=("Ingreso_Total", "sum"),
                    Costos=("Costo_Total", "sum"),
                    Utilidad=("Ganancia_Neta", "sum")
                ).sort_values("Fecha")

                fig = go.Figure()

                for columna, color in [
                    ("Ingresos", "#22D3EE"),
                    ("Costos", "#FB7185"),
                    ("Utilidad", "#4ADE80")
                ]:
                    fig.add_scatter(
                        x=q["Fecha"],
                        y=q[columna],
                        name=columna,
                        mode="lines+markers+text",
                        text=q[columna].map(
                            lambda x: f"{x:.0f}"
                        ),
                        textposition="top center",
                        line=dict(width=3, color=color)
                    )

                st.plotly_chart(
                    estilo_figura(
                        fig,
                        "Fecha",
                        "Monto (Bs.)"
                    ),
                    use_container_width=True
                )

            with derecha:
                st.subheader("6. Ingresos por hora")

                q = df.groupby(
                    "Hora_Entera",
                    as_index=False
                ).agg(
                    Ingresos=("Ingreso_Total", "sum"),
                    Pedidos=("ID_Pedido", "nunique")
                ).sort_values("Hora_Entera")

                fig = px.bar(
                    q,
                    x="Hora_Entera",
                    y="Ingresos",
                    text="Ingresos",
                    color="Ingresos",
                    color_continuous_scale="Plasma",
                    hover_data=["Pedidos"]
                )

                fig.update_traces(
                    texttemplate="Bs. %{text:.2f}",
                    textposition="outside",
                    cliponaxis=False
                )

                st.plotly_chart(
                    estilo_figura(
                        fig,
                        "Hora del día",
                        "Ingresos (Bs.)"
                    ),
                    use_container_width=True
                )

            st.divider()
            st.subheader("📋 Tabla de rendimiento por producto")

            tabla = df.groupby(
                ["Producto", "Categoria"],
                as_index=False
            ).agg(
                Unidades=("Cantidad", "sum"),
                Ingresos=("Ingreso_Total", "sum"),
                Costos=("Costo_Total", "sum"),
                Utilidad=("Ganancia_Neta", "sum")
            )

            tabla["Margen (%)"] = (
                tabla["Utilidad"]
                / tabla["Ingresos"].replace(0, 1)
                * 100
            )

            st.dataframe(
                tabla.style.format({
                    "Ingresos": "Bs. {:.2f}",
                    "Costos": "Bs. {:.2f}",
                    "Utilidad": "Bs. {:.2f}",
                    "Margen (%)": "{:.2f}%"
                }),
                use_container_width=True,
                hide_index=True
            )

            st.subheader("📅 Resumen diario")

            diario = df.groupby(
                "Fecha",
                as_index=False
            ).agg(
                Pedidos=("ID_Pedido", "nunique"),
                Unidades=("Cantidad", "sum"),
                Ingresos=("Ingreso_Total", "sum"),
                Costos=("Costo_Total", "sum"),
                Utilidad=("Ganancia_Neta", "sum")
            )

            st.dataframe(
                diario.style.format({
                    "Ingresos": "Bs. {:.2f}",
                    "Costos": "Bs. {:.2f}",
                    "Utilidad": "Bs. {:.2f}"
                }),
                use_container_width=True,
                hide_index=True
            )


# =========================================================
# 4. BASE DE DATOS Y COPIAS DE SEGURIDAD
# =========================================================

elif menu == "🗄️ Base de datos Excel":
    st.header("🗄️ Base de datos permanente en Excel")

    st.write(
        "Las ventas históricas se conservan entre días. "
        "Cada guardado crea una copia de seguridad del archivo anterior."
    )

    st.code(str(DB))
    st.caption(f"Carpeta de respaldos: {BACKUP_DIR}")

    a, b, c = st.columns(3)

    a.metric("Ventas guardadas", len(st.session_state.ventas))
    b.metric("Productos", len(st.session_state.inventario))
    c.metric(
        "Copias de seguridad",
        len(list(BACKUP_DIR.glob("frappes_database_*.xlsx")))
    )

    tab1, tab2, tab3 = st.tabs([
        "📦 Inventario",
        "💰 Ventas",
        "🧾 Detalle de ventas"
    ])

    with tab1:
        st.dataframe(
            pd.DataFrame([
                {"Producto": nombre, **producto}
                for nombre, producto
                in st.session_state.inventario.items()
            ]),
            use_container_width=True,
            hide_index=True
        )

    with tab2:
        st.dataframe(
            pd.DataFrame([
                {
                    "ID": venta["id"],
                    "Fecha": venta["fecha"],
                    "Hora": venta["hora"],
                    "Cliente": venta["cliente"],
                    "Total": venta["total_venta"],
                    "Costo": venta["costo_total"],
                    "Utilidad": venta["ganancia_neta"],
                    "Estado": venta["estado"]
                }
                for venta in st.session_state.ventas
            ]),
            use_container_width=True,
            hide_index=True
        )

    with tab3:
        st.dataframe(
            obtener_detalles(),
            use_container_width=True,
            hide_index=True
        )

    if DB.exists():
        st.download_button(
            "⬇️ Descargar copia actual de la base de datos",
            data=DB.read_bytes(),
            file_name=(
                f"frappes_database_copia_"
                f"{ahora():%Y%m%d_%H%M}.xlsx"
            ),
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            use_container_width=True
        )

    if st.button(
        "💾 Guardar base de datos ahora",
        use_container_width=True
    ):
        try:
            guardar_db()
            st.success(
                "Base de datos guardada. "
                "Se creó respaldo del archivo anterior."
            )
            st.rerun()

        except Exception as e:
            st.error(f"No se pudo guardar: {e}")

    st.subheader("🛟 Copias de seguridad disponibles")

    copias = sorted(
        BACKUP_DIR.glob("frappes_database_*.xlsx"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

    if copias:
        df_copias = pd.DataFrame([
            {
                "Archivo": p.name,
                "Fecha de creación": datetime.fromtimestamp(
                    p.stat().st_mtime
                ).strftime("%d/%m/%Y %H:%M:%S"),
                "Tamaño (KB)": round(p.stat().st_size / 1024, 1)
            }
            for p in copias[:100]
        ])

        st.dataframe(
            df_copias,
            use_container_width=True,
            hide_index=True
        )

        elegido = st.selectbox(
            "Descargar un respaldo",
            copias,
            format_func=lambda p: p.name
        )

        st.download_button(
            "⬇️ Descargar respaldo seleccionado",
            data=elegido.read_bytes(),
            file_name=elegido.name,
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            )
        )

    else:
        st.info(
            "Las copias se crearán automáticamente antes "
            "del siguiente guardado que modifique el archivo."
        )


# =========================================================
# 5. EXPORTACIÓN BI
# =========================================================

elif menu == "📤 Exportar reporte BI":
    st.header("📤 Suite de inteligencia de negocios")

    st.write(
        "Genera un Excel analítico con tablas, indicadores y gráficos."
    )

    if st.button(
        "🚀 Generar Excel profesional",
        use_container_width=True
    ):
        df = obtener_detalles()

        ventas_df = pd.DataFrame([
            {
                "ID": venta["id"],
                "Fecha": venta["fecha"],
                "Hora": venta["hora"],
                "Cliente": venta["cliente"],
                "Modalidad": venta["servicio"],
                "Metodo_Pago": venta["pago"],
                "Notas": venta.get("notas", ""),
                "Total_Venta": venta["total_venta"],
                "Costo_Total": venta["costo_total"],
                "Ganancia_Neta": venta["ganancia_neta"],
                "Estado": venta["estado"]
            }
            for venta in st.session_state.ventas
        ])

        if not df.empty:
            productos = df.groupby(
                ["Producto", "Categoria"],
                as_index=False
            ).agg(
                Unidades=("Cantidad", "sum"),
                Ingresos=("Ingreso_Total", "sum"),
                Costos=("Costo_Total", "sum"),
                Utilidad=("Ganancia_Neta", "sum")
            )

        else:
            productos = pd.DataFrame(
                columns=[
                    "Producto", "Categoria", "Unidades",
                    "Ingresos", "Costos", "Utilidad"
                ]
            )

        if not productos.empty:
            productos["Margen_%"] = (
                productos["Utilidad"]
                / productos["Ingresos"].replace(0, 1)
            )

            total_ing = productos["Ingresos"].sum()

            productos["Participacion_%"] = (
                productos["Ingresos"] / total_ing
                if total_ing
                else 0
            )

        else:
            productos["Margen_%"] = []
            productos["Participacion_%"] = []

        if not df.empty:
            pagos = df.groupby(
                "Metodo_Pago",
                as_index=False
            ).agg(
                Pedidos=("ID_Pedido", "nunique"),
                Ingresos=("Ingreso_Total", "sum")
            )

            diario = df.groupby(
                "Fecha",
                as_index=False
            ).agg(
                Pedidos=("ID_Pedido", "nunique"),
                Unidades=("Cantidad", "sum"),
                Ingresos=("Ingreso_Total", "sum"),
                Costos=("Costo_Total", "sum"),
                Utilidad=("Ganancia_Neta", "sum")
            )

        else:
            pagos = pd.DataFrame(
                columns=["Metodo_Pago", "Pedidos", "Ingresos"]
            )

            diario = pd.DataFrame(
                columns=[
                    "Fecha", "Pedidos", "Unidades",
                    "Ingresos", "Costos", "Utilidad"
                ]
            )

        inv_df = pd.DataFrame([
            {
                "Producto": nombre,
                "Categoria": producto["categoria"],
                "Precio": producto["precio"],
                "Costo": producto["costo"],
                "Stock": producto["stock"],
                "Utilidad_Unit": (
                    producto["precio"] - producto["costo"]
                )
            }
            for nombre, producto
            in st.session_state.inventario.items()
        ])

        salida = BytesIO()

        with pd.ExcelWriter(
            salida,
            engine="openpyxl"
        ) as writer:
            productos.to_excel(
                writer,
                sheet_name="Productos",
                index=False
            )

            pagos.to_excel(
                writer,
                sheet_name="Metodos de Pago",
                index=False
            )

            diario.to_excel(
                writer,
                sheet_name="Resumen Diario",
                index=False
            )

            inv_df.to_excel(
                writer,
                sheet_name="Inventario",
                index=False
            )

            ventas_df.to_excel(
                writer,
                sheet_name="Ventas",
                index=False
            )

            df.to_excel(
                writer,
                sheet_name="Detalle Ventas",
                index=False
            )

            wb = writer.book

            for ws in wb.worksheets:
                ws.freeze_panes = "A2"
                ws.sheet_view.showGridLines = False

                for celda in ws[1]:
                    celda.fill = PatternFill(
                        "solid",
                        fgColor="16324F"
                    )
                    celda.font = Font(
                        bold=True,
                        color="FFFFFF"
                    )
                    celda.alignment = Alignment(
                        horizontal="center"
                    )

                for columna in ws.columns:
                    letra = get_column_letter(
                        columna[0].column
                    )

                    ancho = max(
                        [
                            len(str(c.value))
                            if c.value is not None
                            else 0
                            for c in columna
                        ] + [12]
                    )

                    ws.column_dimensions[letra].width = min(
                        max(ancho + 3, 14),
                        35
                    )

                if ws.max_row >= 2 and ws.max_column:
                    nombre_tabla = (
                        "Tabla"
                        + "".join(
                            ch for ch in ws.title
                            if ch.isalnum()
                        )[:20]
                    )

                    tabla = Table(
                        displayName=nombre_tabla,
                        ref=ws.dimensions
                    )

                    tabla.tableStyleInfo = TableStyleInfo(
                        name="TableStyleMedium2",
                        showRowStripes=True
                    )

                    ws.add_table(tabla)

            # Dashboard principal de Excel
            dash = wb.create_sheet(
                "Dashboard Ejecutivo",
                0
            )

            dash.sheet_view.showGridLines = False
            dash.merge_cells("B2:Q2")
            dash["B2"] = "FRAPPÉS POS | DASHBOARD EJECUTIVO"

            dash["B2"].fill = PatternFill(
                "solid",
                fgColor="102A43"
            )

            dash["B2"].font = Font(
                size=18,
                bold=True,
                color="FFFFFF"
            )

            dash["B2"].alignment = Alignment(
                horizontal="center"
            )

            dash.row_dimensions[2].height = 38

            total_ingresos = (
                float(ventas_df["Total_Venta"].sum())
                if not ventas_df.empty
                else 0
            )

            total_costos = (
                float(ventas_df["Costo_Total"].sum())
                if not ventas_df.empty
                else 0
            )

            total_utilidad = (
                float(ventas_df["Ganancia_Neta"].sum())
                if not ventas_df.empty
                else 0
            )

            unidades = (
                int(df["Cantidad"].sum())
                if not df.empty
                else 0
            )

            tarjetas = [
                (
                    "INGRESOS (Bs.)",
                    total_ingresos,
                    "B", "D",
                    "0891B2",
                    "#,##0.00"
                ),
                (
                    "COSTOS (Bs.)",
                    total_costos,
                    "E", "G",
                    "D97706",
                    "#,##0.00"
                ),
                (
                    "UTILIDAD (Bs.)",
                    total_utilidad,
                    "H", "J",
                    "15803D",
                    "#,##0.00"
                ),
                (
                    "MARGEN",
                    total_utilidad / total_ingresos
                    if total_ingresos else 0,
                    "K", "M",
                    "6D28D9",
                    "0.00%"
                ),
                (
                    "PEDIDOS",
                    len(ventas_df),
                    "N", "O",
                    "BE185D",
                    "#,##0"
                ),
                (
                    "UNIDADES",
                    unidades,
                    "P", "Q",
                    "0F766E",
                    "#,##0"
                )
            ]

            for (
                etiqueta,
                valor,
                col_inicio,
                col_fin,
                color,
                formato
            ) in tarjetas:
                dash.merge_cells(
                    f"{col_inicio}4:{col_fin}4"
                )

                dash.merge_cells(
                    f"{col_inicio}5:{col_fin}6"
                )

                encabezado = dash[f"{col_inicio}4"]
                encabezado.value = etiqueta
                encabezado.fill = PatternFill(
                    "solid",
                    fgColor=color
                )
                encabezado.font = Font(
                    bold=True,
                    color="FFFFFF"
                )
                encabezado.alignment = Alignment(
                    horizontal="center"
                )

                celda_valor = dash[f"{col_inicio}5"]
                celda_valor.value = valor
                celda_valor.number_format = formato
                celda_valor.fill = PatternFill(
                    "solid",
                    fgColor="EAF2F8"
                )
                celda_valor.font = Font(
                    size=14,
                    bold=True,
                    color="102A43"
                )
                celda_valor.alignment = Alignment(
                    horizontal="center",
                    vertical="center"
                )

            dash["B8"] = "RENDIMIENTO POR PRODUCTO"
            dash["B8"].font = Font(
                bold=True,
                size=12,
                color="102A43"
            )

            columnas_dashboard = [
                "Producto",
                "Categoria",
                "Unidades",
                "Ingresos",
                "Costos",
                "Utilidad",
                "Margen_%",
                "Participacion_%"
            ]

            for j, nombre_columna in enumerate(
                columnas_dashboard,
                2
            ):
                celda = dash.cell(
                    9,
                    j,
                    nombre_columna
                )
                celda.fill = PatternFill(
                    "solid",
                    fgColor="16324F"
                )
                celda.font = Font(
                    bold=True,
                    color="FFFFFF"
                )

            if not productos.empty:
                for i, fila in enumerate(
                    productos[columnas_dashboard].itertuples(
                        index=False,
                        name=None
                    ),
                    10
                ):
                    for j, valor in enumerate(fila, 2):
                        dash.cell(i, j, valor)

            # Gráficos de Excel
            if not productos.empty:
                from openpyxl.chart import BarChart, Reference
                from openpyxl.chart.label import DataLabelList

                graficos = [
                    (
                        "Ingresos por producto (Bs.)",
                        4,
                        "B25"
                    ),
                    (
                        "Costos por producto (Bs.)",
                        5,
                        "J25"
                    ),
                    (
                        "Utilidad por producto (Bs.)",
                        6,
                        "B42"
                    ),
                    (
                        "Unidades vendidas por producto",
                        3,
                        "J42"
                    )
                ]

                for titulo, columna, ubicacion in graficos:
                    grafico = BarChart()
                    grafico.type = "bar"
                    grafico.style = 10
                    grafico.title = titulo
                    grafico.x_axis.title = "Monto / unidades"
                    grafico.y_axis.title = "Producto"
                    grafico.height = 8
                    grafico.width = 15

                    grafico.add_data(
                        Reference(
                            dash,
                            min_col=columna,
                            min_row=9,
                            max_row=9 + len(productos)
                        ),
                        titles_from_data=True
                    )

                    grafico.set_categories(
                        Reference(
                            dash,
                            min_col=2,
                            min_row=10,
                            max_row=9 + len(productos)
                        )
                    )

                    grafico.legend = None
                    grafico.dataLabels = DataLabelList()
                    grafico.dataLabels.showVal = True

                    dash.add_chart(
                        grafico,
                        ubicacion
                    )

            for columna in range(1, 18):
                dash.column_dimensions[
                    get_column_letter(columna)
                ].width = 15

        st.session_state.reporte_bi = salida.getvalue()

        st.success(
            "Excel profesional generado correctamente."
        )

    if "reporte_bi" in st.session_state:
        st.download_button(
            "⬇️ DESCARGAR EXCEL CON DASHBOARD",
            data=st.session_state.reporte_bi,
            file_name=(
                f"Frappes_Dashboard_"
                f"{ahora():%Y%m%d_%H%M}.xlsx"
            ),
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            use_container_width=True
        )


# =========================================================
# MENSAJE FINAL
# =========================================================

st.sidebar.divider()

st.sidebar.caption(
    "Consejo: conserva periódicamente una copia fuera de este equipo. "
    "El almacenamiento local no protege contra daño físico, "
    "robo o pérdida del disco."
)
