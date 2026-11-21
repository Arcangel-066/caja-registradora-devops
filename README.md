# Caja Registradora Inteligente

Aplicación web en Flask para la gestión de productos, inventario, ventas
e ingresos, desarrollada como proyecto integrador de DevOps, Docker y
Automatización. Ver `proyecto_caja_registradora_inteligente.md` para la
especificación completa.

## Ejecución local (sin Docker)

```bash
python -m venv venv
source venv/bin/activate        # En Windows: venv\Scripts\activate

pip install -r requirements.txt

python init_db.py               # Crea data/database.db con productos de ejemplo
python app.py                   # Inicia en http://localhost:5000
```

## Ejecución con Docker

```bash
docker build -t caja-registradora:1.0 .

docker run -d \
  --name caja-app \
  -p 5000:5000 \
  -v caja-datos:/app/data \
  caja-registradora:1.0
```

Luego abrir: http://localhost:5000

El volumen `caja-datos` conserva `database.db` aunque el contenedor se
elimine o se reemplace por una nueva versión.

## Estructura del proyecto

```
caja-registradora/
├── app.py                  # Rutas y lógica de la aplicación Flask
├── init_db.py               # Creación de tablas y datos de ejemplo
├── requirements.txt
├── Dockerfile
├── Jenkinsfile
├── .gitignore
├── templates/
│   ├── base.html
│   ├── index.html            # Panel principal (dashboard)
│   ├── productos.html        # CRUD de productos
│   ├── ventas.html           # Registro de ventas
│   └── ventas_historial.html # Historial de ventas
└── static/
    ├── css/style.css
    └── js/app.js
```

## Siguientes pasos sugeridos (Git, GitHub, Jenkins)

```bash
git init
git add .
git commit -m "chore: iniciar proyecto caja registradora"
git remote add origin https://github.com/TU_USUARIO/caja-registradora-devops.git
git branch -M main
git push -u origin main
```

Configurar un webhook de GitHub hacia Jenkins para que el `Jenkinsfile`
incluido reconstruya la imagen Docker y redepliegue el contenedor en
cada `push` a `main`.
