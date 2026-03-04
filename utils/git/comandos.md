>Inicializa un directorio para utilizarlo de repositorio local<br>

git init<br>

>Verificamos la configuracion actual<br>

git config -l<br>
#Modificamos el email
git config --global -user.email "youremail@example.com"
#Para modificar el usuario 
git config --global -user.name "yourusername"
#Agrega al area de staging los cambios realizados en el directorio 
git add .
#Agrega al repositorio local los cambios del listos en el area de staging
git commit -m "mensaje"
#Muestra el estado actual del area de staging
git status
#Muestra el historial de los commits realizados
git log
#Muestra estadisticas de los cambios realizados en cada commit
git log --stat
#Cambia el HEAD o puntero al ID del commit indicado
git checkout id9ir932f9230
#HEAD: Saca archivos del area de Staging, no los borra
#hard: Borra todo, absolutamente todo.
#Soft: Borra todo el historial y registros del git, pero guarda el los cambios
#que tengamos en staging. 
git reset HEAD or --hard or --soft
#cached: Elimina los archivos de nuestro repositorio local y del area de staging
pero los mantiene en nuestro disco duro. Le dice a Git que deje de trackear.
#forced: elimina los archivos de Git y del disco duro.
git rm --cached or --forced File
#Muestra los cambios realizados en el ultimo commit
git show
#Muestra las diferencias entre el archivo actual y el ultimo commit.
git diff
#Generamos una clave SSH
ssh-keygen -t rsa -b 4096 -C "youremail@example.com"
#Comprobar el proceso de creacion SSH y agregarlo en Windows 
eval $(ssh-agent - s)
ssh-add ~/.ssh/id_rsa
#Agrega un repositorio remoto para poder accederlo localmente.
git remote add origin URL
#Agrega un repositorio remoto para mantener actualizado el fork.
git remote add upstream URL
git pull upstream master
git push origin master
#Muestra los repositorios remotos accesibles actualmente
git remote
#Muestra la ruta de los repositorios remotos disponibles
git remote -v
#Descarga los ultimos cambios presentes en el servidor remoto
git pull origin main
#Permite descargas aunque no sean de las mismas ramas
git pull origin main --allow-unrelated-histories
#Envia los cambios que tenemos en el repositorio local del branch master al repositorio remoto
git push origin master
#Cambia la URL del repositorio remoto
git remote set-url origin URL_SSH_REMOTO
#Muestra una estructura de arblo del git log
git log --all --graph --decorate --oneline
#Agrega un alias al comando
alias arbolito "git log --all --graph --decorate --oneline"
#Agregar etiquetas como por ejemplo de versionado a un ID de commit especifico
git tag -a v0.1 -m "Versionado" id8fuf5
#Muestra las etiquetas activas creadas previamente
git tag
#Muestra la referecia asociada al tag especifico
git show-ref --tags
#Envia los tags previamente creados al repositorio remoto
git push origin --tags
#Borra el tag especifico del repositorio local
git tag -d v0.1
#Borra el tag especifico del repositorio remoto
git push origin :refs/tags/v0.1
#Crear una rama
git branch nombreRama
#Borrar una rama
git branch -D nombreRama
#Nos permite cambiar de branch
git checkout rama
#Lista las ramas disponibles
git branch
#Nos muestra las ramas con sus historias
git show-branch --all
#Enviamos nuestra rama al repositorio remoto
git push origin rama
#Rebase. Nos permite cambiar la historia del commit de una rama
#Reorganizar el trabajo realizado, solo usarlo de manera local
#Primero siempre realizarlo en la rama que va a desaparecer o experimental, luego en la rama principal
git rebase nombreRamaExperimental
git rebase master
#Mostrar graficamente la historia de los commits
gitk
#Stash. Para agregar cambios a un lugar temporal denominado stash
#Su uso es tipico cuando estamos modificando algo y no queremos guardar los cambios
git stash
#Stash es una lista de estados que nos permite guardar cambios para despues.
#Stash. Podemos agregar mensajes al stash para poder identificarlos
git stash save "mensaje asociado al stash"
#Stash se comporta como un stack de datos de manera LIFO. Pop recupera el ultimo estado del stashed
git stash pop
#Stash. Listado de elementos del stash
git stash list
#Crear una rama con el stash
git stash branch <nombre de rama>
#Eliminar el elemento mas reciente del stash
git stash drop
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



