import json
import os
import sys
import webbrowser
from typing import Any, Dict, List, Optional
from flask import Flask, jsonify, render_template_string, request

# ==========================================
# N-ary Tree Data Structure Implementation
# ==========================================


class NaryTreeNode:
  """Represents a node in an N-ary Tree structure.

  Can represent either a folder (directory) or a file.
  """

  def __init__(
      self,
      node_id: str,
      name: str,
      is_file: bool = False,
      file_type: str = "text",
      content: str = "",
  ):
    self.node_id = node_id
    self.name = name
    self.is_file = is_file
    self.file_type = file_type
    self.content = content
    self.children: List["NaryTreeNode"] = []

  def add_child(self, child_node: "NaryTreeNode"):
    self.children.append(child_node)

  def remove_child(self, node_id: str) -> bool:
    for i, child in enumerate(self.children):
      if child.node_id == node_id:
        self.children.pop(i)
        return True
      if child.remove_child(node_id):
        return True
    return False

  def find_node(self, node_id: str) -> Optional["NaryTreeNode"]:
    if self.node_id == node_id:
      return self
    for child in self.children:
      found = child.find_node(node_id)
      if found:
        return found
    return None

  def count_items(self) -> int:
    return len(self.children)

  def to_dict(self) -> Dict[str, Any]:
    return {
        "node_id": self.node_id,
        "name": self.name,
        "is_file": self.is_file,
        "file_type": self.file_type,
        "content": self.content,
        "item_count": self.count_items(),
        "children": [child.to_dict() for child in self.children],
    }

  @classmethod
  def from_dict(cls, data: Dict[str, Any]) -> "NaryTreeNode":
    node = cls(
        node_id=data.get("node_id"),
        name=data.get("name"),
        is_file=data.get("is_file", False),
        file_type=data.get("file_type", "text"),
        content=data.get("content", ""),
    )
    for child_data in data.get("children", []):
      node.add_child(cls.from_dict(child_data))
    return node


class FileSystemTree:
  """Manages the N-ary tree persistence and operations."""

  def __init__(self, storage_file: str = "tree_data.json"):
    self.storage_file = storage_file
    self.root = self.load_tree()

  def load_tree(self) -> NaryTreeNode:
    if os.path.exists(self.storage_file):
      try:
        with open(self.storage_file, "r", encoding="utf-8") as f:
          data = json.load(f)
          return NaryTreeNode.from_dict(data)
      except Exception:
        pass

    root = NaryTreeNode("root", "PROYECTO_SISTEMAS", is_file=False)
    src = NaryTreeNode("src", "src", is_file=False)
    src.add_child(
        NaryTreeNode(
            "main_py",
            "main.py",
            is_file=True,
            file_type="python",
            content="# Python Backend Logic\nprint('Frontend connected successfully!')",
        )
    )
    src.add_child(
        NaryTreeNode(
            "app_js",
            "app.js",
            is_file=True,
            file_type="code",
            content="// Frontend Javascript API Client",
        )
    )

    docs = NaryTreeNode("docs", "documentos", is_file=False)
    docs.add_child(
        NaryTreeNode(
            "report",
            "Informe_Parcial.pdf",
            is_file=True,
            file_type="pdf",
            content="",
        )
    )

    root.add_child(src)
    root.add_child(docs)
    root.add_child(
        NaryTreeNode(
            "readme",
            "README.md",
            is_file=True,
            file_type="text",
            content="# Proyecto Arbol N-ario\nSistema con Frontend y Backend en Flask.",
        )
    )
    return root

  def save_tree(self):
    with open(self.storage_file, "w", encoding="utf-8") as f:
      json.dump(self.root.to_dict(), f, ensure_ascii=False, indent=4)

  def _is_descendant(self, current_node: NaryTreeNode, target_id: str) -> bool:
    if current_node.node_id == target_id:
      return True
    for child in current_node.children:
      if self._is_descendant(child, target_id):
        return True
    return False

  def move_node(self, node_id: str, new_parent_id: str) -> bool:
    if node_id == "root" or node_id == new_parent_id:
      return False

    node_to_move = self.root.find_node(node_id)
    if not node_to_move or self._is_descendant(node_to_move, new_parent_id):
      return False

    new_parent = self.root.find_node(new_parent_id)
    if not new_parent or new_parent.is_file:
      return False

    self.root.remove_child(node_id)
    new_parent.add_child(node_to_move)
    self.save_tree()
    return True


# ==========================================
# Flask Application & Web Interface
# ==========================================

app = Flask(__name__)
fs_tree = FileSystemTree()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Árbol N-ario - Explorador Conectado</title>
    <style>
        :root {
            --bg-color: #1e1e1e;
            --sidebar-bg: #252526;
            --editor-bg: #1e1e1e;
            --text-color: #cccccc;
            --text-bright: #ffffff;
            --accent-color: #0e639c;
            --hover-color: #2a2d2e;
            --selected-color: #37373d;
            --drop-target: #04395e;
            --border-color: #333333;
            --badge-bg: #4d4d4d;
            --status-green: #3fb950;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        body { background-color: var(--bg-color); color: var(--text-color); display: flex; flex-direction: column; height: 100vh; overflow: hidden; }
        
        .app-container { display: flex; flex: 1; overflow: hidden; }

        /* Sidebar / Explorer */
        .sidebar { width: 320px; background-color: var(--sidebar-bg); border-right: 1px solid var(--border-color); display: flex; flex-direction: column; }
        .sidebar-header { padding: 12px 16px; font-size: 11px; font-weight: bold; text-transform: uppercase; letter-spacing: 1px; color: #969696; display: flex; justify-content: space-between; align-items: center; }
        
        /* Search Box */
        .search-box { padding: 8px 12px; border-bottom: 1px solid var(--border-color); }
        .search-input { width: 100%; background: #1e1e1e; border: 1px solid #3c3c3c; color: var(--text-bright); padding: 6px 10px; font-size: 12px; border-radius: 3px; outline: none; }
        .search-input:focus { border-color: var(--accent-color); }

        .tree-container { flex: 1; overflow-y: auto; padding: 4px 0; }
        
        /* Tree Nodes */
        ul { list-style: none; padding-left: 14px; }
        li { margin: 1px 0; }
        .node-row { display: flex; align-items: center; padding: 5px 8px; cursor: pointer; border-radius: 3px; font-size: 13px; user-select: none; }
        .node-row:hover { background-color: var(--hover-color); color: var(--text-bright); }
        .node-row.selected { background-color: var(--selected-color); color: var(--text-bright); font-weight: 500; }
        .node-row.drag-over { background-color: var(--drop-target) !important; outline: 1px dashed #007acc; }
        
        .toggle-icon { width: 16px; text-align: center; font-size: 10px; margin-right: 4px; transition: transform 0.1s; color: #c5c5c5; }
        .toggle-icon.expanded { transform: rotate(90deg); }
        .node-icon { margin-right: 6px; font-size: 14px; }
        .node-name { flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

        .item-badge { background-color: var(--badge-bg); color: #ffffff; font-size: 10px; padding: 1px 6px; border-radius: 10px; margin-left: 6px; }

        /* Actions Toolbar */
        .sidebar-actions { padding: 8px 12px; border-top: 1px solid var(--border-color); display: flex; gap: 6px; background: #2d2d2d; }
        .btn { background: #3c3c3c; color: white; border: none; padding: 6px 10px; font-size: 11px; border-radius: 2px; cursor: pointer; flex: 1; text-align: center; }
        .btn:hover { background: var(--accent-color); }
        .btn-danger:hover { background: #a1260d; }

        /* Main Content */
        .main-content { flex: 1; display: flex; flex-direction: column; background-color: var(--editor-bg); }
        .breadcrumb { padding: 10px 20px; background: #2d2d2d; font-size: 12px; color: #858585; border-bottom: 1px solid var(--border-color); }
        .editor-area { padding: 30px; flex: 1; display: flex; flex-direction: column; }
        .editor-title { font-size: 20px; font-weight: 500; color: var(--text-bright); margin-bottom: 15px; display: flex; align-items: center; gap: 10px; }
        textarea { flex: 1; background: #1e1e1e; color: #9cdcfe; border: 1px solid var(--border-color); padding: 15px; font-family: 'Consolas', monospace; font-size: 14px; resize: none; border-radius: 4px; outline: none; }
        .placeholder-text { color: #666; text-align: center; margin-top: 50px; font-size: 16px; }

        /* Status Bar (Frontend <-> Backend Connection indicator) */
        .status-bar { height: 24px; background-color: #007acc; color: white; font-size: 11px; display: flex; align-items: center; justify-content: space-between; padding: 0 12px; user-select: none; }
        .connection-badge { display: flex; align-items: center; gap: 6px; }
        .status-dot { width: 8px; height: 8px; background-color: var(--status-green); border-radius: 50%; display: inline-block; box-shadow: 0 0 6px var(--status-green); }
    </style>
</head>
<body>

    <div class="app-container">
        <div class="sidebar">
            <div class="sidebar-header">
                <span>Explorador (Árbol N-ario)</span>
            </div>
            <div class="search-box">
                <input type="text" id="searchInput" class="search-input" placeholder="🔍 Buscar carpeta o archivo..." oninput="filterTree()">
            </div>
            <div class="tree-container" id="treeView"></div>
            <div class="sidebar-actions">
                <button class="btn" onclick="openCreateModal(false)">+ 📁 Carpeta</button>
                <button class="btn" onclick="openCreateModal(true)">+ 📄 Archivo</button>
                <button class="btn" onclick="renameCurrentNode()">✏️ Renombrar</button>
                <button class="btn btn-danger" onclick="deleteCurrentNode()">🗑️</button>
            </div>
        </div>

        <div class="main-content">
            <div class="breadcrumb" id="breadcrumbPath">Disco C: / PROYECTO_SISTEMAS</div>
            <div class="editor-area" id="editorArea">
                <div class="placeholder-text">Selecciona un archivo o carpeta para administrar.</div>
            </div>
        </div>
    </div>

    <!-- Connection Status Bar -->
    <div class="status-bar">
        <div class="connection-badge">
            <span class="status-dot"></span>
            <span>Frontend Conectado a Python Backend (HTTP/REST API)</span>
        </div>
        <div id="syncStatus">Sincronizado con tree_data.json</div>
    </div>

<script>
    let treeData = null;
    let selectedNode = null;

    async function fetchTree() {
        setSyncStatus('Cargando backend...');
        try {
            const res = await fetch('/api/tree');
            treeData = await res.json();
            if (!selectedNode) {
                selectedNode = treeData; // Default select Root
            } else {
                // Refresh reference to current selected node
                selectedNode = findNodeInMemory(treeData, selectedNode.node_id) || treeData;
            }
            renderTree();
            loadNodeDetails(selectedNode);
            setSyncStatus('Sincronizado con tree_data.json');
        } catch(e) {
            setSyncStatus('❌ Error de conexión con Python');
        }
    }

    function findNodeInMemory(node, id) {
        if (node.node_id === id) return node;
        if (node.children) {
            for (let child of node.children) {
                let found = findNodeInMemory(child, id);
                if (found) return found;
            }
        }
        return null;
    }

    function setSyncStatus(msg) {
        document.getElementById('syncStatus').textContent = msg;
    }

    function renderTree() {
        const container = document.getElementById('treeView');
        container.innerHTML = '';
        const ul = document.createElement('ul');
        ul.appendChild(createTreeNodeElement(treeData));
        container.appendChild(ul);
    }

    function createTreeNodeElement(node) {
        const li = document.createElement('li');
        const row = document.createElement('div');
        const isSelected = selectedNode && selectedNode.node_id === node.node_id;
        row.className = `node-row ${isSelected ? 'selected' : ''}`;
        row.draggable = node.node_id !== 'root';
        row.dataset.name = node.name.toLowerCase();

        // Drag and Drop
        row.addEventListener('dragstart', (e) => {
            e.stopPropagation();
            e.dataTransfer.setData('text/plain', node.node_id);
        });

        row.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.stopPropagation();
            if (!node.is_file) row.classList.add('drag-over');
        });

        row.addEventListener('dragleave', (e) => {
            e.stopPropagation();
            row.classList.remove('drag-over');
        });

        row.addEventListener('drop', async (e) => {
            e.preventDefault();
            e.stopPropagation();
            row.classList.remove('drag-over');
            const draggedId = e.dataTransfer.getData('text/plain');
            if (!node.is_file && draggedId) {
                await moveNode(draggedId, node.node_id);
            }
        });

        const hasChildren = node.children && node.children.length > 0;
        let toggleSpan = document.createElement('span');
        toggleSpan.className = 'toggle-icon ' + (hasChildren ? 'expanded' : '');
        toggleSpan.innerHTML = hasChildren ? '▶' : '';
        
        let iconSpan = document.createElement('span');
        iconSpan.className = 'node-icon';
        iconSpan.innerHTML = node.is_file ? getFileIcon(node.file_type) : '📁';

        let nameSpan = document.createElement('span');
        nameSpan.className = 'node-name';
        nameSpan.textContent = node.name;

        row.appendChild(toggleSpan);
        row.appendChild(iconSpan);
        row.appendChild(nameSpan);

        if (!node.is_file) {
            let badgeSpan = document.createElement('span');
            badgeSpan.className = 'item-badge';
            badgeSpan.textContent = node.item_count !== undefined ? node.item_count : node.children.length;
            row.appendChild(badgeSpan);
        }

        let subUl = null;
        if (hasChildren) {
            subUl = document.createElement('ul');
            node.children.forEach(child => {
                subUl.appendChild(createTreeNodeElement(child));
            });
            if (toggleSpan.innerHTML) {
                toggleSpan.onclick = (e) => {
                    e.stopPropagation();
                    subUl.style.display = subUl.style.display === 'none' ? 'block' : 'none';
                    toggleSpan.classList.toggle('expanded');
                };
            }
        }

        row.onclick = (e) => {
            e.stopPropagation();
            selectedNode = node;
            renderTree();
            loadNodeDetails(node);
        };

        li.appendChild(row);
        if (subUl) li.appendChild(subUl);
        return li;
    }

    function getFileIcon(type) {
        switch(type) {
            case 'python': return '🐍';
            case 'pdf': return '📄';
            case 'code': return '💻';
            default: return '📝';
        }
    }

    function loadNodeDetails(node) {
        document.getElementById('breadcrumbPath').textContent = "Disco C: / " + node.name;
        const editor = document.getElementById('editorArea');
        if (node.is_file) {
            editor.innerHTML = `
                <div class="editor-title">${getFileIcon(node.file_type)} ${node.name}</div>
                <textarea id="fileContent" oninput="saveContent('${node.node_id}')">${node.content}</textarea>
            `;
        } else {
            editor.innerHTML = `
                <div class="editor-title">📁 ${node.name}</div>
                <p style="color: #858585; margin-top: 10px;">Carpeta seleccionada como destino activo. Contiene ${node.children.length} elementos directos.</p>
            `;
        }
    }

    async function saveContent(nodeId) {
        setSyncStatus('Guardando cambios en backend...');
        const content = document.getElementById('fileContent').value;
        await fetch('/api/update_content', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({node_id: nodeId, content: content})
        });
        setSyncStatus('Sincronizado con tree_data.json');
    }

    async function openCreateModal(isFile) {
        // Fallback to root or current node if it's a file
        let targetFolder = selectedNode;
        if (!targetFolder || targetFolder.is_file) {
            targetFolder = treeData; // Default to Root
        }

        const promptText = isFile ? `Nuevo archivo en "${targetFolder.name}":` : `Nueva carpeta en "${targetFolder.name}":`;
        const name = prompt(promptText);
        if (!name) return;

        let fileType = "text";
        if (isFile && name.endsWith('.py')) fileType = "python";
        if (isFile && name.endsWith('.pdf')) fileType = "pdf";
        if (isFile && name.endsWith('.js')) fileType = "code";

        setSyncStatus('Enviando petición a Python API...');
        const res = await fetch('/api/create', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                parent_id: targetFolder.node_id,
                name: name,
                is_file: isFile,
                file_type: fileType
            })
        });
        const data = await res.json();
        if (data.success) {
            fetchTree();
        } else {
            alert(data.error);
        }
    }

    async function moveNode(nodeId, newParentId) {
        setSyncStatus('Moviendo nodo en la estructura del Árbol N-ario...');
        const res = await fetch('/api/move', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({node_id: nodeId, new_parent_id: newParentId})
        });
        const data = await res.json();
        if (data.success) {
            fetchTree();
        } else {
            alert(data.error || "No se pudo mover el elemento.");
            setSyncStatus('Sincronizado con tree_data.json');
        }
    }

    async function renameCurrentNode() {
        if (!selectedNode || selectedNode.node_id === 'root') {
            alert("Selecciona un archivo o carpeta válido para renombrar.");
            return;
        }
        const newName = prompt("Nuevo nombre:", selectedNode.name);
        if (!newName) return;

        const res = await fetch('/api/rename', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({node_id: selectedNode.node_id, new_name: newName})
        });
        const data = await res.json();
        if (data.success) fetchTree();
        else alert(data.error);
    }

    async function deleteCurrentNode() {
        if (!selectedNode || selectedNode.node_id === 'root') {
            alert("No puedes eliminar la raíz del disco.");
            return;
        }
        if (!confirm(`¿Estás seguro de eliminar "${selectedNode.name}"?`)) return;

        const res = await fetch('/api/delete', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({node_id: selectedNode.node_id})
        });
        const data = await res.json();
        if (data.success) {
            selectedNode = treeData;
            fetchTree();
        } else {
            alert(data.error);
        }
    }

    function filterTree() {
        const query = document.getElementById('searchInput').value.toLowerCase().trim();
        const allListItems = document.querySelectorAll('#treeView li');

        if (!query) {
            allListItems.forEach(li => {
                li.style.display = 'block';
            });
            return;
        }

        allListItems.forEach(li => {
            const row = li.querySelector('.node-row');
            const name = row ? row.dataset.name : '';
            if (name.includes(query)) {
                li.style.display = 'block';
                let parent = li.parentElement;
                while (parent && parent.id !== 'treeView') {
                    if (parent.tagName === 'UL' || parent.tagName === 'LI') parent.style.display = 'block';
                    parent = parent.parentElement;
                }
            } else {
                li.style.display = 'none';
            }
        });
    }

    // Initial Load
    fetchTree();
</script>
</body>
</html>
"""


@app.route("/")
def index():
  return render_template_string(HTML_TEMPLATE)


@app.route("/api/tree")
def get_tree():
  return jsonify(fs_tree.root.to_dict())


@app.route("/api/create", methods=["POST"])
def create_node():
  data = request.json
  parent_id = data.get("parent_id")
  name = data.get("name")
  is_file = data.get("is_file", False)
  file_type = data.get("file_type", "text")

  parent_node = fs_tree.root.find_node(parent_id)
  if not parent_node or parent_node.is_file:
    # If target is invalid, default to root
    parent_node = fs_tree.root

  new_id = "node_" + str(os.urandom(4).hex())
  new_node = NaryTreeNode(
      node_id=new_id, name=name, is_file=is_file, file_type=file_type
  )
  parent_node.add_child(new_node)
  fs_tree.save_tree()
  return jsonify({"success": True, "node_id": new_id})


@app.route("/api/move", methods=["POST"])
def move_node():
  data = request.json
  node_id = data.get("node_id")
  new_parent_id = data.get("new_parent_id")

  success = fs_tree.move_node(node_id, new_parent_id)
  if success:
    return jsonify({"success": True})
  return jsonify({
      "success": False,
      "error": (
          "No se puede mover: el destino es inválido o causaría un bucle"
          " jerárquico."
      ),
  })


@app.route("/api/rename", methods=["POST"])
def rename_node():
  data = request.json
  node_id = data.get("node_id")
  new_name = data.get("new_name")

  node = fs_tree.root.find_node(node_id)
  if node:
    node.name = new_name
    fs_tree.save_tree()
    return jsonify({"success": True})
  return jsonify({"success": False, "error": "Nodo no encontrado"})


@app.route("/api/delete", methods=["POST"])
def delete_node():
  data = request.json
  node_id = data.get("node_id")

  success = fs_tree.root.remove_child(node_id)
  if success:
    fs_tree.save_tree()
    return jsonify({"success": True})
  return jsonify({"success": False, "error": "No se pudo eliminar"})


@app.route("/api/update_content", methods=["POST"])
def update_content():
  data = request.json
  node_id = data.get("node_id")
  content = data.get("content")

  node = fs_tree.root.find_node(node_id)
  if node and node.is_file:
    node.content = content
    fs_tree.save_tree()
    return jsonify({"success": True})
  return jsonify({"success": False, "error": "Archivo no encontrado"})


if __name__ == "__main__":
  print("🚀 Servidor del Explorador de Árbol N-ario iniciado...")
  print("Abriendo navegador web automáticamente...")
  webbrowser.open("http://127.0.0.1:5000")
  app.run(debug=True, port=5000)