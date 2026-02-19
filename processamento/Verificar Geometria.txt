from qgis.core import QgsProject, QgsWkbTypes

def verificar_tipo_camada(nome_camada=None):
    """
    Verifica se uma camada é do tipo polígono
    """
    if nome_camada:
        # Busca camada pelo nome
        layer = QgsProject.instance().mapLayersByName(nome_camada)
        if not layer:
            print(f"❌ Camada '{nome_camada}' não encontrada!")
            return False
        layer = layer[0]
    else:
        # Usa camada ativa
        layer = iface.activeLayer()
        if not layer:
            print("❌ Nenhuma camada ativa selecionada!")
            return False
    
    # Verifica o tipo de geometria
    tipo_geometria = layer.geometryType()
    
    print(f"📋 Informações da camada: {layer.name()}")
    print(f"   Tipo de camada: {layer.type()}")
    print(f"   Tipo de geometria: {tipo_geometria}")
    
    if tipo_geometria == QgsWkbTypes.PolygonGeometry:
        print("   ✅ É uma camada de POLÍGONO")
        return True
    elif tipo_geometria == QgsWkbTypes.LineGeometry:
        print("   📏 É uma camada de LINHA")
        return False
    elif tipo_geometria == QgsWkbTypes.PointGeometry:
        print("   📍 É uma camada de PONTO")
        return False
    else:
        print("   ❓ Tipo de geometria desconhecido")
        return False

# Exemplos de uso:
verificar_tipo_camada()  # Verifica camada ativa
# verificar_tipo_camada("nome_da_sua_camada")  # Verifica pelo nome