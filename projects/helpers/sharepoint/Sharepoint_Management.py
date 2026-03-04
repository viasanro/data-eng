# Databricks notebook source
from office365.runtime.auth.authentication_context import ClientCredential
from office365.sharepoint.client_context import ClientContext
from office365.sharepoint.files.file import File

# COMMAND ----------

class SharepointManagement():
  """Clase para administrar (listar, bajar, subir) archivos de Sharepoint."""
  def __init__(self, tenant_name, site, subfolder, secretuser, secretpass):
    """Inicializa la clase con los parametros necesarios para conectarse a Sharepoint.
    
    Args:
        tenant_name (str): Nombre del inquilino de Sharepoint (ejemplo: <mytenantname>)
        site (str): Nombre del sitio de Sharepoint (ejemplo: <mysitename>)
        subfolder (str): Nombre del subdirectorio donde se almacenaran los archivos (ejemplo: <subdirectoriodentrodelsite>)
        secretuser (str): Nombre del secret de Azure Key Vault con el usuario para conectarse al sitio (ejemplo: <secretuser>)
        secretpass (str): Nombre del secret de Azure Key Vault con la contraseña para conectarse al sitio (ejemplo: <secretpassword>)
    """
    self.tenant_name = tenant_name
    self.site = site
    self.user = dbutils.secrets.get(scope = 'KeyVault', key = secretuser)
    self.password = dbutils.secrets.get(scope = 'KeyVault', key = secretpass)
    self.site_url = f'https://{tenant_name}.sharepoint.com/sites/{site}'
    self.folder_relative_url = f"/sites/{site}/Shared Documents/{subfolder}"

  def setUrlDescarga(self,url_descarga):
    """Establece la url del archivo a descargar.
        Args:
            url_descarga (str): Url del archivo a descargar (ejemplo: /sites/mysitename/Shared%20Documents/subfolder/filename.xlsx)
    """
    self.url_descarga = url_descarga
  
  def __conectar(self):
    """Establece la conexion a Sharepoint y devuelve el contexto de conexión."""
    try:
      credentials = ClientCredential(self.user, self.password)
      ctx = ClientContext(self.site_url).with_credentials(credentials)
      return ctx
    except Exception as e:
      return e
  
  def listArchivos(self):
    """Devuelve una lista con los nombres de los archivos contenidos en el subdirectorio establecido en la variable self.folder_relative_url."""
    try:
      ctx = self.__conectar()
    except Exception as e:
      return e
    folder = ctx.web.get_folder_by_server_relative_url(self.folder_relative_url)
    folder_content = folder.files 
    ctx.load(folder_content)
    ctx.execute_query()
    archivos = [item.name for item in folder_content]
    return archivos

  def downloadArchivo(self, filename):
    """Descarga el archivo especificado en la variable url_descarga a la ruta especificada por la variable filename.
        Args:
            filename (str): Ruta donde se almacenara el archivo (ejemplo: /dbfs/local_disk0/tmp/nombreArchivo.xlsx)
    """
    try:
      ctx = self.__conectar()
  
      with open(filename, 'wb') as outputfile:
        response = File.open_binary(ctx, self.url_descarga )
        outputfile.write(response.content)
      
    except Exception as e:
      return e
    
  
  def uploadArchivo(self, nombre, contenido):
    """Sube el archivo con el nombre y contenido especificados a la ruta especificada por la variable self.folder_relative_url.
        Args:
            nombre (str): Nombre del archivo (ejemplo: filename.xlsx)
            contenido (bytes): Datos binarios que representan el contenido del archivo (archivo Excel en nuestro caso)
    """  
    try:
      ctx = self.__conectar()
      target_folder = self.folder_relative_url
      target_folder = ctx.web.get_folder_by_server_relative_url(target_folder)
      target_folder.upload_file(nombre, contenido).execute_query()
    except Exception as e:
      return e
