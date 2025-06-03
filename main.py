# main.py
# IMPORTANTE: Para usar a funcionalidade de clonagem de repositórios Git (definindo GIT_REPO_URL),
# o comando 'git' deve estar instalado e acessível no PATH do sistema.
# Se 'git' não estiver disponível, a clonagem será pulada ou falhará,
# e o script tentará usar o diretório local especificado em BASE_CODE_DIR.

import os
import logging
import shutil # Para remover diretório clonado, se necessário
import hashlib # Adicionado para a função process_file que usa hashlib

from code_indexer.chunker.code_chunker import CodeChunker
from code_indexer.merkle_tree.merkle import MerkleTree
from code_indexer.client import IndexerClient, OBFUSCATION_KEY, obfuscate_file_path
from code_indexer.git_operations import GitRepoCloner # Nova importação

# Configuração do logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(module)s] - %(message)s')

# --- Configurações ---
# Diretório base para o código a ser indexado.
# Pode ser um diretório local existente ou um diretório onde um repo será clonado.
BASE_CODE_DIR = "indexed_code_source" # Um diretório genérico que conterá o código

# Configurações para clonagem Git (opcional)
# Deixe GIT_REPO_URL como None ou "" para pular a clonagem e usar o BASE_CODE_DIR como está.
# GIT_REPO_URL = "https://github.com/git-fixtures/basic.git" # Repositório pequeno para teste
GIT_REPO_URL = "https://github.com/pallets/click.git" # Um repositório real, mas não muito grande
# GIT_REPO_URL = None # Descomente para pular a clonagem

# Se GIT_REPO_URL for fornecido, o repositório será clonado dentro de BASE_CODE_DIR,
# em um subdiretório nomeado a partir da URL do repo (simplificado).
# Por exemplo, "https://github.com/pallets/click.git" -> "indexed_code_source/click" (após sanitização)

SERVER_URL = "http://localhost:8080/api" # URL do servidor de indexação (hipotético)
CLEANUP_CLONED_REPO_AFTER_RUN = True # Define se o repositório clonado deve ser removido após a execução


def get_repo_name_from_url(url: str) -> str:
    """Extrai um nome de diretório a partir da URL do repositório."""
    if not url:
        return "unknown_repo"
    repo_name = url.split('/')[-1]
    if repo_name.endswith(".git"):
        repo_name = repo_name[:-4]
    # Sanitiza para evitar caracteres problemáticos em nomes de diretório
    return "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in repo_name)


def process_file(file_path: str, chunker: CodeChunker, client: IndexerClient) -> list[dict]:
    """
    Processa um único arquivo: faz chunking, constrói Merkle Tree, e (simula) envia chunks para embedding.
    (Conteúdo desta função permanece o mesmo do passo anterior, apenas movido aqui para clareza)
    """
    logging.info(f"Processando arquivo: {file_path}...")
    processed_chunks_metadata = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        logging.error(f"Erro ao ler o arquivo {file_path}: {e}")
        return processed_chunks_metadata

    if not content.strip():
        logging.info(f"Arquivo {file_path} está vazio ou contém apenas espaços em branco. Pulando.")
        return processed_chunks_metadata

    code_chunks_content = chunker.chunk_python_code(content)
    if not code_chunks_content:
        logging.info(f"Nenhum chunk gerado para {file_path}. Pulando.")
        return processed_chunks_metadata

    logging.info(f"Gerados {len(code_chunks_content)} chunks para {file_path}.")
    merkle_tree = MerkleTree(data_blocks=code_chunks_content)
    root_hash = merkle_tree.get_root_hash()

    if not root_hash:
        logging.warning(f"Não foi possível obter o hash raiz da Merkle Tree para {file_path}. Pulando.")
        return processed_chunks_metadata

    logging.info(f"Hash raiz da Merkle Tree para {file_path}: {root_hash}")
    needs_resync = client.sync_merkle_tree(root_hash)

    if not needs_resync:
        logging.info(f"Conteúdo de {file_path} (hash: {root_hash}) já está sincronizado com o servidor.")
        obf_path = obfuscate_file_path(file_path, OBFUSCATION_KEY)
        for i, chunk_c in enumerate(code_chunks_content):
            simulated_cached_id = hashlib.sha256((chunk_c + obf_path + str(i)).encode()).hexdigest()[:16]
            processed_chunks_metadata.append({
                "original_file_path": file_path,
                "obfuscated_file_path": obf_path,
                "chunk_index": i,
                "content_preview": chunk_c[:50].replace('\n', ' ') + "...",
                "embedding_id": simulated_cached_id,
                "status": "cached"
            })
        return processed_chunks_metadata

    logging.info(f"Resincronização necessária para {file_path}. Enviando chunks para embedding...")
    current_line_number = 1
    for i, chunk_code in enumerate(code_chunks_content):
        chunk_line_count = chunk_code.count('\n') + 1
        start_line = current_line_number
        end_line = current_line_number + chunk_line_count -1

        embedding_id = client.send_chunk_for_embedding(
            chunk_content=chunk_code,
            original_file_path=file_path,
            start_line=start_line,
            end_line=end_line
        )

        obf_path = obfuscate_file_path(file_path, OBFUSCATION_KEY)
        if embedding_id:
            processed_chunks_metadata.append({
                "original_file_path": file_path,
                "obfuscated_file_path": obf_path,
                "chunk_index": i,
                "content_preview": chunk_code[:50].replace('\n', ' ') + "...",
                "embedding_id": embedding_id,
                "lines": f"{start_line}-{end_line}",
                "status": "processed"
            })
        else:
            processed_chunks_metadata.append({
                "original_file_path": file_path,
                "obfuscated_file_path": obf_path,
                "chunk_index": i,
                "content_preview": chunk_code[:50].replace('\n', ' ') + "...",
                "embedding_id": None,
                "lines": f"{start_line}-{end_line}",
                "status": "failed"
            })
        current_line_number = end_line + 1

    return processed_chunks_metadata


def main():
    logging.info("Iniciando processo de indexação de código...")

    actual_code_dir = BASE_CODE_DIR
    cloned_repo_path = None

    if GIT_REPO_URL:
        logging.info(f"Tentando clonar o repositório: {GIT_REPO_URL}")
        cloner = GitRepoCloner()
        if not cloner.is_git_available():
            logging.error("Git não está disponível. Não é possível clonar. Verifique a instalação do Git.")
            # Decide se quer continuar com o BASE_CODE_DIR padrão ou parar.
            # Por agora, vamos parar se a clonagem for solicitada mas o git não estiver disponível.
            return

        repo_name = get_repo_name_from_url(GIT_REPO_URL)
        # Cria o diretório base se não existir
        if not os.path.exists(BASE_CODE_DIR):
            os.makedirs(BASE_CODE_DIR)
            logging.info(f"Diretório base '{BASE_CODE_DIR}' criado.")

        cloned_repo_path = os.path.join(BASE_CODE_DIR, repo_name)

        # Se o diretório já existir, pode ser de uma clonagem anterior.
        # Poderia adicionar lógica para `git pull` ou remover e clonar novamente.
        # Por simplicidade, se existir, vamos tentar usá-lo, assumindo que está correto.
        # Para um comportamento mais robusto, seria melhor remover e clonar ou fazer pull.
        if os.path.exists(cloned_repo_path):
            logging.warning(f"Diretório de clone '{cloned_repo_path}' já existe. "
                            "Usando o conteúdo existente. Para garantir a versão mais recente, "
                            "remova o diretório ou implemente 'git pull'.")
            actual_code_dir = cloned_repo_path
        else:
            if cloner.clone_repository(GIT_REPO_URL, cloned_repo_path):
                logging.info(f"Repositório clonado com sucesso em '{cloned_repo_path}'.")
                actual_code_dir = cloned_repo_path
            else:
                logging.error(f"Falha ao clonar o repositório '{GIT_REPO_URL}'. "
                              f"Verifique a URL e a disponibilidade do Git. "
                              f"Tentando usar '{BASE_CODE_DIR}' como fallback se existir, ou parando.")
                # Se o clone falhar, decide se quer parar ou usar um diretório local padrão.
                # Se BASE_CODE_DIR não tiver conteúdo útil, o processamento será vazio.
                if not os.path.exists(BASE_CODE_DIR) or not os.listdir(BASE_CODE_DIR):
                    logging.error(f"Clonagem falhou e '{BASE_CODE_DIR}' está vazio ou não existe. Nada para indexar.")
                    return
                logging.warning(f"Usando '{BASE_CODE_DIR}' como fallback.")
                actual_code_dir = BASE_CODE_DIR # Fallback para o diretório base original
    else:
        logging.info("Nenhuma URL de repositório Git fornecida. Usando o diretório local padrão se existir.")
        # Cria o diretório base se não existir, caso o usuário queira colocar arquivos manualmente.
        if not os.path.exists(BASE_CODE_DIR):
            os.makedirs(BASE_CODE_DIR)
            logging.info(f"Diretório base '{BASE_CODE_DIR}' criado. Coloque os arquivos para indexar aqui se não estiver clonando.")
        actual_code_dir = BASE_CODE_DIR


    logging.info(f"Diretório de código para indexação: '{actual_code_dir}'")

    chunker = CodeChunker()
    client = IndexerClient(server_url=SERVER_URL)
    all_processed_metadata = []

    if not os.path.exists(actual_code_dir) or not os.path.isdir(actual_code_dir):
        logging.error(f"Diretório de código '{actual_code_dir}' não encontrado ou não é um diretório.")
        # Limpeza se um clone foi tentado e falhou de forma estranha
        if GIT_REPO_URL and cloned_repo_path and CLEANUP_CLONED_REPO_AFTER_RUN:
            logging.info(f"Realizando limpeza do diretório de clone (se existir): {cloned_repo_path}")
            shutil.rmtree(cloned_repo_path, ignore_errors=True)
        return

    # Percorrer recursivamente o diretório de código
    for root, _, files in os.walk(actual_code_dir):
        # Ignorar diretórios .git
        if '.git' in root.split(os.sep):
            logging.info(f"Ignorando diretório .git: {root}")
            continue

        for file_name in files:
            if file_name.endswith(".py"): # Processar apenas arquivos Python
                file_path = os.path.join(root, file_name)
                file_metadata = process_file(file_path, chunker, client)
                all_processed_metadata.extend(file_metadata)
            else:
                logging.debug(f"Ignorando arquivo não-python: {file_name} em {root}")

    logging.info("\n--- Resumo do Processamento ---")
    if all_processed_metadata:
        for meta in all_processed_metadata:
            logging.info(
                f"File: {meta['original_file_path']}, "
                f"Chunk: {meta['chunk_index']}, "
                f"ObfPath: {meta['obfuscated_file_path'][:20]}..., "
                f"EmbID: {meta['embedding_id']}, "
                f"Status: {meta['status']}"
            )
    else:
        logging.info("Nenhum chunk foi processado.")

    # Limpeza opcional do repositório clonado
    if GIT_REPO_URL and cloned_repo_path and CLEANUP_CLONED_REPO_AFTER_RUN and os.path.exists(cloned_repo_path):
        logging.info(f"Realizando limpeza do diretório de clone: {cloned_repo_path}")
        try:
            shutil.rmtree(cloned_repo_path)
            logging.info(f"Diretório '{cloned_repo_path}' removido com sucesso.")
        except Exception as e:
            logging.error(f"Erro ao remover o diretório '{cloned_repo_path}': {e}")

    logging.info("Processo de indexação de código concluído.")

if __name__ == "__main__":
    # Para testar a clonagem, certifique-se que GIT_REPO_URL está definido.
    # Para testar sem clonagem, defina GIT_REPO_URL = None
    # e coloque arquivos em "indexed_code_source/" manualmente.

    # Exemplo: GIT_REPO_URL = "https://github.com/pallets/click.git"
    # Exemplo: GIT_REPO_URL = None
    #          (e crie indexed_code_source/meu_modulo.py com algum código)

    # Limpar o diretório 'sample_code' que não é mais usado diretamente pelo main.py
    # se GIT_REPO_URL estiver ativo.
    if os.path.exists("sample_code") and GIT_REPO_URL:
        logging.info("Limpando o diretório 'sample_code' antigo...")
        shutil.rmtree("sample_code", ignore_errors=True)

    main()
