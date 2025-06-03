# code_indexer/merkle_tree/merkle.py
# Este módulo implementará a Merkle Tree para indexação eficiente do codebase.

import hashlib

class MerkleNode:
    """
    Representa um nó na Merkle Tree.
    Pode ser um nó folha (contendo o hash de um bloco de dados)
    ou um nó interno (contendo o hash de seus nós filhos).
    """
    def __init__(self, hash_value: str, left=None, right=None):
        self.hash_value = hash_value
        self.left: 'MerkleNode' | None = left
        self.right: 'MerkleNode' | None = right

    def __repr__(self):
        return f"MerkleNode(hash='{self.hash_value[:8]}...')"

class MerkleTree:
    """
    Implementa uma Merkle Tree para verificar a integridade dos dados
    e identificar rapidamente alterações.
    """
    def __init__(self, data_blocks: list[str]):
        """
        Constrói a Merkle Tree a partir de uma lista de blocos de dados.

        Args:
            data_blocks: Uma lista de strings, onde cada string é um bloco de dados
                         (por exemplo, um chunk de código ou o conteúdo de um arquivo).
                         Se a lista estiver vazia, a raiz será None.
        """
        if not data_blocks:
            self.root_node: MerkleNode | None = None
            self.leaves: list[MerkleNode] = []
            return

        self.leaves = [MerkleNode(self._hash_data_block(block)) for block in data_blocks]
        self.root_node = self._build_tree(self.leaves)

    @staticmethod
    def _hash_data_block(data_block: str) -> str:
        """
        Calcula o hash SHA256 de um bloco de dados.
        """
        return hashlib.sha256(data_block.encode('utf-8')).hexdigest()

    def _build_tree(self, nodes: list[MerkleNode]) -> MerkleNode | None:
        """
        Constrói recursivamente a árvore a partir de uma lista de nós.
        """
        if not nodes:
            return None
        if len(nodes) == 1:
            return nodes[0]

        new_level_nodes = []
        for i in range(0, len(nodes), 2):
            left_child = nodes[i]
            # Se houver um número ímpar de nós, o último nó é duplicado para formar um par
            right_child = nodes[i+1] if (i+1) < len(nodes) else left_child

            combined_hash_input = left_child.hash_value + right_child.hash_value
            parent_hash = hashlib.sha256(combined_hash_input.encode('utf-8')).hexdigest()
            parent_node = MerkleNode(parent_hash, left_child, right_child)
            new_level_nodes.append(parent_node)

        return self._build_tree(new_level_nodes)

    def get_root_hash(self) -> str | None:
        """
        Retorna o hash da raiz da Merkle Tree.
        Retorna None se a árvore estiver vazia.
        """
        return self.root_node.hash_value if self.root_node else None

if __name__ == '__main__':
    # Exemplo de uso (para teste rápido)

    # Caso 1: Lista de blocos de dados
    data = ["bloco1_conteudo_do_arquivo_A",
            "bloco2_conteudo_do_arquivo_B",
            "bloco3_conteudo_do_arquivo_C",
            "bloco4_conteudo_do_arquivo_D"]

    print(f"Construindo Merkle Tree para: {data}")
    merkle_tree = MerkleTree(data)
    root_hash = merkle_tree.get_root_hash()
    print(f"Hash da Raiz: {root_hash}")
    if merkle_tree.root_node and merkle_tree.root_node.left:
        print(f"Hash do filho esquerdo da raiz: {merkle_tree.root_node.left.hash_value[:16]}...")
    if merkle_tree.root_node and merkle_tree.root_node.right:
        print(f"Hash do filho direito da raiz: {merkle_tree.root_node.right.hash_value[:16]}...")

    print("\n" + "="*50 + "\n")

    # Caso 2: Número ímpar de blocos
    data_odd = ["bloco_X", "bloco_Y", "bloco_Z"]
    print(f"Construindo Merkle Tree para: {data_odd}")
    merkle_tree_odd = MerkleTree(data_odd)
    root_hash_odd = merkle_tree_odd.get_root_hash()
    print(f"Hash da Raiz (ímpar): {root_hash_odd}")
    # Imprimir folhas para verificar a duplicação do último nó no primeiro nível de combinação
    if merkle_tree_odd.root_node and merkle_tree_odd.root_node.left and merkle_tree_odd.root_node.left.left:
        print(f"Folha 1: {merkle_tree_odd.root_node.left.left.hash_value[:8]}")
    if merkle_tree_odd.root_node and merkle_tree_odd.root_node.left and merkle_tree_odd.root_node.left.right:
         print(f"Folha 2: {merkle_tree_odd.root_node.left.right.hash_value[:8]}")
    if merkle_tree_odd.root_node and merkle_tree_odd.root_node.right and merkle_tree_odd.root_node.right.left: # Este seria o Z
         print(f"Folha 3: {merkle_tree_odd.root_node.right.left.hash_value[:8]}")
    if merkle_tree_odd.root_node and merkle_tree_odd.root_node.right and merkle_tree_odd.root_node.right.right: # Este seria o Z duplicado
         print(f"Folha 4 (duplicada de 3): {merkle_tree_odd.root_node.right.right.hash_value[:8]}")


    print("\n" + "="*50 + "\n")

    # Caso 3: Um único bloco de dados
    data_single = ["apenas_um_bloco"]
    print(f"Construindo Merkle Tree para: {data_single}")
    merkle_tree_single = MerkleTree(data_single)
    root_hash_single = merkle_tree_single.get_root_hash()
    print(f"Hash da Raiz (único): {root_hash_single}")
    # O hash da raiz deve ser o hash do único bloco
    print(f"Hash do bloco: {MerkleTree._hash_data_block(data_single[0])}")
    assert root_hash_single == MerkleTree._hash_data_block(data_single[0])

    print("\n" + "="*50 + "\n")

    # Caso 4: Lista vazia
    data_empty = []
    print(f"Construindo Merkle Tree para: {data_empty}")
    merkle_tree_empty = MerkleTree(data_empty)
    root_hash_empty = merkle_tree_empty.get_root_hash()
    print(f"Hash da Raiz (vazio): {root_hash_empty}")
    assert root_hash_empty is None
