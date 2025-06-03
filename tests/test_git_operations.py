# tests/test_git_operations.py
import unittest
from unittest.mock import patch, MagicMock, PropertyMock
import subprocess
import os

# Adicionar o diretório pai ao sys.path para encontrar code_indexer
# import sys
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from code_indexer.git_operations import GitRepoCloner

class TestGitRepoCloner(unittest.TestCase):

    @patch('code_indexer.git_operations.shutil.which')
    def test_init_git_found(self, mock_shutil_which):
        """Testa a inicialização quando 'git' é encontrado."""
        mock_shutil_which.return_value = "/usr/bin/git"
        with patch('code_indexer.git_operations.logging') as mock_logging:
            cloner = GitRepoCloner()
            self.assertTrue(cloner.is_git_available())
            self.assertEqual(cloner.git_executable, "/usr/bin/git")
            mock_logging.info.assert_called_with("Executável Git encontrado em: /usr/bin/git")

    @patch('code_indexer.git_operations.shutil.which')
    def test_init_git_not_found(self, mock_shutil_which):
        """Testa a inicialização quando 'git' NÃO é encontrado."""
        mock_shutil_which.return_value = None
        with patch('code_indexer.git_operations.logging') as mock_logging:
            cloner = GitRepoCloner()
            self.assertFalse(cloner.is_git_available())
            self.assertIsNone(cloner.git_executable)
            mock_logging.warning.assert_called_with("Comando 'git' não encontrado no PATH do sistema. A clonagem de repositórios não funcionará.")

    @patch('code_indexer.git_operations.subprocess.run')
    @patch('code_indexer.git_operations.shutil.which')
    def test_clone_repository_success(self, mock_shutil_which, mock_subprocess_run):
        """Testa a clonagem bem-sucedida de um repositório."""
        mock_shutil_which.return_value = "/usr/bin/git" # Git está disponível

        # Configurar o mock para subprocess.run
        mock_process_result = MagicMock()
        mock_process_result.returncode = 0
        mock_process_result.stdout = "Cloning into 'test_repo'..."
        mock_process_result.stderr = ""
        mock_subprocess_run.return_value = mock_process_result

        cloner = GitRepoCloner()
        with patch('code_indexer.git_operations.logging') as mock_logging:
            success = cloner.clone_repository("https://fake.repo/test.git", "local/test_repo")

            self.assertTrue(success)
            mock_subprocess_run.assert_called_once_with(
                ["/usr/bin/git", "clone", "https://fake.repo/test.git", "local/test_repo"],
                capture_output=True, text=True, check=False
            )
            mock_logging.info.assert_any_call("Repositório 'https://fake.repo/test.git' clonado com sucesso para 'local/test_repo'.")
            mock_logging.debug.assert_any_call("Git clone stdout:
Cloning into 'test_repo'...")


    @patch('code_indexer.git_operations.subprocess.run')
    @patch('code_indexer.git_operations.shutil.which')
    def test_clone_repository_failure_return_code(self, mock_shutil_which, mock_subprocess_run):
        """Testa a falha na clonagem devido a um código de retorno não-zero."""
        mock_shutil_which.return_value = "/usr/bin/git"

        mock_process_result = MagicMock()
        mock_process_result.returncode = 128 # Código de erro comum do git (ex: repo não encontrado)
        mock_process_result.stdout = ""
        mock_process_result.stderr = "fatal: repository 'https://fake.repo/nonexistent.git' not found"
        mock_subprocess_run.return_value = mock_process_result

        cloner = GitRepoCloner()
        with patch('code_indexer.git_operations.logging') as mock_logging:
            success = cloner.clone_repository("https://fake.repo/nonexistent.git", "local/fail_repo")

            self.assertFalse(success)
            mock_subprocess_run.assert_called_once()
            mock_logging.error.assert_any_call("Falha ao clonar o repositório 'https://fake.repo/nonexistent.git'. Código de retorno: 128")
            mock_logging.error.assert_any_call("Git clone stderr:
fatal: repository 'https://fake.repo/nonexistent.git' not found")

    @patch('code_indexer.git_operations.shutil.which')
    def test_clone_repository_git_not_available(self, mock_shutil_which):
        """Testa a tentativa de clonagem quando o git não está disponível."""
        mock_shutil_which.return_value = None # Git não disponível

        cloner = GitRepoCloner()
        with patch('code_indexer.git_operations.logging') as mock_logging:
            success = cloner.clone_repository("https://fake.repo/any.git", "local/any_repo")

            self.assertFalse(success)
            mock_logging.error.assert_called_with("Git não está disponível. Não é possível clonar o repositório.")

    @patch('code_indexer.git_operations.subprocess.run')
    @patch('code_indexer.git_operations.shutil.which')
    def test_clone_empty_url_or_path(self, mock_shutil_which, mock_subprocess_run):
        """Testa a clonagem com URL ou caminho local vazios."""
        mock_shutil_which.return_value = "/usr/bin/git"
        cloner = GitRepoCloner()

        with patch('code_indexer.git_operations.logging') as mock_logging:
            self.assertFalse(cloner.clone_repository("", "local/path"))
            mock_logging.error.assert_called_with("URL do repositório e caminho local não podem ser vazios.")

        with patch('code_indexer.git_operations.logging') as mock_logging:
            self.assertFalse(cloner.clone_repository("http://some.url", ""))
            mock_logging.error.assert_called_with("URL do repositório e caminho local não podem ser vazios.")

        mock_subprocess_run.assert_not_called() # subprocess.run não deve ser chamado


    @patch('code_indexer.git_operations.subprocess.run')
    @patch('code_indexer.git_operations.shutil.which')
    def test_clone_subprocess_filenotfound_error(self, mock_shutil_which, mock_subprocess_run):
        """Testa o tratamento de FileNotFoundError do subprocess."""
        mock_shutil_which.return_value = "/usr/bin/nonexistent_git_just_in_case" # Simula que foi encontrado, mas falha ao rodar
        mock_subprocess_run.side_effect = FileNotFoundError("git command not found")

        cloner = GitRepoCloner()
        # É preciso re-instanciar para que o self.git_executable seja o mockado
        cloner.git_executable = "/usr/bin/nonexistent_git_just_in_case"

        with patch('code_indexer.git_operations.logging') as mock_logging:
            success = cloner.clone_repository("https://fake.repo/test.git", "local/test_repo")
            self.assertFalse(success)
            mock_logging.error.assert_any_call(
                "Comando '/usr/bin/nonexistent_git_just_in_case' não encontrado durante a execução do subprocess. "
                "Verifique se o Git está instalado e no PATH."
            )

    @patch('code_indexer.git_operations.subprocess.run')
    @patch('code_indexer.git_operations.shutil.which')
    def test_clone_subprocess_timeout_error(self, mock_shutil_which, mock_subprocess_run):
        """Testa o tratamento de TimeoutExpired do subprocess."""
        mock_shutil_which.return_value = "/usr/bin/git"
        mock_subprocess_run.side_effect = subprocess.TimeoutExpired(cmd="git clone", timeout=10)

        cloner = GitRepoCloner()
        with patch('code_indexer.git_operations.logging') as mock_logging:
            success = cloner.clone_repository("https://fake.repo/test.git", "local/test_repo")
            self.assertFalse(success)
            mock_logging.error.assert_any_call(
                "Timeout ao tentar clonar 'https://fake.repo/test.git'. O repositório pode ser muito grande ou a rede lenta."
            )

    @patch('code_indexer.git_operations.subprocess.run')
    @patch('code_indexer.git_operations.shutil.which')
    def test_clone_subprocess_generic_exception(self, mock_shutil_which, mock_subprocess_run):
        """Testa o tratamento de uma exceção genérica do subprocess."""
        mock_shutil_which.return_value = "/usr/bin/git"
        mock_subprocess_run.side_effect = Exception("Algo muito ruim aconteceu")

        cloner = GitRepoCloner()
        with patch('code_indexer.git_operations.logging') as mock_logging:
            success = cloner.clone_repository("https://fake.repo/test.git", "local/test_repo")
            self.assertFalse(success)
            mock_logging.error.assert_any_call(
                "Uma exceção inesperada ocorreu ao tentar clonar 'https://fake.repo/test.git': Algo muito ruim aconteceu"
            )

if __name__ == '__main__':
    unittest.main()
