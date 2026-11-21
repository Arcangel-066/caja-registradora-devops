"""
Caja Registradora Inteligente
Aplicación web en Flask para la gestión de productos, inventario,
ventas e ingresos.
"""
import os
import sqlite3
from datetime import datetime

from flask import Flask, flash, redirect, render_template, request, url_for

from init_db import DB_PATH, init_db

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")


# ---------------------------------------------------------------------------
# Utilidades de acceso a datos
# ---------------------------------------------------------------------------
def get_db_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def validar_producto(nombre, precio, stock):
    if not nombre:
        return "El nombre del producto es obligatorio."
    try:
        precio_f = float(precio)
    except (TypeError, ValueError):
        return "El precio debe ser un número válido."
    if precio_f <= 0:
        return "El precio debe ser mayor que cero."
    try:
        stock_i = int(stock)
    except (TypeError, ValueError):
        return "El stock debe ser un número entero válido."
    if stock_i < 0:
        return "El stock no puede ser negativo."
    return None


# ---------------------------------------------------------------------------
# Panel principal (Dashboard)
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    conn = get_db_connection()
    hoy = datetime.now().strftime("%Y-%m-%d")

    total_ventas_hoy = conn.execute(
        "SELECT COALESCE(SUM(total), 0) AS total FROM ventas WHERE date(fecha) = ?",
        (hoy,),
    ).fetchone()["total"]

    cantidad_productos = conn.execute(
        "SELECT COUNT(*) AS total FROM productos"
    ).fetchone()["total"]

    ultima_venta = conn.execute(
        "SELECT * FROM ventas ORDER BY fecha DESC LIMIT 1"
    ).fetchone()

    ingresos_acumulados = conn.execute(
        "SELECT COALESCE(SUM(total), 0) AS total FROM ventas"
    ).fetchone()["total"]

    conn.close()

    return render_template(
        "index.html",
        total_ventas_hoy=total_ventas_hoy,
        cantidad_productos=cantidad_productos,
        ultima_venta=ultima_venta,
        ingresos_acumulados=ingresos_acumulados,
    )


# ---------------------------------------------------------------------------
# Gestión de productos (CRUD)
# ---------------------------------------------------------------------------
@app.route("/productos")
def listar_productos():
    conn = get_db_connection()
    productos = conn.execute("SELECT * FROM productos ORDER BY nombre").fetchall()
    conn.close()
    return render_template("productos.html", productos=productos)


@app.route("/productos/nuevo", methods=["POST"])
def crear_producto():
    nombre = request.form.get("nombre", "").strip()
    precio = request.form.get("precio", "")
    stock = request.form.get("stock", "")

    error = validar_producto(nombre, precio, stock)
    if error:
        flash(error, "error")
        return redirect(url_for("listar_productos"))

    conn = get_db_connection()
    conn.execute(
        "INSERT INTO productos (nombre, precio, stock) VALUES (?, ?, ?)",
        (nombre, float(precio), int(stock)),
    )
    conn.commit()
    conn.close()
    flash(f"Producto '{nombre}' creado correctamente.", "success")
    return redirect(url_for("listar_productos"))


@app.route("/productos/<int:producto_id>/editar", methods=["POST"])
def editar_producto(producto_id):
    nombre = request.form.get("nombre", "").strip()
    precio = request.form.get("precio", "")
    stock = request.form.get("stock", "")

    error = validar_producto(nombre, precio, stock)
    if error:
        flash(error, "error")
        return redirect(url_for("listar_productos"))

    conn = get_db_connection()
    conn.execute(
        "UPDATE productos SET nombre = ?, precio = ?, stock = ? WHERE id = ?",
        (nombre, float(precio), int(stock), producto_id),
    )
    conn.commit()
    conn.close()
    flash("Producto actualizado correctamente.", "success")
    return redirect(url_for("listar_productos"))


@app.route("/productos/<int:producto_id>/eliminar", methods=["POST"])
def eliminar_producto(producto_id):
    conn = get_db_connection()

    referencias = conn.execute(
        "SELECT COUNT(*) AS total FROM detalle_venta WHERE producto_id = ?",
        (producto_id,),
    ).fetchone()["total"]

    if referencias > 0:
        conn.close()
        flash(
            "No se puede eliminar: el producto tiene ventas registradas en el historial.",
            "error",
        )
        return redirect(url_for("listar_productos"))

    conn.execute("DELETE FROM productos WHERE id = ?", (producto_id,))
    conn.commit()
    conn.close()
    flash("Producto eliminado correctamente.", "success")
    return redirect(url_for("listar_productos"))


# ---------------------------------------------------------------------------
# Registro de ventas
# ---------------------------------------------------------------------------
@app.route("/ventas")
def registrar_venta_form():
    conn = get_db_connection()
    productos = conn.execute("SELECT * FROM productos ORDER BY nombre").fetchall()
    conn.close()
    return render_template("ventas.html", productos=productos)


@app.route("/ventas/nueva", methods=["POST"])
def registrar_venta():
    producto_ids = request.form.getlist("producto_id")
    cantidades = request.form.getlist("cantidad")

    items = []
    for pid, cant in zip(producto_ids, cantidades):
        if not pid or not cant:
            continue
        try:
            pid_i = int(pid)
            cant_i = int(cant)
        except ValueError:
            continue
        if cant_i > 0:
            items.append((pid_i, cant_i))

    if not items:
        flash("Debes seleccionar al menos un producto con una cantidad válida.", "error")
        return redirect(url_for("registrar_venta_form"))

    conn = get_db_connection()
    try:
        conn.execute("BEGIN")

        total_venta = 0.0
        detalles = []

        # 1. Validar existencia y stock, calcular subtotales
        for pid, cant in items:
            producto = conn.execute(
                "SELECT * FROM productos WHERE id = ?", (pid,)
            ).fetchone()

            if producto is None:
                raise ValueError(f"El producto con id {pid} no existe.")
            if producto["stock"] < cant:
                raise ValueError(
                    f"Stock insuficiente para '{producto['nombre']}' "
                    f"(disponible: {producto['stock']}, solicitado: {cant})."
                )

            subtotal = producto["precio"] * cant
            total_venta += subtotal
            detalles.append((pid, cant, subtotal))

        # 2. Registrar la venta
        cursor = conn.execute("INSERT INTO ventas (total) VALUES (?)", (total_venta,))
        venta_id = cursor.lastrowid

        # 3. Guardar el detalle y descontar inventario
        for pid, cant, subtotal in detalles:
            conn.execute(
                "INSERT INTO detalle_venta (venta_id, producto_id, cantidad, subtotal) "
                "VALUES (?, ?, ?, ?)",
                (venta_id, pid, cant, subtotal),
            )
            conn.execute(
                "UPDATE productos SET stock = stock - ? WHERE id = ?", (cant, pid)
            )

        conn.commit()
        flash(f"Venta registrada correctamente. Total: ${total_venta:,.2f}", "success")
    except ValueError as e:
        conn.rollback()
        flash(str(e), "error")
    finally:
        conn.close()

    return redirect(url_for("registrar_venta_form"))


# ---------------------------------------------------------------------------
# Historial de ventas
# ---------------------------------------------------------------------------
@app.route("/ventas/historial")
def historial_ventas():
    conn = get_db_connection()
    ventas = conn.execute("SELECT * FROM ventas ORDER BY fecha DESC").fetchall()

    historial = []
    for venta in ventas:
        detalles = conn.execute(
            """
            SELECT dv.cantidad, dv.subtotal, p.nombre
            FROM detalle_venta dv
            JOIN productos p ON p.id = dv.producto_id
            WHERE dv.venta_id = ?
            """,
            (venta["id"],),
        ).fetchall()
        historial.append({"venta": venta, "detalles": detalles})

    conn.close()
    return render_template("ventas_historial.html", historial=historial)


if __name__ == "__main__":
    init_db()
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=5000, debug=debug_mode)
