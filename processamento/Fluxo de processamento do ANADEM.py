from qgis.core import (
    QgsProject,
    QgsRasterLayer,
    QgsVectorLayer,
    QgsCoordinateReferenceSystem,
    Qgis,
    QgsMessageLog
)
from qgis.PyQt.QtWidgets import QFileDialog, QInputDialog
from qgis.utils import iface
from qgis import processing
import os

# -------------------------------------------------------------------
# CONTROLE DE PROGRESSO
# -------------------------------------------------------------------

TOTAL_STEPS = 7  # número de etapas principais do fluxo

def log_step(step, text):
    """
    Exibe a progressão do script:
    - step: número da etapa (1, 2, 3, ...)
    - text: descrição curta do que está acontecendo
    """
    pct = int(step / TOTAL_STEPS * 100)
    msg = f"[{step}/{TOTAL_STEPS} - {pct}%] {text}"

    # Console do QGIS
    print(msg)

    # Log de mensagens (painel Logs)
    QgsMessageLog.logMessage(msg, 'Hidrologia', Qgis.Info)

    # Barra de mensagens de aviso
    iface.messageBar().pushMessage(
        'Hidrologia',
        msg,
        level=Qgis.Info,
        duration=5  # segundos
    )

# -------------------------------------------------------------------
# FUNÇÕES AUXILIARES DE DIÁLOGO
# -------------------------------------------------------------------

def escolher_raster(titulo="Selecione um raster"):
    path, _ = QFileDialog.getOpenFileName(
        iface.mainWindow(),
        titulo,
        "",
        "Raster (*.tif *.tiff *.img *.asc);;Todos os arquivos (*.*)"
    )
    if not path:
        raise Exception("Operação cancelada pelo usuário (raster).")
    return path

def escolher_vetor(titulo="Selecione um vetor"):
    path, _ = QFileDialog.getOpenFileName(
        iface.mainWindow(),
        titulo,
        "",
        "Vetores (*.gpkg *.shp *.geojson *.json);;Todos os arquivos (*.*)"
    )
    if not path:
        raise Exception("Operação cancelada pelo usuário (vetor).")
    return path

def escolher_saida_raster(titulo, nome_sugerido):
    path, _ = QFileDialog.getSaveFileName(
        iface.mainWindow(),
        titulo,
        nome_sugerido,
        "GeoTIFF (*.tif);;Todos os arquivos (*.*)"
    )
    if not path:
        raise Exception("Operação cancelada pelo usuário (saída raster).")
    # Garante extensão .tif
    if not path.lower().endswith(".tif"):
        path = path + ".tif"
    return path

# -------------------------------------------------------------------
# 1) ESCOLHER ANADEM
# -------------------------------------------------------------------

log_step(1, "Selecionando e carregando o raster ANADEM.")
anadem_path = escolher_raster("Selecione o raster ANADEM")

anadem_layer = QgsRasterLayer(anadem_path, "ANADEM_original")
if not anadem_layer.isValid():
    raise Exception("Raster ANADEM inválido.")

# -------------------------------------------------------------------
# 2) ESCOLHER SRC DO ANADEM (EPSG)
#    0 = manter SRC atual do raster
# -------------------------------------------------------------------

proj = QgsProject.instance()
crs_proj = proj.crs()

log_step(2, "Definindo SRC do ANADEM (EPSG).")
epsg_valor, ok = QInputDialog.getInt(
    iface.mainWindow(),
    "SRC do ANADEM",
    "Informe o código EPSG do ANADEM.\n"
    "Use 0 para manter o SRC já definido no raster:",
    value=crs_proj.postgisSrid()
)

if not ok:
    raise Exception("Operação cancelada ao definir SRC.")

if epsg_valor > 0:
    novo_crs = QgsCoordinateReferenceSystem.fromEpsgId(epsg_valor)
    anadem_layer.setCrs(novo_crs)

# -------------------------------------------------------------------
# 3) REPROJETAR PARA O SRC DO PROJETO, SE NECESSÁRIO
# -------------------------------------------------------------------

log_step(3, "Verificando necessidade de reprojeção para o SRC do projeto.")
target_crs = crs_proj
reproj_layer = anadem_layer
reproj_path = anadem_path

if anadem_layer.crs() != target_crs:
    params_reproj = {
        'INPUT': anadem_layer,
        'SOURCE_CRS': anadem_layer.crs(),
        'TARGET_CRS': target_crs,
        'RESAMPLING': 0,         # Nearest neighbor
        'NODATA': None,
        'TARGET_RESOLUTION': None,
        'OPTIONS': '',
        'DATA_TYPE': 0,          # mesmo tipo de dado
        'TARGET_EXTENT': None,
        'TARGET_EXTENT_CRS': target_crs,
        'MULTITHREADING': False,
        'EXTRA': '',
        'OUTPUT': 'TEMPORARY_OUTPUT'
    }
    reproj_res = processing.run("gdal:warpreproject", params_reproj)
    reproj_path = reproj_res['OUTPUT']
    reproj_layer = QgsRasterLayer(reproj_path, "ANADEM_reprojetado")
    if not reproj_layer.isValid():
        raise Exception("Falha ao reprojetar o ANADEM.")
    log_step(3, "Reprojeção para o SRC do projeto concluída.")
else:
    log_step(3, "Reprojeção não necessária (ANADEM já no SRC do projeto).")
    reproj_layer = anadem_layer
    reproj_path = anadem_path

# -------------------------------------------------------------------
# 4) RECORTAR A PARTIR DE UMA CAMADA DE MÁSCARA (CAIXA DE DIÁLOGO)
# -------------------------------------------------------------------

log_step(4, "Selecionando camada de máscara e recortando o ANADEM.")
mask_path = escolher_vetor("Selecione a camada de máscara (vetor)")
mask_layer = QgsVectorLayer(mask_path, "mascara", "ogr")
if not mask_layer.isValid():
    raise Exception("Camada de máscara inválida.")

params_clip = {
    'INPUT': reproj_path,
    'MASK': mask_layer,
    'SOURCE_CRS': None,
    'TARGET_CRS': None,
    'NODATA': None,
    'ALPHA_BAND': False,
    'CROP_TO_CUTLINE': True,
    'KEEP_RESOLUTION': True,
    'SET_RESOLUTION': False,
    'X_RESOLUTION': 0,
    'Y_RESOLUTION': 0,
    'MULTITHREADING': False,
    'OPTIONS': '',
    'DATA_TYPE': 0,
    'EXTRA': '',
    'OUTPUT': 'TEMPORARY_OUTPUT'
}

clip_res = processing.run("gdal:cliprasterbymasklayer", params_clip)
dem_clip_path = clip_res['OUTPUT']
dem_clip_layer = QgsRasterLayer(dem_clip_path, "ANADEM_recortado")
if not dem_clip_layer.isValid():
    raise Exception("Falha ao recortar o raster pela máscara.")
log_step(4, "Recorte do ANADEM pela máscara concluído.")

# -------------------------------------------------------------------
# 5) r.fill.dir – MDE SEM DEPRESSÃO + DIREÇÃO DE FLUXO
#    (ESCOLHER SAÍDA EM CAIXA DE DIÁLOGO)
# -------------------------------------------------------------------

log_step(5, "Configurando saídas e executando r.fill.dir.")
saida_mde_sem_dep = escolher_saida_raster(
    "Salvar MDE sem depressão (r.fill.dir)",
    os.path.join(os.path.dirname(dem_clip_path), "mde_sem_depressao.tif")
)

saida_dir_fluxo_filldir = escolher_saida_raster(
    "Salvar direção de fluxo (r.fill.dir)",
    os.path.join(os.path.dirname(dem_clip_path), "direcao_fluxo_filldir.tif")
)

params_filldir = {
    'input': dem_clip_layer,           # Elevation (raster recortado)
    'format': 0,                       # 0 = grass (formato da direção)
    'f': False,                        # não usar "Find unresolved areas only"
    'output': saida_mde_sem_dep,       # Depressionless DEM
    'direction': saida_dir_fluxo_filldir,  # Flow direction
    'areas': 'TEMPORARY_OUTPUT',       # problem areas (não precisamos salvar)
    'GRASS_REGION_PARAMETER': dem_clip_layer,
    'GRASS_REGION_CELLSIZE_PARAMETER': 0,  # 0 = usar resolução do raster
    'GRASS_RASTER_FORMAT_OPT': '',
    'GRASS_RASTER_FORMAT_META': ''
}

res_filldir = processing.run("grass7:r.fill.dir", params_filldir)

dem_filled_path = res_filldir['output']
dem_filled_layer = QgsRasterLayer(dem_filled_path, "MDE_sem_depressao")
dir_fluxo_layer = QgsRasterLayer(saida_dir_fluxo_filldir, "Direcao_fluxo_filldir")

if dem_filled_layer.isValid():
    QgsProject.instance().addMapLayer(dem_filled_layer)
if dir_fluxo_layer.isValid():
    QgsProject.instance().addMapLayer(dir_fluxo_layer)

log_step(5, "r.fill.dir concluído – MDE sem depressão e direção de fluxo gerados.")

# -------------------------------------------------------------------
# 6) r.watershed – DEFINIÇÃO DO THRESHOLD E PREPARO DO DEM
# -------------------------------------------------------------------

log_step(6, "Definindo limiar (threshold) para r.watershed.")
threshold, ok = QInputDialog.getInt(
    iface.mainWindow(),
    "r.watershed - Threshold",
    "Tamanho mínimo do exterior da bacia (nº de células):",
    value=1000,   # valor pré-definido
    min=1
)
if not ok:
    raise Exception("Operação cancelada ao definir o threshold.")

dem_filled_layer = QgsRasterLayer(dem_filled_path, "MDE_sem_depressao_base")
if not dem_filled_layer.isValid():
    raise Exception("MDE sem depressão inválido para o r.watershed.")

log_step(6, "Threshold definido e MDE sem depressão preparado para r.watershed.")

# -------------------------------------------------------------------
# 7) r.watershed – SAÍDAS COM CAIXA DE DIÁLOGO
#    - número de células que drenam -> accumulation
#    - direção de drenagem          -> drainage
#    - segmento de fluxo            -> stream
# -------------------------------------------------------------------

log_step(7, "Configurando saídas e executando r.watershed.")
saida_acumulacao = escolher_saida_raster(
    "Salvar número de células que drenam (acumulação)",
    os.path.join(os.path.dirname(dem_filled_path), "acumulacao_celulas.tif")
)

saida_direcao_drenagem = escolher_saida_raster(
    "Salvar direção de drenagem",
    os.path.join(os.path.dirname(dem_filled_path), "direcao_drenagem.tif")
)

saida_stream_segmentos = escolher_saida_raster(
    "Salvar segmentos de fluxo (stream)",
    os.path.join(os.path.dirname(dem_filled_path), "segmentos_fluxo.tif")
)

params_watershed = {
    'elevation': dem_filled_layer,           # DEM sem depressão
    'depression': None,
    'flow': None,
    'disturbed_land': None,
    'blocking': None,
    'threshold': threshold,
    'max_slope_length': 0,
    'convergence': 5,
    'memory': 300,
    # flags
    's': False,
    'm': False,
    '4': False,
    'a': False,
    'b': False,
    # saídas de interesse
    'accumulation': saida_acumulacao,           # número de células que drenam
    'drainage': saida_direcao_drenagem,         # direção de drenagem
    'basin': 'TEMPORARY_OUTPUT',
    'stream': saida_stream_segmentos,           # segmentos de fluxo
    'half_basin': 'TEMPORARY_OUTPUT',
    'length_slope': 'TEMPORARY_OUTPUT',
    'slope_steepness': 'TEMPORARY_OUTPUT',
    'tci': 'TEMPORARY_OUTPUT',
    'spi': 'TEMPORARY_OUTPUT',
    'GRASS_REGION_PARAMETER': dem_filled_layer,
    'GRASS_REGION_CELLSIZE_PARAMETER': 0,
    'GRASS_RASTER_FORMAT_OPT': '',
    'GRASS_RASTER_FORMAT_META': ''
}

res_watershed = processing.run("grass7:r.watershed", params_watershed)

# Adiciona saídas principais ao projeto
lyr_acc = QgsRasterLayer(saida_acumulacao, "Acumulacao_celulas")
lyr_drn = QgsRasterLayer(saida_direcao_drenagem, "Direcao_drenagem")
lyr_str = QgsRasterLayer(saida_stream_segmentos, "Segmentos_fluxo")

for lyr in (lyr_acc, lyr_drn, lyr_str):
    if lyr.isValid():
        QgsProject.instance().addMapLayer(lyr)

log_step(7, "r.watershed concluído – camadas de acumulação, direção e segmentos de fluxo criadas.")

print("Fluxo completo concluído com sucesso.")
