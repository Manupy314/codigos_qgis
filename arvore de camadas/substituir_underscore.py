# -*- coding: utf-8 -*-
from qgis.core import QgsProject, QgsLayerTreeGroup, QgsLayerTreeLayer

root = QgsProject.instance().layerTreeRoot()

def renomear_no(no):
    # Se for GRUPO
    if isinstance(no, QgsLayerTreeGroup):
        nome_antigo = no.name()
        nome_novo = nome_antigo.replace("_", " ")
        if nome_antigo != nome_novo:
            no.setName(nome_novo)
            print(f"✔ Grupo renomeado: {nome_antigo} -> {nome_novo}")

        # Chamar recursivamente para filhos
        for filho in no.children():
            renomear_no(filho)

    # Se for CAMADA
    elif isinstance(no, QgsLayerTreeLayer):
        layer = no.layer()
        if layer:
            nome_antigo = layer.name()
            nome_novo = nome_antigo.replace("_", " ")
            if nome_antigo != nome_novo:
                layer.setName(nome_novo)
                print(f"✔ Camada renomeada: {nome_antigo} -> {nome_novo}")

# Executar para todos os itens da raiz
for item in root.children():
    renomear_no(item)

print("\n✓ Concluído! Todos os '_' foram substituídos por espaços.")
