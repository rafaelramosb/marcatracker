import os
import time
from datetime import datetime
import uuid
from playwright.sync_api import sync_playwright
from src.models import db, DataSource, DataSyncLog, SimilarMark, Trademark

class SICWebScraperService:
    """Servicio para realizar scraping del portal web de la SIC"""
    
    def __init__(self):
        self.sic_url = "https://sipi.sic.gov.co/sipi/Extra/IP/TM/Qbe.aspx"
        self.search_results = []
    
    def scrape_trademark_search(self, search_terms=None):
        """Realiza búsquedas en el portal de la SIC"""
        try:
            # Registrar inicio de sincronización
            data_source = DataSource.query.filter_by(source_type='sic_web').first()
            if not data_source:
                data_source = DataSource(
                    id=str(uuid.uuid4()),
                    name='Portal Web SIC',
                    description='Buscador de marcas de la SIC',
                    source_type='sic_web',
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
            
            # Si no se proporcionan términos de búsqueda, usar marcas registradas por usuarios
            if not search_terms:
                user_trademarks = Trademark.query.all()
                search_terms = [tm.name for tm in user_trademarks]
            
            # Iniciar Playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                # Navegar a la página de búsqueda
                page.goto(self.sic_url)
                
                total_results = []
                
                # Realizar búsquedas para cada término
                for term in search_terms:
                    try:
                        # Esperar a que cargue la página
                        page.wait_for_selector('#txtDenominacion', state='visible')
                        
                        # Limpiar campo de búsqueda anterior
                        page.fill('#txtDenominacion', '')
                        
                        # Ingresar término de búsqueda
                        page.fill('#txtDenominacion', term)
                        
                        # Hacer clic en el botón de búsqueda
                        page.click('#btnBuscar')
                        
                        # Esperar resultados
                        page.wait_for_selector('#grvConsulta', state='visible', timeout=30000)
                        
                        # Extraer resultados
                        results = self._extract_search_results(page)
                        
                        # Añadir a resultados totales
                        total_results.extend(results)
                        
                        # Esperar un poco entre búsquedas para no sobrecargar el servidor
                        time.sleep(2)
                    
                    except Exception as e:
                        print(f"Error en búsqueda de '{term}': {str(e)}")
                        continue
                
                browser.close()
            
            # Comparar con marcas registradas
            similar_marks = self._process_search_results(total_results)
            
            # Actualizar log de sincronización
            sync_log.status = 'completado'
            sync_log.records_processed = len(total_results)
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
            
            print(f"Error en scraping del portal SIC: {str(e)}")
            return False
    
    def _extract_search_results(self, page):
        """Extrae los resultados de búsqueda de la página"""
        results = []
        
        # Obtener filas de la tabla de resultados
        rows = page.query_selector_all('#grvConsulta tr:not(:first-child)')
        
        for row in rows:
            try:
                # Extraer datos de cada columna
                columns = row.query_selector_all('td')
                if len(columns) >= 6:
                    application_number = columns[0].inner_text().strip()
                    name = columns[1].inner_text().strip()
                    nice_class = columns[2].inner_text().strip()
                    status = columns[3].inner_text().strip()
                    
                    # Extraer fecha de solicitud (formato puede variar)
                    application_date_str = columns[4].inner_text().strip()
                    try:
                        application_date = datetime.strptime(application_date_str, '%d/%m/%Y')
                    except:
                        application_date = None
                    
                    # Construir URL de detalle
                    detail_url = f"https://sipi.sic.gov.co/sipi/Extra/IP/TM/Qbe.aspx?sid={application_number}"
                    
                    results.append({
                        'application_number': application_number,
                        'name': name,
                        'nice_classification': nice_class,
                        'status': status,
                        'application_date': application_date,
                        'source': 'sic_web',
                        'source_url': detail_url
                    })
            except Exception as e:
                print(f"Error al extraer datos de fila: {str(e)}")
                continue
        
        return results
    
    def _process_search_results(self, search_results):
        """Procesa los resultados de búsqueda y los compara con marcas registradas"""
        similar_marks = []
        
        # Obtener todas las marcas registradas por usuarios
        user_trademarks = Trademark.query.all()
        
        for user_tm in user_trademarks:
            for result in search_results:
                # Comparación simple por nombre (en producción se usarían algoritmos más sofisticados)
                similarity_score = self._calculate_similarity(user_tm.name, result['name'])
                
                # Si la similitud supera un umbral, registrar como marca similar
                if similarity_score > 0.6:  # Umbral arbitrario para este ejemplo
                    similar_mark = SimilarMark(
                        id=str(uuid.uuid4()),
                        trademark_id=user_tm.id,
                        name=result['name'],
                        registration_number=None,
                        application_number=result['application_number'],
                        application_date=result['application_date'],
                        nice_classification=result['nice_classification'],
                        similarity_score=similarity_score,
                        similarity_type='nombre',
                        source=result['source'],
                        source_url=result['source_url']
                    )
                    db.session.add(similar_mark)
                    similar_marks.append(similar_mark)
        
        db.session.commit()
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
