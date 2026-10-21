import osmnx as ox
import random
from geohash import geohash
import math
from faker import Faker

fake = Faker("pt_BR")

class Entregador:
    def __init__(self, id: int, latitude: float, longitude: float, precisao: int = 8):
        self.id = id
        self.nome = fake.first_name() + " " + fake.last_name()
        self.velocidade = random.randint(10, 30)
        self.latitude = latitude
        self.longitude = longitude
        self.geohash = geohash(self.latitude, self.longitude, precisao)

def sigma_distribuicao(sigma_m: float, lat: float) -> tuple:
    sigma_lat = sigma_m / 111_320
    sigma_lon = sigma_m / (111_320 * math.cos(math.radians(lat)))
    return sigma_lat, sigma_lon

def gerar_entregadores(n: int, restaurantes: list, grafo, sigma: float) -> list:
    lats_iniciais = []
    lons_iniciais = []
    base, resto = divmod(n, len(restaurantes))
    extras = set(random.sample(range(len(restaurantes)), resto))

    for i, (lat_centro, lon_centro) in enumerate(restaurantes):
        quantidade = base + (1 if i in extras else 0)
        sigma_lat, sigma_lon = sigma_distribuicao(sigma, lat_centro)

        for _ in range(quantidade):
            lats_iniciais.append(random.gauss(lat_centro, sigma_lat))
            lons_iniciais.append(random.gauss(lon_centro, sigma_lon))

    nos_proximos = ox.distance.nearest_nodes(grafo, X=lons_iniciais, Y=lats_iniciais)

    frota = []
    for id_atual, no in enumerate(nos_proximos, start=1):
        lat_rua = grafo.nodes[no]["y"]
        lon_rua = grafo.nodes[no]["x"]
        frota.append(Entregador(id_atual, lat_rua, lon_rua, 8))

    return frota