import sqlite3
import os
import hashlib
import shutil
from datetime import datetime
from typing import Optional, Tuple

DB_NAME = 'comercial_v3.db'
BACKUP_DIR = 'backups'

class SistemaComercial:
    def __init__(self):
        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR)
        self.inicializar_db_completo()
        self.criar_usuario_padrao()
    
    def hash_senha(self, senha: str) -> str:
        salt = "sistema_comercial_v4_2024"
        return hashlib.sha256((senha + salt).encode()).hexdigest()
    
    def inicializar_db_completo(self):
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario TEXT UNIQUE NOT NULL,
                    senha TEXT NOT NULL,
                    cargo TEXT NOT NULL CHECK (cargo IN ('admin', 'vendedor')),
                    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS produtos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    preco REAL NOT NULL CHECK (preco > 0),
                    estoque INTEGER NOT NULL DEFAULT 0 CHECK (estoque >= 0),
                    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS vendas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    produto_id INTEGER NOT NULL,
                    quantidade INTEGER NOT NULL CHECK (quantidade > 0),
                    total REAL NOT NULL CHECK (total > 0),
                    usuario TEXT NOT NULL,
                    data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (produto_id) REFERENCES produtos (id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS compras (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    produto_id INTEGER NOT NULL,
                    quantidade INTEGER NOT NULL CHECK (quantidade > 0),
                    custo_unitario REAL NOT NULL CHECK (custo_unitario > 0),
                    custo_total REAL NOT NULL CHECK (custo_total > 0),
                    usuario TEXT NOT NULL,
                    data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (produto_id) REFERENCES produtos (id)
                )
            ''')
            
            conn.commit()
            print("Banco de dados inicializado com sucesso!")
    
    def criar_usuario_padrao(self):
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM usuarios WHERE usuario = 'admin'")
            if not cursor.fetchone():
                senha_hash = self.hash_senha('admin123')
                cursor.execute(
                    "INSERT INTO usuarios (usuario, senha, cargo) VALUES (?, ?, ?)",
                    ('admin', senha_hash, 'admin')
                )
                conn.commit()
                print("Usuario admin criado: admin / admin123")
    
    def fazer_login(self) -> Optional[Tuple[str, str]]:
        print("\n" + "="*50)
        print("                SISTEMA DE LOGIN")
        print("="*50)
        
        usuario = input("Usuario: ").strip()
        senha = input("Senha: ").strip()
        
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT usuario, cargo FROM usuarios WHERE usuario = ? AND senha = ?',
                (usuario, self.hash_senha(senha))
            )
            return cursor.fetchone()
    
    def cadastrar_usuario(self):
        print("\n" + "="*50)
        print("                NOVO USUARIO")
        print("="*50)
        
        usuario = input("Nome de usuario: ").strip()
        senha = input("Senha: ").strip()
        print("Cargo: [1] Admin  [2] Vendedor")
        cargo_op = input("Opcao (1 ou 2): ").strip()
        cargo = 'admin' if cargo_op == '1' else 'vendedor'
        
        try:
            with sqlite3.connect(DB_NAME) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT INTO usuarios (usuario, senha, cargo) VALUES (?, ?, ?)',
                    (usuario, self.hash_senha(senha), cargo)
                )
                conn.commit()
            print(f"Usuario '{usuario}' criado como {cargo.upper()}!")
        except sqlite3.IntegrityError:
            print("ERRO: Usuario ja existe!")
    
    def listar_produtos(self):
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM produtos ORDER BY nome')
            produtos = cursor.fetchall()
            
            if not produtos:
                print("\nNenhum produto cadastrado!")
                return
            
            print("\n" + "="*70)
            print(f"{'ID':<5} {'PRODUTO':<25} {'PRECO':<12} {'ESTOQUE':<10} {'STATUS'}")
            print("-"*70)
            for p in produtos:
                status = "CRITICO" if p[3] < 10 else "OK"
                print(f"{p[0]:<5} {p[1]:<25} R${p[2]:<10.2f} {p[3]:<10} {status}")
            print("="*70)
    
    def estoque_critico(self):
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT nome, estoque FROM produtos WHERE estoque < 10 ORDER BY estoque')
            criticos = cursor.fetchall()
            if criticos:
                print("\n" + "-"*40)
                print("ESTOQUE CRITICO (menos de 10 unidades):")
                for p in criticos:
                    print(f"  {p[0]}: {p[1]} unidades")
    
    def cadastrar_produto(self):
        print("\n" + "-"*40)
        print("CADASTRO DE NOVO PRODUTO")
        print("-"*40)
        
        nome = input("Nome do produto: ").strip()
        try:
            preco = float(input("Preco (R$): "))
            estoque = int(input("Estoque inicial: "))
            
            with sqlite3.connect(DB_NAME) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT INTO produtos (nome, preco, estoque) VALUES (?, ?, ?)',
                    (nome, preco, estoque)
                )
                conn.commit()
            print(f"Produto '{nome}' cadastrado com sucesso!")
        except ValueError:
            print("ERRO: Digite valores numericos validos!")
    
    def realizar_venda(self, produto_id: int, quantidade: int, usuario: str):
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT nome, preco, estoque FROM produtos WHERE id = ?', (produto_id,))
            produto = cursor.fetchone()
            
            if not produto:
                print("ERRO: Produto nao encontrado!")
                return
            
            if produto[2] < quantidade:
                print(f"ERRO: Estoque insuficiente! Disponivel: {produto[2]}")
                return
            
            total = produto[1] * quantidade
            cursor.execute('UPDATE produtos SET estoque = estoque - ? WHERE id = ?', (quantidade, produto_id))
            cursor.execute(
                'INSERT INTO vendas (produto_id, quantidade, total, usuario) VALUES (?, ?, ?, ?)',
                (produto_id, quantidade, total, usuario)
            )
            conn.commit()
            
            print("\n" + "-"*40)
            print("VENDA REALIZADA COM SUCESSO!")
            print(f"Produto: {produto[0]}")
            print(f"Quantidade: {quantidade}")
            print(f"Total: R$ {total:.2f}")
            print("-"*40)
    
    def registrar_compra(self, produto_id: int, quantidade: int, custo_total: float, usuario: str):
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT nome FROM produtos WHERE id = ?', (produto_id,))
            produto = cursor.fetchone()
            
            if not produto:
                print("ERRO: Produto nao encontrado!")
                return
            
            custo_unit = custo_total / quantidade
            cursor.execute('UPDATE produtos SET estoque = estoque + ? WHERE id = ?', (quantidade, produto_id))
            cursor.execute(
                'INSERT INTO compras (produto_id, quantidade, custo_unitario, custo_total, usuario) VALUES (?, ?, ?, ?, ?)',
                (produto_id, quantidade, custo_unit, custo_total, usuario)
            )
            conn.commit()
            
            print("\n" + "-"*40)
            print("COMPRA REGISTRADA!")
            print(f"Produto: {produto[0]}")
            print(f"Quantidade: {quantidade}")
            print(f"Total: R$ {custo_total:.2f}")
            print("-"*40)
    
    def relatorio_vendas(self):
        hoje = datetime.now().strftime('%Y-%m-%d')
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT p.nome, v.quantidade, v.total, v.data, v.usuario
                FROM vendas v JOIN produtos p ON v.produto_id = p.id 
                WHERE DATE(v.data) = ? ORDER BY v.data DESC
            ''', (hoje,))
            vendas = cursor.fetchall()
            
            if not vendas:
                print("\nNenhuma venda realizada hoje!")
                return
            
            print("\n" + "="*80)
            print(f"{'PRODUTO':<25} {'QTD':<6} {'TOTAL':<12} {'USUARIO':<12} {'DATA/HORA'}")
            print("-"*80)
            total_dia = 0
            for v in vendas:
                print(f"{v[0]:<25} {v[1]:<6} R${v[2]:<11.2f} {v[4]:<12} {v[3][:16]}")
                total_dia += v[2]
            print("-"*80)
            print(f"TOTAL DO DIA:                                    R$ {total_dia:>10.2f}")
            print("="*80)
    
    def menu_vendedor(self, usuario: str):
        while True:
            print("\n" + "="*50)
            print(f"             MENU VENDEDOR - {usuario}")
            print("="*50)
            print("1. Listar Estoque")
            print("2. Realizar Venda")
            print("3. Relatorio Vendas Hoje")
            print("4. Sair")
            
            op = input("\nSua opcao: ").strip()
            
            if op == '1':
                self.listar_produtos()
                self.estoque_critico()
            elif op == '2':
                self.listar_produtos()
                try:
                    pid = int(input("ID do produto: "))
                    qtd = int(input("Quantidade: "))
                    self.realizar_venda(pid, qtd, usuario)
                except ValueError:
                    print("ERRO: Digite numeros validos!")
            elif op == '3':
                self.relatorio_vendas()
            elif op == '4':
                break
            input("\nPressione Enter para continuar...")
    
    def menu_admin(self, usuario: str):
        while True:
            print("\n" + "="*50)
            print(f"              MENU ADMIN - {usuario}")
            print("="*50)
            print("1. Cadastrar Produto")
            print("2. Listar Estoque")
            print("3. Realizar Venda")
            print("4. Registrar Compra")
            print("5. Relatorio Vendas")
            print("6. Cadastrar Usuario")
            print("7. Sair")
            
            op = input("\nSua opcao: ").strip()
            
            if op == '1':
                self.cadastrar_produto()
            elif op == '2':
                self.listar_produtos()
                self.estoque_critico()
            elif op == '3':
                self.listar_produtos()
                try:
                    pid = int(input("ID do produto: "))
                    qtd = int(input("Quantidade: "))
                    self.realizar_venda(pid, qtd, usuario)
                except ValueError:
                    print("ERRO: Digite numeros validos!")
            elif op == '4':
                self.listar_produtos()
                try:
                    pid = int(input("ID do produto: "))
                    qtd = int(input("Quantidade: "))
                    custo = float(input("Custo total (R$): "))
                    self.registrar_compra(pid, qtd, custo, usuario)
                except ValueError:
                    print("ERRO: Digite valores validos!")
            elif op == '5':
                self.relatorio_vendas()
            elif op == '6':
                self.cadastrar_usuario()
            elif op == '7':
                break
            input("\nPressione Enter para continuar...")
    
    def main(self):
        print("SISTEMA COMERCIAL v4.1")
        print("Credenciais padrao: admin / admin123")
        print("-"*50)
        
        while True:
            print("\n" + "="*50)
            print("                MENU PRINCIPAL")
            print("="*50)
            print("1. Fazer Login")
            print("2. Cadastrar Novo Usuario")
            print("3. Sair do Sistema")
            
            op = input("\nSua opcao: ").strip()
            
            if op == '1':
                credenciais = self.fazer_login()
                if credenciais:
                    usuario, cargo = credenciais
                    print(f"\nLOGIN REALIZADO! Bem-vindo {usuario} ({cargo.upper()})")
                    if cargo == 'admin':
                        self.menu_admin(usuario)
                    else:
                        self.menu_vendedor(usuario)
                else:
                    print("ERRO: Usuario ou senha invalidos!")
                input("\nPressione Enter para continuar...")
                
            elif op == '2':
                self.cadastrar_usuario()
                input("\nPressione Enter para continuar...")
                
            elif op == '3':
                print("\nObrigado por usar o Sistema Comercial!")
                print("Ate breve!")
                break

if __name__ == "__main__":
    app = SistemaComercial()
    app.main()