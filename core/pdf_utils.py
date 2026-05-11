from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from django.http import HttpResponse
from io import BytesIO
import datetime
import os
import base64
from django.conf import settings


def _armoirie_image(max_width_cm=3.0, max_height_cm=3.0):
    """Retourne un objet Image reportlab de l'armoirie à partir d'un base64.
    La chaîne base64 doit être fournie via settings.ARMOIRIE_BASE64 ou la variable d'environnement ARMOIRIE_BASE64.
    Supporte un data URL (data:image/...;base64,XXXXX) ou un base64 pur.
    """
    b64 = getattr(settings, 'ARMOIRIE_BASE64', None) or os.environ.get('ARMOIRIE_BASE64')
    if not b64:
        return None
    try:
        # Si data URL, extraire la partie après la virgule
        if ',' in b64 and b64.strip().lower().startswith('data:'):
            b64 = b64.split(',', 1)[1]
        raw = base64.b64decode(b64)
        bio = BytesIO(raw)
        img = Image(bio)
        # Redimensionner en gardant les proportions dans une boîte max_width_cm x max_height_cm
        max_w = max_width_cm * cm
        max_h = max_height_cm * cm
        iw, ih = img.wrap(0, 0)
        if iw and ih:
            scale = min(max_w / iw, max_h / ih)
            img._restrictSize(max_w, max_h)
            img.drawWidth = iw * scale
            img.drawHeight = ih * scale
        return img
    except Exception:
        # En cas d'erreur de décodage, ne rien afficher plutôt que de planter
        return None


def generate_conge_pdf(demande_conge):
    """Génère un PDF pour une demande de congé basé sur le formulaire officiel DRENA Abidjan 3"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1.5*cm, leftMargin=1.5*cm, 
                           topMargin=1*cm, bottomMargin=1*cm)
    
    # Styles
    styles = getSampleStyleSheet()
    
    # Style pour l'en-tête ministère
    ministry_style = ParagraphStyle(
        'MinistryStyle',
        parent=styles['Normal'],
        fontSize=10,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
        spaceAfter=5
    )
    
    # Style pour le titre principal
    main_title_style = ParagraphStyle(
        'MainTitle',
        parent=styles['Heading1'],
        fontSize=16,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
        spaceAfter=20,
        spaceBefore=10,
        borderWidth=2,
        borderColor=colors.orange,
        borderPadding=10,
        backColor=colors.white
    )
    
    # Style pour les textes normaux
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=8,
        alignment=TA_LEFT
    )
    
    # Style pour les signatures
    signature_style = ParagraphStyle(
        'Signature',
        parent=styles['Normal'],
        fontSize=10,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
        spaceAfter=5
    )
    
    # Contenu du document
    story = []
    
    # En-tête avec logo et informations officielles
    logo_el = _armoirie_image(max_width_cm=3.0, max_height_cm=3.0) or Spacer(1, 10)
    header_data = [
        [
            # Colonne gauche - Ministère
            Paragraph("MINISTÈRE DE L'ÉDUCATION NATIONALE<br/>ET DE L'ALPHABÉTISATION<br/>------------------------<br/>DIRECTION RÉGIONALE ABIDJAN 3", ministry_style),
            # Colonne centre - Armoirie
            logo_el,
            # Colonne droite - République
            Paragraph("RÉPUBLIQUE DE CÔTE D'IVOIRE<br/><br/>Union-Discipline-Travail", ministry_style)
        ]
    ]
    
    header_table = Table(header_data, colWidths=[6*cm, 3*cm, 6*cm])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('ALIGN', (2, 0), (2, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    story.append(header_table)
    story.append(Spacer(1, 15))
    
    # Référence
    ref_text = "Réf : ......................../MENA/DRENA/ABJ 3/RH"
    story.append(Paragraph(ref_text, normal_style))
    story.append(Spacer(1, 20))
    
    # Titre principal encadré
    story.append(Paragraph("DEMANDE DE CONGÉ ANNUEL INDIVIDUEL", main_title_style))
    story.append(Spacer(1, 20))
    
    # Autorisation du directeur
    directeur_nom = "COULIBALY Apa Patrice"  # Valeur par défaut
    if hasattr(demande_conge, 'directeur') and demande_conge.directeur:
        directeur_nom = f"{demande_conge.directeur.first_name} {demande_conge.directeur.last_name}".upper()
    elif hasattr(demande_conge, 'superieur') and demande_conge.superieur:
        directeur_nom = f"{demande_conge.superieur.first_name} {demande_conge.superieur.last_name}".upper()
    
    directeur_text = f"Je soussigné, <b>{directeur_nom}</b>, Directeur Régional de l'Éducation Nationale et l'Alphabétisation Abidjan 3, autorise"
    story.append(Paragraph(directeur_text, normal_style))
    story.append(Spacer(1, 15))
    
    # Informations de l'agent
    agent_info = f"""
    M<sup>me/M</sup> : <b>{demande_conge.demandeur.first_name} {demande_conge.demandeur.last_name}</b><br/>
    <br/>
    Matricule : <b>{getattr(demande_conge, 'matricule', 'Non renseigné')}</b><br/>
    <br/>
    Emploi : <b>{getattr(demande_conge, 'emploi', 'Non renseigné')}</b><br/>
    <br/>
    Fonction : <b>{getattr(demande_conge, 'fonction', 'Non renseigné')}</b><br/>
    <br/>
    Service : <b>{demande_conge.demandeur.profile.service.nom if hasattr(demande_conge.demandeur, 'profile') and demande_conge.demandeur.profile.service else 'N/A'}</b><br/>
    """
    
    story.append(Paragraph(agent_info, normal_style))
    story.append(Spacer(1, 15))
    
    # Période de congé
    date_debut = demande_conge.date_debut.strftime('%d/%m/%Y')
    date_fin = demande_conge.date_fin.strftime('%d/%m/%Y')
    
    conge_periode = f"à bénéficier d'un congé du <b>{date_debut}</b> au <b>{date_fin}</b>"
    story.append(Paragraph(conge_periode, normal_style))
    story.append(Spacer(1, 10))
    
    # Reprise de service
    date_reprise = (demande_conge.date_fin + datetime.timedelta(days=1)).strftime('%d/%m/%Y')
    reprise_text = f"L'intéressé(e) reprendra service le <b>{date_reprise}</b> à 7h30mn."
    story.append(Paragraph(reprise_text, normal_style))
    story.append(Spacer(1, 10))
    
    # Intérim
    interim_text = "Pendant son absence, l'intérim sera assuré par................................................................."
    story.append(Paragraph(interim_text, normal_style))
    story.append(Spacer(1, 30))
    
    # Date et lieu
    date_actuelle = datetime.datetime.now().strftime('%d/%m/%Y')
    lieu_date = f"Fait à Abidjan, le {date_actuelle}"
    story.append(Paragraph(lieu_date, normal_style))
    story.append(Spacer(1, 30))
    
    # Tableau des signatures - 2 colonnes, 2 lignes
    signature_data = [
        [Paragraph("Signature de l'intéressé(e)", signature_style),
         Paragraph("Décision du Directeur", signature_style)],
        ["", ""]
    ]
    
    signature_table = Table(signature_data, colWidths=[9*cm, 9*cm], rowHeights=[1*cm, 4*cm])
    signature_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
        ('VALIGN', (0, 1), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
    ]))
    
    story.append(signature_table)
    # Pied de page avec contact
    footer_text = "DRENA ABIDJAN3-21 BP 4389 ABIDJAN 21- Tél: 27235118/ 27231912 E-mail: abidjan3dren@yahoo.fr / drenaabidjan3@gmail.com"
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        alignment=TA_CENTER,
        textColor=colors.grey
    )
    story.append(Paragraph(footer_text, footer_style))
    
    # Construction du PDF
    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_absence_pdf(demande_absence):
    """Génère un PDF pour une demande d'absence basé sur le formulaire officiel DRENA Abidjan 3"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1.5*cm, leftMargin=1.5*cm, 
                           topMargin=1*cm, bottomMargin=1*cm)
    
    # Styles
    styles = getSampleStyleSheet()
    
    # Style pour l'en-tête ministère
    ministry_style = ParagraphStyle(
        'MinistryStyle',
        parent=styles['Normal'],
        fontSize=10,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
        spaceAfter=5
    )
    
    # Style pour le titre principal
    main_title_style = ParagraphStyle(
        'MainTitle',
        parent=styles['Heading1'],
        fontSize=16,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
        spaceAfter=20,
        spaceBefore=10,
        borderWidth=2,
        borderColor=colors.red,
        borderPadding=10,
        backColor=colors.white
    )
    
    # Style pour les textes normaux
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=8,
        alignment=TA_LEFT
    )
    
    # Style pour les signatures
    signature_style = ParagraphStyle(
        'Signature',
        parent=styles['Normal'],
        fontSize=10,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
        spaceAfter=5
    )
    
    # Contenu du document
    story = []
    
    # En-tête avec logo et informations officielles
    logo_el = _armoirie_image(max_width_cm=3.0, max_height_cm=3.0) or Spacer(1, 10)
    header_data = [
        [
            # Colonne gauche - Ministère
            Paragraph("MINISTÈRE DE L'ÉDUCATION NATIONALE<br/>ET DE L'ALPHABÉTISATION<br/>------------------------<br/>DIRECTION RÉGIONALE ABIDJAN 3", ministry_style),
            # Colonne centre - Armoirie
            logo_el,
            # Colonne droite - République
            Paragraph("RÉPUBLIQUE DE CÔTE D'IVOIRE<br/><br/>Union-Discipline-Travail", ministry_style)
        ]
    ]
    
    header_table = Table(header_data, colWidths=[6*cm, 3*cm, 6*cm])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('ALIGN', (2, 0), (2, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    story.append(header_table)
    story.append(Spacer(1, 15))
    
    # Référence
    ref_text = "Réf : ......................../MENA/DRENA/ABJ 3/RH"
    story.append(Paragraph(ref_text, normal_style))
    story.append(Spacer(1, 20))
    
    # Titre principal encadré
    story.append(Paragraph("DEMANDE D'AUTORISATION D'ABSENCE", main_title_style))
    story.append(Spacer(1, 20))
    
    # Autorisation du directeur
    directeur_nom = "COULIBALY Apa Patrice"  # Valeur par défaut
    if hasattr(demande_absence, 'directeur') and demande_absence.directeur:
        directeur_nom = f"{demande_absence.directeur.first_name} {demande_absence.directeur.last_name}".upper()
    elif hasattr(demande_absence, 'superieur') and demande_absence.superieur:
        directeur_nom = f"{demande_absence.superieur.first_name} {demande_absence.superieur.last_name}".upper()
    
    directeur_text = f"Je soussigné, <b>{directeur_nom}</b>, Directeur Régional de l'Éducation Nationale et l'Alphabétisation Abidjan 3, autorise"
    story.append(Paragraph(directeur_text, normal_style))
    story.append(Spacer(1, 15))
    
    # Informations de l'agent
    agent_info = f"""
    M<sup>me/M</sup> : <b>{demande_absence.demandeur.first_name} {demande_absence.demandeur.last_name}</b><br/>
    <br/>
    Matricule : <b>{getattr(demande_absence, 'matricule', 'Non renseigné')}</b><br/>
    <br/>
    Emploi : <b>{getattr(demande_absence, 'emploi', 'Non renseigné')}</b><br/>
    <br/>
    Fonction : <b>{getattr(demande_absence, 'fonction', 'Non renseigné')}</b><br/>
    <br/>
    Service : <b>{demande_absence.demandeur.profile.service.nom if hasattr(demande_absence.demandeur, 'profile') and demande_absence.demandeur.profile.service else 'N/A'}</b><br/>
    """
    
    story.append(Paragraph(agent_info, normal_style))
    story.append(Spacer(1, 15))
    
    # Période d'absence
    date_debut = demande_absence.date_debut.strftime('%d/%m/%Y à %H:%M')
    date_fin = demande_absence.date_fin.strftime('%d/%m/%Y à %H:%M')
    
    # Formatage de la durée
    heures = int(demande_absence.duree_heures)
    minutes = int((demande_absence.duree_heures - heures) * 60)
    duree_str = f"{heures}h{minutes:02d}min" if minutes > 0 else f"{heures}h"
    
    absence_periode = f"à bénéficier d'une <b>autorisation d'absence</b> du <b>{date_debut}</b> au <b>{date_fin}</b> (Durée: <b>{duree_str}</b>)"
    story.append(Paragraph(absence_periode, normal_style))
    story.append(Spacer(1, 10))
    
    # Motif
    if demande_absence.motif:
        motif_text = f"<b>Motif :</b> {demande_absence.motif}"
        story.append(Paragraph(motif_text, normal_style))
        story.append(Spacer(1, 10))
    
    # Date et lieu
    date_actuelle = datetime.datetime.now().strftime('%d/%m/%Y')
    lieu_date = f"Fait à Abidjan, le {date_actuelle}"
    story.append(Paragraph(lieu_date, normal_style))
    story.append(Spacer(1, 30))
    
    # Tableau des signatures - 2 colonnes, 2 lignes
    signature_data = [
        [Paragraph("Signature de l'intéressé(e)", signature_style),
         Paragraph("Décision du Directeur", signature_style)],
        ["", ""]
    ]
    
    signature_table = Table(signature_data, colWidths=[9*cm, 9*cm], rowHeights=[1*cm, 4*cm])
    signature_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
        ('VALIGN', (0, 1), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
    ]))
    
    story.append(signature_table)
    # Pied de page avec contact
    footer_text = "DRENA ABIDJAN3-21 BP 4389 ABIDJAN 21- Tél: 27235118/ 27231912 E-mail: abidjan3dren@yahoo.fr / drenaabidjan3@gmail.com"
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        alignment=TA_CENTER,
        textColor=colors.grey
    )
    story.append(Paragraph(footer_text, footer_style))
    
    # Construction du PDF
    doc.build(story)
    buffer.seek(0)
    return buffer


def create_pdf_response(buffer, filename):
    """Crée une réponse HTTP avec le PDF"""
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def generate_attestation_pdf(demande):
    """Génère un PDF d'attestation (travail ou présence) pour une demande."""
    from .models import FicheAgent
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Title'], fontSize=16, spaceAfter=6, alignment=TA_CENTER, fontName='Helvetica-Bold')
    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=11, spaceAfter=4, alignment=TA_CENTER, fontName='Helvetica')
    label_style = ParagraphStyle('Label', parent=styles['Normal'], fontSize=10, fontName='Helvetica-Bold')
    value_style = ParagraphStyle('Value', parent=styles['Normal'], fontSize=10)
    center_style = ParagraphStyle('Center', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER)

    agent = demande.agent
    profile = getattr(agent, 'profile', None)

    # Récupérer la fiche agent si elle existe
    fiche = FicheAgent.objects.filter(user=agent).first() if agent else None

    nom = (fiche.nom if fiche else agent.last_name) or ''
    prenoms = (fiche.prenoms if fiche else agent.first_name) or ''
    matricule = (fiche.matricule if fiche else getattr(profile, 'matricule', '')) or ''
    grade = (fiche.grade if fiche else '') or ''
    emploi = (fiche.emploi if fiche else '') or ''
    fonction = (fiche.fonction if fiche else '') or ''
    date_prise = fiche.date_prise_service if fiche and fiche.date_prise_service else None

    direction_nom = ''
    sous_direction_nom = ''
    service_nom = ''

    if fiche:
        direction_nom = fiche.direction.nom if fiche.direction else ''
        sous_direction_nom = fiche.sous_direction.nom if fiche.sous_direction else ''
        service_nom = fiche.service.nom if fiche.service else ''
    elif profile:
        if profile.direction:
            direction_nom = profile.direction.nom
        if profile.sous_direction:
            sous_direction_nom = profile.sous_direction.nom
        if profile.service:
            service_nom = profile.service.nom

    type_label = demande.get_type_attestation_display()
    today = datetime.date.today()
    numero = demande.numero_attestation or f"ATT-{today.year}-{demande.pk:06d}"

    story = []

    # En-tête armoirie
    armoirie = _armoirie_image(3.0, 3.0)
    if armoirie:
        story.append(armoirie)
        story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("RÉPUBLIQUE DE CÔTE D'IVOIRE", subtitle_style))
    story.append(Paragraph("Union – Discipline – Travail", subtitle_style))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(type_label.upper(), title_style))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(f"N° {numero}", center_style))
    story.append(Spacer(1, 0.8*cm))

    # Corps
    infos = [
        ('Nom et Prénoms', f"{nom} {prenoms}".strip()),
        ('Matricule', matricule),
        ('Grade', grade),
        ('Emploi', emploi),
        ('Fonction', fonction),
        ('Direction', direction_nom),
        ('Sous-Direction', sous_direction_nom),
        ('Service', service_nom),
        ('Date de prise de service', date_prise.strftime('%d/%m/%Y') if date_prise else ''),
    ]

    table_data = [[Paragraph(l, label_style), Paragraph(v or '—', value_style)] for l, v in infos]
    table = Table(table_data, colWidths=[6*cm, 11*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#FFF3E0')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#E65100')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E0E0E0')),
        ('ROWBACKGROUNDS', (1, 0), (1, -1), [colors.white, colors.HexColor('#FAFAFA')]),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(table)
    story.append(Spacer(1, 1*cm))

    # Texte d'attestation
    if demande.type_attestation == 'travail':
        texte = (
            f"Je soussigné(e), certifie que <b>{nom} {prenoms}</b>, Matricule <b>{matricule}</b>, "
            f"occupe le poste de <b>{emploi or 'Agent'}</b> au sein de notre structure "
            f"depuis le <b>{date_prise.strftime('%d/%m/%Y') if date_prise else '...'}</b>. "
            f"La présente attestation est délivrée pour servir et valoir ce que de droit."
        )
    else:
        texte = (
            f"Je soussigné(e), certifie que <b>{nom} {prenoms}</b>, Matricule <b>{matricule}</b>, "
            f"est bien présent(e) et en activité au sein de notre structure. "
            f"La présente attestation de présence est délivrée pour servir et valoir ce que de droit."
        )

    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=11, leading=18, spaceAfter=12)
    story.append(Paragraph(texte, body_style))
    story.append(Spacer(1, 1.5*cm))

    # Signature
    story.append(Paragraph(f"Fait à ................, le {today.strftime('%d/%m/%Y')}", center_style))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("Le Responsable RH", center_style))
    story.append(Spacer(1, 2*cm))
    story.append(Paragraph("Signature et cachet", center_style))

    doc.build(story)
    return buffer.getvalue()
