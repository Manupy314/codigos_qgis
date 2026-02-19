import os

from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsRasterLayer,
    QgsLayerTreeGroup
)
from qgis.PyQt.QtWidgets import QFileDialog, QInputDialog
from qgis.utils import iface

# 0. SELECIONAR GRUPO DO PROJETO

project = QgsProject.instance()
root = project.layerTreeRoot()

grupos = []

def coletar_grupos(node):
    if isinstance(node, QgsLayerTreeGroup):
        grupos.append(node)
        for child in node.children():
            if isinstance(child, QgsLayerTreeGroup):
                coletar_grupos(child)

coletar_grupos(root)

if not grupos:
    raise Exception("Nenhum grupo encontrado no projeto.")

nomes_grupos = [g.name() for g in grupos]

nome_grupo_escolhido, ok = QInputDialog.getItem(
    iface.mainWindow(),
    "Selecionar grupo",
    "Escolha o grupo cujos estilos (.qml) serão exportados:",
    nomes_grupos,
    0,
    False
)

if not ok:
    raise Exception("Operação cancelada.")

group = next((g for g in grupos if g.name() == nome_grupo_escolhido), None)

if group is None:
    raise Exception("Grupo não encontrado.")

layer_nodes = group.findLayers()

if not layer_nodes:
    raise Exception(f"O grupo '{group.name()}' não contém camadas.")

print(f"Grupo selecionado: {group.name()}")
print(f"Total de camadas: {len(layer_nodes)}\n")

# 1. ESCOLHER PASTA DE SAÍDA

output_folder = QFileDialog.getExistingDirectory(
    iface.mainWindow(),
    "Escolha a pasta para salvar os arquivos QML"
)

if not output_folder:
    raise Exception("Nenhuma pasta de saída foi escolhida.")

os.makedirs(output_folder, exist_ok=True)

print(f"Arquivos QML serão salvos em:\n{output_folder}\n")

# 2. EXPORTAR APENAS OS ESTILOS (.qml)

for node in layer_nodes:
    layer = node.layer()
    if layer is None:
        continue

    layer_name = layer.name()

    safe_name = (
        layer_name.replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
        .replace(":", "_")
        .replace("*", "_")
        .replace("?", "_")
        .replace('"', "_")
        .replace("<", "_")
        .replace(">", "_")
        .replace("|", "_")
    )

    style_path = os.path.join(output_folder, f"{safe_name}.qml")

    print(f"Salvando estilo da camada: {layer_name}")

    if isinstance(layer, (QgsVectorLayer, QgsRasterLayer)):
        if layer.saveNamedStyle(style_path):
            print(f"  → Estilo salvo em: {style_path}")
        else:
            print(f"  → Falha ao salvar o estilo.")
    else:
        print(f"  → Tipo de camada não suportado: {type(layer).__name__}")

print("\nExportação de estilos concluída com sucesso.")
