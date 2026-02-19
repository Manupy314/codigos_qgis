import os
from qgis.core import QgsProject

def atualizar_qml_camada_ativa():
    layer = iface.activeLayer()

    if not layer:
        print('❌ Nenhuma camada ativa.')
        return

    caminho_fonte = layer.source()

    # Remove parâmetros extras (caso seja GPKG, por exemplo)
    caminho_fonte = caminho_fonte.split('|')[0]

    if not os.path.exists(caminho_fonte):
        print('❌ Não consegui localizar o arquivo da camada.')
        return

    pasta = os.path.dirname(caminho_fonte)
    nome_base = os.path.splitext(os.path.basename(caminho_fonte))[0]

    caminho_qml = os.path.join(pasta, f'{nome_base}.qml')

    sucesso, mensagem = layer.saveNamedStyle(caminho_qml)

    if sucesso:
        print('✅ QML atualizado com sucesso.')
        print(f'📁 {caminho_qml}')
    else:
        print('❌ Erro ao salvar QML:')
        print(mensagem)


# Executa
atualizar_qml_camada_ativa()
