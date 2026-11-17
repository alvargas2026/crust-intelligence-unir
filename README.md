# San Francisco Crust Pizza · Dashboard UNIR

Aplicación Streamlit con datos oficiales del caso. Incluye KPIs, filtros, visualizaciones, actualización de archivos y asistente de IA opcional.

## Ejecución local

1. Instalar Python 3.10 o posterior.
2. Desde esta carpeta ejecutar `pip install -r requirements.txt`.
3. Ejecutar `streamlit run app.py`.
4. Abrir la URL local mostrada en la terminal.

## Actualización de datos

En la barra lateral, subir un nuevo Excel/CSV de ventas. La aplicación recalcula los resultados sin cambiar código. Si aparecen nuevos ClienteID o ProductoID, subir también los catálogos actualizados. Los archivos nuevos deben mantener las columnas obligatorias. Las cargas son temporales para la sesión; no sustituyen los archivos del servidor.

## Asistente de IA

El asistente generativo requiere clave API de OpenAI: ingresarla en el campo privado de la interfaz o configurar `OPENAI_API_KEY` en los secretos de Streamlit. Sin clave, la aplicación muestra hallazgos calculados por reglas, identificados como tales. La API puede generar costos. El contexto enviado a la API contiene agregados, no nombres individuales de clientes.

## Despliegue público

Subir el proyecto a un repositorio Git y desplegarlo en Streamlit Community Cloud u otro alojamiento compatible. Configurar la clave API en los secretos del alojamiento (nunca en Git). Probar el enlace público en ventana privada antes de entregarlo. Verificar políticas de privacidad y derechos de publicación de las bases antes de compartirlas públicamente.

## Fórmulas

Ventas = suma(VentaNeta); utilidad = suma(UtilidadBruta); margen = utilidad/ventas; ticket = ventas/VentaID únicos; clientes = ClienteID únicos; transacciones = VentaID únicos. Ciudad se toma de ventas, no de la residencia del cliente.

## Pendiente para entrega UNIR

Publicar URL accesible, ejecutar revisión visual en navegador, probar IA con clave válida, analizar hallazgos y redactar documento, presentación y video. Los resultados deben validarse con los datos antes de presentar conclusiones.
