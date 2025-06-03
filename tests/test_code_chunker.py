# tests/test_code_chunker.py
import unittest
from code_indexer.chunker.code_chunker import CodeChunker

class TestCodeChunker(unittest.TestCase):

    def setUp(self):
        self.chunker = CodeChunker()

    def test_empty_code(self):
        """Testa o chunking de uma string de código vazia."""
        self.assertEqual(self.chunker.chunk_python_code(""), [])
        self.assertEqual(self.chunker.chunk_python_code("   \n   \t  "), [])

    def test_code_without_definitions(self):
        """Testa o chunking de código sem classes ou funções."""
        code = "x = 10\ny = 20\nprint(x*y)"
        chunks = self.chunker.chunk_python_code(code)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0], code)

    def test_simple_class_and_function(self):
        """Testa o chunking de uma classe simples e uma função."""
        code = """
class MyClass:
    def method_one(self):
        pass

def another_function():
    print("World")
"""
        chunks = self.chunker.chunk_python_code(code)
        self.assertEqual(len(chunks), 2)
        self.assertTrue(chunks[0].strip().startswith("class MyClass:"))
        self.assertTrue(chunks[1].strip().startswith("def another_function():"))
        self.assertIn("method_one", chunks[0])
        self.assertIn("print(\"World\")", chunks[1])

    def test_multiple_definitions(self):
        """Testa múltiplas classes e funções, incluindo comentários e espaçamento."""
        code = """
# Comentário no início
class FirstClass:
    def first_method(self):
        # Comentário dentro do método
        return 1

class SecondClass(FirstClass): # Herança
    pass # Classe vazia

def first_function():
    return "hello"

def second_function(arg1, arg2): # Função com args
    # Docstring talvez?
    """This is a test function."""
    return arg1 + arg2
"""
        chunks = self.chunker.chunk_python_code(code)
        # Esperamos 4 chunks: FirstClass, SecondClass, first_function, second_function
        self.assertEqual(len(chunks), 4)
        self.assertTrue(chunks[0].strip().startswith("# Comentário no início\nclass FirstClass:"))
        self.assertTrue(chunks[1].strip().startswith("class SecondClass(FirstClass):"))
        self.assertTrue(chunks[2].strip().startswith("def first_function():"))
        self.assertTrue(chunks[3].strip().startswith("def second_function(arg1, arg2):"))

    def test_chunk_content_integrity(self):
        """Verifica se o conteúdo dos chunks é mantido corretamente."""
        code = """
class Test:
    def method(self, param):
        if param > 0:
            return True
        else:
            return False
"""
        chunks = self.chunker.chunk_python_code(code)
        self.assertEqual(len(chunks), 1)
        # Reconstrói o código a partir do chunk para verificar se é idêntico (ignorando whitespace inicial/final do arquivo original)
        # A lógica de chunking atual mantém os newlines originais, então a junção deve ser próxima.
        self.assertEqual(chunks[0].strip(), code.strip())

    def test_class_with_no_methods_then_function(self):
        """Testa uma classe sem métodos seguida por uma função."""
        code = """
class EmptyClass:
    pass

def some_function():
    return "ok"
"""
        chunks = self.chunker.chunk_python_code(code)
        self.assertEqual(len(chunks), 2)
        self.assertTrue(chunks[0].strip().startswith("class EmptyClass:"))
        self.assertTrue(chunks[1].strip().startswith("def some_function():"))

    def test_code_starting_with_decorator(self):
        """Testa código onde uma definição de função é precedida por um decorador."""
        # A regex atual não lida com decoradores como inícios de chunk separados,
        # o decorador fará parte do chunk da função/classe que ele decora.
        code = """
@my_decorator
def decorated_function():
    pass

class MyOtherClass:
    @another_decorator
    def decorated_method(self):
        pass
"""
        chunks = self.chunker.chunk_python_code(code)
        self.assertEqual(len(chunks), 2)
        self.assertTrue(chunks[0].strip().startswith("@my_decorator"))
        self.assertTrue(chunks[0].strip().endswith("pass"))
        self.assertTrue(chunks[1].strip().startswith("class MyOtherClass:"))
        self.assertIn("@another_decorator", chunks[1])


if __name__ == '__main__':
    unittest.main()
