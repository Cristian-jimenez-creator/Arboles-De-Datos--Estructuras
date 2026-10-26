# Arboles-De-Datos--Estructuras
Antenas: red de señales. Prompt: nodo raíz.
Partes de un Árbol de datos Raíz: primer nodo de un Árbol. Nodos: elemento que contiene un Árbol. Nodo Padre: tiene al menos un hijo. Nodo Hijo: nodos que tienen un padre. Nodo Hermano: comparte a un mismo padre. Nodo Hoja: no tienen hijos,siempre se encuentran en los extremos de la estructura. 
# ¿Qué hice?: 
Un Explorador de Archivos interactivo tipo VS Code que permite crear, renombrar, eliminar, buscar en tiempo real, ver contadores de elementos y mover carpetas/archivos mediante Drag and Drop.
# ¿Qué tipo de árbol utilizamos?: 
Un Árbol N-ario (o Árbol General), donde un nodo raíz o padre puede tener múltiples hijos ($N$ hijos) sin límite estricto, ideal para modelar sistemas de directorios.
# ¿Cómo se conecta con el Backend?: 
Mediante una API REST con Flask (Python) y JavaScript (fetch). El frontend envía peticiones HTTP asíncronas al servidor de Python cada vez que el usuario interactúa, y el backend procesa los cambios y los guarda automáticamente en un archivo local (tree_data.json).
# Otros detalles importantes:
## Validación de seguridad: 
El backend previene bucles jerárquicos (evita que una carpeta sea arrastrada dentro de su propia subcarpeta).
# Barra de estado: 
Indicador visual en tiempo real que confirma la conexión activa entre el Frontend y el Backend.
