import cv2
import numpy as np
from PIL import Image
import io
import os
import uuid
import requests
from datetime import datetime
from src.models import db, SimilarMark, Trademark, LogoImage

class ImageComparisonService:
    """Servicio para comparación de imágenes de logos de marcas"""
    
    def __init__(self):
        self.logos_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'storage', 'logos')
        os.makedirs(self.logos_dir, exist_ok=True)
    
    def compare_logos(self, user_trademark_id, new_logo_path):
        """Compara un nuevo logo con los logos de marcas registradas por usuarios"""
        try:
            # Obtener la marca del usuario
            user_tm = Trademark.query.get(user_trademark_id)
            if not user_tm or not user_tm.logo_path or not os.path.exists(user_tm.logo_path):
                return None, 0.0
            
            # Cargar imágenes
            user_logo = cv2.imread(user_tm.logo_path)
            new_logo = cv2.imread(new_logo_path)
            
            if user_logo is None or new_logo is None:
                return None, 0.0
            
            # Redimensionar para comparación
            user_logo = cv2.resize(user_logo, (200, 200))
            new_logo = cv2.resize(new_logo, (200, 200))
            
            # Convertir a escala de grises
            user_logo_gray = cv2.cvtColor(user_logo, cv2.COLOR_BGR2GRAY)
            new_logo_gray = cv2.cvtColor(new_logo, cv2.COLOR_BGR2GRAY)
            
            # Calcular histogramas
            hist1 = cv2.calcHist([user_logo_gray], [0], None, [256], [0, 256])
            hist2 = cv2.calcHist([new_logo_gray], [0], None, [256], [0, 256])
            
            # Normalizar histogramas
            cv2.normalize(hist1, hist1, 0, 1, cv2.NORM_MINMAX)
            cv2.normalize(hist2, hist2, 0, 1, cv2.NORM_MINMAX)
            
            # Calcular similitud
            similarity_score = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
            
            # Detectar características (SIFT)
            sift = cv2.SIFT_create()
            keypoints1, descriptors1 = sift.detectAndCompute(user_logo_gray, None)
            keypoints2, descriptors2 = sift.detectAndCompute(new_logo_gray, None)
            
            # Si no hay suficientes características, usar solo similitud de histograma
            if descriptors1 is None or descriptors2 is None or len(keypoints1) < 2 or len(keypoints2) < 2:
                return user_tm, similarity_score
            
            # Comparar características
            bf = cv2.BFMatcher()
            matches = bf.knnMatch(descriptors1, descriptors2, k=2)
            
            # Aplicar ratio test de Lowe
            good_matches = []
            for m, n in matches:
                if m.distance < 0.75 * n.distance:
                    good_matches.append(m)
            
            # Calcular puntuación basada en coincidencias
            feature_score = len(good_matches) / max(len(keypoints1), len(keypoints2))
            
            # Combinar puntuaciones
            combined_score = (similarity_score + feature_score) / 2
            
            return user_tm, combined_score
            
        except Exception as e:
            print(f"Error en comparación de imágenes: {str(e)}")
            return None, 0.0
    
    def download_and_compare_logo(self, logo_url, trademark_name, application_number=None, nice_classification=None):
        """Descarga un logo desde una URL y lo compara con todas las marcas registradas"""
        try:
            # Descargar imagen
            response = requests.get(logo_url)
            if not response.ok:
                return []
            
            # Crear nombre de archivo único
            filename = f"{uuid.uuid4()}.jpg"
            year_month = datetime.now().strftime("%Y/%m")
            
            # Crear estructura de directorios
            logo_dir = os.path.join(self.logos_dir, year_month)
            os.makedirs(logo_dir, exist_ok=True)
            
            # Ruta completa del archivo
            filepath = os.path.join(logo_dir, filename)
            
            # Guardar imagen
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            # Registrar imagen en la base de datos
            logo_image = LogoImage(
                id=str(uuid.uuid4()),
                filename=filename,
                filepath=filepath,
                source_url=logo_url,
                upload_date=datetime.utcnow()
            )
            db.session.add(logo_image)
            db.session.commit()
            
            # Obtener todas las marcas registradas
            user_trademarks = Trademark.query.all()
            similar_marks = []
            
            # Comparar con cada marca
            for user_tm in user_trademarks:
                if not user_tm.logo_path:
                    continue
                    
                _, similarity_score = self.compare_logos(user_tm.id, filepath)
                
                # Si la similitud supera un umbral, registrar
                if similarity_score > 0.6:  # Umbral arbitrario
                    similar_mark = SimilarMark(
                        id=str(uuid.uuid4()),
                        trademark_id=user_tm.id,
                        name=trademark_name,
                        application_number=application_number,
                        nice_classification=nice_classification,
                        similarity_score=similarity_score,
                        similarity_type='imagen',
                        source='logo_comparison',
                        source_url=logo_url,
                        logo_path=filepath
                    )
                    db.session.add(similar_mark)
                    similar_marks.append(similar_mark)
            
            if similar_marks:
                db.session.commit()
                
            return similar_marks
            
        except Exception as e:
            print(f"Error en descarga y comparación de logo: {str(e)}")
            return []
    
    def save_uploaded_logo(self, file_data, trademark_id=None):
        """Guarda un logo subido por el usuario"""
        try:
            # Crear nombre de archivo único
            filename = f"{uuid.uuid4()}.jpg"
            year_month = datetime.now().strftime("%Y/%m")
            
            # Crear estructura de directorios
            logo_dir = os.path.join(self.logos_dir, year_month)
            os.makedirs(logo_dir, exist_ok=True)
            
            # Ruta completa del archivo
            filepath = os.path.join(logo_dir, filename)
            
            # Guardar imagen
            with open(filepath, 'wb') as f:
                f.write(file_data)
            
            # Registrar imagen en la base de datos
            logo_image = LogoImage(
                id=str(uuid.uuid4()),
                trademark_id=trademark_id,
                filename=filename,
                filepath=filepath,
                upload_date=datetime.utcnow()
            )
            db.session.add(logo_image)
            
            # Si hay un ID de marca, actualizar la referencia
            if trademark_id:
                trademark = Trademark.query.get(trademark_id)
                if trademark:
                    trademark.logo_path = filepath
            
            db.session.commit()
            
            return filepath
            
        except Exception as e:
            print(f"Error al guardar logo: {str(e)}")
            return None
