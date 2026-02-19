from qgis.core import QgsProject, QgsLayerTreeGroup
from qgis.utils import iface
from qgis.PyQt.QtWidgets import QInputDialog

root = QgsProject.instance().layerTreeRoot()

# -------------------------------------------------------------------
# 1. Coletar todos os grupos existentes no projeto (em qualquer nível)
# -------------------------------------------------------------------
grupos = []

def coletar_grupos(node):
    if isinstance(node, QgsLayerTreeGroup):
        grupos.append(node)
        # percorre recursivamente subgrupos
        for child in node.children():
            if isinstance(child, QgsLayerTreeGroup):
                coletar_grupos(child)

coletar_grupos(root)

if not grupos:
    raise Exception("Nenhum grupo encontrado no projeto.")

nomes_grupos = [g.name() for g in grupos]

# -------------------------------------------------------------------
# 2. Caixa de diálogo para o usuário escolher o grupo
# -------------------------------------------------------------------
nome_grupo_escolhido, ok_grp = QInputDialog.getItem(
    iface.mainWindow(),
    "Selecionar grupo",
    "Escolha o grupo cujas camadas serão renomeadas:",
    nomes_grupos,
    0,      # índice padrão
    False   # não permite digitar texto livre
)

if not ok_grp:
    raise Exception("Operação cancelada na seleção do grupo.")

# Encontra o objeto do grupo selecionado
grupo_sel = None
for g in grupos:
    if g.name() == nome_grupo_escolhido:
        grupo_sel = g
        break

if grupo_sel is None:
    raise Exception(f"Grupo '{nome_grupo_escolhido}' não encontrado (isso não era para acontecer).")

# -------------------------------------------------------------------
# 3. Caixa de diálogo para o prefixo
# -------------------------------------------------------------------
prefixo, ok_pref = QInputDialog.getText(
    iface.mainWindow(),
    "Prefixo para renomear",
    f"Digite o prefixo para as camadas do grupo '{nome_grupo_escolhido}' (ex.: BH):"
)

if not ok_pref or not prefixo.strip():
    raise Exception("Operação cancelada ou prefixo vazio.")

prefixo = prefixo.strip()

# -------------------------------------------------------------------
# 4. Pegar as camadas do grupo e renomear na ordem atual
# -------------------------------------------------------------------
layer_nodes = grupo_sel.findLayers()

print(f"Encontradas {len(layer_nodes)} camadas no grupo '{nome_grupo_escolhido}'.")

for i, node in enumerate(layer_nodes, start=1):
    layer = node.layer()
    old_name = layer.name()
    new_name = f"{prefixo}{str(i).zfill(2)}"  # ex.: BH01, BH02...
    layer.setName(new_name)
    print(f"Renomeado: {old_name} → {new_name}")

print(f"\n{len(layer_nodes)} camadas do grupo '{nome_grupo_escolhido}' renomeadas com sucesso.")
