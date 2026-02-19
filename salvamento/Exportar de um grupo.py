import os
import shutil

from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsRasterLayer,
    QgsVectorFileWriter
)

# ============================================================
# >>> ALTERE AQUI: nome EXATO do grupo que você quer exportar
# Exemplo: "BACIAS" ou "MAPAS"
group_name = "MAPAS"
# ============================================================

# ============================================================
# >>> ALTERE AQUI: pasta onde serão salvos os arquivos
output_folder = r"XXXXX"
# ============================================================

os.makedirs(output_folder, exist_ok=True)

project = QgsProject.instance()
root = project.layerTreeRoot()

group = root.findGroup(group_name)

if not group:
    raise Exception(f"Grupo '{group_name}' não encontrado no painel de camadas.")

# Pega todas as camadas (inclusive de subgrupos) dentro do grupo
layer_nodes = group.findLayers()

print(f"Grupo '{group_name}' encontrado com {len(layer_nodes)} camada(s).\n")

transform_context = project.transformContext()

for node in layer_nodes:
    layer = node.layer()
    if layer is None:
        continue

    layer_name = layer.name()
    print(f"Processando camada: {layer_name}")

    # Cria um nome "seguro" para arquivo
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

    # ==========================================
    # CAMADAS VETORIAIS
    # ==========================================
    if isinstance(layer, QgsVectorLayer):
        print(f"  → Salvando VETOR como GeoPackage...")

        data_path = os.path.join(output_folder, f"{safe_name}.gpkg")
        style_path = os.path.join(output_folder, f"{safe_name}.qml")

        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = "GPKG"
        options.fileEncoding = "UTF-8"
        options.layerName = safe_name  # nome da camada dentro do GPKG

        result = QgsVectorFileWriter.writeAsVectorFormatV3(
            layer,
            data_path,
            transform_context,
            options
        )

        # (error_code, error_message, new_path, new_layer)
        error = result[0]
        error_message = result[1]
        new_path = result[2]

        if error == QgsVectorFileWriter.NoError:
            print(f"    ✅ Vetor salvo em: {new_path}")
        else:
            print(f"    ❌ Erro ao salvar vetor '{layer_name}': {error_message}")
            continue

        # Salva simbologia em QML
        if layer.saveNamedStyle(style_path):
            print(f"    🎨 Estilo salvo em: {style_path}")
        else:
            print(f"    ⚠ Não foi possível salvar o estilo da camada '{layer_name}'.")

    # ==========================================
    # CAMADAS RASTER (cópia + QML)
    # ==========================================
    elif isinstance(layer, QgsRasterLayer):
        print(f"  → Salvando RASTER (cópia fiel do original)...")

        origem = layer.source()

        # Pula fontes não-arquivo (WMS, XYZ, etc.)
        if not os.path.isfile(origem):
            print(f"    ❌ Raster '{layer_name}' não é um arquivo local simples (origem: {origem}). Pulando.")
            continue

        # Mesmo nome base do arquivo original
        base_name, ext = os.path.splitext(os.path.basename(origem))
        if not ext:
            ext = ".tif"  # fallback

        raster_path = os.path.join(output_folder, base_name + ext)
        style_path = os.path.join(output_folder, base_name + ".qml")

        try:
            shutil.copy(origem, raster_path)
            print(f"    ✅ Raster copiado fielmente: {raster_path}")
        except Exception as e:
            print(f"    ❌ Erro ao copiar raster '{layer_name}': {e}")
            continue

        # Salva simbologia em QML (mesmo nome do raster)
        if layer.saveNamedStyle(style_path):
            print(f"    🎨 Estilo do raster salvo em: {style_path}")
        else:
            print(f"    ⚠ Não foi possível salvar o estilo do raster '{layer_name}'.")

    # ==========================================
    # TIPO DE CAMADA NÃO RECONHECIDO
    # ==========================================
    else:
        print(f"  ⚠ Tipo de camada não suportado: {type(layer).__name__}")

print(f"\n✅ Exportação concluída! Arquivos salvos em: {output_folder}")
