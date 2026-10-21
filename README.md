# UFood • Monitoramento Geoespacial de Entregadores

**Universidade Federal de Minas Gerais (UFMG)**  
**Departamento de Ciência da Computação (DCC)**  
**Disciplina:** DCC207 – Algoritmos 2 (Prof. Renato Vimieiro)  
**Aluno:** Joseph Patrick Alves de Moura

Sistema de busca e monitoramento de uma frota de entregadores em Belo Horizonte. O usuário escolhe um restaurante (bar ou lanchonete da base da prefeitura), define um raio de busca e vê, em um mapa interativo e em uma tabela, os entregadores mais próximos, com distância e tempo estimado de chegada.

O sistema combina três componentes:

1. **Geohash e Trie compacta.** Cada posição vira um geohash de 8 caracteres em Base32, armazenado em uma Trie compacta. A busca por prefixo retorna os candidatos da região do restaurante e das células adjacentes.
2. **Filtragem geométrica.** Os candidatos são filtrados pela distância de Haversine até o raio escolhido na interface.
3. **Simulador de frota.** Os entregadores são gerados com distribuição normal centrada nos restaurantes e depois projetados na via mais próxima do grafo viário do OpenStreetMap.

---

## Estrutura do projeto

```
.
├── data/
│   ├── base_atividade_economica_prefeitura.csv   # base da prefeitura (Você deve baixá-la)
│   └── bh.graphml                                # malha viária (gerada somente na 1ª execução do código)
├── src/
│   ├── app.py               # interface Streamlit, mapa e tabela
│   ├── entregadores.py
│   ├── geohash.py
│   ├── tratamento_dados.py
│   └── trie.py
├── tests/
│   ├── tests_consultas.py
│   ├── tests_entregadores.py
│   ├── tests_geohash.py
│   └── tests_trie.py
├── requirements.txt
|__ Relatório.pdf
└── README.md
```

## Dados

**Base de restaurantes.** Foi usado o arquivo `atividade-economica`, com data-base de out/2026, do Portal de Dados Abertos da Prefeitura de Belo Horizonte (https://dados.pbh.gov.br/dataset/atividade-economica), salvo como `data/base_atividade_economica_prefeitura.csv`.

A geometria vem em UTM e é convertida para latitude e longitude com `pyproj`. Os restaurantes são filtrados pelos códigos CNAE 5611203, 5611202, 5611205 e 5620104, ou pelo nome fantasia contendo BAR, LANCHONETE ou RESTAURANTE. Os tipos de logradouro abreviados (AVE, RUA, PCA etc.) são expandidos para o nome completo.

**Malha viária.** Na primeira execução, o app baixa o grafo de carros de Belo Horizonte pelo OpenStreetMap (`osmnx`) e salva em `data/bh.graphml`. Nas execuções seguintes, ele carrega o arquivo local. Essa primeira execução precisa de internet e pode demorar alguns minutos.

## Como executar

### 1. Pré-requisitos

- Python 3.12 ou superior
- Acesso à internet na primeira execução (para baixar a malha viária)

### 2. Criar o ambiente e instalar as dependências

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Colocar a base de dados

Copie o CSV da prefeitura para `data/base_atividade_economica_prefeitura.csv`.

### 4. Rodar a interface

A partir da raiz do projeto:

```bash
streamlit run src/app.py
```

O navegador abre em `http://localhost:8501`.

### 5. Como usar o sistema

1. Digite o nome ou o endereço de um estabelecimento na barra lateral e escolha-o na lista.
2. Ajuste o raio de busca (padrão de 2 km).
3. Informe a quantidade de entregadores (N) e clique em **Gerar Entregadores**. Isso descarta a frota anterior e gera N posições do zero.
4. O mapa e a tabela mostram os entregadores dentro do raio. As motos laranjas são os filtrados, e os círculos cinzas são os descartados.

A seção **Histórico de consultas**, no fim da página, mostra o tempo de cada consulta em milissegundos, para o relatório.

## Testes

Os testes ficam em `tests/` e usam `unittest`, sem dependências extras. Rode a partir da raiz do projeto:

Linux/macOS:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

Windows (PowerShell):

```powershell
$env:PYTHONPATH="src"; python -m unittest discover -s tests -v
```

Os testes cobrem:

- `tests_geohash.py`: divisão de coordenadas, intercalação binária, Base32, vizinhança de células e busca de prefixos.
- `tests_trie.py`: inserção, busca exata, prefixos, divisão de nós e `retorna_prefixo`.
- `tests_entregadores.py`: distribuição normal e criação de entregadores.
- `tests_consultas.py`: Haversine, escolha de precisão, índice, consulta com raio e tabela de resultados.

## Decisões de projeto

**Geohash de 8 níveis.** Cada coordenada gera 40 bits, 20 de longitude e 20 de latitude, intercalados com a longitude primeiro.

**Trie compacta.** Os nós guardam trechos de string, e não caracteres. Como visto em aula, um nó com o filho `$` marca o fim de uma palavra. Uma folha também é fim de palavra, e por isso não recebe `$`. A busca por prefixo desce até o nó correspondente e coleta as folhas da subárvore, o que custa O(m + k), com m o tamanho do prefixo e k o número de resultados.

**Índice de entregadores.** A Trie guarda apenas geohashes distintos. Um dicionário associa cada geohash à lista de entregadores que caíram naquela célula. Assim, dois entregadores na mesma célula não se perdem.

**Prefixo da busca.** O app escolhe o maior prefixo cuja célula ainda é maior que o raio. Para 2 km, o prefixo tem 5 caracteres, com células de cerca de 4,6 km. Com a célula do restaurante e as 8 vizinhas, o círculo de atendimento fica totalmente coberto. O problema de borda é tratado antes da filtragem geométrica.

**Distribuição dos entregadores.** Os N entregadores são divididos igualmente entre os restaurantes. Se N não for múltiplo do número de restaurantes, o resto é sorteado. Cada entregador tem posição normal em torno do restaurante, com σ = 700 m (isso faz com que a maioria se concentra no centro de onde vemos.).

**Correção de posição.** As posições sorteadas são projetadas na interseção de via mais próxima do grafo, usando o osmnx, executado ao gera toda a frota.

**Tempo estimado.** ETA = distância / velocidade × 60, com velocidade sorteada entre 10 e 30 km/h, em linha reta. É uma estimativa simplificada, que não usa o tempo real do trajeto pelas vias.

## Tecnologias
Python, Streamlit, Folium (`streamlit-folium`), OSMnx, pandas, pyproj, Faker. Todas as estruturas de dados (geohash, Trie e busca por prefixo) foram implementadas do zero, sem bibliotecas prontas.