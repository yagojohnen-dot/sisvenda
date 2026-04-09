import sqlite3

# Conexão e Criação das Tabelas
def inicializar_db():
    conn = sqlite3.connect('sistema_vendas.db')
    cursor = conn.cursor()
    
    # Tabela de Produtos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            preco REAL NOT NULL,
            estoque INTEGER NOT NULL
        )
    ''')
    
    # Tabela de Vendas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER,
            quantidade INTEGER,
            total REAL,
            data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (produto_id) REFERENCES produtos (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Funções de Operação
def cadastrar_produto(nome, preco, estoque):
    conn = sqlite3.connect('sistema_vendas.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO produtos (nome, preco, estoque) VALUES (?, ?, ?)', (nome, preco, estoque))
    conn.commit()
    conn.close()
    print(f"\nProduto '{nome}' cadastrado com sucesso!")

def listar_produtos():
    conn = sqlite3.connect('sistema_vendas.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM produtos')
    produtos = cursor.fetchall()
    conn.close()
    
    print("\n--- ESTOQUE ATUAL ---")
    for p in produtos:
        print(f"ID: {p[0]} | Nome: {p[1]} | Preço: R${p[2]:.2f} | Estoque: {p[3]}")

def realizar_venda(produto_id, qtd):
    conn = sqlite3.connect('sistema_vendas.db')
    cursor = conn.cursor()
    
    # Verifica se o produto existe e tem estoque
    cursor.execute('SELECT preco, estoque FROM produtos WHERE id = ?', (produto_id,))
    produto = cursor.fetchone()
    
    if produto and produto[1] >= qtd:
        total = produto[0] * qtd
        novo_estoque = produto[1] - qtd
        
        # Atualiza estoque
        cursor.execute('UPDATE produtos SET estoque = ? WHERE id = ?', (novo_estoque, produto_id))
        # Registra venda
        cursor.execute('INSERT INTO vendas (produto_id, quantidade, total) VALUES (?, ?, ?)', (produto_id, qtd, total))
        
        conn.commit()
        print(f"\nVenda realizada! Total: R${total:.2f}")
    else:
        print("\nErro: Produto insuficiente ou ID inválido.")
    
    conn.close()

# Menu Principal
def menu():
    inicializar_db()
    while True:
        print("\n=== SISVENDA - MENU ===")
        print("1. Cadastrar Produto")
        print("2. Listar Produtos")
        print("3. Realizar Venda")
        print("0. Sair")
        
        opcao = input("Escolha uma opção: ")
        
        if opcao == '1':
            nome = input("Nome do produto: ")
            preco = float(input("Preço: "))
            estoque = int(input("Quantidade inicial: "))
            cadastrar_produto(nome, preco, estoque)
        elif opcao == '2':
            listar_produtos()
        elif opcao == '3':
            listar_produtos()
            p_id = int(input("ID do produto: "))
            qtd = int(input("Quantidade: "))
            realizar_venda(p_id, qtd)
        elif opcao == '0':
            break
        else:
            print("Opção inválida!")

if __name__ == "__main__":
    menu()