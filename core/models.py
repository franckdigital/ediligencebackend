from django.db import models
from django.contrib.auth.models import User

from django.utils import timezone

class ImputationFile(models.Model):
    MODE_CHOICES = [
        ('lecture_seule', 'Lecture seule'),
        ('intervenant', 'Intervenant'),
    ]
    diligence = models.ForeignKey('Diligence', on_delete=models.CASCADE, related_name='imputation_files')
    agent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='imputation_files')
    file = models.FileField(upload_to='imputation_files/', null=True, blank=True)
    sfdt_content = models.TextField(null=True, blank=True, help_text="Contenu du document Word au format Syncfusion SFDT")
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default='lecture_seule')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='imputation_files_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.diligence} - {self.agent} ({self.mode})"

class Direction(models.Model):
    """Une Direction est une entité qui regroupe plusieurs services.
    Par exemple: Direction des Ressources Humaines, Direction Financière, etc."""
    nom = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Direction'
        verbose_name_plural = 'Directions'
        ordering = ['nom']

    def __str__(self):
        return self.nom
    
    @property
    def nombre_services(self):
        """Retourne le nombre de services dans cette direction"""
        return self.services.count()

    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = timezone.now()
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)

class Service(models.Model):
    """Un Service est une unité qui appartient à une Direction.
    Par exemple: Service Paie (Direction RH), Service Comptabilité (Direction Financière)"""
    nom = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    direction = models.ForeignKey(
        Direction,
        on_delete=models.CASCADE,  # Si une direction est supprimée, ses services le sont aussi
        related_name='services',
        help_text='La direction à laquelle ce service appartient',
        null=True,  # Temporairement nullable pour la migration
        blank=True
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        verbose_name = 'Service'
        verbose_name_plural = 'Services'
        ordering = ['direction__nom', 'nom']  # Trié par direction puis par nom de service
        unique_together = ['nom', 'direction']  # Un nom de service doit être unique dans une direction
    
    def __str__(self):
        return f"{self.nom} ({self.direction.nom})"

    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = timezone.now()
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)

import secrets

import secrets

class UserProfile(models.Model):
    empreinte_hash = models.CharField(max_length=255, blank=True, null=True, help_text="Hash de l'empreinte digitale de l'utilisateur")
    ROLE_CHOICES = [
        ('ADMIN', 'Admin'),
        ('DIRECTEUR', 'Directeur'),  # Peut voir toutes les diligences de sa direction
        ('SUPERIEUR', 'Superieur'),  # Peut voir les diligences de son service
        ('AGENT', 'Agent'),          # Peut voir ses propres diligences
        ('SECRETAIRE', 'Secretaire'),# Peut voir les diligences de son service
        ('PRESTATAIRE', 'Prestataire'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    matricule = models.CharField(max_length=64, blank=True, null=True)
    telephone = models.CharField(max_length=32, unique=True, blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='AGENT')
    service = models.ForeignKey(
        Service,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        help_text='Le service auquel l\'utilisateur est rattaché'
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = timezone.now()
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Profil utilisateur'
        verbose_name_plural = 'Profils utilisateurs'

    def __str__(self):
        service_info = f" - {self.service}" if self.service else ""
        return f"{self.user.username} ({self.get_role_display()}){service_info}"

    @property
    def direction(self):
        """Retourne la direction de l'utilisateur via son service"""
        return self.service.direction if self.service else None
    
    def __str__(self):
        return f"{self.user.username} - {self.role}"

class Courrier(models.Model):
    TYPE_CHOICES = [
        ('ordinaire', 'Ordinaire'),
        ('confidentiel', 'Confidentiel'),
    ]
    
    SENS_CHOICES = [
        ('arrivee', 'Arrivée'),
        ('depart', 'Départ'),
    ]
    
    CATEGORIE_CHOICES = [
        ('Demande', 'Demande'),
        ('Invitation', 'Invitation'),
        ('Réclamation', 'Réclamation'),
        ('Autre', 'Autre'),
    ]

    reference = models.CharField(max_length=255, unique=True)
    expediteur = models.CharField(max_length=255)
    destinataire = models.CharField(max_length=255, null=True, blank=True)
    objet = models.TextField()
    date_reception = models.DateField()
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True, related_name='courriers')
    categorie = models.CharField(max_length=64, choices=CATEGORIE_CHOICES, default='Demande')
    type_courrier = models.CharField(max_length=20, choices=TYPE_CHOICES, default='ordinaire')
    sens = models.CharField(max_length=20, choices=SENS_CHOICES, default='arrivee')
    fichier_joint = models.FileField(upload_to='courriers/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.reference} - {self.objet}"

class CourrierAccess(models.Model):
    """Modèle pour gérer l'accès aux courriers confidentiels"""
    courrier = models.ForeignKey(Courrier, on_delete=models.CASCADE, related_name='access_permissions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courrier_access')
    granted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='granted_courrier_access')
    granted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('courrier', 'user')
        verbose_name = 'Accès Courrier'
        verbose_name_plural = 'Accès Courriers'
    
    def __str__(self):
        return f"Accès {self.courrier.reference} pour {self.user.username}"

class CourrierImputation(models.Model):
    """Modèle pour l'imputation des courriers confidentiels basé sur ImputationAccess"""
    ACCESS_TYPE_CHOICES = [
        ('view', 'Lecture'),
        ('edit', 'Édition'),
    ]
    courrier = models.ForeignKey(Courrier, on_delete=models.CASCADE, related_name='imputation_access')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courrier_imputation_access')
    access_type = models.CharField(max_length=10, choices=ACCESS_TYPE_CHOICES, default='view')
    granted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='granted_courrier_imputation')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('courrier', 'user', 'access_type')
        verbose_name = 'Imputation Courrier'
        verbose_name_plural = 'Imputations Courriers'

    def __str__(self):
        return f"{self.user.username} - {self.courrier.reference} ({self.access_type})"

class Diligence(models.Model):
    TYPE_CHOICES = [
        ('courrier', 'Basée sur courrier'),
        ('spontanee', 'Spontanée'),
    ]
    
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('en_cours', 'En cours de traitement'),
        ('en_correction', 'Demande de correction'),
        ('demande_validation', 'Demande de validation'),
        ('termine', 'Terminé'),
        ('archivee', 'Archivée'),
    ]
    
    CATEGORIE_CHOICES = [
        ('URGENT', 'Urgent'),
        ('NORMAL', 'Normal'),
        ('BASSE', 'Basse priorité')
    ]
    
    DOMAINE_CHOICES = [
        ('representations', 'Représentations'),
        ('projet_x', 'Projet X'),
        ('projet_y', 'Projet Y'),
        ('atelier', 'Atelier'),
        ('evenements', 'Événements'),
        ('formation', 'Formation'),
        ('communication', 'Communication'),
        ('logistique', 'Logistique'),
        ('budget', 'Budget'),
        ('autre', 'Autre'),
    ]
    
    # Type de diligence
    type_diligence = models.CharField(max_length=20, choices=TYPE_CHOICES, default='courrier')
    
    # Référence et courrier associé
    reference_courrier = models.CharField(max_length=255)
    courrier = models.ForeignKey(Courrier, on_delete=models.SET_NULL, null=True, blank=True, related_name='diligences')
    
    # Domaine pour archivage automatique
    domaine = models.CharField(max_length=50, choices=DOMAINE_CHOICES, default='autre')
    
    # Informations de base
    categorie = models.CharField(max_length=64)
    statut = models.CharField(max_length=32, choices=STATUT_CHOICES, default='en_attente')
    
    # Délais d'exécution
    date_limite = models.DateField(blank=True, null=True)
    date_rappel_1 = models.DateField(blank=True, null=True, help_text="Premier rappel avant échéance")
    date_rappel_2 = models.DateField(blank=True, null=True, help_text="Deuxième rappel avant échéance")
    
    # Progression
    pourcentage_avancement = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # Fichiers et documents
    fichier_joint = models.FileField(
        upload_to='diligences/',
        blank=True,
        null=True,
        max_length=500
    )
    
    # Commentaires et instructions
    commentaires = models.TextField(blank=True, null=True)
    commentaires_agents = models.TextField(blank=True, null=True)
    instructions = models.TextField(blank=True, null=True)
    nouvelle_instruction = models.TextField(blank=True, null=True)
    
    # Informations du courrier (si applicable)
    date_reception = models.DateField(blank=True, null=True)
    expediteur = models.CharField(max_length=255, blank=True, null=True)
    objet = models.TextField(blank=True, null=True)
    
    # Relations
    agents = models.ManyToManyField(User, related_name='diligences')
    services_concernes = models.ManyToManyField(Service, related_name='diligences_concernes')
    direction = models.ForeignKey(Direction, on_delete=models.SET_NULL, null=True, blank=True, related_name='diligences')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    archived_at = models.DateTimeField(null=True, blank=True)
    archived_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='diligences_archived')
    validated_at = models.DateTimeField(null=True, blank=True)
    validated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='diligences_validated')

class ImputationAccess(models.Model):
    ACCESS_TYPE_CHOICES = [
        ('view', 'Lecture'),
        ('edit', 'Édition'),
    ]
    diligence = models.ForeignKey('Diligence', on_delete=models.CASCADE, related_name='imputation_access')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='imputation_access')
    access_type = models.CharField(max_length=10, choices=ACCESS_TYPE_CHOICES, default='view')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('diligence', 'user', 'access_type')

    def __str__(self):
        return f"{self.user.username} - {self.diligence} ({self.access_type})"
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    validated_at = models.DateTimeField(null=True, blank=True)
    archived_at = models.DateTimeField(null=True, blank=True)
    archived_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='diligences_archivees'
    )


    def __str__(self):
        return f"{self.reference_courrier} - {self.direction.nom if self.direction else 'Sans direction'}"

    def get_direction(self):
        """Retourne la direction de la diligence, soit directement assignée soit via le service"""
        if self.direction:
            return self.direction
        if self.services_concernes.exists():
            return self.services_concernes.first().direction
        return None

# --- MODÈLE POUR GESTION DES DOCUMENTS DE DILIGENCE ---
class DiligenceDocument(models.Model):
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('en_revision', 'En révision'),
        ('valide', 'Validé'),
        ('archive', 'Archivé'),
    ]
    
    diligence = models.ForeignKey(Diligence, on_delete=models.CASCADE, related_name='documents')
    titre = models.CharField(max_length=255)
    contenu = models.TextField(blank=True, null=True, help_text="Contenu éditable directement dans l'application")
    fichier = models.FileField(upload_to='diligence_documents/', blank=True, null=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='brouillon')
    version = models.PositiveIntegerField(default=1)
    
    # Métadonnées
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    validated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='documents_validated')
    validated_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Document de Diligence'
        verbose_name_plural = 'Documents de Diligence'
    
    def __str__(self):
        return f"{self.titre} - {self.diligence.reference_courrier} (v{self.version})"

# --- MODÈLE POUR NOTIFICATIONS ---
class DiligenceNotification(models.Model):
    TYPE_CHOICES = [
        ('rappel_delai', 'Rappel de délai'),
        ('nouvelle_diligence', 'Nouvelle diligence'),
        ('validation_requise', 'Validation requise'),
        ('document_valide', 'Document validé'),
        ('diligence_archivee', 'Diligence archivée'),
        ('conges_validation', 'Validation de congé'),
        ('conges_rejet', 'Rejet de congé'),
        ('absences_validation', 'Validation d\'absence'),
        ('absences_rejet', 'Rejet d\'absence'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='diligence_notifications')
    diligence = models.ForeignKey(Diligence, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    type_notification = models.CharField(max_length=30, choices=TYPE_CHOICES)
    message = models.TextField()
    lien = models.CharField(max_length=255, blank=True, default='')
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification de Diligence'
        verbose_name_plural = 'Notifications de Diligence'
    
    def __str__(self):
        return f"{self.get_type_notification_display()} - {self.user.username}"

class Notification(models.Model):
    TYPES_NOTIF = [
        ('demande_approuvee', 'Demande approuvée'),
        ('demande_rejetee', 'Demande rejetée'),
        ('nouvelle_demande', 'Nouvelle demande'),
        ('rappel', 'Rappel'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type_notif = models.CharField(max_length=30, choices=TYPES_NOTIF, default='nouvelle_demande')
    contenu = models.TextField(blank=True, null=True)
    message = models.TextField(blank=True, null=True)  # Pour compatibilité
    lien = models.CharField(max_length=255, blank=True, null=True)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
    
    def __str__(self):
        return f"{self.get_type_notif_display()} - {self.user.username} - {self.created_at.strftime('%d/%m/%Y %H:%M')}"

class Observation(models.Model):
    diligence = models.ForeignKey(Diligence, on_delete=models.CASCADE)
    auteur = models.ForeignKey(User, on_delete=models.CASCADE)
    texte = models.TextField()
    date_observation = models.DateTimeField(auto_now_add=True)

class Evenement(models.Model):
    titre = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    lieu = models.CharField(max_length=255)
    date_debut = models.DateField()
    date_fin = models.DateField()
    organisateur = models.ForeignKey(User, on_delete=models.CASCADE)
    statut = models.CharField(max_length=64)

class EtapeEvenement(models.Model):
    evenement = models.ForeignKey(Evenement, on_delete=models.CASCADE)
    nom_etape = models.CharField(max_length=255)
    responsable = models.ForeignKey(User, on_delete=models.CASCADE)
    statut = models.CharField(max_length=64)
    date_echeance = models.DateField()

#class Presence(models.Model):
    #evenement = models.ForeignKey(Evenement, on_delete=models.CASCADE)
    #participant = models.CharField(max_length=255)
    #present = models.BooleanField()
    #horodatage = models.DateTimeField(auto_now_add=True)

class Prestataire(models.Model):
    
    secteur_activite = models.CharField(max_length=255)
    zone_geographique = models.CharField(max_length=255)
    email = models.EmailField()
    telephone = models.CharField(max_length=32)
    abonnement_actif = models.BooleanField(default=False)
    profil_complet = models.TextField()
    note_moyenne = models.FloatField(default=0)

class PrestataireEtape(models.Model):
    prestataire = models.ForeignKey(Prestataire, on_delete=models.CASCADE)
    etape = models.ForeignKey(EtapeEvenement, on_delete=models.CASCADE)
    statut = models.CharField(max_length=64)
    commission = models.DecimalField(max_digits=10, decimal_places=2)

class Evaluation(models.Model):
    prestataire = models.ForeignKey(Prestataire, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    note = models.IntegerField()
    commentaire = models.TextField()
    date_evaluation = models.DateTimeField(auto_now_add=True)


# --- MODULE GESTION D'ACTIVITE ---

class Activite(models.Model):
    TYPE_CHOICES = [
        ('atelier', 'Atelier'),
        ('seminaire', 'Séminaire'),
        ('colloque', 'Colloque'),
        ('reunion', 'Réunion'),
        ('ceremonie', 'Cérémonie'),
        ('autre', 'Autre'),
    ]
    
    ETAT_CHOICES = [
        ('planifiee', 'Planifiée'),
        ('en_cours', 'En cours'),
        ('terminee', 'Terminée'),
        ('suspendue', 'Suspendue'),
    ]
    
    nom = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    type_activite = models.CharField(max_length=20, choices=TYPE_CHOICES, default='autre')
    service = models.ForeignKey('Service', on_delete=models.PROTECT, null=True, blank=True)
    responsable_principal = models.ForeignKey(User, related_name='activites_responsable', on_delete=models.SET_NULL, null=True)
    date_debut = models.DateField()
    date_fin_prevue = models.DateField()
    date_fin_effective = models.DateField(blank=True, null=True)
    etat = models.CharField(max_length=20, choices=ETAT_CHOICES, default='planifiee')
    lieu = models.CharField(max_length=255, blank=True, null=True)
    budget_previsionnel = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    nombre_participants_prevu = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nom} ({self.get_type_activite_display()})"

    class Meta:
        verbose_name = "Activité"
        verbose_name_plural = "Activités"

class Domaine(models.Model):
    """Domaines/Commissions pour subdiviser une activité"""
    nom = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    activite = models.ForeignKey(Activite, related_name='domaines', on_delete=models.CASCADE)
    superviseur = models.ForeignKey(User, related_name='domaines_supervises', on_delete=models.SET_NULL, null=True)
    date_debut = models.DateField()
    date_fin_prevue = models.DateField()
    date_fin_effective = models.DateField(blank=True, null=True)
    pourcentage_avancement = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nom} - {self.activite.nom}"

    class Meta:
        verbose_name = "Domaine"
        verbose_name_plural = "Domaines"

# Garder le modèle Projet pour compatibilité (sera migré progressivement)
class Projet(models.Model):
    nom = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    direction = models.ForeignKey('Direction', on_delete=models.PROTECT, null=True, blank=True)
    service = models.ForeignKey('Service', on_delete=models.PROTECT, null=True, blank=True)
    ETAT_CHOICES = [
        ('planifie', 'Planifié'),
        ('en_cours', 'En cours'),
        ('termine', 'Terminé'),
        ('suspendu', 'Suspendu'),
    ]
    dateDebut = models.DateField()
    dateFinPrevue = models.DateField()
    dateFinEffective = models.DateField(blank=True, null=True)
    etat = models.CharField(max_length=20, choices=ETAT_CHOICES, default='planifie')
    responsable = models.ForeignKey(User, related_name='projets_responsable', on_delete=models.SET_NULL, null=True)
    membres = models.ManyToManyField(User, related_name='projets_membre', blank=True)
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nom

class Tache(models.Model):
    # Relations avec les nouveaux modèles
    domaine = models.ForeignKey(Domaine, related_name='taches', on_delete=models.CASCADE, null=True, blank=True)
    # Garder projet pour compatibilité
    projet = models.ForeignKey(Projet, on_delete=models.CASCADE, null=True, blank=True)
    
    titre = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    responsable = models.ForeignKey(User, related_name='taches_responsable', on_delete=models.SET_NULL, null=True)
    
    # Support pour les sous-tâches
    tache_parent = models.ForeignKey('self', related_name='sous_taches', on_delete=models.CASCADE, null=True, blank=True)
    
    ETAT_CHOICES = [
        ('a_faire', 'À faire'),
        ('en_attente', 'En attente'),
        ('en_cours', 'En cours'),
        ('terminee', 'Terminée'),
        ('annulee', 'Annulée'),
    ]
    PRIORITE_CHOICES = [
        ('basse', 'Basse'),
        ('moyenne', 'Moyenne'),
        ('haute', 'Haute'),
    ]
    
    etat = models.CharField(max_length=20, choices=ETAT_CHOICES, default='a_faire')
    priorite = models.CharField(max_length=20, choices=PRIORITE_CHOICES, default='moyenne')
    date_debut = models.DateField(null=True, blank=True)
    date_fin_prevue = models.DateField(null=True, blank=True)
    date_fin_effective = models.DateField(null=True, blank=True)
    pourcentage_avancement = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # Champs pour compatibilité avec l'ancien système
    directeurs = models.ManyToManyField(
        User, related_name='directeurs_taches', blank=True
    )
    superieurs = models.ManyToManyField(
        User, related_name='superieurs_taches', blank=True
    )
    agents = models.ManyToManyField(
        User, related_name='agents_taches', blank=True
    )
    secretaires = models.ManyToManyField(
        User, related_name='secretaires_taches', blank=True
    )
    
    # Champs de dates et timestamps
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        if self.domaine:
            return f"{self.titre} ({self.domaine.nom})"
        elif self.projet:
            return f"{self.titre} ({self.projet.nom})"
        return self.titre
    
    @property
    def is_sous_tache(self):
        return self.tache_parent is not None
    
    def get_niveau_hierarchie(self):
        """Retourne le niveau hiérarchique de la tâche (0=tâche principale, 1=sous-tâche, etc.)"""
        niveau = 0
        parent = self.tache_parent
        while parent:
            niveau += 1
            parent = parent.tache_parent
        return niveau

class Commentaire(models.Model):
    contenu = models.TextField()
    auteur = models.ForeignKey(User, related_name='commentaires', on_delete=models.CASCADE)
    tache = models.ForeignKey(Tache, related_name='commentaires', on_delete=models.CASCADE)
    createdAt = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.auteur.username}: {self.contenu[:30]}..."

class Fichier(models.Model):
    nom = models.CharField(max_length=255)
    url = models.URLField()
    type = models.CharField(max_length=100)
    taille = models.IntegerField()
    tache = models.ForeignKey(Tache, related_name='fichiers', on_delete=models.SET_NULL, null=True, blank=True)
    projet = models.ForeignKey(Projet, related_name='fichiers', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.nom

class TacheHistorique(models.Model):
    tache = models.ForeignKey('Tache', related_name='historiques', on_delete=models.CASCADE)
    utilisateur = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=255)
    details = models.TextField(blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tache} - {self.action} - {self.date.strftime('%Y-%m-%d %H:%M')}"

# --- Modèle Agent (système multi-sites, QR, connexion, etc.) ---
from django.contrib.auth.models import User

from django.core.exceptions import ValidationError

class Bureau(models.Model):
    nom = models.CharField(max_length=255, unique=True, help_text="Nom ou référence du bureau")
    latitude_centre = models.DecimalField(max_digits=22, decimal_places=17, help_text="Latitude du centre du bureau")
    longitude_centre = models.DecimalField(max_digits=22, decimal_places=17, help_text="Longitude du centre du bureau")
    rayon_metres = models.IntegerField(help_text="Rayon de la zone autorisée en mètres")

    def clean(self):
        # Validation avancée : coordonnées uniques
        if Bureau.objects.exclude(pk=self.pk).filter(latitude_centre=self.latitude_centre, longitude_centre=self.longitude_centre).exists():
            raise ValidationError("Un bureau existe déjà à ces coordonnées GPS.")

    def delete(self, *args, **kwargs):
        if self.agent_set.exists():
            raise ValidationError("Ce bureau est encore lié à des agents et ne peut pas être supprimé.")
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.nom

class Agent(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='agent_profile')
    nom = models.CharField(max_length=255)
    prenom = models.CharField(max_length=255, blank=True, null=True)
    telephone = models.CharField(max_length=30, blank=True, null=True)
    matricule = models.CharField(max_length=100, unique=True)
    poste = models.CharField(max_length=100)
    service = models.ForeignKey('Service', on_delete=models.CASCADE, null=True, blank=True, help_text="Service de rattachement")
    bureau = models.ForeignKey('Bureau', on_delete=models.SET_NULL, null=True, blank=True, help_text="Bureau de rattachement de l'agent")
    empreinte_hash = models.TextField(null=True, blank=True, help_text="Hash de l'empreinte digitale de l'agent")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = timezone.now()
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nom} {self.prenom or ''} ({self.poste})"


class Presence(models.Model):
    STATUT_CHOICES = [
        ('présent', 'Présent'),
        ('absent', 'Absent'),
        ('en mission', 'En mission'),
        ('permission accordée', 'Permission accordée'),
    ]
    # id: UUID ou BigAutoField (par défaut)
    agent = models.ForeignKey('Agent', on_delete=models.CASCADE, related_name='presences')
    date_presence = models.DateField()
    heure_arrivee = models.TimeField(null=True, blank=True)
    heure_depart = models.TimeField(null=True, blank=True)
    statut = models.CharField(max_length=32, choices=STATUT_CHOICES)
    # empreinte_hash removed - using simple button presence now
    latitude = models.DecimalField(max_digits=10, decimal_places=6)
    longitude = models.DecimalField(max_digits=10, decimal_places=6)
    localisation_valide = models.BooleanField(default=False)
    commentaire = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Présence'
        verbose_name_plural = 'Présences'
        unique_together = ('agent', 'date_presence')
        ordering = ['-date_presence', '-heure_arrivee']

    def __str__(self):
        return f"{self.agent.username} - {self.date_presence} ({self.statut})"

    def save(self, *args, **kwargs):
        # TODO: Calcul automatique du statut selon la logique métier (voir doc)
        # TODO: Calcul de localisation_valide selon distance GPS
        super().save(*args, **kwargs)

# --- RolePermission for editable roles/permissions ---
class RolePermission(models.Model):
    ROLE_CHOICES = [
        ('ADMIN', 'Admin'),
        ('DIRECTEUR', 'Directeur'),
        ('SUPERIEUR', 'Superieur'),
        ('AGENT', 'Agent'),
        ('SECRETAIRE', 'Secretaire'),
        ('PRESTATAIRE', 'Prestataire'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    permission = models.CharField(max_length=100)
    description = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        unique_together = ('role', 'permission')
        verbose_name = 'Role Permission'
        verbose_name_plural = 'Role Permissions'

    def __str__(self):
        return f"{self.role} - {self.permission}"


class UserDiligenceComment(models.Model):
    """Commentaires spécifiques par utilisateur et par diligence"""
    diligence = models.ForeignKey('Diligence', on_delete=models.CASCADE, related_name='user_comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='diligence_comments')
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('diligence', 'user')
        verbose_name = 'User Diligence Comment'
        verbose_name_plural = 'User Diligence Comments'

    def __str__(self):
        return f"Comment by {self.user.username} on Diligence #{self.diligence.id}"


class UserDiligenceInstruction(models.Model):
    """Instructions spécifiques par utilisateur et par diligence"""
    diligence = models.ForeignKey('Diligence', on_delete=models.CASCADE, related_name='user_instructions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='diligence_instructions')
    instruction = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('diligence', 'user')
        verbose_name = 'User Diligence Instruction'
        verbose_name_plural = 'User Diligence Instructions'

    def __str__(self):
        return f"Instruction by {self.user.username} for Diligence #{self.diligence.id}"


class DemandeConge(models.Model):
    """Modèle pour les demandes de congé des agents"""
    TYPE_CONGE_CHOICES = [
        ('annuel', 'Congé annuel'),
        ('maladie', 'Congé maladie'),
        ('maternite', 'Congé maternité'),
        ('paternite', 'Congé paternité'),
        ('sans_solde', 'Congé sans solde'),
        ('formation', 'Congé formation'),
        ('exceptionnel', 'Congé exceptionnel'),
    ]
    
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('approuve', 'Approuvé'),
        ('rejete', 'Rejeté'),
        ('annule', 'Annulé'),
    ]
    
    demandeur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='demandes_conge')
    
    # Informations personnelles
    matricule = models.CharField(max_length=50, default='', help_text="Matricule de l'agent")
    emploi = models.CharField(max_length=100, default='', help_text="Emploi occupé")
    fonction = models.CharField(max_length=100, default='', help_text="Fonction exercée")
    
    type_conge = models.CharField(max_length=20, choices=TYPE_CONGE_CHOICES)
    date_debut = models.DateField()
    date_fin = models.DateField()
    nombre_jours = models.PositiveIntegerField()
    motif = models.TextField()
    adresse_conge = models.TextField(help_text="Adresse pendant le congé")
    telephone_conge = models.CharField(max_length=20, help_text="Téléphone pendant le congé")
    
    # Validation hiérarchique
    directeur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='conges_directeur', help_text="Directeur sélectionné")
    superieur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='conges_superieur', help_text="Supérieur hiérarchique sélectionné")
    superieur_hierarchique = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='conges_a_valider')
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')
    date_validation = models.DateTimeField(null=True, blank=True)
    commentaire_validation = models.TextField(blank=True, null=True)
    
    # Documents
    document_demande = models.FileField(upload_to='conges/demandes/', null=True, blank=True)
    document_reponse = models.FileField(upload_to='conges/reponses/', null=True, blank=True)
    
    # Agents concernés (même direction/service)
    agents_concernes = models.ManyToManyField(User, blank=True, related_name='conges_concernes', help_text="Agents de la même direction/service informés de ce congé")
    
    # Métadonnées
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Demande de congé'
        verbose_name_plural = 'Demandes de congé'
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"Congé {self.type_conge} - {self.demandeur.username} ({self.date_debut} au {self.date_fin})"
    
    def save(self, *args, **kwargs):
        # Calculer automatiquement le nombre de jours
        if self.date_debut and self.date_fin:
            self.nombre_jours = (self.date_fin - self.date_debut).days + 1
        super().save(*args, **kwargs)


class DemandeAbsence(models.Model):
    """Modèle pour les demandes d'autorisation d'absence"""
    TYPE_ABSENCE_CHOICES = [
        ('personnelle', 'Raison personnelle'),
        ('medicale', 'Rendez-vous médical'),
        ('familiale', 'Raison familiale'),
        ('administrative', 'Démarche administrative'),
        ('formation', 'Formation'),
        ('mission', 'Mission'),
        ('autre', 'Autre'),
    ]
    
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('approuve', 'Approuvé'),
        ('rejete', 'Rejeté'),
        ('annule', 'Annulé'),
    ]
    
    demandeur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='demandes_absence')
    
    # Informations personnelles
    matricule = models.CharField(max_length=50, default='', help_text="Matricule de l'agent")
    emploi = models.CharField(max_length=100, default='', help_text="Emploi occupé")
    fonction = models.CharField(max_length=100, default='', help_text="Fonction exercée")
    
    type_absence = models.CharField(max_length=20, choices=TYPE_ABSENCE_CHOICES)
    date_debut = models.DateTimeField()
    date_fin = models.DateTimeField()
    duree_heures = models.DecimalField(max_digits=4, decimal_places=2, help_text="Durée en heures")
    motif = models.TextField()
    
    # Validation hiérarchique
    directeur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='absences_directeur', help_text="Directeur sélectionné")
    superieur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='absences_superieur', help_text="Supérieur hiérarchique sélectionné")
    superieur_hierarchique = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='absences_a_valider')
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')
    date_validation = models.DateTimeField(null=True, blank=True)
    commentaire_validation = models.TextField(blank=True, null=True)
    
    # Documents
    document_demande = models.FileField(upload_to='absences/demandes/', null=True, blank=True)
    document_reponse = models.FileField(upload_to='absences/reponses/', null=True, blank=True)
    
    # Agents concernés (même direction/service)
    agents_concernes = models.ManyToManyField(User, blank=True, related_name='absences_concernes', help_text="Agents de la même direction/service informés de cette absence")
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Demande d\'absence'
        verbose_name_plural = 'Demandes d\'absence'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Absence {self.type_absence} - {self.demandeur.username} ({self.date_debut.strftime('%d/%m/%Y %H:%M')})"
    
    def save(self, *args, **kwargs):
        # Calculer automatiquement la durée en heures
        if self.date_debut and self.date_fin:
            delta = self.date_fin - self.date_debut
            self.duree_heures = delta.total_seconds() / 3600
        super().save(*args, **kwargs)
