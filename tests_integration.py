import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import tempfile
from datetime import datetime

# Ajustar la ruta para importar desde src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.sic_gaceta_service import SICGacetaService
from src.services.image_comparison_service import ImageComparisonService
from src.models import DataSource, DataSyncLog, SimilarMark, Trademark, GacetaDocument, LogoImage

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
    
    @patch('json.dump')
    def test_save_trademarks_to_json(self, mock_dump):
        """Prueba el guardado de marcas en archivo JSON"""
        # Datos de prueba
        trademarks = [
            {
                'application_number': '12-345678',
                'name': 'MARCA EJEMPLO',
                'nice_classification': '35',
                'source': 'gaceta',
                'application_date': datetime.now()
            }
        ]
        
        # Ejecutar la función
        self.service.save_trademarks_to_json(trademarks, 'test_id')
        
        # Verificar que se llamó a json.dump
        mock_dump.assert_called_once()


class TestImageComparisonService(unittest.TestCase):
    """Pruebas unitarias para el servicio de comparación de imágenes"""
    
    def setUp(self):
        """Configuración inicial para las pruebas"""
        self.service = ImageComparisonService()
        
        # Crear imágenes de prueba
        self.test_image1_path = os.path.join(tempfile.gettempdir(), "test_logo1.jpg")
        self.test_image2_path = os.path.join(tempfile.gettempdir(), "test_logo2.jpg")
        
        # Crear archivos de imagen vacíos para las pruebas
        with open(self.test_image1_path, 'wb') as f:
            f.write(b'Test image 1')
        
        with open(self.test_image2_path, 'wb') as f:
            f.write(b'Test image 2')
    
    def tearDown(self):
        """Limpieza después de las pruebas"""
        if os.path.exists(self.test_image1_path):
            os.remove(self.test_image1_path)
        
        if os.path.exists(self.test_image2_path):
            os.remove(self.test_image2_path)
    
    @patch('cv2.imread')
    @patch('cv2.resize')
    @patch('cv2.cvtColor')
    @patch('cv2.calcHist')
    @patch('cv2.normalize')
    @patch('cv2.compareHist')
    @patch('cv2.SIFT_create')
    def test_compare_logos(self, mock_sift, mock_compare_hist, mock_normalize, 
                          mock_calc_hist, mock_cvt_color, mock_resize, mock_imread):
        """Prueba la comparación de logos"""
        # Configurar mocks
        mock_imread.return_value = MagicMock()
        mock_resize.return_value = MagicMock()
        mock_cvt_color.return_value = MagicMock()
        mock_calc_hist.return_value = MagicMock()
        mock_normalize.return_value = None
        mock_compare_hist.return_value = 0.75  # Similitud del 75%
        
        # Configurar SIFT
        mock_sift_instance = MagicMock()
        mock_sift_instance.detectAndCompute.return_value = ([], None)
        mock_sift.return_value = mock_sift_instance
        
        # Crear mock de Trademark
        trademark = MagicMock()
        trademark.logo_path = self.test_image1_path
        
        # Patch para Trademark.query.get
        with patch('src.services.image_comparison_service.Trademark') as mock_trademark_model:
            mock_trademark_model.query.get.return_value = trademark
            
            # Ejecutar la función
            _, score = self.service.compare_logos('test_id', self.test_image2_path)
            
            # Verificar resultado
            self.assertEqual(score, 0.75)
    
    @patch('requests.get')
    def test_download_and_compare_logo(self, mock_get):
        """Prueba la descarga y comparación de logos"""
        # Configurar mock de respuesta
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.content = b'Test image content'
        mock_get.return_value = mock_response
        
        # Patch para la función compare_logos
        with patch.object(self.service, 'compare_logos', return_value=(MagicMock(), 0.8)):
            # Patch para los modelos
            with patch('src.services.image_comparison_service.Trademark'):
                with patch('src.services.image_comparison_service.LogoImage'):
                    with patch('src.services.image_comparison_service.SimilarMark'):
                        with patch('src.services.image_comparison_service.db'):
                            # Ejecutar la función
                            result = self.service.download_and_compare_logo(
                                'http://example.com/logo.jpg', 
                                'Test Trademark'
                            )
                            
                            # Verificar que se llamó a requests.get
                            mock_get.assert_called_once_with('http://example.com/logo.jpg')


if __name__ == '__main__':
    unittest.main()
