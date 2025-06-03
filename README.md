# Code Indexer Engine

## Descrição

O Code Indexer Engine é um protótipo de sistema projetado para indexar codebases de forma eficiente, permitindo uma compreensão semântica profunda e recuperação de contexto relevante. Este projeto é inspirado nos princípios de indexação rápida de codebases, utilizando Merkle Trees para identificação eficiente de alterações e um fluxo de trabalho que prioriza a privacidade do código do usuário.

Atualmente, o sistema implementa as seguintes funcionalidades principais:
-   **Chunking Semântico**: Divide arquivos de código Python em pedaços menores (chunks) com base em estruturas semânticas como classes e funções.
-   **Merkle Trees**: Gera uma Merkle Tree para os chunks de cada arquivo, permitindo uma "impressão digital" do conteúdo que pode ser usada para detectar alterações rapidamente.
-   **Cliente de Embedding Simulado**: Inclui um cliente que simula a interação com um servidor de embedding remoto. Este cliente envia chunks de código (com caminhos ofuscados para privacidade) e "sincroniza" o estado do codebase usando o hash raiz da Merkle Tree.
-   **Clonagem de Repositórios Git**: Pode clonar um repositório Git de uma URL fornecida para indexar seu conteúdo.

## Funcionalidades

-   **Chunking de Código Python**:
    -   Divide o código em `code_indexer.chunker.CodeChunker` usando expressões regulares para identificar classes e funções.
    -   Planejado: Melhorar com análise baseada em AST (Abstract Syntax Tree) para maior precisão.
-   **Geração de Merkle Tree**:
    -   `code_indexer.merkle_tree.MerkleTree` constrói uma árvore de hashes para os chunks de um arquivo.
    -   Usa SHA256 para os hashes.
    -   Permite a obtenção de um hash raiz único para o conteúdo do arquivo processado.
-   **Cliente Simulado para Servidor de Embedding**:
    -   `code_indexer.client.IndexerClient` simula a comunicação com um servidor externo.
    -   `sync_merkle_tree(root_hash)`: Verifica (simuladamente) se o servidor precisa de uma resincronização dos chunks.
    -   `send_chunk_for_embedding(...)`: Envia (simuladamente) chunks para o servidor, que retornaria um ID de embedding.
    -   `obfuscate_file_path(...)`: Ofusca os caminhos dos arquivos antes do envio para proteger a privacidade.
-   **Clonagem de Repositórios Git**:
    -   `code_indexer.git_operations.GitRepoCloner` permite clonar repositórios Git públicos.
    -   Requer que o comando `git` esteja instalado no sistema.

## Como Funciona (Arquitetura Simplificada)

1.  **Configuração**: O script `main.py` é configurado com um diretório base e, opcionalmente, uma URL de um repositório Git.
2.  **Clonagem (Opcional)**: Se uma `GIT_REPO_URL` for fornecida, o sistema clona o repositório para um subdiretório local.
3.  **Leitura de Arquivos**: O sistema percorre o diretório de código especificado, procurando por arquivos Python (`.py`).
4.  **Processamento por Arquivo**:
    a.  **Chunking**: O conteúdo do arquivo é dividido em chunks semânticos.
    b.  **Merkle Tree**: Uma Merkle Tree é construída a partir dos chunks do arquivo, e um hash raiz é gerado.
    c.  **Sincronização (Simulada)**: O `IndexerClient` envia o hash raiz para um servidor simulado.
    d.  **Envio para Embedding (Simulado)**: Se o servidor indicar que uma resincronização é necessária, cada chunk é enviado (com caminho ofuscado e informações de linha) para o servidor simulado para "geração de embedding". Um ID de embedding é retornado.
5.  **Coleta de Metadados**: Informações sobre os chunks processados (caminho do arquivo, ID do embedding, status) são coletadas e logadas.

## Requisitos

-   **Python 3.7+** (pode funcionar em versões anteriores, mas testado com 3.7+).
-   **Git**: Necessário se você pretende usar a funcionalidade de clonagem de repositórios (`GIT_REPO_URL` em `main.py`). Deve estar instalado e acessível no PATH do sistema.
-   Bibliotecas Python:
    -   Nenhuma biblioteca externa é necessária além da biblioteca padrão do Python.

## Como Usar

1.  **Configuração Inicial**:
    -   Certifique-se de ter Python 3.7 ou superior instalado.
    -   Se você planeja clonar repositórios Git, instale o Git e certifique-se de que ele está no PATH do seu sistema.
    -   Clone este repositório (se você o estiver lendo em outro lugar) ou baixe os arquivos.

2.  **Executando o `main.py`**:
    -   Abra um terminal na raiz do projeto.
    -   Execute o script com: `python main.py`

3.  **Configuração no `main.py`**:
    O comportamento do `main.py` pode ser ajustado pelas seguintes constantes no topo do arquivo:
    -   `BASE_CODE_DIR = "indexed_code_source"`: Diretório base onde o código a ser indexado está localizado ou onde os repositórios serão clonados.
    -   `GIT_REPO_URL = "https://github.com/pallets/click.git"`: URL do repositório Git a ser clonado. Defina como `None` ou uma string vazia para pular a clonagem e usar o conteúdo local em `BASE_CODE_DIR`.
    -   `SERVER_URL = "http://localhost:8080/api"`: URL do servidor de indexação/embedding simulado. (Atualmente não faz chamadas de rede reais).
    -   `CLEANUP_CLONED_REPO_AFTER_RUN = True`: Se `True` e um repositório foi clonado, ele será removido do `BASE_CODE_DIR` após a execução do script. Defina como `False` para manter o repositório clonado.

    **Exemplo de Cenários:**
    -   **Para clonar e indexar o repositório 'click'**: Mantenha `GIT_REPO_URL = "https://github.com/pallets/click.git"`.
    -   **Para indexar código local**:
        1.  Defina `GIT_REPO_URL = None`.
        2.  Crie o diretório `indexed_code_source` (ou o que estiver em `BASE_CODE_DIR`).
        3.  Coloque seus arquivos Python dentro de `indexed_code_source/`.
        4.  Execute `python main.py`.

## Estrutura do Projeto

```
.
├── code_indexer/         # Módulo principal da lógica de indexação
│   ├── __init__.py
│   ├── chunker/          # Lógica de chunking de código
│   │   ├── __init__.py
│   │   └── code_chunker.py
│   ├── merkle_tree/      # Implementação da Merkle Tree
│   │   ├── __init__.py
│   │   └── merkle.py
│   ├── client.py         # Cliente simulado para servidor de embedding
│   └── git_operations.py # Funcionalidades para clonagem Git
├── tests/                # Testes unitários
│   ├── __init__.py
│   ├── test_code_chunker.py
│   ├── test_merkle.py
│   ├── test_client.py
│   └── test_git_operations.py
├── main.py               # Ponto de entrada principal para executar a indexação
└── README.md             # Este arquivo
```

## Próximos Passos / TODO

Esta é uma lista de possíveis melhorias e funcionalidades futuras, baseadas nos prompts originais de design:

-   **Implementação Real do Servidor**: Desenvolver o servidor de embedding que armazena embeddings em um banco de dados vetorial (ex: Turbopuffer) e lida com as requisições do cliente.
-   **Análise AST para Chunking**: Substituir o chunking baseado em regex por uma abordagem mais robusta usando Abstract Syntax Trees (AST) com ferramentas como `tree-sitter` para suportar mais linguagens e garantir chunks semanticamente mais coesos.
-   **Suporte a Mais Linguagens**: Expandir o chunker e o processamento para outras linguagens além de Python.
-   **Geração Real de Embeddings**: Integrar modelos de embedding reais (ex: `unixcoder-base`, `voyage-code-2`, ou modelos da OpenAI) no servidor.
-   **Cache de Embeddings**: Implementar o cache de embeddings indexado pelo hash do chunk no lado do servidor.
-   **Indexação do Histórico Git**: Expandir `git_operations` para indexar o histórico Git (SHAs de commit, parentesco, etc.).
-   **Interface de Consulta**: Desenvolver uma interface para que os usuários possam fazer perguntas sobre o codebase ou solicitar conclusões de código, utilizando os embeddings armazenados.
-   **Empacotamento e Distribuição**: Tornar o projeto instalável e mais fácil de usar como uma ferramenta de linha de comando ou biblioteca.
-   **Segurança dos Embeddings**: Pesquisar e implementar medidas para mitigar riscos de segurança relacionados aos embeddings armazenados.
