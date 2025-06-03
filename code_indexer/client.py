# code_indexer/client.py
# Este módulo define o cliente para interagir com um servidor de indexação hipotético.

import hashlib
import logging
import os
import base64

# Configuração básica do logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Chave secreta simulada para ofuscação. Em um cenário real, isso seria gerenciado de forma mais segura.
# Poderia ser derivado de informações do projeto ou do usuário.
OBFUSCATION_KEY = "my_super_secret_key_for_paths"

def obfuscate_file_path(file_path: str, key: str) -> str:
    """
    Ofusca o caminho do arquivo dividindo-o em segmentos e aplicando uma transformação.
    Esta é uma ofuscação simples para demonstração.
    Em um sistema real, usaria criptografia mais robusta (ex: AES GCM para cada segmento).
    A ideia é que o servidor não veja os caminhos reais, mas o cliente possa revertê-los se necessário
    (embora a reversão não seja implementada aqui).
    """
    if not file_path:
        return ""

    # Usar o hash da chave para garantir um comprimento fixo para XOR, por exemplo
    key_hash = hashlib.sha256(key.encode()).digest()

    segments = file_path.split(os.sep)
    obfuscated_segments = []

    for segment in segments:
        segment_bytes = segment.encode('utf-8')
        obfuscated_segment_bytes = bytearray()
        for i in range(len(segment_bytes)):
            obfuscated_segment_bytes.append(segment_bytes[i] ^ key_hash[i % len(key_hash)])
        # Usar base64 para garantir que os bytes resultantes sejam strings válidas para caminhos/JSON
        obfuscated_segments.append(base64.urlsafe_b64encode(obfuscated_segment_bytes).decode('utf-8'))

    return os.sep.join(obfuscated_segments)

class IndexerClient:
    """
    Cliente para interagir com um servidor de indexação e embedding (hipotético).
    """
    def __init__(self, server_url: str, api_key: str | None = None):
        """
        Inicializa o cliente.

        Args:
            server_url: A URL base do servidor de indexação.
            api_key: Uma chave de API opcional para autenticação.
        """
        self.server_url = server_url
        self.api_key = api_key
        logging.info(f"IndexerClient inicializado para o servidor: {self.server_url}")

    def sync_merkle_tree(self, root_hash: str) -> bool:
        """
        Simula o envio do hash raiz da Merkle Tree local para o servidor.
        O servidor responderia se uma resincronização completa dos chunks é necessária.

        Args:
            root_hash: O hash raiz da Merkle Tree local.

        Returns:
            True se a resincronização for necessária (o servidor não tem o hash ou tem uma versão diferente),
            False caso contrário (o servidor tem o mesmo hash raiz, chunks estão sincronizados).
        """
        logging.info(f"Sincronizando Merkle Tree com raiz: {root_hash}...")
        # Simulação: Em um cenário real, faria uma requisição HTTP (ex: POST)
        # para um endpoint como {self.server_url}/sync_tree
        # com o root_hash no corpo da requisição.

        # Para este exemplo, vamos assumir que quase sempre precisa de resync,
        # a menos que o hash seja um valor específico "conhecido" pelo servidor simulado.
        if root_hash == "SIMULATED_KNOWN_HASH":
            logging.info("Servidor respondeu: Merkle Tree está sincronizada (hash conhecido).")
            return False

        logging.info("Servidor respondeu: Merkle Tree não sincronizada ou desconhecida. Resincronização necessária.")
        return True # Indica que a resincronização é necessária

    def send_chunk_for_embedding(self,
                                 chunk_content: str,
                                 original_file_path: str,
                                 start_line: int,
                                 end_line: int) -> str | None:
        """
        Simula o envio de um chunk de código para o servidor para geração de embedding.
        O caminho do arquivo original é ofuscado antes do envio.

        Args:
            chunk_content: O conteúdo do chunk de código.
            original_file_path: O caminho original do arquivo de onde o chunk foi extraído.
            start_line: A linha inicial do chunk no arquivo original.
            end_line: A linha final do chunk no arquivo original.

        Returns:
            Um ID de embedding simulado (string) se o processamento for bem-sucedido,
            None em caso de falha.
        """
        obfuscated_path = obfuscate_file_path(original_file_path, OBFUSCATION_KEY)

        logging.info(f"Enviando chunk para embedding:")
        logging.info(f"  Caminho Original: {original_file_path}")
        logging.info(f"  Caminho Ofuscado: {obfuscated_path}")
        logging.info(f"  Linhas: {start_line}-{end_line}")
        logging.info(f"  Conteúdo do Chunk (primeiros 50 chars): '{chunk_content[:50].replace('\n', ' ')}...'")

        # Simulação: Em um cenário real, faria uma requisição HTTP (ex: POST)
        # para um endpoint como {self.server_url}/embed_chunk
        # com chunk_content, obfuscated_path, start_line, end_line no corpo.
        # O servidor geraria o embedding, armazenaria e retornaria um ID.

        # Simular sucesso e falha
        if "erro" in chunk_content.lower(): # Simular falha se o chunk contiver "erro"
            logging.error("Servidor simulado: Falha ao processar chunk para embedding.")
            return None

        # Gerar um ID de embedding simulado (hash do conteúdo + caminho ofuscado)
        embedding_id_payload = chunk_content + obfuscated_path + str(start_line) + str(end_line)
        simulated_embedding_id = hashlib.sha256(embedding_id_payload.encode('utf-8')).hexdigest()[:16]

        logging.info(f"Servidor simulado: Chunk processado. ID do Embedding: {simulated_embedding_id}")
        return simulated_embedding_id

if __name__ == '__main__':
    # Exemplo de uso
    client = IndexerClient(server_url="http://localhost:8080/api", api_key="dummy_key")

    # Teste de ofuscação
    test_path = "src/app/components/my_component.py"
    obfuscated = obfuscate_file_path(test_path, OBFUSCATION_KEY)
    print(f"Caminho original: {test_path}")
    print(f"Caminho ofuscado: {obfuscated}")
    # Para testar a "reversão" (não faz parte do client, mas para entender a ofuscação)
    # deobfuscated = obfuscate_file_path(obfuscated, OBFUSCATION_KEY) # XORing de novo com a mesma chave reverte
    # print(f"Caminho 'de-ofuscado': {deobfuscated}") # Não será igual ao original devido ao base64 e split

    print("\n--- Testando sync_merkle_tree ---")
    client.sync_merkle_tree("SOME_NEW_ROOT_HASH_12345")
    client.sync_merkle_tree("SIMULATED_KNOWN_HASH") # Deve indicar que não precisa de resync

    print("\n--- Testando send_chunk_for_embedding ---")
    sample_chunk_1 = "class MyClass:\n    def __init__(self):\n        pass"
    client.send_chunk_for_embedding(sample_chunk_1, "project/module/file1.py", 1, 3)

    sample_chunk_2_with_error = "def problematic_function():\n    return erro / 0"
    client.send_chunk_for_embedding(sample_chunk_2_with_error, "project/module/file2.py", 5, 6)
