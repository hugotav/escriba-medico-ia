import bcrypt

# Digite aqui as senhas em texto puro que você quer usar
senhas = ["hugo@2026", "marcela@2026"]

print("Copie os hashes abaixo:\n")

for senha in senhas:
    # Gera a criptografia no padrão exato que o sistema exige
    hash_senha = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()
    print(f"Para a senha '{senha}':")
    print(hash_senha)
    print("-" * 40)