from qgis.core import QgsProject, QgsVectorFileWriter, QgsVectorLayer, QgsWkbTypes
import os

# ============================================================
# CONFIGURAÇÕES
# ============================================================

# Pasta onde serão salvos os shapes individuais
PASTA_SAIDA = r"C:\Users\manuela.duarte\Desktop\RO_435_MANU_TRECHO 1_\18_11"

# Nome da camada vetorial que você quer dividir
NOME_CAMADA = "Bacias Hidrográficas"  # ALTERE AQUI

# ============================================================
# SCRIPT
# ============================================================

# Garante que a pasta de saída existe
os.makedirs(PASTA_SAIDA, exist_ok=True)

# Pega a camada do projeto
project = QgsProject.instance()
layer = project.mapLayersByName(NOME_CAMADA)

if not layer:
    # Tenta pegar a camada ativa se não encontrar pelo nome
    layer = iface.activeLayer()
    if not layer:
        raise Exception(f"Camada '{NOME_CAMADA}' não encontrada e nenhuma camada ativa!")
else:
    layer = layer[0]

# CORREÇÃO: Verifica se é polígono da forma correta
if layer.geometryType() != QgsWkbTypes.PolygonGeometry:
    raise Exception("A camada deve ser do tipo polígono!")

print(f"✅ Processando camada: {layer.name()}")
print(f"✅ Número de polígonos: {layer.featureCount()}")
print(f"✅ Pasta de saída: {PASTA_SAIDA}")

# Contador de polígonos processados
contador = 0

# Processa cada polígono individualmente
for feature in layer.getFeatures():
    # Cria uma camada temporária em memória
    temp_layer = QgsVectorLayer("Polygon?crs=" + layer.crs().authid(), "temp", "memory")
    provider = temp_layer.dataProvider()
    
    # Adiciona os campos (atributos) originais
    provider.addAttributes(layer.fields())
    temp_layer.updateFields()
    
    # Adiciona apenas este polígono à camada temporária
    provider.addFeature(feature)
    
    # Define o nome do arquivo
    nome_base = layer.name().replace(" ", "_")
    
    # Tenta usar um campo como identificador, senão usa número sequencial
    nome_feature = f"poligono_{contador + 1:03d}"
    
    # Verifica se tem campo 'nome' ou similar
    campos_nome = ['nome', 'name', 'id', 'fid', 'gid', 'bacia', 'subbacia']
    for campo in campos_nome:
        if campo in [field.name().lower() for field in layer.fields()]:
            valor = feature[campo]
            if valor and str(valor).strip():
                nome_feature = str(valor).replace(" ", "_").replace("/", "_").replace("\\", "_")
                break
    
    nome_arquivo = f"{nome_base}_{nome_feature}.shp"
    caminho_completo = os.path.join(PASTA_SAIDA, nome_arquivo)
    
    # Salva o polígono individual
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = "ESRI Shapefile"
    options.fileEncoding = "UTF-8"
    
    error = QgsVectorFileWriter.writeAsVectorFormatV3(
        temp_layer,
        caminho_completo,
        QgsProject.instance().transformContext(),
        options
    )
    
    if error[0] == QgsVectorFileWriter.NoError:
        print(f"✅ Salvo: {nome_arquivo}")
        contador += 1
    else:
        print(f"❌ Erro ao salvar {nome_arquivo}: {error[1]}")

print(f"\n🎉 Processamento concluído!")
print(f"📁 Total de polígonos salvos: {contador}")
print(f"📂 Pasta: {PASTA_SAIDA}")
