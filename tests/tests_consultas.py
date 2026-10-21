import unittest
from app import (
    haversine_km,
    escolher_precisao,
    construir_indice,
    consultar,
    montar_tabela
)
from geohash import geohash

class TesteEntregador:
    def __init__(self, id, lat, lon, velocidade=30):
        self.id = id
        self.latitude = lat
        self.longitude = lon
        self.velocidade = velocidade
        self.nome = f"Entregador {id}"
        self.geohash = geohash(lat, lon, 8)

class TestAppHelpers(unittest.TestCase):

    def test_haversine_distancia(self):
        d_zero = haversine_km(-19.9191, -43.9386, -19.9191, -43.9386)
        self.assertAlmostEqual(d_zero, 0.0, places=4)

        d = haversine_km(-19.9191, -43.9386, -19.9320, -43.9378)
        self.assertTrue(1.3 < d < 1.6)

    def test_escolher_precisao(self):
        lat = -19.9191
        p_grande = escolher_precisao(15.0, lat)
        p_pequeno = escolher_precisao(0.5, lat)

        self.assertLess(p_grande, p_pequeno)
        self.assertTrue(1 <= p_grande <= 8)
        self.assertTrue(1 <= p_pequeno <= 8)

    def test_construir_indice_e_consultar(self):
        lat_ref, lon_ref = -19.9191, -43.9386
        e1 = TesteEntregador(1, lat_ref + 0.002, lon_ref + 0.002)
        e2 = TesteEntregador(2, lat_ref + 0.07, lon_ref + 0.07)

        frota = [e1, e2]
        trie, indice = construir_indice(frota)

        self.assertIn(e1.geohash, indice)
        self.assertTrue(trie.busca(e1.geohash))

        res = consultar(trie, indice, lat_ref, lon_ref, raio_km=1.0)
        dentro_ids = [item[0].id for item in res["dentro"]]
        self.assertIn(1, dentro_ids)
        self.assertNotIn(2, dentro_ids)

    def test_montar_tabela(self):
        e1 = TesteEntregador(1, -19.9191, -43.9386, velocidade=30)
        dentro = [(e1, 1.5, 3.0)]
        df = montar_tabela(dentro)

        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]["ID Entregador"], "#ENT-0001")
        self.assertEqual(df.iloc[0]["Distância"], 1.5)
        self.assertEqual(df.iloc[0]["ETA"], 3.0)

if __name__ == "__main__":
    unittest.main()