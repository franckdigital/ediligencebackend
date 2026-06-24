"""
Module scanner — 3 sources d'acquisition :
  1. eSCL (scanners réseau HP/Canon/Epson/Ricoh via HTTP)
  2. Agent local (scanner USB via http://localhost:9191)
  3. Dossier de surveillance (watch folder via Celery Beat)

Endpoints :
  GET  /api/scan/discover/        → scanners eSCL détectés sur le LAN
  POST /api/scan/scan/            → déclenche un scan eSCL
  POST /api/scan/pre-classify/    → OCR + IA sur fichier(s), renvoie champs pré-remplis
  POST /api/scan/batch-import/    → crée les courriers validés par l'opérateur
  GET  /api/scan/watch-status/    → état du dossier de surveillance
"""
import logging
import os
import uuid
import tempfile
from datetime import date as dt_date

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

logger = logging.getLogger(__name__)

SUPPORTED_EXTS = {'.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.webp'}


# ─── 1. Découverte eSCL ───────────────────────────────────────────────────────

class ScannerDiscoverView(APIView):
    """Découvre les scanners eSCL disponibles sur le réseau local."""
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        scanners = []

        # Tentative mDNS/Bonjour (zeroconf)
        try:
            from zeroconf import Zeroconf, ServiceBrowser
            import threading, time

            found = []
            lock = threading.Lock()

            class Listener:
                def add_service(self, zc, type_, name):
                    info = zc.get_service_info(type_, name)
                    if info and info.addresses:
                        addr = '.'.join(str(b) for b in info.addresses[0])
                        port = info.port
                        with lock:
                            found.append({
                                'name': name.split('.')[0],
                                'ip': addr,
                                'port': port,
                                'protocol': 'escl',
                                'url': f'http://{addr}:{port}',
                            })
                def remove_service(self, *a): pass
                def update_service(self, *a): pass

            zc = Zeroconf()
            ServiceBrowser(zc, '_uscan._tcp.local.', Listener())
            time.sleep(3)
            zc.close()
            scanners.extend(found)
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"mDNS scanner discovery error: {e}")

        # IPs configurées manuellement dans settings.SCANNER_IPS
        for ip in getattr(settings, 'SCANNER_IPS', []):
            info = _probe_escl(ip)
            if info:
                scanners.append(info)

        return Response({'scanners': scanners, 'count': len(scanners)})


# ─── 2. Scan eSCL ─────────────────────────────────────────────────────────────

class ScannerScanView(APIView):
    """Déclenche un scan sur un scanner eSCL réseau."""
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        scanner_url = request.data.get('scanner_url', '').rstrip('/')
        resolution  = int(request.data.get('resolution', 300))
        color_mode  = request.data.get('color_mode', 'Grayscale')  # Color|Grayscale|BlackAndWhite
        source      = request.data.get('source', 'Platen')          # Platen|Feeder
        format_out  = request.data.get('format', 'pdf')             # pdf|jpeg

        if not scanner_url:
            return Response({'error': 'scanner_url requis'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            pages = _escl_scan(scanner_url, resolution, color_mode, source, format_out)
            return Response({'pages': pages, 'count': len(pages)})
        except Exception as e:
            logger.error(f"eSCL scan error ({scanner_url}): {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ─── 3. Pré-classification IA ─────────────────────────────────────────────────

class ScanPreClassifyView(APIView):
    """
    Reçoit un ou plusieurs fichiers (du scanner ou upload manuel),
    lance OCR + analyse IA et renvoie les champs pré-remplis.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        files = request.FILES.getlist('files')
        if not files:
            return Response({'error': 'Aucun fichier fourni'}, status=status.HTTP_400_BAD_REQUEST)

        results = []
        for f in files:
            try:
                result = _pre_classify_file(f)
                results.append(result)
            except Exception as e:
                results.append({
                    'filename': f.name,
                    'error': str(e),
                    'objet': '',
                    'expediteur': '',
                    'sens': 'arrivee',
                    'niveau_urgence': 'normal',
                })

        return Response({'documents': results, 'count': len(results)})


# ─── 4. Import en lot ─────────────────────────────────────────────────────────

class ScanBatchImportView(APIView):
    """
    Reçoit les documents validés par l'opérateur et crée les courriers.
    Chaque document est un dict JSON dans request.data['documents'],
    avec un file_key correspondant à request.FILES[file_key].
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        from core.models import Courrier

        try:
            import json
            raw = request.data.get('documents')
            documents = json.loads(raw) if isinstance(raw, str) else (raw or [])
        except Exception:
            return Response({'error': 'Format documents invalide'}, status=status.HTTP_400_BAD_REQUEST)

        files = request.FILES
        created, errors = [], []

        for doc in documents:
            try:
                file_key = doc.get('file_key')
                file_obj = files.get(file_key) if file_key else None

                # Date de réception
                date_str = doc.get('date_reception') or str(dt_date.today())
                try:
                    from datetime import datetime
                    date_reception = datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    date_reception = dt_date.today()

                courrier = Courrier(
                    expediteur   = doc.get('expediteur', 'Inconnu'),
                    destinataire = doc.get('destinataire', ''),
                    objet        = doc.get('objet') or 'Document scanné',
                    date_reception = date_reception,
                    sens         = doc.get('sens', 'arrivee'),
                    type_courrier= doc.get('type_courrier', 'ordinaire'),
                    categorie    = doc.get('categorie', 'Autre'),
                    niveau_urgence = doc.get('niveau_urgence', 'normal'),
                    theme        = doc.get('theme', ''),
                    mots_cles    = doc.get('mots_cles', []),
                    resume_ia    = doc.get('resume_ia', ''),
                    ocr_text     = doc.get('ocr_text', ''),
                    traitement_statut = 'termine' if doc.get('ocr_text') else 'en_attente',
                )

                if file_obj:
                    ext = os.path.splitext(file_obj.name)[1].lower() or '.pdf'
                    courrier.fichier_joint.save(
                        f"scan_{uuid.uuid4().hex}{ext}",
                        ContentFile(file_obj.read()),
                        save=False,
                    )

                courrier.save()
                created.append({'id': courrier.pk, 'reference': courrier.reference, 'objet': courrier.objet})

            except Exception as e:
                logger.error(f"ScanBatchImport error: {e}")
                errors.append({'error': str(e), 'document': doc.get('objet', '?')})

        code = status.HTTP_201_CREATED if created else status.HTTP_400_BAD_REQUEST
        return Response({'created': created, 'errors': errors, 'count': len(created)}, status=code)


# ─── 5. État du dossier de surveillance ───────────────────────────────────────

class ScanWatchStatusView(APIView):
    """Retourne l'état du dossier de surveillance (nombre de fichiers en attente)."""
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        watch_dir = getattr(settings, 'SCAN_WATCH_FOLDER', None)
        if not watch_dir or not os.path.exists(watch_dir):
            return Response({'enabled': False, 'watch_folder': watch_dir})

        files = [
            f for f in os.listdir(watch_dir)
            if os.path.splitext(f)[1].lower() in SUPPORTED_EXTS
        ]
        return Response({
            'enabled': True,
            'watch_folder': watch_dir,
            'pending': len(files),
            'files': files[:20],
        })


# ─── Helpers eSCL ─────────────────────────────────────────────────────────────

def _probe_escl(ip, port=80):
    """Vérifie si un scanner eSCL répond à l'adresse donnée."""
    import requests
    urls = [f'http://{ip}:{port}/eSCL/ScannerCapabilities',
            f'http://{ip}/eSCL/ScannerCapabilities',
            f'https://{ip}/eSCL/ScannerCapabilities']
    for url in urls:
        try:
            r = requests.get(url, timeout=3)
            if r.status_code == 200:
                base = url.replace('/eSCL/ScannerCapabilities', '')
                return {'name': f'Scanner ({ip})', 'ip': ip, 'protocol': 'escl', 'url': base}
        except Exception:
            continue
    return None


ESCL_SCAN_SETTINGS_TMPL = """<?xml version="1.0" encoding="UTF-8"?>
<scan:ScanSettings
    xmlns:scan="http://schemas.hp.com/imaging/escl/2011/05/03"
    xmlns:pwg="http://www.pwg.org/schemas/2010/12/sm">
  <pwg:Version>2.6</pwg:Version>
  <scan:Intent>TextAndGraphic</scan:Intent>
  <pwg:ScanRegions>
    <pwg:ScanRegion>
      <pwg:ContentRegionUnits>escl:ThreeHundredthsOfInches</pwg:ContentRegionUnits>
      <pwg:Height>3507</pwg:Height>
      <pwg:Width>2481</pwg:Width>
      <pwg:XOffset>0</pwg:XOffset>
      <pwg:YOffset>0</pwg:YOffset>
    </pwg:ScanRegion>
  </pwg:ScanRegions>
  <scan:InputSource>{source}</scan:InputSource>
  <scan:ColorMode>{color_mode}</scan:ColorMode>
  <scan:XResolution>{resolution}</scan:XResolution>
  <scan:YResolution>{resolution}</scan:YResolution>
  <pwg:DocumentFormat>{mime}</pwg:DocumentFormat>
</scan:ScanSettings>"""


def _escl_scan(scanner_url, resolution=300, color_mode='Grayscale', source='Platen', fmt='pdf'):
    """Déclenche un scan via eSCL et retourne la liste des pages."""
    import requests

    mime = 'application/pdf' if fmt == 'pdf' else 'image/jpeg'
    ext  = '.pdf' if fmt == 'pdf' else '.jpeg'

    xml_body = ESCL_SCAN_SETTINGS_TMPL.format(
        source=source, color_mode=color_mode,
        resolution=resolution, mime=mime,
    )

    # 1. Créer le job
    resp = requests.post(
        f"{scanner_url}/eSCL/ScanJobs",
        data=xml_body.encode('utf-8'),
        headers={'Content-Type': 'text/xml; charset=utf-8'},
        timeout=30,
    )
    resp.raise_for_status()
    job_url = resp.headers.get('Location', '').rstrip('/')
    if not job_url:
        job_url = f"{scanner_url}/eSCL/ScanJobs/1"

    # 2. Récupérer les pages
    pages = []
    page_num = 1
    while True:
        try:
            page_resp = requests.get(f"{job_url}/NextDocument", timeout=60, stream=True)
            if page_resp.status_code in (404, 409):
                break
            page_resp.raise_for_status()

            raw = page_resp.content
            filename = f"scans/{uuid.uuid4().hex}{ext}"
            path = default_storage.save(filename, ContentFile(raw))
            url  = default_storage.url(path)
            pages.append({'page': page_num, 'url': url, 'path': path, 'size': len(raw)})
            page_num += 1

        except Exception:
            if page_num == 1:
                raise
            break

    return pages


# ─── Helper pré-classification ────────────────────────────────────────────────

def _pre_classify_file(file_obj):
    """
    Sauvegarde le fichier temporairement, extrait le texte (OCR),
    puis lance l'analyse heuristique / OpenAI.
    """
    ext = os.path.splitext(file_obj.name)[1].lower() or '.pdf'
    tmp_path = None

    try:
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            for chunk in file_obj.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name

        ocr_text = _extract_text(tmp_path, ext)

        from core.tasks_courrier import _analyze_heuristic
        from django.conf import settings

        openai_key = getattr(settings, 'OPENAI_API_KEY', None)
        if openai_key and ocr_text:
            from core.tasks_courrier import _analyze_with_openai
            analysis = _analyze_with_openai(ocr_text, '', openai_key)
        else:
            analysis = _analyze_heuristic(ocr_text or '', '')

        # Sauvegarde dans media/scan/
        file_obj.seek(0)
        media_filename = f"scan/{uuid.uuid4().hex}{ext}"
        media_path = default_storage.save(media_filename, ContentFile(file_obj.read()))
        media_url  = default_storage.url(media_path)

        return {
            'filename': file_obj.name,
            'file_key': media_filename,
            'file_url': media_url,
            'ocr_text': ocr_text[:2000] if ocr_text else '',
            'objet':    analysis.get('resume', '')[:200],
            'expediteur': '',
            'destinataire': '',
            'sens': 'arrivee',
            'type_courrier': 'ordinaire',
            'categorie': 'Autre',
            'date_reception': str(dt_date.today()),
            'niveau_urgence': analysis.get('niveau_urgence', 'normal'),
            'theme': analysis.get('theme', ''),
            'mots_cles': analysis.get('mots_cles', []),
            'resume_ia': analysis.get('resume', ''),
            'service_propose': analysis.get('service_propose', ''),
        }

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


def _extract_text(file_path, ext):
    """Extrait le texte d'un fichier PDF ou image."""
    text = ''

    if ext == '.pdf':
        try:
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages[:5]:
                    t = page.extract_text()
                    if t:
                        text += t + '\n\n'
            text = text.strip()
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"pdfplumber extract error: {e}")

        if not text:
            try:
                import pytesseract
                from pdf2image import convert_from_path
                pages = convert_from_path(file_path, first_page=1, last_page=3, dpi=200)
                for p in pages:
                    text += pytesseract.image_to_string(p, lang='fra+eng') + '\n\n'
                text = text.strip()
            except ImportError:
                pass
            except Exception as e:
                logger.warning(f"Tesseract PDF error: {e}")

    elif ext in ('.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.webp'):
        try:
            import pytesseract
            from PIL import Image
            img = Image.open(file_path)
            text = pytesseract.image_to_string(img, lang='fra+eng').strip()
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"Tesseract image error: {e}")

    return text
