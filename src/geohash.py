def divisao_coordenada(coordenada: float, nivel: int, intervalo: tuple) -> str:

    if nivel == 0:
        return ""

    if coordenada < intervalo[0] or coordenada > intervalo[1]:
        return None

    meio = (intervalo[0] + intervalo[1]) / 2

    if coordenada < meio:
        return "0" + divisao_coordenada(coordenada, nivel - 1, (intervalo[0], meio))
    else:
        return "1" + divisao_coordenada(coordenada, nivel - 1, (meio, intervalo[1]))

def intercalacao_binaria(lat_bin: str, lon_bin: str) -> str:
    
    intercalado = ""
    for i in range(len(lat_bin)):
        intercalado += lon_bin[i] + lat_bin[i]

    if len(lon_bin) > len(lat_bin):
        intercalado += lon_bin[-1]

    return intercalado

def binario_para_32(num: str) -> int:
    alfabeto = "0123456789bcdefghjkmnpqrstuvwxyz"

    resultado = ""

    for i in range(0, len(num), 5):
        bloco = num[i:i + 5]
        decimal = int(bloco, 2)
        resultado += alfabeto[decimal]

    return resultado

def geohash(latitude: float, longitude: float, precisao: int) -> str:
    
    qtde_bits_total = precisao * 5

    qtde_bits_lat = qtde_bits_total // 2
    qtde_bits_lon = qtde_bits_total // 2 + 1 if qtde_bits_total % 2 else qtde_bits_total // 2
    
    lat_bin = divisao_coordenada(latitude, qtde_bits_lat, (-90, 90))
    lon_bin = divisao_coordenada(longitude, qtde_bits_lon, (-180, 180))

    intercalado = intercalacao_binaria(lat_bin, lon_bin)

    return binario_para_32(intercalado)

def grades_vizinhas(lat: float, lon: float, precisao: int) -> set:
    
    bits = 5 * precisao
    bits_lon = (bits + 1) // 2
    bits_lat = bits // 2
    altura = 180 / 2 ** bits_lat 
    largura = 360 / 2 ** bits_lon 

    celulas = set()
    for dlat in (-1, 0, 1):
        for dlon in (-1, 0, 1):
            celulas.add(geohash(lat + dlat * altura, lon + dlon * largura, precisao))
    
    return celulas

def buscar_proximos(trie, lat: float, lon: float, m: int) -> set:

    encontrados = set()
    for celula in grades_vizinhas(lat, lon, m):
        encontrados.update(trie.retorna_prefixo(celula))
    return encontrados