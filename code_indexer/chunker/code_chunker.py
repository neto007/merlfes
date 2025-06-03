# code_indexer/chunker/code_chunker.py
# Este módulo será responsável por dividir o código em chunks semânticos.

import re

class CodeChunker:
    """
    Responsável por dividir o código em pedaços (chunks) semanticamente significativos.
    """

    def __init__(self):
        # Regex para identificar definições de classe e função em Python.
        # Isso é uma simplificação inicial. Para uma solução robusta,
        # uma análise baseada em AST (Abstract Syntax Tree) com tree-sitter seria ideal.
        # Exemplo: "class MyClass:" ou "def my_function(arg1, arg2):"
        self.python_structure_pattern = re.compile(
            r"^(?:class\s+\w+\s*\(?[^)]*\)?:|def\s+\w+\s*\(?[^)]*\)?:)"
        )

    def chunk_python_code(self, code_content: str) -> list[str]:
        """
        Divide o conteúdo de um arquivo de código Python em chunks.

        Atualmente, divide o código com base nas definições de classe e função.
        Esta é uma implementação inicial e pode ser aprimorada.

        Args:
            code_content: Uma string contendo o código Python.

        Returns:
            Uma lista de strings, onde cada string é um chunk de código.
        """
        if not code_content.strip():
            return []

        lines = code_content.splitlines(keepends=True)
        chunks = []
        current_chunk_lines = []

        for line in lines:
            # Se a linha corresponde a um início de classe/função E já temos algo no chunk atual,
            # então o chunk atual é finalizado e um novo começa.
            # O strip() na linha é para o regex funcionar corretamente em linhas com indentação.
            if self.python_structure_pattern.match(line.strip()) and current_chunk_lines:
                chunks.append("".join(current_chunk_lines))
                current_chunk_lines = [line]
            else:
                current_chunk_lines.append(line)

        # Adiciona o último chunk restante
        if current_chunk_lines:
            chunks.append("".join(current_chunk_lines))

        return chunks

if __name__ == '__main__':
    # Exemplo de uso (para teste rápido)
    sample_code = """
class MyClass:
    def method_one(self):
        pass

    def method_two(self):
        # Um comentário
        return "Hello"

def another_function():
    # Outra função
    print("World")

class AnotherClass(MyClass):
    def __init__(self, value):
        self.value = value
"""
    chunker = CodeChunker()
    code_chunks = chunker.chunk_python_code(sample_code)

    print(f"Código original:
{sample_code}")
    print("\n" + "="*20 + " CHUNKS GERADOS " + "="*20 + "\n")
    for i, chunk_code in enumerate(code_chunks):
        print(f"--- Chunk {i+1} ---
{chunk_code.strip()}")
        print("-"*(15 + len(str(i+1))))
    print("\n" + "="*50)

    empty_code = ""
    print(f"\nTestando código vazio: {chunker.chunk_python_code(empty_code)}")

    code_without_defs = "x = 10\ny = 20\nprint(x+y)"
    print(f"\nTestando código sem definições de classe/função:
{code_without_defs}")
    chunks_no_defs = chunker.chunk_python_code(code_without_defs)
    for i, chunk_code in enumerate(chunks_no_defs):
        print(f"--- Chunk {i+1} ---
{chunk_code.strip()}")
        print("-"*(15 + len(str(i+1))))
