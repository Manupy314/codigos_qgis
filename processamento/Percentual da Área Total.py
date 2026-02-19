### se não tem o cmapo de área
"AREA_HA" / aggregate(@layer, 'sum', "AREA_HA") * 100

### se já tem campo de área
$area / aggregate(layer:=@layer, aggregate:='sum', expression:=$area) * 100
