layer = iface.activeLayer()
selecionadas = layer.selectedFeatures()

if not selecionadas:
    print("Nenhuma feição selecionada.")
else:
    for f in selecionadas:
        print(f"ID interno: {f.id()}, atributos: {f.attributes()}")
