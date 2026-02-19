from qgis.utils import iface
from qgis.core import QgsProject
from qgis.PyQt.QtWidgets import QInputDialog

proj = QgsProject.instance()
root = proj.layerTreeRoot()

# 1. Pede ao usuário o texto que os nomes das camadas devem começar
prefixo, ok = QInputDialog.getText(
    iface.mainWindow(),
    "Filtrar camadas",
    "Digite o texto que o nome das camadas deve começar (ex.: BH, Bacias_Hidrogrficas):"
)

if not ok or not prefixo.strip():
    raise Exception("Operação cancelada ou prefixo vazio.")

prefixo = prefixo.strip()

# 2. Pede ao usuário se a ordenação será ascendente ou descendente
opcoes_ordem = ["Ascendente (sul → norte)", "Descendente (norte → sul)"]
ordem_escolhida, ok2 = QInputDialog.getItem(
    iface.mainWindow(),
    "Ordem de latitude",
    "Escolha a ordem de latitude:",
    opcoes_ordem,
    0,          # índice padrão (Ascendente)
    False       # não permite edição livre do texto
)

if not ok2:
    raise Exception("Operação cancelada na escolha da ordem.")

# Define se será reverse ou não no sorted()
if "Ascendente" in ordem_escolhida:
    reverse_flag = False   # sul → norte (lat menor para maior)
else:
    reverse_flag = True    # norte → sul (lat maior para menor)

# 3. Seleciona as camadas cujo nome começa com o prefixo informado
layers = [
    l for l in proj.mapLayers().values()
    if l.isSpatial() and l.name().startswith(prefixo)
]

if not layers:
    raise Exception(f"Nenhuma camada encontrada com prefixo '{prefixo}'.")

print(f"{len(layers)} camadas encontradas com prefixo '{prefixo}'.")

# 4. Cria lista (layer, latitude do centro da extensão)
layer_lat = []
for layer in layers:
    ext = layer.extent()
    centro = ext.center()
    lat = centro.y()
    layer_lat.append((layer, lat))

# 5. Ordena pela latitude conforme escolha do usuário
layer_lat_sorted = sorted(layer_lat, key=lambda x: x[1], reverse=reverse_flag)

# Atenção:
# Vamos inserir SEMPRE na posição 0, então o último inserido fica no topo.
# Para que a ordem final no painel acompanhe a lista 'layer_lat_sorted',
# vamos iterar sobre ela em ordem inversa.
layer_lat_sorted_reverse = list(reversed(layer_lat_sorted))

# 6. Reorganiza as camadas existentes no painel de camadas
for lyr, _ in layer_lat_sorted_reverse:
    node = root.findLayer(lyr.id())
    if not node:
        continue
    parent = node.parent()          # mantém o grupo original
    clone = node.clone()            # faz um clone do nó
    parent.insertChildNode(0, clone)  # insere o clone no topo do grupo
    parent.removeChildNode(node)      # remove o nó original (que será deletado)

print(f"Camadas reorganizadas pela latitude ({ordem_escolhida}).")
