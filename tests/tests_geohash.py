import unittest
from geohash import (
    divisao_coordenada,
    intercalacao_binaria,
    binario_para_32,
    geohash,
    grades_vizinhas,
    buscar_proximos
)
from trie import Trie

class TestGeohash(unittest.TestCase):

    #Teste de range e tamanho
    def test_divisao_coordenada_norte_sul(self):
        self.assertTrue(divisao_coordenada(10.0, 3, (-90, 90)).startswith("1"))
        self.assertTrue(divisao_coordenada(-19.9, 3, (-90, 90)).startswith("0"))

    def test_divisao_coordenada_tamanho(self):
        res = divisao_coordenada(-19.9191, 10, (-90, 90))
        self.assertEqual(len(res), 10)

    def test_divisao_coordenada_fora_limite(self):
        self.assertIsNone(divisao_coordenada(95.0, 5, (-90, 90)))
        self.assertIsNone(divisao_coordenada(-190.0, 5, (-180, 180)))


    #Testando a intercalação e conversão
    def test_intercalacao_binaria(self):
        lat_bin = "010"
        lon_bin = "111"
        self.assertEqual(intercalacao_binaria(lat_bin, lon_bin), "101110")

    def test_intercalacao_binaria_impar(self):
        lat_bin = "01"
        lon_bin = "110"
        self.assertEqual(intercalacao_binaria(lat_bin, lon_bin), "10110")

    def test_binario_para_32(self):
        bits = "00000" + "01010" + "11111"
        self.assertEqual(binario_para_32(bits), "0bz")

    #Testando o geohash pronto
    def test_geohash_bh_e_prefixos(self):
        lat, lon = -19.9191, -43.9386
        h8 = geohash(lat, lon, 8)
        h5 = geohash(lat, lon, 5)
        self.assertEqual(len(h8), 8)
        self.assertEqual(len(h5), 5)
        self.assertTrue(h8.startswith(h5))
        self.assertEqual(h8, "7h2y8juf")

    def test_grades_vizinhas(self):
        lat, lon = -19.9191, -43.9386
        vizinhos = grades_vizinhas(lat, lon, 6)
        self.assertEqual(len(vizinhos), 9)
        self.assertIn(geohash(lat, lon, 6), vizinhos)

    def test_buscar_proximos(self):
        trie = Trie()
        lat, lon = -19.9191, -43.9386
        h_centro = geohash(lat, lon, 8)
        h_vizinho = geohash(lat + 0.001, lon + 0.001, 8)
        h_distante = geohash(-19.8000, -43.8000, 8)

        trie.inserir(h_centro)
        trie.inserir(h_vizinho)
        trie.inserir(h_distante)

        encontrados = buscar_proximos(trie, lat, lon, m=5)
        self.assertIn(h_centro, encontrados)
        self.assertIn(h_vizinho, encontrados)

if __name__ == "__main__":
    unittest.main()