import sqlite3
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

import numpy as np

# Dicionário para mapear os identificadores dos nós para nomes legíveis
nome_formatado = {
    'guarda': 'Guarda',
    'biblioteca': 'Biblioteca',
    'escada_esquerda_primeiro_piso': 'Escada',
    'elevador_esquerdo_primeiro_piso': 'Elevador',
    'escada_esquerda_quarto_piso': 'Quarto Piso',
    'elevador_esquerdo_quarto_piso': 'Quarto Piso',
    4007: 'Sala 4007',
    4010: 'Sala 4010',
    4013: 'Sala 4013',
    4014: 'Sala 4014',
    'salao_de_honra': 'Salão de Honra',
    'sala_dos_professores': 'Sala dos Professores',
    'auditorio_quarto_piso': 'Auditório - Quarto Piso'
}

# Função para construir o grafo com base na escolha do usuário (escada ou elevador)
def construir_grafo(modo_transporte):
    G = nx.Graph()

    # Coordenadas dos nós (x, y, z)
    posicoes = {
        'guarda': (520, 620, 0),
        'escada_esquerda_primeiro_piso': (510, 550, 0),
        'elevador_esquerdo_primeiro_piso': (514, 527, 0),
        'escada_esquerda_quarto_piso': (510,  550, 3),
        'elevador_esquerdo_quarto_piso': (514, 527, 3),
        4007: (380, 580, 3),
        4010: (300, 580, 3),
        4013: (260, 580, 3),
        4014: (215, 580, 3),
        'biblioteca': (650, 580, 3),
        'salao_de_honra': (537, 580, 3),
        'sala_dos_professores': (465, 580, 3),
        'auditorio_quarto_piso': (537, 510, 3)
    }# Ao atualizar o grafo precisamos lembrar de atualizar os nome na visualizacao

    # Conectar nós do primeiro andar ao quarto andar
    if modo_transporte == 'Escada':
        G.add_edge('guarda', 'escada_esquerda_primeiro_piso', weight=calcular_distancia(*posicoes['guarda'], *posicoes['escada_esquerda_primeiro_piso']))
        G.add_edge('escada_esquerda_primeiro_piso', 'escada_esquerda_quarto_piso', weight=calcular_distancia(*posicoes['escada_esquerda_primeiro_piso'], *posicoes['escada_esquerda_quarto_piso']))
    elif modo_transporte == 'Elevador':
        G.add_edge('guarda', 'elevador_esquerdo_primeiro_piso', weight=calcular_distancia(*posicoes['guarda'], *posicoes['elevador_esquerdo_primeiro_piso']))
        G.add_edge('elevador_esquerdo_primeiro_piso', 'elevador_esquerdo_quarto_piso', weight=calcular_distancia(*posicoes['elevador_esquerdo_primeiro_piso'], *posicoes['elevador_esquerdo_quarto_piso']))

    # Conectar nós do quarto andar com base nas distâncias físicas
    G.add_edge('elevador_esquerdo_quarto_piso', 'salao_de_honra', weight=calcular_distancia(*posicoes['elevador_esquerdo_quarto_piso'], *posicoes['salao_de_honra']))
    G.add_edge('escada_esquerda_quarto_piso', 'salao_de_honra', weight=calcular_distancia(*posicoes['escada_esquerda_quarto_piso'], *posicoes['salao_de_honra']))
    G.add_edge('salao_de_honra', 'sala_dos_professores', weight=calcular_distancia(*posicoes['salao_de_honra'], *posicoes['sala_dos_professores']))
    G.add_edge('salao_de_honra', 4007, weight=calcular_distancia(*posicoes['salao_de_honra'], *posicoes[4007]))
    G.add_edge('salao_de_honra', 4010, weight=calcular_distancia(*posicoes['salao_de_honra'], *posicoes[4010]))
    G.add_edge('salao_de_honra', 4013, weight=calcular_distancia(*posicoes['salao_de_honra'], *posicoes[4013]))
    G.add_edge('salao_de_honra', 4014, weight=calcular_distancia(*posicoes['salao_de_honra'], *posicoes[4014]))
    G.add_edge('salao_de_honra', 'biblioteca', weight=calcular_distancia(*posicoes['salao_de_honra'], *posicoes['biblioteca']))

    # Conectar elevador do quarto andar a outras salas
    G.add_edge('elevador_esquerdo_quarto_piso', 'auditorio_quarto_piso', weight=calcular_distancia(*posicoes['elevador_esquerdo_quarto_piso'], *posicoes['auditorio_quarto_piso']))

    # Conectar as outras salas entre si
    G.add_edge(4013, 4010, weight=calcular_distancia(*posicoes[4013], *posicoes[4010]))
    G.add_edge(4014, 4013, weight=calcular_distancia(*posicoes[4014], *posicoes[4013]))

    return G, posicoes

# Função para gerar instruções de direção e de andar com base no caminho
def gerar_instrucoes(caminho, posicoes):
    instrucoes = []

    for i in range(1, len(caminho)):
        no_atual = caminho[i]
        no_anterior = caminho[i - 1]
        
        # Coordenadas dos nós
        coord_anterior = posicoes[no_anterior]
        coord_atual = posicoes[no_atual]

        # Verificar se há mudança de andar (eixo Z)
        if coord_anterior[2] != coord_atual[2]:
            if coord_atual[2] > coord_anterior[2]:
                instrucoes.append(f"Suba de {nome_formatado.get(no_anterior, no_anterior)} para o {nome_formatado.get(no_atual, no_atual)}.")
            else:
                instrucoes.append(f"Desça de {nome_formatado.get(no_anterior, no_anterior)} para o {nome_formatado.get(no_atual, no_atual)}.")
        else:
            # Se estiver no mesmo andar, calcular direção
            vetor_caminhado = calcular_vetor_direcao(coord_anterior, coord_atual)
            versor_atual = calcular_versor(vetor_caminhado)

            if i < len(caminho) - 1:
                no_proximo = caminho[i + 1]
                coord_proximo = posicoes[no_proximo]
                vetor_seguinte = calcular_vetor_direcao(coord_atual, coord_proximo)
                versor_seguinte = calcular_versor(vetor_seguinte)

                resultado = produto_vetorial(versor_atual, versor_seguinte)
                
                if np.isclose(resultado, 0, atol=0.02):
                    instrucoes.append(f"Siga em frente até {nome_formatado.get(no_atual, no_atual)}.")
                elif resultado < 0:
                    instrucoes.append(f"Siga até {nome_formatado.get(no_atual, no_atual)} e vire à esquerda.")
                elif resultado > 0:
                    instrucoes.append(f"Siga até {nome_formatado.get(no_atual, no_atual)} e vire à direita.")
            else:
                # Último nó
                instrucoes.append(f"Siga em frente até {nome_formatado.get(no_atual, no_atual)}.")

    return instrucoes

def visualizar_e_instruir(path, pos, andar_imgs):
    instrucoes = gerar_instrucoes(path, pos)

    # Criar uma lista de andares distintos pelos quais o caminho passa
    andares_no_caminho = sorted(set(pos[no][2] for no in path))

    # Configurar a grade dos subplots (2 colunas, número de linhas depende da quantidade de andares)
    fig, axs = plt.subplots(nrows=len(andares_no_caminho) // 2 + len(andares_no_caminho) % 2, ncols=2, figsize=(12, 6))
    axs = axs.flatten()  # Garantir que temos um array 1D de subplots

    # Iterar sobre os andares presentes no caminho e plotar em cada subplot
    for idx, andar in enumerate(andares_no_caminho):
        caminho_no_andar = [no for no in path if pos[no][2] == andar]

        if andar in andar_imgs and len(caminho_no_andar) >= 1:
            visualizar_caminho_2d(caminho_no_andar, pos, andar, andar_imgs[andar], axs[idx])
        else:
            print(f"Sem caminho suficiente para visualização no andar {andar + 1} ou imagem não encontrada.")

    # Exibir as instruções
    for instrucao in instrucoes:
        print(instrucao)

    plt.tight_layout()
    plt.show()


# Função para visualizar o caminho em 2D em um subplot específico
def visualizar_caminho_2d(caminho, posicoes, andar, imagem_planta, ax):
    """
    Visualiza o caminho realizado em um andar específico sobre a planta do andar, dentro de um subplot.
    
    Parâmetros:
    - caminho: lista de nós (locais) no caminho deste andar.
    - posicoes: dicionário com coordenadas (x, y, z) de cada nó.
    - andar: número do andar em que o caminho está sendo traçado.
    - imagem_planta: caminho para a imagem da planta do andar correspondente.
    - ax: Subplot onde o gráfico será desenhado.
    """
    
    # Carregar a imagem da planta do andar
    img = mpimg.imread(imagem_planta)

    if len(caminho) == 1:
        print(f"Visualizando nó único no andar {andar + 1}.")
    
    # Coordenadas (x, y) no andar atual
    coords_x = [posicoes[no][0] for no in caminho]
    coords_y = [posicoes[no][1] for no in caminho]

    # Exibir a imagem do andar no subplot específico
    ax.imshow(img, extent=[0, img.shape[1], img.shape[0], 0])
    
    # Traçar o caminho (ou apenas o ponto se houver apenas um nó)
    ax.plot(coords_x, coords_y, marker='o', color='red', markersize=5, linewidth=2)
    ax.set_title(f'Caminho no Andar {andar + 1}')
    ax.axis('off')  # Remover os eixos para melhorar a visualização

import math
import numpy as np

# Função para calcular a distância Euclidiana em 3D entre dois pontos
def calcular_distancia(x1, y1, z1, x2, y2, z2):
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2 + (z2 - z1)**2)

# Função para calcular o vetor direção entre dois nós
def calcular_vetor_direcao(p1, p2):
    return (p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2])

# Função para calcular o produto vetorial entre dois vetores (somente x, y)
def produto_vetorial(v1, v2):
    return v1[0] * v2[1] - v1[1] * v2[0]

# Função para calcular o versor (vetor unitário) de um vetor direção
def calcular_versor(vetor):
    norm = np.linalg.norm(vetor)
    return (vetor[0] / norm, vetor[1] / norm) if norm != 0 else (0, 0)


# Dicionário que mapeia os andares às imagens das plantas
andar_imgs = {
    0: 'planta_0.png',
    1: 'planta_1.png',
    2: 'planta_2.png',
    3: 'planta_3.png'
}

# Função para buscar a sala no banco de dados e gerar o gráfico 2D
def buscar_sala(nome_ou_sala, modo_transporte):
    try:
        banco = sqlite3.connect('wazime.db')
        cursor = banco.cursor()

        if nome_ou_sala.isdigit():
            sala_destino = nome_ou_sala
            cursor.execute("SELECT Nome, Secao, Sala FROM cadastro WHERE Sala = ?", (sala_destino,))
            resultado = cursor.fetchone()
        else:
            nome = nome_ou_sala.lower()
            cursor.execute("SELECT Nome, Secao, Sala FROM cadastro WHERE LOWER(Nome) = ? OR LOWER(Sala) = ?", (nome, nome))
            resultado = cursor.fetchone()

        if resultado:
            nome, secao, sala = resultado
            print(f"Nome: {nome}, Seção: {secao}, Sala: {sala}")

            if isinstance(sala, int) or str(sala).isdigit():
                sala_destino = int(sala)
            else:
                sala_destino = sala

            G, pos = construir_grafo(modo_transporte)

            if sala_destino in G.nodes:
                path = nx.shortest_path(G, 'guarda', sala_destino, weight='weight')
                visualizar_e_instruir(path, pos, andar_imgs)
            else:
                print(f"Sala {sala_destino} não está no grafo.")
        else:
            print(f"Nome ou sala {nome_ou_sala} não foi encontrado no banco de dados.")

        banco.close()

    except sqlite3.Error as erro:
        print("Erro ao realizar a pesquisa:", erro)


# Função para cadastrar as informações no banco de dados SQLite
def cadastrar(nome, secao, sala):
    if not nome.strip() or not secao.strip() or not sala.strip():
        print("Erro: todos os campos devem ser preenchidos.")
        return
    try:
        banco = sqlite3.connect('wazime.db')
        cursor = banco.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS cadastro (Nome TEXT, Secao TEXT, Sala TEXT)""")
        cursor.execute("INSERT INTO cadastro (Nome, Secao, Sala) VALUES (?, ?, ?)", (nome, secao, sala))
        banco.commit()
        banco.close()
        print("Dados inseridos com sucesso!")
    except sqlite3.Error as erro:
        print("Erro ao inserir os dados:", erro)


class MyGridLayout(GridLayout):
    def __init__(self, **kwargs):
        super(MyGridLayout, self).__init__(**kwargs)
        self.cols = 2

        # Nome
        self.add_widget(Label(text="Nome:"))
        self.nome_input = TextInput(multiline=False)
        self.add_widget(self.nome_input)

        # Secao
        self.add_widget(Label(text="Seção:"))
        self.secao_input = TextInput(multiline=False)
        self.add_widget(self.secao_input)

        # Sala
        self.add_widget(Label(text="Sala:"))
        self.sala_input = TextInput(multiline=False)
        self.add_widget(self.sala_input)

        # Modo de transporte (Escada ou Elevador)
        self.add_widget(Label(text="Modo de Transporte:"))
        self.modo_transporte_spinner = Spinner(
            text='Escada',
            values=('Escada', 'Elevador')
        )
        self.add_widget(self.modo_transporte_spinner)

        # Botão para Cadastrar
        self.cadastrar_button = Button(text="Cadastrar")
        self.cadastrar_button.bind(on_press=self.cadastrar)
        self.add_widget(self.cadastrar_button)

        # Botão para Pesquisar
        self.pesquisar_button = Button(text="Pesquisar")
        self.pesquisar_button.bind(on_press=self.pesquisar)
        self.add_widget(self.pesquisar_button)

    # Função chamada ao clicar no botão "Cadastrar"
    def cadastrar(self, instance):
        nome = self.nome_input.text
        secao = self.secao_input.text
        sala = self.sala_input.text
        cadastrar(nome, secao, sala)

    # Função chamada ao clicar no botão "Pesquisar"
    def pesquisar(self, instance):
        nome = self.nome_input.text
        modo_transporte = self.modo_transporte_spinner.text
        buscar_sala(nome, modo_transporte)


class MyApp(App):
    def build(self):
        return MyGridLayout()


if __name__ == "__main__":
    MyApp().run()