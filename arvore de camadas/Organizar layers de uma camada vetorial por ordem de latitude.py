from qgis.core import QgsField
from qgis.PyQt.QtCore import QVariant

# 1. Pega a camada ativa (selecionada no painel de camadas)
layer = iface.activeLayer()
if not layer:
    raise Exception("Nenhuma camada ativa. Selecione a camada das BHs no painel de camadas.")

# 2. Garante que é vetorial
if not layer.isSpatial():
    raise Exception("A camada ativa não é espacial.")

print(f"Camada ativa: {layer.name()}")

# 3. Tenta colocar em modo de edição
if not layer.isEditable():
    ok = layer.startEditing()
    if not ok:
        raise Exception(
            "Não foi possível colocar a camada em modo de edição.\n"
            "Verifique se a camada não é WMS/WFS, se não está marcada como somente leitura,\n"
            "e se você tem permissão de escrita na pasta do arquivo."
        )

# 4. Nomes dos campos
nome_campo_lat = "lat_centro"
nome_campo_ordem = "ordem_lat"
nome_campo_leg = "BH_legenda"

pr = layer.dataProvider()

# 5. Cria campos, se não existirem
campos_existentes = [f.name() for f in layer.fields()]
novos_campos = []

if nome_campo_lat not in campos_existentes:
    novos_campos.append(QgsField(nome_campo_lat, QVariant.Double))

if nome_campo_ordem not in campos_existentes:
    novos_campos.append(QgsField(nome_campo_ordem, QVariant.Int))

if nome_campo_leg not in campos_existentes:
    novos_campos.append(QgsField(nome_campo_leg, QVariant.String))

if novos_campos:
    pr.addAttributes(novos_campos)
    layer.updateFields()
    print("Novos campos criados:", [c.name() for c in novos_campos])
else:
    print("Campos já existiam, não foi necessário criar novos.")

# 6. Recarrega lista de campos e pega os índices
fields = layer.fields()
idx_lat = fields.indexOf(nome_campo_lat)
idx_ordem = fields.indexOf(nome_campo_ordem)
idx_leg = fields.indexOf(nome_campo_leg)

if idx_lat == -1 or idx_ordem == -1 or idx_leg == -1:
    raise Exception("Algum índice de campo deu -1. Confira se os campos foram criados corretamente.")

print(f"Índices -> lat: {idx_lat}, ordem: {idx_ordem}, legenda: {idx_leg}")

# 7. Monta lista (fid, latitude)
lista = []
for feat in layer.getFeatures():
    geom = feat.geometry()
    if geom is None or geom.isEmpty():
        continue
    centro = geom.centroid().asPoint()
    lat = centro.y()
    lista.append((feat.id(), lat))

if not lista:
    raise Exception("Nenhuma feição com geometria válida foi encontrada.")

print(f"Total de feições consideradas: {len(lista)}")

# 8. Ordena pela latitude
# reverse=False -> de sul para norte (lat menor para maior)
# reverse=True  -> de norte para sul (lat maior para menor)
lista_ordenada = sorted(lista, key=lambda x: x[1], reverse=False)

# 9. Atualiza atributos com ordem e rótulo BHxx
for i, (fid, lat) in enumerate(lista_ordenada, start=1):
    layer.changeAttributeValue(fid, idx_lat, float(lat))
    layer.changeAttributeValue(fid, idx_ordem, int(i))
    bh_label = f"BH{i:02d}"  # BH01, BH02, ...
    layer.changeAttributeValue(fid, idx_leg, bh_label)

# 10. Tenta salvar as alterações
if not layer.commitChanges():
    # Se der problema ao salvar, imprime os erros
    print("Não foi possível salvar as alterações. Erros:")
    for err in layer.commitErrors():
        print(err)
    raise Exception("Falha ao salvar alterações na camada.")
else:
    print("Campos lat_centro, ordem_lat e BH_legenda atualizados e salvos com sucesso.")
