# tests/test_merkle.py
import unittest
import hashlib
from code_indexer.merkle_tree.merkle import MerkleTree, MerkleNode

class TestMerkleTree(unittest.TestCase):

    def _hash(self, data: str) -> str:
        return hashlib.sha256(data.encode('utf-8')).hexdigest()

    def test_empty_tree(self):
        """Testa a criação de uma Merkle Tree com lista de dados vazia."""
        mt = MerkleTree([])
        self.assertIsNone(mt.root_node)
        self.assertEqual(mt.get_root_hash(), None)
        self.assertEqual(mt.leaves, [])

    def test_single_data_block(self):
        """Testa a árvore com um único bloco de dados."""
        data = ["block1"]
        hashed_block1 = self._hash("block1")

        mt = MerkleTree(data)
        self.assertIsNotNone(mt.root_node)
        self.assertEqual(mt.get_root_hash(), hashed_block1)
        self.assertEqual(len(mt.leaves), 1)
        self.assertEqual(mt.leaves[0].hash_value, hashed_block1)
        self.assertIsNone(mt.root_node.left) # Nó raiz é a própria folha
        self.assertIsNone(mt.root_node.right)

    def test_two_data_blocks(self):
        """Testa a árvore com dois blocos de dados (um nível de nós internos)."""
        data = ["blockA", "blockB"]
        hash_a = self._hash("blockA")
        hash_b = self._hash("blockB")

        combined_hash = self._hash(hash_a + hash_b)

        mt = MerkleTree(data)
        self.assertIsNotNone(mt.root_node)
        self.assertEqual(mt.get_root_hash(), combined_hash)
        self.assertEqual(len(mt.leaves), 2)
        self.assertEqual(mt.leaves[0].hash_value, hash_a)
        self.assertEqual(mt.leaves[1].hash_value, hash_b)

        self.assertIsNotNone(mt.root_node.left)
        self.assertEqual(mt.root_node.left.hash_value, hash_a)
        self.assertIsNotNone(mt.root_node.right)
        self.assertEqual(mt.root_node.right.hash_value, hash_b)

    def test_three_data_blocks(self):
        """Testa a árvore com três blocos de dados (duplicação do último)."""
        data = ["d1", "d2", "d3"]
        h1 = self._hash("d1")
        h2 = self._hash("d2")
        h3 = self._hash("d3")

        # Nível 1 de hashes (folhas)
        # h1, h2, h3

        # Nível 2 de combinações
        # Combina h1 e h2 -> h12
        # Combina h3 e h3 (duplicado) -> h33
        h12 = self._hash(h1 + h2)
        h33 = self._hash(h3 + h3) # h3 é duplicado

        # Nível 3 de combinações (raiz)
        # Combina h12 e h33 -> root_hash
        root_hash_val = self._hash(h12 + h33)

        mt = MerkleTree(data)
        self.assertEqual(mt.get_root_hash(), root_hash_val)
        self.assertEqual(len(mt.leaves), 3)
        self.assertEqual(mt.leaves[0].hash_value, h1)
        self.assertEqual(mt.leaves[1].hash_value, h2)
        self.assertEqual(mt.leaves[2].hash_value, h3)

        # Verificando a estrutura
        # Raiz
        self.assertIsNotNone(mt.root_node)
        # Filhos da raiz
        node_h12 = mt.root_node.left
        node_h33 = mt.root_node.right
        self.assertIsNotNone(node_h12)
        self.assertEqual(node_h12.hash_value, h12)
        self.assertIsNotNone(node_h33)
        self.assertEqual(node_h33.hash_value, h33)

        # Filhos de node_h12
        self.assertIsNotNone(node_h12.left)
        self.assertEqual(node_h12.left.hash_value, h1) # Folha h1
        self.assertIsNotNone(node_h12.right)
        self.assertEqual(node_h12.right.hash_value, h2) # Folha h2

        # Filhos de node_h33
        self.assertIsNotNone(node_h33.left)
        self.assertEqual(node_h33.left.hash_value, h3) # Folha h3
        self.assertIsNotNone(node_h33.right)
        self.assertEqual(node_h33.right.hash_value, h3) # Folha h3 (duplicada)


    def test_four_data_blocks(self):
        """Testa a árvore com quatro blocos de dados (árvore balanceada)."""
        data = ["data1", "data2", "data3", "data4"]
        h1 = self._hash("data1")
        h2 = self._hash("data2")
        h3 = self._hash("data3")
        h4 = self._hash("data4")

        h12 = self._hash(h1 + h2)
        h34 = self._hash(h3 + h4)

        root_val = self._hash(h12 + h34)

        mt = MerkleTree(data)
        self.assertEqual(mt.get_root_hash(), root_val)

        # Verificações de estrutura (opcional, mas bom para garantir)
        self.assertEqual(mt.root_node.left.hash_value, h12)
        self.assertEqual(mt.root_node.right.hash_value, h34)
        self.assertEqual(mt.root_node.left.left.hash_value, h1)
        self.assertEqual(mt.root_node.left.right.hash_value, h2)
        self.assertEqual(mt.root_node.right.left.hash_value, h3)
        self.assertEqual(mt.root_node.right.right.hash_value, h4)

    def test_merkle_node_representation(self):
        """Testa a representação em string do MerkleNode."""
        node = MerkleNode("a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0")
        self.assertEqual(repr(node), "MerkleNode(hash='a1b2c3d4...')")
        short_hash_node = MerkleNode("short")
        self.assertEqual(repr(short_hash_node), "MerkleNode(hash='short')")


if __name__ == '__main__':
    unittest.main()
