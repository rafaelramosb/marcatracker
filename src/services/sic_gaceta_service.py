import os
import requests
import tempfile
import re
import json
from datetime import datetime
from bs4 import BeautifulSoup
import subprocess
from src.models import db, DataSource, DataSyncLog, SimilarMark, Trademark, GacetaDocument
import uuid

class SICGacetaService:
    """Servicio para la integración con la Gaceta de la SIC"""
    
    def __init__(self):
        self.sic_url = "https://www.sic.gov.co/gaceta-de-propiedad-industrial"
        self.base_storage_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'storage', 'gacetas')
        self.json_storage_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'storage', 'json')
        
        # Asegurar que existan los directorios
        os.makedirs(self.base_storage_path, exist_ok=True)
        os.makedirs(self.json_storage_path, exist_ok=True)
    
    def check_new_gacetas(self):
        """Verifica si hay nuevas gacetas disponibles"""
        try:
            # Obtener la página principal de gacetas
            response = requests.get(self.sic_url)
            response.raise_for_status()
            
            # Parsear el HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Buscar enlaces a PDFs de gacetas
            gaceta_links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.endswith('.pdf') and 'gaceta' in href.lower():
                    gaceta_links.append(href)
            
            return gaceta_links
        except Exception as e:
            print(f"Error al verificar nuevas gacetas: {str(e)}")
            return []
    
    def download_gaceta(self, url):
        """Descarga una gaceta desde la URL proporcionada y almacena referencia en BD"""
        try:
            # Extraer nombre del archivo de la URL
            filename = os.path.basename(url)
            
            # Organizar por año/mes
            current_date = datetime.now()
            year_dir = os.path.join(self.base_storage_path, str(current_date.year))
            month_dir = os.path.join(year_dir, f"{current_date.month:02d}")
            
            # Crear directorios si no existen
            os.makedirs(month_dir, exist_ok=True)
            
            # Ruta completa del archivo
            filepath = os.path.join(month_dir, filename)
            
            # Verificar si ya existe en la base de datos
            existing_doc = GacetaDocument.query.filter_by(url=url).first()
            if existing_doc:
                return existing_doc.filepath
            
            # Descargar el archivo si no existe en el sistema de archivos
            if not os.path.exists(filepath):
                response = requests.get(url, stream=True)
                response.raise_for_status()
                
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
            
            # Registrar en la base de datos
            gaceta_doc = GacetaDocument(
                id=str(uuid.uuid4()),
                filename=filename,
                filepath=filepath,
                url=url,
                download_date=datetime.utcnow(),
                processed=False
            )
            
            db.session.add(gaceta_doc)
            db.session.commit()
            
            return filepath
        except Exception as e:
            print(f"Error al descargar gaceta: {str(e)}")
            return None
    
    def extract_text_from_pdf(self, pdf_path):
        """Extrae el texto de un PDF usando pdftotext (poppler-utils)"""
        try:
            # Crear archivo temporal para el texto
            txt_path = pdf_path.replace('.pdf', '.txt')
            
            # Ejecutar pdftotext
            subprocess.run(['pdftotext', '-layout', pdf_path, txt_path], check=True)
            
            # Leer el texto extraído
            with open(txt_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
            
            # Limpiar archivo temporal
            os.remove(txt_path)
            
            return text
        except Exception as e:
            print(f"Error al extraer texto del PDF: {str(e)}")
            return ""
    
    def parse_trademark_data(self, text):
        """Analiza el texto extraído para identificar marcas registradas"""
        trademarks = []
        
        # Patrones para identificar secciones de marcas en la gaceta
        # Estos patrones deben ajustarse según el formato exacto de la gaceta de la SIC
        section_pattern = r"SOLICITUDES DE REGISTRO DE MARCA"
        entry_pattern = r"(\d{2}-\d+)\s+(.+?)\s+Clase:\s+(\d+)"
        
        # Buscar sección de solicitudes de registro
        sections = re.split(section_pattern, text)
        if len(sections) > 1:
            # Analizar entradas en la sección
            for match in re.finditer(entry_pattern, sections[1]):
                application_number = match.group(1)
                name = match.group(2).strip()
                nice_class = match.group(3)
                
                trademarks.append({
                    'application_number': application_number,
                    'name': name,
                    'nice_classification': nice_class,
                    'source': 'gaceta',
                    'application_date': datetime.now()  # Aproximado, se debería extraer del texto
                })
        
        return trademarks
    
    def save_trademarks_to_json(self, trademarks, gaceta_id):
        """Guarda las marcas extraídas en un archivo JSON"""
        try:
            # Crear nombre de archivo basado en ID de gaceta
            json_filename = f"gaceta_{gaceta_id}_trademarks.json"
            json_filepath = os.path.join(self.json_storage_path, json_filename)
            
            # Convertir fechas a strings para serialización JSON
            serializable_trademarks = []
            for tm in trademarks:
                tm_copy = tm.copy()
                if 'application_date' in tm_copy and isinstance(tm_copy['application_date'], datetime):
                    tm_copy['application_date'] = tm_copy['application_date'].isoformat()
                serializable_trademarks.append(tm_copy)
            
            # Guardar en archivo JSON
            with open(json_filepath, 'w', encoding='utf-8') as f:
                json.dump(serializable_trademarks, f, ensure_ascii=False, indent=2)
            
            return json_filepath
        except Exception as e:
            print(f"Error al guardar marcas en JSON: {str(e)}")
            return None
    
    def compare_with_registered_trademarks(self, new_trademarks):
        """Compara las nuevas marcas con las registradas por usuarios"""
        similar_marks = []
        
        # Obtener todas las marcas registradas por usuarios
        user_trademarks = Trademark.query.all()
        
        for user_tm in user_trademarks:
            for new_tm in new_trademarks:
                # Comparación simple por nombre (en producción se usarían algoritmos más sofisticados)
                similarity_score = self._calculate_similarity(user_tm.name, new_tm['name'])
                
                # Si la similitud supera un umbral, registrar como marca similar
                if similarity_score > 0.6:  # Umbral arbitrario para este ejemplo
                    similar_mark = SimilarMark(
                        id=str(uuid.uuid4()),
                        trademark_id=user_tm.id,
                        name=new_tm['name'],
                        registration_number=None,
                        application_number=new_tm['application_number'],
                        application_date=new_tm['application_date'],
                        nice_classification=new_tm['nice_classification'],
                        similarity_score=similarity_score,
                        similarity_type='nombre',
                        source=new_tm['source'],
                        source_url=None
                    )
                    similar_marks.append(similar_mark)
        
        return similar_marks
    
    def _calculate_similarity(self, str1, str2):
        """Calcula la similitud entre dos cadenas (implementación simple)"""
        # En producción, se usarían algoritmos como Levenshtein, Jaro-Winkler, etc.
        # Esta es una implementación muy básica para el ejemplo
        str1 = str1.lower()
        str2 = str2.lower()
        
        # Contar palabras comunes
        words1 = set(str1.split())
        words2 = set(str2.split())
        common_words = words1.intersection(words2)
        
        if not words1 or not words2:
            return 0
        
        # Calcular similitud como proporción de palabras comunes
        return len(common_words) / max(len(words1), len(words2))
    
    def process_gaceta(self, gaceta_url):
        """Procesa una gaceta completa"""
        try:
            # Registrar inicio de sincronización
            data_source = DataSource.query.filter_by(source_type='gaceta').first()
            if not data_source:
                data_source = DataSource(
                    id=str(uuid.uuid4()),
                    name='Gaceta de Propiedad Industrial',
                    description='Publicación oficial de la SIC',
                    source_type='gaceta',
                    url=self.sic_url,
                    auth_required=False,
                    sync_frequency=24,  # Diario
                    is_active=True
                )
                db.session.add(data_source)
                db.session.commit()
            
            sync_log = DataSyncLog(
                id=str(uuid.uuid4()),
                data_source_id=data_source.id,
                start_time=datetime.utcnow(),
                status='en_proceso'
            )
            db.session.add(sync_log)
            db.session.commit()
            
            # Descargar la gaceta
            pdf_path = self.download_gaceta(gaceta_url)
            if not pdf_path:
                sync_log.status = 'error'
                sync_log.error_message = 'No se pudo descargar la gaceta'
                sync_log.end_time = datetime.utcnow()
                db.session.commit()
                return False
            
            # Buscar el documento en la base de datos
            gaceta_doc = GacetaDocument.query.filter_by(filepath=pdf_path).first()
            
            # Extraer texto
            text = self.extract_text_from_pdf(pdf_path)
            if not text:
                sync_log.status = 'error'
                sync_log.error_message = 'No se pudo extraer texto de la gaceta'
                sync_log.end_time = datetime.utcnow()
                db.session.commit()
                return False
            
            # Analizar marcas
            new_trademarks = self.parse_trademark_data(text)
            
            # Guardar marcas en JSON
            if gaceta_doc:
                json_path = self.save_trademarks_to_json(new_trademarks, gaceta_doc.id)
                
                # Actualizar documento de gaceta
                gaceta_doc.processed = True
                gaceta_doc.processing_date = datetime.utcnow()
                db.session.commit()
            
            # Comparar con marcas registradas
            similar_marks = self.compare_with_registered_trademarks(new_trademarks)
            
            # Guardar marcas similares en la base de datos
            for mark in similar_marks:
                db.session.add(mark)
            
            # Actualizar log de sincronización
            sync_log.status = 'completado'
            sync_log.records_processed = len(new_trademarks)
            sync_log.records_added = len(similar_marks)
            sync_log.end_time = datetime.utcnow()
            
            # Actualizar última sincronización
            data_source.last_sync = datetime.utcnow()
            
            db.session.commit()
            
            return True
        except Exception as e:
            # Registrar error
            if 'sync_log' in locals():
                sync_log.status = 'error'
                sync_log.error_message = str(e)
                sync_log.end_time = datetime.utcnow()
                db.session.commit()
            
            print(f"Error al procesar gaceta: {str(e)}")
            return False
