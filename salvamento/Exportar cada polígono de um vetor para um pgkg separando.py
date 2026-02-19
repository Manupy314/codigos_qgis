from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsFeature,
    QgsWkbTypes,
    QgsVectorFileWriter
)
from qgis.PyQt.QtWidgets import QFileDialog
import os
import re

# --------------------------------------------------------
# FUNÇÃO AUXILIAR PARA "LIMPAR" NOMES DE ARQUIVO
# --------------------------------------------------------
def slugify(text):
    """
    Remove caracteres problemáticos para nome de arquivo.
    Troca espaços por _ e remove caracteres especiais.
    """
    text = text.strip().replace(" ", "_")
    # Mantém apenas letras, números, _ e -
    text = re.sub(r"[^A-Za-z0-9_\-]", "", text)
    if not text:
        text = "layer"
    return text

# --------------------------------------------------------
# 0) PEGAR CAMADA ATIVA
# --------------------------------------------------------
layer = iface.activeLayer()

if layer is None:
    raise Exception("Nenhuma camada ativa. Selecione uma camada na legenda antes de rodar o script.")

if layer.geometryType() != QgsWkbTypes.PolygonGeometry:
    raise Exception("A camada ativa não é poligonal. Escolha uma camada de polígonos.")

# --------------------------------------------------------
# 1) DEFINIR CONJUNTO DE FEIÇÕES (SELECIONADAS OU TODAS)
# --------------------------------------------------------
selected_feats = layer.selectedFeatures()

if selected_feats:
    feats = selected_feats
    print(f"Usando {len(feats)} feições SELECIONADAS.")
else:
    feats = list(layer.getFeatures())
    print(f"Nenhuma seleção encontrada. Usando TODAS as {len(feats)} feições.")

if not feats:
    raise Exception("Não há feições para processar.")

# --------------------------------------------------------
# 2) ESCOLHER PASTA DE SAÍDA (CAIXA DE DIÁLOGO)
# --------------------------------------------------------
out_dir = QFileDialog.getExistingDirectory(
    iface.mainWindow(),
    "Selecione a pasta onde os arquivos serão salvos"
)

if not out_dir:
    raise Exception("Operação cancelada: nenhuma pasta selecionada.")

print(f"Pasta de saída: {out_dir}")

# --------------------------------------------------------
# 3) CONFIGURAÇÕES BÁSICAS
# --------------------------------------------------------
crs = layer.crs()
fields = layer.fields()
base_name = slugify(layer.name())

project = QgsProject.instance()

# --------------------------------------------------------
# 4) CRIAR ARQUIVO PARA CADA POLÍGONO
# --------------------------------------------------------
for feat in feats:
    feat_id = feat.id()

    # Nome base do arquivo
    file_name = f"{base_name}_id{feat_id}"
    file_name = slugify(file_name)

    # Caminho completo do arquivo GPKG
    out_path = os.path.join(out_dir, f"{file_name}.gpkg")

    # Criar camada em memória
    uri = f"Polygon?crs={crs.authid()}"
    mem_layer = QgsVectorLayer(uri, file_name, "memory")
    prov = mem_layer.dataProvider()

    # Copiar estrutura de campos
    prov.addAttributes(fields)
    mem_layer.updateFields()

    # Criar nova feição com mesma geometria e atributos
    new_feat = QgsFeature(mem_layer.fields())
    new_feat.setGeometry(feat.geometry())

    for field in fields:
        new_feat[field.name()] = feat[field.name()]

    prov.addFeature(new_feat)
    mem_layer.updateExtents()

    # Salvar em disco como GPKG
    error = QgsVectorFileWriter.writeAsVectorFormat(
        mem_layer,
        out_path,
        "UTF-8",
        crs,
        "GPKG"
    )

    if error == QgsVectorFileWriter.NoError:
        print(f"Salvo: {out_path}")
        # Adicionar arquivo salvo ao projeto
        saved_layer = QgsVectorLayer(out_path, file_name, "ogr")
        if saved_layer.isValid():
            project.addMapLayer(saved_layer)
        else:
            print(f"Aviso: arquivo salvo, mas não foi possível carregar no QGIS: {out_path}")
    else:
        print(f"ERRO ao salvar: {out_path}")

print("Concluído: um arquivo GPKG criado para cada polígono.")
