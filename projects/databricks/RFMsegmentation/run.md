#### Dataest
El dataset se encuentra en la carpeta data (online_retail.csv)<br>

#### Como ejecutarlo en databricks
1. Abre tu Workspace en Databricks
2. Click en Importar
3. Subir archivo 'rfm-segmentation.py'
4. Click en Data Ingestion
Aqui tienes la opcion de crear una tabla o subirlo directamente a un volumen.
Yo, particularmente los subí a un volumen, para usar la opcion read_files al leerlos, una vez que lo subas modficas las celdas 5 y 6 de la notebook respectivamente que es donde ser realiza el listado y   la carga de datos.
Importante: mantener el nombre de los dataframes para que el resto del código funcione.
6. Selecciona un Cluster
7. Ejecuta todas las celdas 