from qgis.core import QgsCategorizedSymbolRenderer
from qgis.utils import iface
import re

# Camada ativa
layer = iface.activeLayer()
if layer is None:
    raise Exception("Nenhuma camada ativa selecionada.")

renderer = layer.renderer()

# Verifica se é categorizado
if not isinstance(renderer, QgsCategorizedSymbolRenderer):
    raise Exception("A camada ativa não usa simbologia Categorizada.")

# Pega as categorias atuais
cats = renderer.categories()

# Função para fazer 'ordem natural' (BH_1, BH_2, ..., BH_10 etc.)
def natural_key(cat):
    # Pode usar cat.label() ou cat.value(), escolha o que preferir
    text = str(cat.label())
    # separa em blocos de texto e números
    parts = re.split(r'(\d+)', text)
    out = []
    for p in parts:
        if p.isdigit():
            out.append(int(p))
        else:
            out.append(p.lower())
    return out

# Ordena as categorias
cats_sorted = sorted(cats, key=natural_key)

# Cria novo renderer categorizado, mantendo o mesmo campo da classificação
new_renderer = QgsCategorizedSymbolRenderer(renderer.classAttribute(), cats_sorted)

# Aplica na camada
layer.setRenderer(new_renderer)
layer.triggerRepaint()

print("Categorias reordenadas em ordem alfanumérica (natural).")
