### **Comandos Esenciales**<br><br>

>Help<br>

git *comando* --help

>Inicializa un directorio para utilizarlo de repositorio local<br>

git init<br>

>Verificamos la configuracion actual<br>

git config -l<br>

>Modificamos el email<br>

git config --global -user.email *"youremail@example.com"*<br>

>Para modificar el usuario<br>

git config --global -user.name *"yourusername"*<br>

>Crear una rama<br>

git branch *nombreRama*<br>

>Borrar una rama<br>

git branch -D *nombreRama*<br>

>Nos permite cambiar de branch<br>

git checkout *rama*<br>

>Lista las ramas disponibles<br>

git branch<br>

>Visualizar las ramas remotas<br>

git branch -r<br>

>Visualizar todas las ramas<br>

git branch -a<br>

>Agrega al area de staging los cambios realizados en el directorio<br>

git add .<br>

>Agrega al repositorio local los cambios del listos en el area de staging<br>

git commit -m *"mensaje"*<br>

>Muestra el estado actual del area de staging<br>

git status<br>

>Muestra el historial de los commits realizados<br>

git log<br>

>Muestra estadisticas de los cambios realizados en cada commit<br>

git log --stat<br>

>Cambia el puntero HEAD al ID del commit indicado<br>

git checkout *id9ir932f9230*<br>

>Mueve la rama a un commit anterior. Reescribe la historia<br>

git reset HEAD or --hard or --soft<br>
- **HEAD:** Saca archivos del area de Staging, no los borra<br>
- **hard:** Borra todo, absolutamente todo<br>
- **Soft:** Borra todo el historial y registros del git, pero guarda el los cambios<br>

>Eliminación de archivos<br>

git rm --cached or --forced *File*<br>
- **cached:** Elimina los archivos de nuestro repositorio local y del area de staging
pero los mantiene en nuestro disco duro. Le dice a Git que deje de trackear.<br>
- **forced:** elimina los archivos de Git y del disco duro.<br>

>Muestra los cambios realizados en el ultimo commit<br>

git show<br>

>Muestra las diferencias entre el archivo actual y el ultimo commit<br>

git diff<br>

>Muestra los repositorios remotos accesibles actualmente<br>

git remote<br>

>Muestra la ruta de los repositorios remotos disponibles<br>

git remote -v<br>

>Agrega un repositorio remoto para poder accederlo localmente. Se usa si alias origin no existe<br>

git remote add origin *URL*<br>

>Cambia la URL del repositorio remoto. Se usa si el alias origin ya existe<br>

git remote set-url origin *URL_SSH_REMOTO*<br>

>Descarga los ultimos cambios presentes en el servidor remoto<br>

git pull origin main<br>

>Permite descargas aunque no sean de las mismas ramas<br>

git pull origin main --allow-unrelated-histories<br>

>Envia los cambios que tenemos en el repositorio local del branch main al repositorio remoto<br>

git push origin main<br>

>Enviamos nuestra rama al repositorio remoto<br>

git push origin rama<br>

>Rebase.<br>

git rebase *nombreRamaExperimental*<br>
git rebase *master*<br>
- Nos permite cambiar la historia del commit de una rama<br>
- Reorganizar el trabajo realizado, solo usarlo de manera local<br>
- Primero siempre realizarlo en la rama que va a desaparecer o experimental, luego en la rama principal<br><br>

>Stash<br>

git stash<br>
- Para agregar cambios a un lugar temporal denominado stash<br>
- Su uso es tipico cuando estamos modificando algo y no queremos guardar los cambios<br>
- Stash es una lista de estados que nos permite guardar cambios para despues<br><br>
- Stash. Podemos agregar mensajes al stash para poder identificarlos<br>

git stash save *"mensaje asociado al stash"*<br><br>
- Stash se comporta como un stack de datos de manera LIFO. Pop recupera el ultimo estado del stashed<br>

git stash pop<br><br>
- Stash. Listado de elementos del stash<br>

git stash list<br><br>
- Crear una rama con el stash<br>

git stash branch *nombre_de_rama*<br><br>
- Eliminar el elemento mas reciente del stash<br>

git stash drop<br><br>

### **Comandos Avanzados**<br><br>

>Clean<br> 

- Archivos que son parte de tu proyecto pero no deberias agregar, o que quieres borrar<br>
- Se exeptuan los archivos contenidos en el archivo *.gitignore*<br>
- --dry-run lista los archivos que va a borrar, pero no los borra aun<br>

git clean --dry-run<br><br>
- Para borrarlos ejecutamos el comando con el parametro -f<br>

git clean -f<br><br>

> Cherry-pick<br>

- Cuando necesitamos un avance de una de las ramas en la rama principal<br>
- Nos ubicamos en la rama y ejecutamos el siguiente comando para buscar el commit<br>

git checkout rama<br>
- Para listar y encontrar cual fue es el commit que nos interesa<br>

git log -oneline<br>  
git cherry-pick *commit_id*<br><br>

>amend 
- Lo que hace es remendar el ultimo commit realizado en caso de que nos haya faltado algo<br>
- Debemos de anhadir el cambio con add necesariamente luego se realiza el commit<br>

git add *File_or_Path*<br>
git commit --amend<br><br>

>Git Reset y Reflog<br>

- Usese en caso de emergencia<br>
- Aqui encontramos el hash como la posicion del head a lo largo del tiempo<br>
- Buscamos el ultimo hash donde funcionaba correctamente<br>

git reflog<br>
git reset --HARD *id_hash*<br>

> Búsqueda de archivos y commits de git con *grep* y *log*<br>

git grep -n *palabra*   *-n para saber en que linea utilice la palabra*<br>
git grep -c *palabra*   *-c para saber cuantas veces utilice la palabra*<br>
git log -S *palabra*    *Nos muestra toda vez que use la palabra en los commits*<br><br>

>Conteo de commits por usuario<br>

git shortlog -sn --all --no-merges<br><br>

### **Comandos Complementarios**<br>

>Generamos una clave SSH<br>

ssh-keygen -t rsa -b 4096 -C "youremail@example.com"<br>

>Comprobar el proceso de creacion SSH y agregarlo en Windows<br>

eval $(ssh-agent - s)<br>
ssh-add ~/.ssh/id_rsa<br>

>Agrega un repositorio remoto para mantener actualizado el fork<br>

git remote add upstream URL<br>
git pull upstream master<br>
git push origin master<br>

>Muestra una estructura de arblo del git log<br>

git log --all --graph --decorate --oneline<br>

>Agrega un alias al comando<br>

alias arbolito "git log --all --graph --decorate --oneline"<br>

>Agregar etiquetas como por ejemplo de versionado a un ID de commit especifico<br>

git tag -a v0.1 -m "Versionado" id8fuf5<br>

>Muestra las etiquetas activas creadas previamente<br>

git tag<br>

>Muestra la referecia asociada al tag especifico<br>

git show-ref --tags<br>

>Envia los tags previamente creados al repositorio remoto<br>

git push origin --tags<br>

>Borra el tag especifico del repositorio local<br>

git tag -d v0.1<br>

>Borra el tag especifico del repositorio remoto<br>

git push origin :refs/tags/v0.1<br>

>Nos muestra las ramas con sus historias<br>

git show-branch --all<br>

>Mostrar graficamente la historia de los commits<br>

gitk<br><br>

>git log<br>

- Te muestra el id commit y el titulo del commit.<br>

git log --oneline<br>

- Te muestra donde se encuentra el head point en el log.<br>

git log --decorate<br>

- Explica el numero de lineas que se cambiaron brevemente.<br>

git log --stat<br>

- Explica el numero de lineas que se cambiaron y te muestra que se cambio en el contenido.<br>

git log -p<br>

- Indica que commits ha realizado un usuario, mostrando el usuario y el titulo de sus commits.<br>

git shortlog<br>
git log --graph --oneline --decorate y<br>

- Muestra mensajes personalizados de los commits.<br>

git log --pretty=format:"%cn hizo un commit %h el dia %cd"<br>

- Limitamos el numero de commits.<br>

git log -3<br>

- Commits para localizar por fechas.<br>

git log --after="2018-1-2" ,<br>
git log --after="today" y<br>
git log --after="2018-1-2" --before="today"<br>

- Commits realizados por autor que cumplan exactamente con el nombre.<br>

git log --author="Name_Author"<br> 

- Busca los commits que cumplan tal cual esta escrito entre las comillas<br>

git log --grep="INVIE"<br>

-Busca los commits que cumplan sin importar mayusculas o minusculas.<br>

git log --grep="INVIE" -i <br>

- Busca los commits en un archivo en especifico.<br>

git log -- index.html<br>

- guardar los logs en un archivo txt<br>

git log > log.txt<br>