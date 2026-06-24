"""
Pipeline de traitement automatique des courriers :
  process_courrier_pipeline  → point d'entrée, déclenché par signal post_save
    ├── generate_thumbnail_task  → miniature JPEG 400×400
    ├── extract_ocr_text_task    → extraction texte (pdfplumber → Tesseract)
    └── analyze_courrier_ia_task → résumé, mots-clés, thème, urgence
"""
import io
import logging
import os
import re
from collections import Counter

from celery import shared_task, chain
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)


# ─── Point d'entrée ──────────────────────────────────────────────────────────

@shared_task(bind=True, max_retries=3, default_retry_delay=60, name='core.tasks_courrier.process_courrier_pipeline')
def process_courrier_pipeline(self, courrier_id):
    """Déclenche le pipeline complet sur un courrier qui vient d'obtenir un fichier."""
    try:
        from core.models import Courrier
        try:
            courrier = Courrier.objects.get(pk=courrier_id)
        except Courrier.DoesNotExist:
            logger.warning(f"process_courrier_pipeline: courrier {courrier_id} introuvable")
            return

        if not courrier.fichier_joint:
            return

        Courrier.objects.filter(pk=courrier_id).update(traitement_statut='en_cours')

        workflow = chain(
            generate_thumbnail_task.si(courrier_id),
            extract_ocr_text_task.si(courrier_id),
            analyze_courrier_ia_task.si(courrier_id),
        )
        workflow.apply_async()

    except Exception as exc:
        logger.error(f"process_courrier_pipeline error [{courrier_id}]: {exc}")
        try:
            from core.models import Courrier
            Courrier.objects.filter(pk=courrier_id).update(traitement_statut='erreur')
        except Exception:
            pass
        raise self.retry(exc=exc)


# ─── Tâche 1 : Miniature ──────────────────────────────────────────────────────

@shared_task(bind=True, max_retries=2, name='core.tasks_courrier.generate_thumbnail_task')
def generate_thumbnail_task(self, courrier_id):
    """Génère une miniature JPEG 400×400 à partir du fichier joint."""
    try:
        from core.models import Courrier
        try:
            courrier = Courrier.objects.get(pk=courrier_id)
        except Courrier.DoesNotExist:
            return

        if not courrier.fichier_joint:
            return

        file_path = courrier.fichier_joint.path
        ext = os.path.splitext(file_path)[1].lower()
        img = None

        if ext == '.pdf':
            try:
                from pdf2image import convert_from_path
                pages = convert_from_path(file_path, first_page=1, last_page=1, dpi=100)
                if pages:
                    img = pages[0]
            except ImportError:
                logger.warning("pdf2image non installé — miniature PDF ignorée")
            except Exception as e:
                logger.warning(f"Erreur miniature PDF [{courrier_id}]: {e}")

        elif ext in ('.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp'):
            try:
                from PIL import Image
                img = Image.open(file_path)
            except Exception as e:
                logger.warning(f"Erreur ouverture image [{courrier_id}]: {e}")

        if img is not None:
            try:
                from PIL import Image
                if img.mode not in ('RGB', 'L'):
                    img = img.convert('RGB')
                img.thumbnail((400, 400), Image.LANCZOS)
                buf = io.BytesIO()
                img.save(buf, format='JPEG', quality=82, optimize=True)
                buf.seek(0)
                slug = re.sub(r'[^\w\-]', '_', courrier.reference or str(courrier_id))
                filename = f"thumb_{slug}.jpg"
                courrier.thumbnail.save(filename, ContentFile(buf.read()), save=True)
                logger.info(f"Miniature générée pour courrier {courrier_id}")
            except ImportError:
                logger.warning("Pillow non installé — miniature ignorée")

    except Exception as exc:
        logger.error(f"generate_thumbnail_task error [{courrier_id}]: {exc}")
        raise self.retry(exc=exc)


# ─── Tâche 2 : OCR ───────────────────────────────────────────────────────────

@shared_task(bind=True, max_retries=2, name='core.tasks_courrier.extract_ocr_text_task')
def extract_ocr_text_task(self, courrier_id):
    """Extrait le texte du fichier joint (pdfplumber puis Tesseract en fallback)."""
    try:
        from core.models import Courrier
        try:
            courrier = Courrier.objects.get(pk=courrier_id)
        except Courrier.DoesNotExist:
            return

        if not courrier.fichier_joint:
            return

        file_path = courrier.fichier_joint.path
        ext = os.path.splitext(file_path)[1].lower()
        ocr_text = ''

        if ext == '.pdf':
            # Tentative 1 : pdfplumber (PDF textuel, rapide, sans OCR)
            try:
                import pdfplumber
                with pdfplumber.open(file_path) as pdf:
                    pages_text = []
                    for page in pdf.pages[:5]:
                        t = page.extract_text()
                        if t:
                            pages_text.append(t)
                    ocr_text = '\n\n'.join(pages_text).strip()
            except ImportError:
                pass
            except Exception as e:
                logger.warning(f"pdfplumber error [{courrier_id}]: {e}")

            # Tentative 2 : Tesseract (PDF scanné / image)
            if not ocr_text:
                try:
                    import pytesseract
                    from pdf2image import convert_from_path
                    pages = convert_from_path(file_path, first_page=1, last_page=3, dpi=200)
                    texts = [pytesseract.image_to_string(p, lang='fra+eng') for p in pages]
                    ocr_text = '\n\n'.join(texts).strip()
                except ImportError:
                    logger.warning("pytesseract/pdf2image non installé — OCR PDF ignoré")
                except Exception as e:
                    logger.warning(f"Tesseract PDF error [{courrier_id}]: {e}")

        elif ext in ('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff'):
            try:
                import pytesseract
                from PIL import Image
                img = Image.open(file_path)
                ocr_text = pytesseract.image_to_string(img, lang='fra+eng').strip()
            except ImportError:
                logger.warning("pytesseract non installé — OCR image ignoré")
            except Exception as e:
                logger.warning(f"Tesseract image error [{courrier_id}]: {e}")

        if ocr_text:
            Courrier.objects.filter(pk=courrier_id).update(ocr_text=ocr_text)
            logger.info(f"OCR extrait {len(ocr_text)} caractères pour courrier {courrier_id}")

    except Exception as exc:
        logger.error(f"extract_ocr_text_task error [{courrier_id}]: {exc}")
        raise self.retry(exc=exc)


# ─── Tâche 3 : Analyse IA ────────────────────────────────────────────────────

@shared_task(bind=True, max_retries=2, name='core.tasks_courrier.analyze_courrier_ia_task')
def analyze_courrier_ia_task(self, courrier_id):
    """Produit : résumé, mots-clés, thème, service proposé, niveau d'urgence."""
    try:
        from core.models import Courrier
        from django.conf import settings

        try:
            courrier = Courrier.objects.get(pk=courrier_id)
        except Courrier.DoesNotExist:
            return

        corpus = ' '.join(filter(None, [
            courrier.ocr_text or '',
            courrier.objet or '',
            courrier.expediteur or '',
        ]))

        if not corpus.strip():
            Courrier.objects.filter(pk=courrier_id).update(traitement_statut='termine')
            return

        openai_key = getattr(settings, 'OPENAI_API_KEY', None)
        if openai_key:
            result = _analyze_with_openai(corpus, courrier.objet or '', openai_key)
        else:
            result = _analyze_heuristic(corpus, courrier.objet or '')

        Courrier.objects.filter(pk=courrier_id).update(
            resume_ia=result.get('resume', ''),
            mots_cles=result.get('mots_cles', []),
            theme=result.get('theme', ''),
            service_propose=result.get('service_propose', ''),
            niveau_urgence=result.get('niveau_urgence', 'normal'),
            traitement_statut='termine',
        )
        logger.info(f"Analyse IA terminée pour courrier {courrier_id} — urgence={result.get('niveau_urgence')}")

    except Exception as exc:
        logger.error(f"analyze_courrier_ia_task error [{courrier_id}]: {exc}")
        try:
            from core.models import Courrier
            Courrier.objects.filter(pk=courrier_id).update(traitement_statut='erreur')
        except Exception:
            pass
        raise self.retry(exc=exc)


# ─── Analyse heuristique (sans API externe) ───────────────────────────────────

STOPWORDS_FR = {
    'le', 'la', 'les', 'de', 'du', 'des', 'un', 'une', 'et', 'en', 'à', 'au', 'aux',
    'ce', 'se', 'sa', 'son', 'ses', 'est', 'par', 'pour', 'sur', 'dans', 'que', 'qui',
    'il', 'elle', 'nous', 'vous', 'ils', 'elles', 'on', 'je', 'tu', 'ou', 'pas', 'ne',
    'plus', 'avec', 'tout', 'être', 'avoir', 'faire', 'très', 'bien', 'aussi', 'même',
    'cette', 'cet', 'ces', 'leur', 'leurs', 'dont', 'mais', 'donc', 'car', 'alors',
    'comme', 'quand', 'sous', 'entre', 'vers', 'chez', 'votre', 'notre', 'après',
}

THEMES_MAP = {
    'Formation':      ['formation', 'apprentissage', 'stage', 'séminaire', 'atelier', 'concours', 'bourse'],
    'Finance':        ['budget', 'financement', 'trésorerie', 'comptabilité', 'paiement', 'facture', 'remboursement', 'crédit'],
    'Personnel':      ['personnel', 'recrutement', 'nomination', 'mutation', 'congé', 'absence', 'affectation', 'retraite'],
    'Juridique':      ['contrat', 'marché', 'juridique', 'contentieux', 'décision', 'arrêté', 'loi', 'décret'],
    'Infrastructure': ['travaux', 'construction', 'bâtiment', 'réhabilitation', 'équipement', 'infrastructure'],
    'Partenariat':    ['partenariat', 'coopération', 'accord', 'convention', 'protocole', 'mou'],
    'Administratif':  ['réunion', 'ordre du jour', 'convocation', 'procès-verbal', 'rapport', 'note'],
}

URGENCE_MAP = [
    ('critique', ['très urgent', 'extrêmement urgent', 'critique', 'immédiat', 'sans délai', 'immédiatement']),
    ('haute',    ['urgent', 'dès que possible', "d'urgence", 'prioritaire', 'délai court', 'rapide']),
    ('faible',   ['pour information', 'à votre convenance', 'pour archivage', 'classement', 'pour mémoire']),
]


def _analyze_heuristic(text, objet=''):
    text_lower = (text + ' ' + objet).lower()

    # Urgence
    niveau_urgence = 'normal'
    for niveau, keywords in URGENCE_MAP:
        if any(kw in text_lower for kw in keywords):
            niveau_urgence = niveau
            break

    # Thème
    theme = 'Général'
    best_count = 0
    for t, keywords in THEMES_MAP.items():
        count = sum(1 for kw in keywords if kw in text_lower)
        if count > best_count:
            best_count = count
            theme = t

    # Mots-clés
    words = re.findall(r'\b[a-zàâéèêëîïôùûüç]{4,}\b', text_lower)
    word_counts = Counter(w for w in words if w not in STOPWORDS_FR)
    mots_cles = [w for w, _ in word_counts.most_common(10)]

    # Résumé (3 premières phrases significatives)
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    meaningful = [s.strip() for s in sentences if len(s.strip()) > 30][:3]
    resume = '. '.join(meaningful)
    if len(resume) > 600:
        resume = resume[:597] + '…'

    return {
        'resume': resume,
        'mots_cles': mots_cles,
        'theme': theme,
        'service_propose': '',
        'niveau_urgence': niveau_urgence,
    }


def _analyze_with_openai(text, objet, api_key):
    try:
        import json
        import openai
        openai.api_key = api_key

        prompt = (
            "Analyse ce courrier administratif et réponds uniquement en JSON valide :\n"
            '{"resume":"2-3 phrases","mots_cles":["mot1","mot2"],'
            '"theme":"Formation|Finance|Personnel|Juridique|Infrastructure|Partenariat|Administratif|Général",'
            '"service_propose":"service ou direction concerné",'
            '"niveau_urgence":"faible|normal|haute|critique"}\n\n'
            f"Objet: {objet}\nContenu:\n{text[:3000]}"
        )

        response = openai.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0,
            max_tokens=400,
        )
        content = response.choices[0].message.content.strip()
        # Nettoyer les blocs markdown éventuels
        content = re.sub(r'^```json\s*|\s*```$', '', content).strip()
        return json.loads(content)

    except Exception as e:
        logger.warning(f"OpenAI analysis failed: {e} — fallback heuristique")
        return _analyze_heuristic(text, objet)
