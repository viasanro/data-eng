**Esenciales**<br>

>Inicializa un directorio para utilizarlo de repositorio local<br>

git init<br>

>Verificamos la configuracion actual<br>

git config -l<br>

>Modificamos el email<br>

git config --global -user.email "youremail@example.com"<br>

>Para modificar el usuario<br>

git config --global -user.name "yourusername"<br>

>Crear una rama<br>

git branch nombreRama<br>

>Borrar una rama<br>

git branch -D nombreRama<br>

>Nos permite cambiar de branch<br>

git checkout rama<br>

>Lista las ramas disponibles<br>

git branch<br>

>Agrega al area de staging los cambios realizados en el directorio<br>

git add .<br>

>Agrega al repositorio local los cambios del listos en el area de staging<br>

git commit -m "mensaje"<br>

>Muestra el estado actual del area de staging<br>

git status<br>

>Muestra el historial de los commits realizados<br>

git log<br>

>Muestra estadisticas de los cambios realizados en cada commit<br>

git log --stat<br>

>Cambia el puntero HEAD al ID del commit indicado<br>

git checkout id9ir932f9230<br>

>Mueve la rama a un commit anterior. Reescribe la historia<br>

git reset HEAD or --hard or --soft<br>
- **HEAD:** Saca archivos del area de Staging, no los borra<br>
- **hard:** Borra todo, absolutamente todo<br>
- **Soft:** Borra todo el historial y registros del git, pero guarda el los cambios<br>

>Eliminación de archivos<br>

git rm --cached or --forced File<br>
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

git remote add origin URL<br>

>Cambia la URL del repositorio remoto. Se usa si el alias origin ya existe<br>

git remote set-url origin URL_SSH_REMOTO<br>

>Descarga los ultimos cambios presentes en el servidor remoto<br>

git pull origin main<br>

>Permite descargas aunque no sean de las mismas ramas<br>

git pull origin main --allow-unrelated-histories<br>

>Envia los cambios que tenemos en el repositorio local del branch main al repositorio remoto<br>

git push origin main<br>

>Enviamos nuestra rama al repositorio remoto<br>

git push origin rama<br>

>Rebase.<br>

git rebase nombreRamaExperimental<br>
git rebase master<br>
- Nos permite cambiar la historia del commit de una rama<br>
- Reorganizar el trabajo realizado, solo usarlo de manera local<br>
- Primero siempre realizarlo en la rama que va a desaparecer o experimental, luego en la rama principal<br><br>

>Stash<br>

git stash<br>
- Para agregar cambios a un lugar temporal denominado stash<br>
- Su uso es tipico cuando estamos modificando algo y no queremos guardar los cambios<br>
- Stash es una lista de estados que nos permite guardar cambios para despues<br><br>
- Stash. Podemos agregar mensajes al stash para poder identificarlos<br>

git stash save "mensaje asociado al stash"<br><br>
- Stash se comporta como un stack de datos de manera LIFO. Pop recupera el ultimo estado del stashed<br>

git stash pop<br><br>
- Stash. Listado de elementos del stash<br>

git stash list<br><br>
- Crear una rama con el stash<br>

git stash branch nombre_de_rama<br><br>
- Eliminar el elemento mas reciente del stash<br>

git stash drop<br><br>

**Complementarios** <br>

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

gitk<br>

#Clean. Archivos que son parte de tu proyecto pero no deberias agregar, o que quieres borrar.
#Se exeptuan los archivos contenidos en el archivo .gitignore
#--dry-run lista los archivos que va a borrar, pero no los borra aun.
git clean --dry-run
#Para borrarlos ejecutamos el comando con el parametro -f
git clean -f
#Cherry-pick. Cuando necesitamos un avance de una de las ramas en la rama principal
git checkout rama #nos ubicamos en la rama y ejecutamos el siguiente comando para buscar el commit
git log -oneline  #para listar y encontrar cual fue es el commit que nos interesa
git cherry-pick <commit_id>
#amend. Lo que hace es remendar el ultimo commit realizado en caso de que nos haya faltado algo.
#Debemos de anhadir el cambio con add necesariamente luego se realiza el commit.
git add <File or Path>
git commit --amend
#Git Reset y Reflog. Usese en caso de emergencia.
git reflog   #Aqui encontramos el hash como la posicion del head a lo largo del tiempo
             #Buscamos el ultimo hash donde funcionaba correctamente
git reset --HARD <id_hash>
#Buscar en archivos y commits de git con grep y log
git grep -n <palabra>   #-n para saber en que linea utilice la palabra
git grep -c <palabra>   #-c para saber cuantas veces utilice la palabra
git log -S <palabra>    #Nos muestra todas veces que use la palabra en los commits
#Ver cuantos commits se realizaron por usuario
git shortlog -sn --all --no-merges
#Visualizar las ramas remotas
git branch -r
#Visualizar todas las ramas
git branch -a
#Help del comando
git <comando> --help
