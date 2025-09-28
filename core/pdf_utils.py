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
    header_data = [
        [
            # Colonne gauche - Ministère
            Paragraph("MINISTÈRE DE L'ÉDUCATION NATIONALE<br/>ET DE L'ALPHABÉTISATION<br/>------------------------<br/>DIRECTION RÉGIONALE ABIDJAN 3", ministry_style),
            # Colonne centre - Logo (placeholder)
            Paragraph("🇨🇮", ParagraphStyle('Logo', parent=styles['Normal'], fontSize=30, alignment=TA_CENTER)),
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
    header_data = [
        [
            # Colonne gauche - Ministère
            Paragraph("MINISTÈRE DE L'ÉDUCATION NATIONALE<br/>ET DE L'ALPHABÉTISATION<br/>------------------------<br/>DIRECTION RÉGIONALE ABIDJAN 3", ministry_style),
            # Colonne centre - Logo (placeholder)
            Paragraph("🇨🇮", ParagraphStyle('Logo', parent=styles['Normal'], fontSize=30, alignment=TA_CENTER)),
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
