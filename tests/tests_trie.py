import unittest
from trie import Trie

class TestTrie(unittest.TestCase):

    #Testes de inserção e buscas completas
    def setUp(self):
        self.trie = Trie()

    def test_insercao_e_busca_simples(self):
        self.trie.inserir("7h2y8juf")
        self.assertTrue(self.trie.busca("7h2y8juf"))
        self.assertFalse(self.trie.busca("7h2y8jug"))

    def test_busca_prefixo_incompleto(self):
        self.trie.inserir("7h2y8juf")
        self.assertFalse(self.trie.busca("7h2y"))

    def test_palavra_prefixo_de_outra(self):
        self.trie.inserir("7h2y")
        self.trie.inserir("7h2y8juf")
        self.assertTrue(self.trie.busca("7h2y"))
        self.assertTrue(self.trie.busca("7h2y8juf"))

    def test_divisao_de_nos(self):
        self.trie.inserir("7h2y8juf")
        self.trie.inserir("7h2y8jug")

        self.assertTrue(self.trie.busca("7h2y8juf"))
        self.assertTrue(self.trie.busca("7h2y8jug"))

        resultado = self.trie.retorna_prefixo("7h2y8ju")
        self.assertEqual(set(resultado), {"7h2y8juf", "7h2y8jug"})


    #Testes para retornar ramo de prefixos
    def test_retorna_prefixo_varios_niveis(self):
        palavras = ["7h2y8juf", "7h2y8jug", "7h2y8j12", "7h2z1111"]
        for p in palavras:
            self.trie.inserir(p)

        self.assertEqual(
            set(self.trie.retorna_prefixo("7h2y")),
            {"7h2y8juf", "7h2y8jug", "7h2y8j12"}
        )
        self.assertEqual(
            set(self.trie.retorna_prefixo("7h2")),
            {"7h2y8juf", "7h2y8jug", "7h2y8j12", "7h2z1111"}
        )

    def test_retorna_prefixo_inexistente(self):
        self.trie.inserir("7h2y8juf")
        self.assertEqual(self.trie.retorna_prefixo("6abc"), [])

if __name__ == "__main__":
    unittest.main()