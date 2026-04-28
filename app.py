import sqlite3
import os
import hashlib
import getpass  # Biblioteca para esconder a senha
from datetime import datetime
from typing import Optional, Tuple

DB_NAME = 'comercial_v.db'
BACKUP_DIR = 'backups'

class SistemaComercial:
    def __init__(self):
        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR)
        self.inicializar_db_completo()
        self.criar_usuario_padrao()
    
    def limpar_tela(self):
        # Limpa o terminal dependendo do sistema operacional
        os.system('cls' if os.name == 'nt' else 'clear')
    
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
            
            conn.commit()
    
    def criar_usuario_padrao(self):
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            # Novo usuário padrão solicitado
            novo_user = 'yago'
            nova_senha = '050811yago'
            
            cursor.execute("SELECT 1 FROM usuarios WHERE usuario = ?", (novo_user,))
            if not cursor.fetchone():
                senha_hash = self.hash_senha(nova_senha)
                cursor.execute(
                    "INSERT INTO usuarios (usuario, senha, cargo) VALUES (?, ?, ?)",
                    (novo_user, senha_hash, 'admin')
                )
                conn.commit()
                print(f"✅ Usuário mestre '{novo_user}' configurado.")

    def fazer_login(self) -> Optional[Tuple[str, str]]:
        print("\n" + "="*50)
        print("                SISTEMA DE LOGIN v4.2")
        print("="*50)
        
        usuario = input("👤 Usuário: ").strip()
        # getpass esconde os caracteres enquanto você digita
        senha = getpass.getpass("🔒 Senha: ").strip() 
        
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT usuario, cargo FROM usuarios WHERE usuario = ? AND senha = ?',
                (usuario, self.hash_senha(senha))
            )
            resultado = cursor.fetchone()
            
            if resultado:
                self.limpar_tela() # Esconde os dados de login limpando a tela
                return resultado
            return None

    def cadastrar_usuario(self):
        print("\n" + "="*50)
        print("                NOVO USUARIO")
        print("="*50)
        
        usuario = input("👤 Nome de usuario: ").strip()
        senha1 = getpass.getpass("🔒 Senha (min 4 chars): ").strip()
        senha2 = getpass.getpass("🔒 Confirme senha: ").strip()
        
        if senha1 != senha2:
            print("❌ Senhas não conferem!")
            return
        
        if len(senha1) < 4:
            print("❌ Senha muito curta!")
            return
        
        print("Cargo: [1] Admin  [2] Vendedor")
        cargo_op = input("Opção (1/2): ").strip()
        cargo = 'admin' if cargo_op == '1' else 'vendedor'
        
        try:
            with sqlite3.connect(DB_NAME) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT INTO usuarios (usuario, senha, cargo) VALUES (?, ?, ?)',
                    (usuario, self.hash_senha(senha1), cargo)
                )
                conn.commit()
            print(f"✅ '{usuario}' criado como {cargo.upper()}!")
        except sqlite3.IntegrityError:
            print("❌ Usuario já existe!")

    def listar_produtos(self):
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM produtos ORDER BY nome')
            produtos = cursor.fetchall()
            
            if not produtos:
                print("\n❌ Nenhum produto!")
                return
            
            print("\n" + "="*70)
            print(f"{'ID':<5} {'PRODUTO':<25} {'PREÇO':<12} {'ESTOQUE':<10} {'STATUS'}")
            print("-"*70)
            for p in produtos:
                status = "🚨 CRÍTICO" if p[3] < 10 else "✅ OK"
                print(f"{p[0]:<5} {p[1]:<25} R${p[2]:<10.2f} {p[3]:<10} {status}")
            print("="*70)

    def cadastrar_produto(self):
        print("\n🆕 CADASTRO PRODUTO")
        nome = input("Nome: ").strip()
        try:
            preco = float(input("Preço R$: "))
            estoque = int(input("Estoque: "))
            with sqlite3.connect(DB_NAME) as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO produtos (nome, preco, estoque) VALUES (?, ?, ?)', (nome, preco, estoque))
                conn.commit()
            print(f"✅ '{nome}' cadastrado!")
        except ValueError:
            print("❌ Números inválidos!")

    def realizar_venda(self, produto_id: int, quantidade: int, usuario: str):
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT nome, preco, estoque FROM produtos WHERE id = ?', (produto_id,))
            produto = cursor.fetchone()
            
            if not produto or produto[2] < quantidade:
                print("❌ Produto inexistente ou estoque insuficiente!")
                return
            
            total = produto[1] * quantidade
            cursor.execute('UPDATE produtos SET estoque = estoque - ? WHERE id = ?', (quantidade, produto_id))
            cursor.execute('INSERT INTO vendas (produto_id, quantidade, total, usuario) VALUES (?, ?, ?, ?)',
                         (produto_id, quantidade, total, usuario))
            conn.commit()
            print(f"\n✅ VENDA OK! R${total:.2f}")

    def menu_admin(self, usuario: str):
        while True:
            print(f"\n👑 PAINEL ADMIN - Logado como: {usuario}")
            print("1. 🆕 Novo Produto  2. 📋 Estoque  3. 💰 Venda  4. 👤 Novo Usuário  5. 🚪 Sair")
            op = input("Opção: ").strip()
            if op == '1': self.cadastrar_produto()
            elif op == '2': self.listar_produtos()
            elif op == '3':
                self.listar_produtos()
                try:
                    pid = int(input("ID: ")); qtd = int(input("Qtd: "))
                    self.realizar_venda(pid, qtd, usuario)
                except: print("❌ Erro nos dados!")
            elif op == '4': self.cadastrar_usuario()
            elif op == '5': break

    def main(self):
        while True:
            print("\n🎯 SISTEMA COMERCIAL v4.2")
            print("1. Login  2. Sair")
            op = input("Opção: ").strip()
            
            if op == '1':
                credenciais = self.fazer_login()
                if credenciais:
                    user, cargo = credenciais
                    if cargo == 'admin': self.menu_admin(user)
                    else: print("Menu vendedor não implementado nesta versão.")
                else:
                    print("❌ Login ou Senha incorretos!")
            elif op == '2':
                break

if __name__ == "__main__":
    app = SistemaComercial()
    app.main()