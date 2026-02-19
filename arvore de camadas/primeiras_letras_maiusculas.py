# Script para formatar legendas - primeira letra maiúscula, resto minúsculo
from qgis.core import QgsCategorizedSymbolRenderer, QgsRendererCategory

def formatar_legenda_maiuscula_minuscula():
    # Pega a camada ativa
    layer = iface.activeLayer()

    if not layer:
        print("❌ Nenhuma camada selecionada! Selecione a camada no painel de camadas.")
        return

    if layer.type() != layer.VectorLayer:
        print("❌ A camada selecionada não é uma camada vetorial!")
        return

    # Verifica se é uma camada categorizada
    renderer = layer.renderer()
    if not isinstance(renderer, QgsCategorizedSymbolRenderer):
        print("❌ A camada não está usando renderização categorizada!")
        return

    # Cria novas categorias com os nomes formatados
    novas_categorias = []

    for categoria in renderer.categories():
        simbolo = categoria.value()
        label_original = categoria.label()

        # Formata o texto: primeira letra maiúscula, resto minúsculo
        if label_original:
            # Divide o texto em partes (para tratar casos como "Af - Tropical...")
            partes = label_original.split(' - ')

            if len(partes) > 1:
                # Se tem separador " - ", formata ambas as partes
                parte1 = partes[0]  # Mantém a sigla como está (Af, Am, etc.)
                parte2 = partes[1].capitalize()  # Formata a descrição
                novo_label = f"{parte1} - {parte2}"
            else:
                # Se não tem separador, formata todo o texto
                novo_label = label_original.capitalize()
        else:
            novo_label = label_original

        # Cria uma nova categoria com o nome formatado
        nova_categoria = QgsRendererCategory(
            simbolo,
            categoria.symbol().clone(),
            novo_label
        )
        novas_categorias.append(nova_categoria)
        print(f"✅ Formatado: '{label_original}' → '{novo_label}'")

    # Cria e aplica o novo renderizador
    novo_renderer = QgsCategorizedSymbolRenderer(
        renderer.classAttribute(),
        novas_categorias
    )

    layer.setRenderer(novo_renderer)

    # Atualiza a legenda no projeto
    layer.triggerRepaint()
    iface.layerTreeView().refreshLayerSymbology(layer.id())

    print(f"\n✅ Legenda formatada com sucesso!")
    print(f"📊 Total de categorias processadas: {len(novas_categorias)}")

# Executa a função
formatar_legenda_maiuscula_minuscula()
