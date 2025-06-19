import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import tempfile
from datetime import datetime

# Ajustar la ruta para importar desde src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.sic_gaceta_service import SICGacetaService
from src.models import DataSource, DataSyncLog, SimilarMark, Trademark

class TestSICGacetaService(unittest.TestCase):
    """Pruebas unitarias para el servicio de integración con la Gaceta de la SIC"""
    
    def setUp(self):
        """Configuración inicial para las pruebas"""
        self.service = SICGacetaService()
        
        # Crear un archivo PDF de prueba
        self.test_pdf_path = os.path.join(tempfile.gettempdir(), "test_gaceta.pdf")
        with open(self.test_pdf_path, 'wb') as f:
            f.write(b'%PDF-1.5\nTest PDF content')
    
    def tearDown(self):
        """Limpieza después de las pruebas"""
        if os.path.exists(self.test_pdf_path):
            os.remove(self.test_pdf_path)
    
    @patch('requests.get')
    def test_check_new_gacetas(self, mock_get):
        """Prueba la verificación de nuevas gacetas"""
        # Configurar el mock
        mock_response = MagicMock()
        mock_response.text = """
        <html>
            <body>
                <a href="https://www.sic.gov.co/sites/default/files/gaceta/gaceta_123.pdf">Gaceta 123</a>
                <a href="https://www.sic.gov.co/sites/default/files/otros/otro_archivo.pdf">Otro PDF</a>
                <a href="https://www.sic.gov.co/pagina">Página normal</a>
            </body>
        </html>
        """
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        # Ejecutar la función
        result = self.service.check_new_gacetas()
        
        # Verificar resultados
        self.assertEqual(len(result), 2)
        self.assertIn("gaceta_123.pdf", result[0])
    
    @patch('subprocess.run')
    def test_extract_text_from_pdf(self, mock_run):
        """Prueba la extracción de texto de un PDF"""
        # Configurar el mock
        mock_run.return_value = MagicMock()
        
        # Crear archivo de texto simulado
        txt_path = self.test_pdf_path.replace('.pdf', '.txt')
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("SOLICITUDES DE REGISTRO DE MARCA\n12-345678 MARCA EJEMPLO Clase: 35")
        
        # Ejecutar la función
        result = self.service.extract_text_from_pdf(self.test_pdf_path)
        
        # Verificar resultados
        self.assertIn("SOLICITUDES DE REGISTRO DE MARCA", result)
        self.assertIn("MARCA EJEMPLO", result)
        
        # Limpiar
        if os.path.exists(txt_path):
            os.remove(txt_path)
    
    def test_parse_trademark_data(self):
        """Prueba el análisis de datos de marcas en el texto extraído"""
        # Texto de ejemplo
        text = """
        SUPERINTENDENCIA DE INDUSTRIA Y COMERCIO
        GACETA DE PROPIEDAD INDUSTRIAL
        
        SOLICITUDES DE REGISTRO DE MARCA
        
        12-345678 MARCA EJEMPLO Clase: 35
        13-987654 OTRA MARCA Clase: 42
        """
        
        # Ejecutar la función
        result = self.service.parse_trademark_data(text)
        
        # Verificar resultados
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['name'], "MARCA EJEMPLO")
        self.assertEqual(result[0]['nice_classification'], "35")
        self.assertEqual(result[1]['name'], "OTRA MARCA")
        self.assertEqual(result[1]['nice_classification'], "42")
    
    def test_calculate_similarity(self):
        """Prueba el cálculo de similitud entre cadenas"""
        # Casos de prueba
        test_cases = [
            ("Marca Ejemplo", "MARCA EJEMPLO", 1.0),  # Idénticas (ignorando mayúsculas)
            ("Marca Ejemplo", "Marca Diferente", 0.5),  # Una palabra en común
            ("Marca Ejemplo", "Ejemplo Marca", 1.0),  # Mismas palabras, orden diferente
            ("Marca Ejemplo", "Otra Cosa", 0.0),  # Sin palabras en común
            ("", "Marca", 0.0)  # Cadena vacía
        ]
        
        for str1, str2, expected in test_cases:
            result = self.service._calculate_similarity(str1, str2)
            self.assertAlmostEqual(result, expected, places=1)

if __name__ == '__main__':
    unittest.main()
