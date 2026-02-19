root = QgsProject.instance().layerTreeRoot()
grupo = root.findGroup("RASTER")   # Nome do grupo

if not grupo:
    raise Exception("Grupo não encontrado!")

for node in grupo.children():
    lyr = node.layer()
    if lyr:  # garante que é camada, não grupo
        lyr.setName(lyr.name().lower())

print("Todos os nomes de camadas do grupo MAPAS foram convertidos para CAIXA ALTA.")