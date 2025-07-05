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
    CATEGORIE_CHOICES = [
        ('Demande', 'Demande'),
        ('Invitation', 'Invitation'),
        ('Réclamation', 'Réclamation'),
        ('Autre', 'Autre'),
    ]

    reference = models.CharField(max_length=255, unique=True)
    expediteur = models.CharField(max_length=255)
    objet = models.TextField()
    date_reception = models.DateField()
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True, related_name='courriers')
    categorie = models.CharField(max_length=64, choices=CATEGORIE_CHOICES, default='Demande')
    fichier_joint = models.FileField(upload_to='courriers/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.reference} - {self.objet}"

class Diligence(models.Model):
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
    reference_courrier = models.CharField(max_length=255)
    courrier = models.ForeignKey(Courrier, on_delete=models.SET_NULL, null=True, blank=True, related_name='diligences')
    categorie = models.CharField(max_length=64)
    statut = models.CharField(max_length=32, choices=STATUT_CHOICES, default='en_attente')
    fichier_joint = models.FileField(
        upload_to='diligences/',
        blank=True,
        null=True,
        max_length=500  # Augmenter la longueur max pour les noms de fichiers longs
    )
    commentaires = models.TextField(blank=True, null=True)
    commentaires_agents = models.TextField(blank=True, null=True)
    instructions = models.TextField(blank=True, null=True)
    nouvelle_instruction = models.TextField(blank=True, null=True)
    date_limite = models.DateField(blank=True, null=True)
    date_reception = models.DateField(blank=True, null=True)
    expediteur = models.CharField(max_length=255, blank=True, null=True)
    objet = models.TextField(blank=True, null=True)
    agents = models.ManyToManyField(User, related_name='diligences')
    services_concernes = models.ManyToManyField(Service, related_name='diligences_concernes')
    direction = models.ForeignKey(Direction, on_delete=models.SET_NULL, null=True, blank=True, related_name='diligences')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    archived_at = models.DateTimeField(null=True, blank=True)
    archived_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='diligences_archived')
    validated_at = models.DateTimeField(null=True, blank=True)

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

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

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


# --- MODULE SUIVI PROJETS & TACHES ---

class Projet(models.Model):
    nom = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    direction = models.ForeignKey('Direction', on_delete=models.PROTECT, null=True, blank=True)
    service = models.ForeignKey('Service', on_delete=models.PROTECT, null=True, blank=True)
    directeurs = models.ManyToManyField(
        User, related_name='directeurs', blank=True, limit_choices_to={'role': 'directeur'}
    )
    superieurs = models.ManyToManyField(
        User, related_name='superieurs', blank=True, limit_choices_to={'role': 'superviseur'}
    )
    agents = models.ManyToManyField(
        User, related_name='agents', blank=True, limit_choices_to={'role': 'agent'}
    )
    secretaires = models.ManyToManyField(
        User, related_name='secretaires', blank=True, limit_choices_to={'role': 'secretaire'}
    )
    ETAT_CHOICES = [
        ('planifie', 'Planifié'),
        ('en_cours', 'En cours'),
        ('termine', 'Terminé'),
        ('suspendu', 'Suspendu'),
    ]
    nom = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
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
    projet = models.ForeignKey(Projet, on_delete=models.CASCADE)
    titre = models.CharField(max_length=100)
    directeurs = models.ManyToManyField(
        User, related_name='directeurs_taches', blank=True, limit_choices_to={'role': 'directeur'}
    )
    superieurs = models.ManyToManyField(
        User, related_name='superieurs_taches', blank=True, limit_choices_to={'role': 'superviseur'}
    )
    agents = models.ManyToManyField(
        User, related_name='agents_taches', blank=True, limit_choices_to={'role': 'agent'}
    )
    secretaires = models.ManyToManyField(
        User, related_name='secretaires_taches', blank=True, limit_choices_to={'role': 'secretaire'}
    )
    ETAT_CHOICES = [
        ('a_faire', 'À faire'),
        ('en_cours', 'En cours'),
        ('termine', 'Terminé'),
        ('bloque', 'Bloqué'),
    ]
    PRIORITE_CHOICES = [
        ('basse', 'Basse'),
        ('moyenne', 'Moyenne'),
        ('haute', 'Haute'),
    ]
    titre = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    etat = models.CharField(max_length=20, choices=ETAT_CHOICES, default='a_faire')
    dateDebut = models.DateField(blank=True, null=True)
    dateEcheance = models.DateField(blank=True, null=True)
    priorite = models.CharField(max_length=10, choices=PRIORITE_CHOICES, default='moyenne')
    responsable = models.ForeignKey(User, related_name='taches_responsable', on_delete=models.SET_NULL, null=True)
    agentsAffectes = models.ManyToManyField(User, related_name='taches_agent', blank=True)
    projet = models.ForeignKey(Projet, related_name='taches', on_delete=models.CASCADE)
    parentTache = models.ForeignKey('self', related_name='sous_taches', on_delete=models.CASCADE, null=True, blank=True)
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.titre

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
    latitude_centre = models.DecimalField(max_digits=9, decimal_places=6, help_text="Latitude du centre du bureau")
    longitude_centre = models.DecimalField(max_digits=9, decimal_places=6, help_text="Longitude du centre du bureau")
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
        return f"{self.nom} {self.prenom or ''} ({self.role})"


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
    empreinte_hash = models.TextField(null=True, blank=True, help_text="Hash de l'empreinte digitale scannée")
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
