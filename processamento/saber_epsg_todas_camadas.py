from qgis.core import QgsProject

projeto = QgsProject.instance()

for layer in projeto.mapLayers().values():
    crs = layer.crs()
    print("Camada:", layer.name())
    print("  AuthID:", crs.authid())          # Ex.: 'EPSG:31982' ou 'USER:100001'
    print("  EPSG numérico:", crs.postgisSrid())  # Ex.: 31982
    print("  Descrição:", crs.description())
