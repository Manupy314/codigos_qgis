import re
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout, QListWidget, QPushButton, QLabel, QListWidgetItem
from qgis.core import (
    QgsProject,
    QgsLayerTreeGroup,
    QgsCategorizedSymbolRenderer,
    QgsGraduatedSymbolRenderer,
    QgsRuleBasedRenderer,
    QgsRendererCategory,
    QgsRendererRange
)


def title_case_preservando_siglas(texto: str) -> str:
    """
    Coloca 'Primeira Letra Maiúscula' por palavra,
    preservando siglas (2+ letras todas maiúsculas) e números.
    """
    if not texto:
        return texto

    tokens = re.split(r'(\s+)', texto.strip())
    saida = []

    for token in tokens:
        if token.isspace() or token == '':
            saida.append(token)
            continue

        nucleo = re.sub(r'^[^\wÀ-ÿ]+|[^\wÀ-ÿ]+$', '', token)

        if len(nucleo) >= 2 and nucleo.isupper():
            saida.append(token)
            continue

        if nucleo.isdigit() or (nucleo and nucleo[0].isdigit()):
            saida.append(token)
            continue

        primeira = token[0].upper()
        resto = token[1:].lower() if len(token) > 1 else ''
        saida.append(primeira + resto)

    return ''.join(saida)


def formatar_label_legenda(label_original: str) -> str:
    """
    Se tiver ' - ', mantém a parte 1 e formata a parte 2.
    Senão, formata tudo.
    """
    if not label_original:
        return label_original

    partes = label_original.split(' - ')
    if len(partes) > 1:
        parte1 = partes[0].strip()
        parte2 = ' - '.join(partes[1:]).strip()
        return f'{parte1} - {title_case_preservando_siglas(parte2)}'

    return title_case_preservando_siglas(label_original.strip())


def formatar_renderer_se_existir(layer) -> int:
    """
    Formata rótulos internos do renderizador quando aplicável:
    - Categorizado: labels das categorias
    - Graduado: labels dos ranges
    - Rule-based: labels das regras
    Retorna quantidade de itens de legenda alterados (aproximado).
    """
    renderer = layer.renderer()
    if not renderer:
        return 0

    alterados = 0

    # 1) Categorizado
    if isinstance(renderer, QgsCategorizedSymbolRenderer):
        novas = []
        for cat in renderer.categories():
            novo_label = formatar_label_legenda(cat.label())
            novas.append(QgsRendererCategory(cat.value(), cat.symbol().clone(), novo_label))
            if novo_label != cat.label():
                alterados += 1

        novo_renderer = QgsCategorizedSymbolRenderer(renderer.classAttribute(), novas)
        layer.setRenderer(novo_renderer)
        return alterados

    # 2) Graduado
    if isinstance(renderer, QgsGraduatedSymbolRenderer):
        novos_ranges = []
        for r in renderer.ranges():
            novo_label = formatar_label_legenda(r.label())
            novos_ranges.append(QgsRendererRange(r.lowerValue(), r.upperValue(), r.symbol().clone(), novo_label))
            if novo_label != r.label():
                alterados += 1

        novo_renderer = QgsGraduatedSymbolRenderer(renderer.classAttribute(), novos_ranges)
        novo_renderer.setMode(renderer.mode())
        layer.setRenderer(novo_renderer)
        return alterados

    # 3) Rule-based
    if isinstance(renderer, QgsRuleBasedRenderer):
        root = renderer.rootRule()

        def percorrer_regra(regra):
            nonlocal alterados
            if regra.label():
                novo_label = formatar_label_legenda(regra.label())
                if novo_label != regra.label():
                    regra.setLabel(novo_label)
                    alterados += 1
            for filho in regra.children():
                percorrer_regra(filho)

        percorrer_regra(root)
        layer.setRenderer(renderer)
        return alterados

    # Outros tipos (Single Symbol etc.) não têm uma lista clara de labels para mexer
    return 0


def listar_grupos_recursivo(grupo_raiz: QgsLayerTreeGroup, prefixo=''):
    saida = []
    for filho in grupo_raiz.children():
        if isinstance(filho, QgsLayerTreeGroup):
            caminho = f'{prefixo}{filho.name()}'
            saida.append((filho, caminho))
            saida.extend(listar_grupos_recursivo(filho, prefixo=f'{caminho} / '))
    return saida


def formatar_grupo_e_camadas(grupo_obj: QgsLayerTreeGroup) -> dict:
    """
    Formata:
    - nome do grupo
    - nome de todas as camadas do grupo (inclui subgrupos)
    - legendas internas do renderer quando existir
    """
    resultado = {
        'grupos_renomeados': 0,
        'camadas_renomeadas': 0,
        'itens_legenda_alterados': 0,
        'camadas_total': 0
    }

    # Renomeia o grupo selecionado
    nome_grupo_original = grupo_obj.name()
    nome_grupo_novo = title_case_preservando_siglas(nome_grupo_original)
    if nome_grupo_novo != nome_grupo_original:
        grupo_obj.setName(nome_grupo_novo)
        resultado['grupos_renomeados'] += 1

    # Renomeia camadas + renderizadores
    for node_layer in grupo_obj.findLayers():
        layer = node_layer.layer()
        if not layer:
            continue

        resultado['camadas_total'] += 1

        # 1) nome da camada (sempre)
        nome_original = layer.name()
        nome_novo = title_case_preservando_siglas(nome_original)
        if nome_novo != nome_original:
            layer.setName(nome_novo)
            resultado['camadas_renomeadas'] += 1

        # 2) labels de legenda (se existirem no renderer)
        resultado['itens_legenda_alterados'] += formatar_renderer_se_existir(layer)

        layer.triggerRepaint()

    return resultado


def abrir_dialogo_grupos():
    raiz = QgsProject.instance().layerTreeRoot()
    grupos = listar_grupos_recursivo(raiz)

    if not grupos:
        print('❌ Não encontrei grupos no projeto.')
        return

    dialogo = QDialog()
    dialogo.setWindowTitle('Selecionar grupos para formatar nomes e legendas')
    layout = QVBoxLayout(dialogo)

    layout.addWidget(QLabel('Selecione um ou mais grupos (inclui subgrupos):'))

    lista = QListWidget()
    lista.setSelectionMode(QListWidget.MultiSelection)

    for grupo_obj, caminho in grupos:
        item = QListWidgetItem(caminho)
        item.setData(Qt.UserRole, grupo_obj)
        lista.addItem(item)

    layout.addWidget(lista)

    botao = QPushButton('Executar')
    layout.addWidget(botao)

    def executar():
        itens = lista.selectedItems()
        if not itens:
            print('❌ Nenhum grupo selecionado.')
            dialogo.close()
            return

        total_grupos = 0
        total_camadas = 0
        total_camadas_renomeadas = 0
        total_itens_legenda = 0

        for item in itens:
            grupo_obj = item.data(Qt.UserRole)
            res = formatar_grupo_e_camadas(grupo_obj)

            total_grupos += res['grupos_renomeados']
            total_camadas += res['camadas_total']
            total_camadas_renomeadas += res['camadas_renomeadas']
            total_itens_legenda += res['itens_legenda_alterados']

        iface.layerTreeView().refreshLayerSymbology()
        print('✅ Processo finalizado.')
        print(f'📁 Grupos renomeados: {total_grupos}')
        print(f'🧱 Camadas no(s) grupo(s): {total_camadas}')
        print(f'📝 Camadas renomeadas: {total_camadas_renomeadas}')
        print(f'🏷️ Itens de legenda alterados (renderers): {total_itens_legenda}')

        dialogo.close()

    botao.clicked.connect(executar)
    dialogo.exec_()


# Executa
abrir_dialogo_grupos()
