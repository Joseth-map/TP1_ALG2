class Node():    
    def __init__(self, valor: str):   
        self.valor = valor
        self.filhos = []

class Trie():
    def __init__(self):
        self.raiz = Node("")

    @staticmethod
    def comparacao(no: Node, palavra: str, prefixo: int) -> tuple:
        cont = 0

        for char in no.valor:
            if prefixo >= len(palavra) or char != palavra[prefixo]:
                return (False, prefixo, cont)
            else:
                prefixo += 1
                cont += 1

        return (True, prefixo, cont)

    def busca(self, palavra: str, retorno=1) -> bool:
        atual = self.raiz
        prefixo = 0
        
        while prefixo < len(palavra):
            for filho in atual.filhos:
                casou, novo_prefixo, _ = self.comparacao(filho, palavra, prefixo)
                if casou:
                    atual = filho
                    prefixo = novo_prefixo
                    break
            else:
                if retorno:
                    return False
                else:
                    return (False, atual, prefixo)
        
        if retorno:
            return len(atual.filhos) == 0 or any(filho.valor == "$" for filho in atual.filhos)
        else:
            return (True, atual, len(palavra)-1)      

    def retorna_prefixo(self, palavra:str) -> tuple:
        
        def percorrer(no: Node, lista: list, prefixo: str) -> None:

            if not no.filhos:
                lista.append(prefixo)
                return
            
            for filho in no.filhos:
                if filho.valor == "$":
                    lista.append(prefixo)
                elif not filho.filhos:
                    lista.append(prefixo + filho.valor)
                else:
                    percorrer(filho, lista, prefixo+filho.valor)
        
        resultado = []
        no_inicial = None
        prefixo_acumulado = ""

        resultado_busca, no, prefixo = self.busca(palavra, 0)     

        if resultado_busca:
            no_inicial = no
            prefixo_acumulado = palavra
        else:
            resto = palavra[prefixo:]
            no_inicial = None
            
            for filho in no.filhos:
                if filho.valor.startswith(resto):
                    no_inicial = filho
                    prefixo_acumulado = palavra[:prefixo] + filho.valor
                    break

            if no_inicial is None:
                return resultado

        percorrer(no_inicial, resultado, prefixo_acumulado)

        return resultado

    def inserir(self, palavra: str) -> None:
        resultado_busca, no_pai, prefixo = self.busca(palavra, 0)

        if resultado_busca:
            if no_pai.filhos and not any(f.valor == "$" for f in no_pai.filhos):
                no_pai.filhos.append(Node("$"))
            return
        
        resto = palavra[prefixo:]

        no = None
        resultado_comp, prefixo_plv_comp, prefixo_no_comp = False, 0, 0
        for filho in no_pai.filhos:
            resultado_comp, prefixo_plv_comp, prefixo_no_comp = self.comparacao(filho, resto, 0)
            if prefixo_no_comp:
                no = filho
                break

        if no is None:
            if not no_pai.filhos and no_pai is not self.raiz:
                no_pai.filhos.append(Node("$"))
            no_pai.filhos.append(Node(resto))
            return

        if resultado_comp:
            if prefixo_no_comp == len(resto):
                
                if no.filhos and not any(f.valor == "$" for f in no.filhos):
                    no.filhos.append(Node("$"))
            else:
                
                if not no.filhos:
                    no.filhos.append(Node("$"))
                no.filhos.append(Node(resto[prefixo_no_comp:]))
            return

        sufixo = Node(no.valor[prefixo_no_comp:])
        sufixo.filhos = no.filhos
        no.valor = no.valor[:prefixo_no_comp]

        sobra = resto[prefixo_no_comp:]
        if sobra:
            no.filhos = [sufixo, Node(sobra)]
        else:
            no.filhos = [sufixo, Node("$")]        

    def imprimir(self) -> None:
       
        def percorrer(no: Node, nivel: int):
            for filho in no.filhos:
                print(f" {"  " * nivel} ├── {filho.valor}")
                percorrer(filho, nivel + 1)

        print("RAIZ")
        percorrer(self.raiz, 1)