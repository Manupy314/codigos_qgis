from qgis.PyQt.QtWidgets import QFileDialog, QInputDialog
from qgis.gui import QgsProjectionSelectionDialog
from qgis.core import (
    QgsProject,
    QgsRasterLayer,
    QgsVectorLayer,
    QgsWkbTypes
)
from qgis import processing
import os

# ============================================================
# 1. ESCOLHER O RASTER ANADEM
# ============================================================

anadem_path, _ = QFileDialog.getOpenFileName(
    None,
    "Selecione o raster ANADEM",
    "",
    "Raster (*.tif *.img *.asc *.sdat *.bil);;Todos (*.*)"
)

if not anadem_path:
    raise Exception("Operação cancelada pelo usuário (nenhum raster selecionado).")

anadem_layer = QgsRasterLayer(anadem_path, "ANADEM_ORIG")
if not anadem_layer.isValid():
    raise Exception("O raster selecionado não é válido.")

QgsProject.instance().addMapLayer(anadem_layer)

# ============================================================
# 2. ESCOLHER O NOVO SRC/CRS PARA REPROJETAR
# ============================================================

proj_dlg = QgsProjectionSelectionDialog()
proj_dlg.setCrs(anadem_layer.crs())  # começa mostrando o SRC atual

if proj_dlg.exec_() != proj_dlg.Accepted:
    raise Exception("Operação cancelada pelo usuário (nenhum SRC selecionado).")

target_crs = proj_dlg.crs()

# Reprojetar usando algoritmo GDAL "Warpreproject"
params_reproj = {
    'INPUT': anadem_layer,
    'SOURCE_CRS': anadem_layer.crs(),
    'TARGET_CRS': target_crs,
    'RESAMPLING': 0,           # 0 = Nearest neighbour (ajuste se quiser outro)
    'NODATA': None,
    'TARGET_RESOLUTION': None,
    'OPTIONS': '',
    'DATA_TYPE': 0,            # 0 = manter tipo de dado
    'TARGET_EXTENT': None,
    'TARGET_EXTENT_CRS': None,
    'MULTITHREADING': True,
    'EXTRA': '',
    'OUTPUT': 'TEMPORARY_OUTPUT'
}

reproj_result = processing.run("gdal:warpreproject", params_reproj)
reproj_path = reproj_result['OUTPUT']

anadem_reproj = QgsRasterLayer(reproj_path, "ANADEM_REPROJETADO")
if not anadem_reproj.isValid():
    raise Exception("Falha ao carregar o raster reprojetado.")
QgsProject.instance().addMapLayer(anadem_reproj)

# ============================================================
# 3. ESCOLHER CAMADA DE RECORTE (VETOR POLIGONAL)
# ============================================================

# Lista apenas camadas vetoriais de polígono no projeto
all_layers = list(QgsProject.instance().mapLayers().values())
polygon_layers = [
    lyr for lyr in all_layers
    if isinstance(lyr, QgsVectorLayer)
    and lyr.geometryType() == QgsWkbTypes.PolygonGeometry
]

if not polygon_layers:
    raise Exception("Nenhuma camada vetorial poligonal encontrada para recorte.")

layer_names = [lyr.name() for lyr in polygon_layers]

mask_name, ok = QInputDialog.getItem(
    None,
    "Camada de recorte",
    "Escolha a camada de recorte (polígono):",
    layer_names,
    0,
    False
)

if not ok:
    raise Exception("Operação cancelada pelo usuário (nenhuma camada de recorte selecionada).")

mask_layer = polygon_layers[layer_names.index(mask_name)]

# ============================================================
# 4. ESCOLHER O LOCAL E NOME DO ARQUIVO DE SAÍDA
# ============================================================

# Sugestão automática de nome de arquivo
base_name = os.path.splitext(os.path.basename(anadem_path))[0]
sugestao_nome = base_name + "_recortado.tif"

output_path, _ = QFileDialog.getSaveFileName(
    None,
    "Salvar ANADEM recortado",
    sugestao_nome,
    "GeoTIFF (*.tif);;Todos (*.*)"
)

if not output_path:
    raise Exception("Operação cancelada pelo usuário (nenhum arquivo de saída escolhido).")

# Garantir extensão .tif, se o usuário não colocar
if not output_path.lower().endswith(".tif"):
    output_path = output_path + ".tif"

# ============================================================
# 5. RECORTAR O ANADEM REPROJETADO PELA MÁSCARA
# ============================================================

params_clip = {
    'INPUT': anadem_reproj,
    'MASK': mask_layer,
    'SOURCE_CRS': anadem_reproj.crs(),
    'TARGET_CRS': anadem_reproj.crs(),
    'NODATA': None,
    'ALPHA_BAND': False,
    'CROP_TO_CUTLINE': True,
    'KEEP_RESOLUTION': True,
    'SET_RESOLUTION': False,
    'X_RESOLUTION': None,
    'Y_RESOLUTION': None,
    'MULTITHREADING': True,
    'OPTIONS': '',
    'DATA_TYPE': 0,
    'EXTRA': '',
    'OUTPUT': output_path
}

clip_result = processing.run("gdal:cliprasterbymasklayer", params_clip)

final_raster = QgsRasterLayer(output_path, os.path.basename(output_path))
if final_raster.isValid():
    QgsProject.instance().addMapLayer(final_raster)
else:
    raise Exception("O raster recortado foi criado, mas não pôde ser carregado no QGIS.")

print("Processo concluído com sucesso!")
print("Arquivo salvo em:", output_path)
