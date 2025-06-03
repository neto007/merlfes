# code_indexer/git_operations.py
# Este módulo lida com operações Git, como clonar repositórios.
# REQUISITO: O comando 'git' deve estar instalado e acessível no PATH do sistema
# para que as funcionalidades deste módulo operem corretamente.

import subprocess
import logging
import shutil # Para verificar se o git está no PATH

class GitRepoCloner:
    """
    Responsável por clonar repositórios Git.
    """

    def __init__(self):
        self.git_executable = shutil.which("git") # Verifica se 'git' está no PATH e obtém o executável
        if not self.git_executable:
            logging.warning("Comando 'git' não encontrado no PATH do sistema. A clonagem de repositórios não funcionará.")
        else:
            logging.info(f"Executável Git encontrado em: {self.git_executable}")

    def is_git_available(self) -> bool:
        """Verifica se o executável git foi encontrado."""
        return bool(self.git_executable)

    def clone_repository(self, repo_url: str, local_path: str) -> bool:
        """
        Clona um repositório Git de uma URL para um caminho local.

        Args:
            repo_url: A URL do repositório Git (ex: https://github.com/user/repo.git).
            local_path: O caminho no sistema de arquivos local onde o repositório será clonado.

        Returns:
            True se o clone for bem-sucedido, False caso contrário.
        """
        if not self.is_git_available():
            logging.error("Git não está disponível. Não é possível clonar o repositório.")
            return False

        if not repo_url or not local_path:
            logging.error("URL do repositório e caminho local não podem ser vazios.")
            return False

        logging.info(f"Tentando clonar '{repo_url}' para '{local_path}'...")

        try:
            # O comando será: git clone <repo_url> <local_path>
            process = subprocess.run(
                [self.git_executable, "clone", repo_url, local_path],
                capture_output=True,  # Captura stdout e stderr
                text=True,            # Decodifica output para string
                check=False           # Não lança exceção automaticamente para códigos de retorno não-zero
            )

            if process.returncode == 0:
                logging.info(f"Repositório '{repo_url}' clonado com sucesso para '{local_path}'.")
                # stdout pode conter mensagens úteis do git clone
                if process.stdout:
                    logging.debug(f"Git clone stdout:
{process.stdout}")
                return True
            else:
                logging.error(f"Falha ao clonar o repositório '{repo_url}'. Código de retorno: {process.returncode}")
                if process.stderr:
                    logging.error(f"Git clone stderr:
{process.stderr}")
                # Se o diretório foi criado mas o clone falhou (raro, mas possível),
                # ou se o diretório já existia e o clone falhou, pode ser útil limpá-lo
                # ou avisar o usuário. Por ora, apenas logamos o erro.
                return False
        except FileNotFoundError:
            # Isso não deve acontecer se self.git_executable foi encontrado, mas como fallback.
            logging.error(f"Comando '{self.git_executable}' não encontrado durante a execução do subprocess. "
                          "Verifique se o Git está instalado e no PATH.")
            return False
        except subprocess.TimeoutExpired:
            logging.error(f"Timeout ao tentar clonar '{repo_url}'. O repositório pode ser muito grande ou a rede lenta.")
            return False
        except Exception as e:
            logging.error(f"Uma exceção inesperada ocorreu ao tentar clonar '{repo_url}': {e}")
            return False

if __name__ == '__main__':
    # Exemplo de uso (requer que 'git' esteja instalado)
    logging.basicConfig(level=logging.DEBUG) # Para ver todos os logs do exemplo

    cloner = GitRepoCloner()

    if not cloner.is_git_available():
        print("Git não está disponível no sistema. Saindo do exemplo.")
    else:
        # NOTA: Este exemplo tentará clonar um repositório real.
        # Escolha um repositório pequeno e público para teste.
        # Cuidado com o local_path para não sobrescrever nada importante.
        # Ex: um repositório de exemplo do GitHub ou um seu que seja pequeno.
        # repo_to_clone = "https://github.com/git-fixtures/basic.git" # Repositório pequeno para teste
        repo_to_clone = "https://github.com/pallets/flask.git" # Um repo maior para testar o output
        # repo_to_clone = "https://github.com/nonexistent/repo123xyz.git" # Para testar falha

        clone_target_dir = "temp_cloned_repo_flask" # Será criado na raiz do projeto atual

        print(f"\nTentando clonar: {repo_to_clone} para {clone_target_dir}")
        success = cloner.clone_repository(repo_to_clone, clone_target_dir)

        if success:
            print(f"Clone bem-sucedido. Verifique o diretório: {clone_target_dir}")
            # Em uma aplicação real, você poderia listar os arquivos ou fazer algo com o repo.
            # Lembre-se de deletar `temp_cloned_repo` após o teste se não precisar mais.
            # Para limpeza: shutil.rmtree(clone_target_dir, ignore_errors=True)
        else:
            print(f"Falha ao clonar. Verifique os logs.")

        # Teste com URL inválida (ou repositório inexistente)
        print("\nTentando clonar um repositório inválido:")
        invalid_repo = "https://github.com/invalid-user-xyz/invalid-repo-abc.git"
        invalid_target_dir = "temp_cloned_repo_invalid"
        success_invalid = cloner.clone_repository(invalid_repo, invalid_target_dir)
        if not success_invalid:
            print("Falha ao clonar repositório inválido, como esperado.")
        else:
            print("Algo inesperado aconteceu, o clone do repositório inválido parece ter funcionado.")
            # shutil.rmtree(invalid_target_dir, ignore_errors=True)
