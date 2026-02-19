# Script para substituir siglas de Köppen pelos nomes completos na legenda
from qgis.core import QgsProject, QgsCategorizedSymbolRenderer, QgsRendererCategory

# Dicionário com a tradução das siglas para nomes completos
KOPPEN_NAMES = {
    # Grupo A - Climas Tropicais
    "Af": "Af - Tropical chuvoso da floresta",
    "Am": "Am - Tropical de monção",
    "Aw": "Aw - Tropical com inverno seco",
    "As": "As - Tropical com verão seco",

    # Grupo B - Climas Secos
    "BWh": "BWh - Desértico quente",
    "BWk": "BWk - Desértico frio",
    "BSh": "BSh - Estepário quente",
    "BSk": "BSk - Estepário frio",

    # Grupo C - Climas Temperados
    "Cfa": "Cfa - Subtropical úmido",
    "Cfb": "Cfb - Oceânico",
    "Cfc": "Cfc - Subpolar oceânico",
    "Csa": "Csa - Mediterrâneo de verão quente",
    "Csb": "Csb - Mediterrâneo de verão fresco",
    "Csc": "Csc - Mediterrâneo de verão curto e fresco",
    "Cwa": "Cwa - Subtropical de inverno seco",
    "Cwb": "Cwb - Temperado de altitude com inverno seco",
    "Cwc": "Cwc - Subpolar de altitude com inverno seco",

    # Grupo D - Climas Continentais
    "Dfa": "Dfa - Continental úmido de verão quente",
    "Dfb": "Dfb - Continental úmido de verão fresco",
    "Dfc": "Dfc - Subártico",
    "Dfd": "Dfd - Subártico extremamente frio",
    "Dwa": "Dwa - Continental com inverno seco e verão quente",
    "Dwb": "Dwb - Continental com inverno seco e verão fresco",
    "Dwc": "Dwc - Subártico com inverno seco",
    "Dwd": "Dwd - Subártico extremamente frio com inverno seco",
    "Dsa": "Dsa - Continental mediterrâneo de verão quente",
    "Dsb": "Dsb - Continental mediterrâneo de verão fresco",
    "Dsc": "Dsc - Subártico mediterrâneo",
    "Dsd": "Dsd - Subártico mediterrâneo extremamente frio",

    # Grupo E - Climas Polares
    "ET": "ET - Tundra",
    "EF": "EF - Geleira permanente (polar)"
}

def atualizar_legenda_koppen():
    # === ALTERAÇÃO AQUI ===
    # Pegue a camada pelo nome exato no QGIS
    layer = QgsProject.instance().mapLayersByName("CLIMA")[0]

    if not layer:
        print("❌ Camada não encontrada! Verifique o nome exato da camada.")
        return

    if layer.type() != layer.VectorLayer:
        print("❌ A camada não é vetorial!")
        return

    renderer = layer.renderer()
    if not isinstance(renderer, QgsCategorizedSymbolRenderer):
        print("❌ A camada não possui categorias!")
        return

    novas_categorias = []

    for categoria in renderer.categories():
        simbolo = categoria.value()
        label_original = categoria.label()

        nome_completo = KOPPEN_NAMES.get(str(simbolo))
        if nome_completo:
            nova_categoria = QgsRendererCategory(
                simbolo,
                categoria.symbol().clone(),
                nome_completo
            )
            print(f"Atualizado: {simbolo} → {nome_completo}")
        else:
            nova_categoria = QgsRendererCategory(
                simbolo,
                categoria.symbol().clone(),
                label_original
            )
            print(f"Mantido: {simbolo} (não encontrado no dicionário)")

        novas_categorias.append(nova_categoria)

    novo_renderer = QgsCategorizedSymbolRenderer(
        renderer.classAttribute(),
        novas_categorias
    )

    layer.setRenderer(novo_renderer)
    layer.triggerRepaint()

    print("\n✓ Legenda atualizada com sucesso!")
    print("Categorias processadas:", len(novas_categorias))

# Executa a função
atualizar_legenda_koppen()
