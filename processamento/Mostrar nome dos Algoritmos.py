for alg in QgsApplication.processingRegistry().algorithms():
    name = alg.displayName().lower()
    if "XXXXX" in name or "XXXX" in name or "XXXXX" in name or "XXXXX" in name:
        print(alg.id(), " --> ", alg.displayName())


###### OR

for alg in QgsApplication.processingRegistry().algorithms():
    name = alg.displayName().lower()
    if "XXXXXXXXX" in name :
        print(alg.id(), " --> ", alg.displayName())
