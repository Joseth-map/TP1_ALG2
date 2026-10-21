import unittest
import math
from entregadores import Entregador, sigma_distribuicao, gerar_entregadores

class TestEntregadores(unittest.TestCase):

    def test_sigma_distribuicao(self):
        sigma_m = 700.0
        lat = -19.9191
        s_lat, s_lon = sigma_distribuicao(sigma_m, lat)
        
        self.assertAlmostEqual(s_lat, sigma_m / 111320, places=6)
        self.assertGreater(s_lon, s_lat)

    def test_criacao_entregador(self):
        e = Entregador(id=1, latitude=-19.9191, longitude=-43.9386, precisao=8)
        self.assertEqual(e.id, 1)
        self.assertTrue(isinstance(e.nome, str))
        self.assertTrue(5 <= e.velocidade <= 50)
        self.assertEqual(len(e.geohash), 8)

if __name__ == "__main__":
    unittest.main()