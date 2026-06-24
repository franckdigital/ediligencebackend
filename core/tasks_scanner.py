"""
Tâche Celery Beat : surveille un dossier et crée automatiquement des courriers
à partir des fichiers déposés par le scanner (scan-to-folder).

Configuration dans settings.py :
  SCAN_WATCH_FOLDER = '/srv/scan/entrant'   # ou 'C:/Scan/entrant'
  SCAN_AUTO_CREATE  = True                  # créer courrier sans validation opérateur
"""
import logging
import os
import uuid
from datetime import date

from celery import shared_task

logger = logging.getLogger(__name__)

SUPPORTED_EXTS = {'.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp'}


@shared_task(name='core.tasks_scanner.watch_scan_folder')
def watch_scan_folder():
    """
    Polling du dossier de surveillance toutes les 30 secondes (via Celery Beat).
    Chaque fichier trouvé est :
      1. Renommé en .processing (évite le double traitement)
      2. OCR + analyse IA
      3. Sauvegardé comme Courrier (statut nouveau, traitement_statut=terminé)
      4. Supprimé du dossier
    """
    from django.conf import settings
    from django.core.files import File
    from core.models import Courrier
    from core.views_scanner import _extract_text
    from core.tasks_courrier import _analyze_heuristic

    watch_dir = getattr(settings, 'SCAN_WATCH_FOLDER', None)
    if not watch_dir or not os.path.exists(watch_dir):
        return {'status': 'skipped', 'reason': 'SCAN_WATCH_FOLDER non configuré ou inexistant'}

    processed = 0
    errors    = 0

    for filename in sorted(os.listdir(watch_dir)):
        ext = os.path.splitext(filename)[1].lower()
        if ext not in SUPPORTED_EXTS:
            continue

        filepath = os.path.join(watch_dir, filename)
        processing_path = filepath + '.processing'

        # Réservation atomique — empêche le double traitement
        try:
            os.rename(filepath, processing_path)
        except OSError:
            continue

        try:
            # OCR
            ocr_text = _extract_text(processing_path, ext)

            # Analyse IA
            analysis = _analyze_heuristic(ocr_text or '', os.path.splitext(filename)[0])

            # Création du courrier
            with open(processing_path, 'rb') as f:
                courrier = Courrier(
                    expediteur     = 'Scanner automatique',
                    objet          = analysis.get('resume', '')[:200] or f'Document scanné — {filename}',
                    date_reception = date.today(),
                    sens           = 'arrivee',
                    type_courrier  = 'ordinaire',
                    categorie      = 'Autre',
                    ocr_text       = ocr_text,
                    resume_ia      = analysis.get('resume', ''),
                    mots_cles      = analysis.get('mots_cles', []),
                    theme          = analysis.get('theme', ''),
                    niveau_urgence = analysis.get('niveau_urgence', 'normal'),
                    traitement_statut = 'termine',
                )
                dest_name = f"scan/{uuid.uuid4().hex}{ext}"
                courrier.fichier_joint.save(dest_name, File(f), save=False)
                courrier.save()

            os.remove(processing_path)
            processed += 1
            logger.info(f"watch_scan_folder: courrier créé depuis {filename} → {courrier.reference}")

        except Exception as e:
            errors += 1
            logger.error(f"watch_scan_folder: erreur sur {filename}: {e}")
            # Restaurer le fichier original
            try:
                os.rename(processing_path, filepath)
            except Exception:
                pass

    return {'processed': processed, 'errors': errors}
