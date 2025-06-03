# tests/test_client.py
import unittest
from unittest.mock import patch, MagicMock
import os
import hashlib
import base64

from code_indexer.client import IndexerClient, obfuscate_file_path, OBFUSCATION_KEY

class TestPathObfuscation(unittest.TestCase):

    def test_obfuscate_empty_path(self):
        self.assertEqual(obfuscate_file_path("", OBFUSCATION_KEY), "")

    def test_obfuscate_simple_path(self):
        path = "src/file.py"
        obfuscated = obfuscate_file_path(path, OBFUSCATION_KEY)
        self.assertIsNotNone(obfuscated)
        self.assertNotEqual(obfuscated, path)

        # Check if segments are present (though transformed)
        self.assertEqual(len(obfuscated.split(os.sep)), len(path.split(os.sep)))

    def test_obfuscation_consistency(self):
        path = "a/very/long/path/to/a/file/for/testing.py"
        key = "test_key"
        obfuscated1 = obfuscate_file_path(path, key)
        obfuscated2 = obfuscate_file_path(path, key)
        self.assertEqual(obfuscated1, obfuscated2)

    def test_obfuscation_with_different_key(self):
        path = "src/another.txt"
        obfuscated1 = obfuscate_file_path(path, "key1")
        obfuscated2 = obfuscate_file_path(path, "key2")
        self.assertNotEqual(obfuscated1, obfuscated2)

    def test_internal_xor_and_base64_logic_basic(self):
        """ Test a single segment to understand the transformation parts. """
        segment = "my_segment"
        key_hash = hashlib.sha256(OBFUSCATION_KEY.encode()).digest()

        segment_bytes = segment.encode('utf-8')
        obfuscated_segment_bytes = bytearray()
        for i in range(len(segment_bytes)):
            obfuscated_segment_bytes.append(segment_bytes[i] ^ key_hash[i % len(key_hash)])

        expected_b64 = base64.urlsafe_b64encode(obfuscated_segment_bytes).decode('utf-8')

        # Test with a path that has only one segment
        obfuscated_path = obfuscate_file_path(segment, OBFUSCATION_KEY)
        self.assertEqual(obfuscated_path, expected_b64)


class TestIndexerClient(unittest.TestCase):

    def setUp(self):
        self.server_url = "http://fake-server.com/api"
        self.client = IndexerClient(server_url=self.server_url, api_key="test_api_key")

    @patch('code_indexer.client.logging') # Mock logging para evitar output durante os testes
    def test_sync_merkle_tree_needs_resync(self, mock_logging):
        """Testa sync_merkle_tree quando uma resincronização é necessária."""
        root_hash = "UNKNOWN_HASH_123"
        self.assertTrue(self.client.sync_merkle_tree(root_hash))
        mock_logging.info.assert_any_call(f"Sincronizando Merkle Tree com raiz: {root_hash}...")
        mock_logging.info.assert_any_call("Servidor respondeu: Merkle Tree não sincronizada ou desconhecida. Resincronização necessária.")

    @patch('code_indexer.client.logging')
    def test_sync_merkle_tree_no_resync(self, mock_logging):
        """Testa sync_merkle_tree quando o hash é conhecido e não precisa de resync."""
        root_hash = "SIMULATED_KNOWN_HASH" # Definido no client.py para não precisar de resync
        self.assertFalse(self.client.sync_merkle_tree(root_hash))
        mock_logging.info.assert_any_call("Servidor respondeu: Merkle Tree está sincronizada (hash conhecido).")

    @patch('code_indexer.client.obfuscate_file_path')
    @patch('code_indexer.client.logging')
    def test_send_chunk_for_embedding_success(self, mock_logging, mock_obfuscate):
        """Testa send_chunk_for_embedding com sucesso."""
        original_path = "project/file.py"
        obfuscated_path_mock = "OBFUSCATED_PATH"
        mock_obfuscate.return_value = obfuscated_path_mock

        chunk_content = "def my_func():\n    pass"
        start_line, end_line = 1, 2

        expected_payload = chunk_content + obfuscated_path_mock + str(start_line) + str(end_line)
        expected_embedding_id = hashlib.sha256(expected_payload.encode('utf-8')).hexdigest()[:16]

        embedding_id = self.client.send_chunk_for_embedding(chunk_content, original_path, start_line, end_line)

        self.assertEqual(embedding_id, expected_embedding_id)
        mock_obfuscate.assert_called_once_with(original_path, OBFUSCATION_KEY)
        mock_logging.info.assert_any_call(f"Servidor simulado: Chunk processado. ID do Embedding: {expected_embedding_id}")

    @patch('code_indexer.client.obfuscate_file_path')
    @patch('code_indexer.client.logging')
    def test_send_chunk_for_embedding_failure(self, mock_logging, mock_obfuscate):
        """Testa send_chunk_for_embedding quando o servidor simulado falha."""
        original_path = "project/file_with_error.py"
        obfuscated_path_mock = "OBFUSCATED_ERROR_PATH"
        mock_obfuscate.return_value = obfuscated_path_mock

        chunk_content_with_error = "erro simulado no chunk" # Contém "erro"
        start_line, end_line = 5, 5

        embedding_id = self.client.send_chunk_for_embedding(chunk_content_with_error, original_path, start_line, end_line)

        self.assertIsNone(embedding_id)
        mock_obfuscate.assert_called_once_with(original_path, OBFUSCATION_KEY)
        mock_logging.error.assert_any_call("Servidor simulado: Falha ao processar chunk para embedding.")

if __name__ == '__main__':
    unittest.main()
