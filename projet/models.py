from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


# =============================================================================
# A. GESTION DES PROJETS
# =============================================================================

class Projet(models.Model):
    """Projet administratif avec suivi complet."""

    STATUT_CHOICES = [
        ('planifie', 'Planifié'),
        ('en_cours', 'En cours'),
        ('termine', 'Terminé'),
        ('en_retard', 'En retard'),
        ('suspendu', 'Suspendu'),
    ]

    titre = models.CharField("Titre du projet", max_length=255)
    description = models.TextField("Description", blank=True, default="")
    objectifs = models.TextField("Objectifs", blank=True, default="")
    date_debut = models.DateField("Date de début")
    date_fin_prevue = models.DateField("Date de fin prévue")
    date_fin_effective = models.DateField("Date de fin effective", blank=True, null=True)
    budget_prevu = models.DecimalField(
        "Budget prévu", max_digits=15, decimal_places=2, blank=True, null=True
    )
    budget_consomme = models.DecimalField(
        "Budget consommé", max_digits=15, decimal_places=2, default=0
    )
    statut = models.CharField("Statut", max_length=20, choices=STATUT_CHOICES, default='planifie')
    pourcentage_avancement = models.DecimalField(
        "Avancement (%)", max_digits=5, decimal_places=2, default=0
    )

    # Relations
    responsable = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='projets_geres', verbose_name="Responsable principal"
    )
    equipe = models.ManyToManyField(
        User, related_name='projets_equipe', blank=True, verbose_name="Équipe projet"
    )
    direction = models.ForeignKey(
        'core.Direction', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='projets_module', verbose_name="Direction"
    )
    service = models.ForeignKey(
        'core.Service', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='projets_module', verbose_name="Service"
    )

    # Lien avec les diligences / courriers
    diligence = models.ForeignKey(
        'core.Diligence', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='projets_lies', verbose_name="Diligence liée"
    )
    courrier = models.ForeignKey(
        'core.Courrier', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='projets_lies', verbose_name="Courrier lié"
    )

    # Métadonnées
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='projets_crees', verbose_name="Créé par"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'projet'
        ordering = ['-created_at']
        verbose_name = "Projet"
        verbose_name_plural = "Projets"
        indexes = [
            models.Index(fields=['statut']),
            models.Index(fields=['responsable']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return self.titre

    @property
    def est_en_retard(self):
        if self.statut == 'termine':
            return False
        return self.date_fin_prevue and self.date_fin_prevue < timezone.now().date()

    @property
    def nombre_taches(self):
        return self.taches.count()

    @property
    def taches_terminees(self):
        return self.taches.filter(statut='termine').count()

    @property
    def taches_en_cours(self):
        return self.taches.filter(statut='en_cours').count()

    @property
    def taches_a_faire(self):
        return self.taches.filter(statut='a_faire').count()

    def calculer_avancement(self):
        """Calcul automatique du progrès basé sur les tâches."""
        taches = self.taches.all()
        if not taches.exists():
            return 0

        # Avancement pondéré si poids défini, sinon simple ratio
        taches_avec_poids = taches.filter(poids__gt=0)
        if taches_avec_poids.exists():
            total_poids = sum(t.poids for t in taches)
            if total_poids == 0:
                return 0
            avancement = sum(
                (t.poids * (100 if t.statut == 'termine' else t.pourcentage_avancement))
                for t in taches
            ) / total_poids
        else:
            total = taches.count()
            terminees = taches.filter(statut='termine').count()
            avancement = (terminees / total) * 100 if total > 0 else 0

        return round(avancement, 2)

    def mettre_a_jour_avancement(self):
        """Met à jour le pourcentage d'avancement et détecte les retards."""
        self.pourcentage_avancement = self.calculer_avancement()
        if self.est_en_retard and self.statut not in ('termine', 'suspendu'):
            self.statut = 'en_retard'
        if self.pourcentage_avancement >= 100 and self.statut != 'termine':
            self.statut = 'termine'
            self.date_fin_effective = timezone.now().date()
        self.save(update_fields=['pourcentage_avancement', 'statut', 'date_fin_effective', 'updated_at'])


# =============================================================================
# B. GESTION DES TÂCHES
# =============================================================================

class Tache(models.Model):
    """Tâche liée à un projet (type Asana)."""

    STATUT_CHOICES = [
        ('a_faire', 'À faire'),
        ('en_cours', 'En cours'),
        ('termine', 'Terminé'),
    ]

    PRIORITE_CHOICES = [
        ('haute', 'Haute'),
        ('moyenne', 'Moyenne'),
        ('basse', 'Basse'),
    ]

    titre = models.CharField("Titre", max_length=255)
    description = models.TextField("Description", blank=True, default="")
    projet = models.ForeignKey(
        Projet, on_delete=models.CASCADE, related_name='taches', verbose_name="Projet"
    )
    responsable = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='projet_taches_responsable', verbose_name="Responsable"
    )
    agents_assignes = models.ManyToManyField(
        User, related_name='projet_taches_assignees', blank=True,
        verbose_name="Agents assignés"
    )
    date_debut = models.DateField("Date de début", blank=True, null=True)
    date_fin_prevue = models.DateField("Date de fin prévue", blank=True, null=True)
    date_fin_effective = models.DateField("Date de fin effective", blank=True, null=True)
    priorite = models.CharField("Priorité", max_length=10, choices=PRIORITE_CHOICES, default='moyenne')
    statut = models.CharField("Statut", max_length=10, choices=STATUT_CHOICES, default='a_faire')
    pourcentage_avancement = models.DecimalField(
        "Avancement (%)", max_digits=5, decimal_places=2, default=0
    )
    poids = models.PositiveIntegerField("Poids (pondération)", default=1)
    ordre = models.PositiveIntegerField("Ordre d'affichage", default=0)

    # Dépendance pour Gantt
    tache_dependante = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='taches_dependantes', verbose_name="Dépend de"
    )

    # Lien avec diligences / courriers
    diligence = models.ForeignKey(
        'core.Diligence', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='taches_projet_liees', verbose_name="Diligence liée"
    )
    courrier = models.ForeignKey(
        'core.Courrier', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='taches_projet_liees', verbose_name="Courrier lié"
    )

    # Métadonnées
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='projet_taches_creees', verbose_name="Créé par"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'projet'
        ordering = ['ordre', '-priorite', '-created_at']
        verbose_name = "Tâche"
        verbose_name_plural = "Tâches"
        indexes = [
            models.Index(fields=['statut']),
            models.Index(fields=['projet', 'statut']),
            models.Index(fields=['responsable']),
        ]

    def __str__(self):
        return f"{self.titre} ({self.projet.titre})"

    @property
    def est_en_retard(self):
        if self.statut == 'termine':
            return False
        return self.date_fin_prevue and self.date_fin_prevue < timezone.now().date()

    @property
    def nombre_sous_taches(self):
        return self.sous_taches.count()

    @property
    def sous_taches_terminees(self):
        return self.sous_taches.filter(statut='termine').count()

    def calculer_avancement(self):
        """Calcul avancement basé sur les sous-tâches."""
        st = self.sous_taches.all()
        if not st.exists():
            return 100 if self.statut == 'termine' else self.pourcentage_avancement
        total = st.count()
        terminees = st.filter(statut='termine').count()
        return round((terminees / total) * 100, 2) if total > 0 else 0


# =============================================================================
# SOUS-TÂCHES
# =============================================================================

class SousTache(models.Model):
    """Sous-tâche appartenant à une tâche."""

    STATUT_CHOICES = [
        ('a_faire', 'À faire'),
        ('en_cours', 'En cours'),
        ('termine', 'Terminé'),
    ]

    titre = models.CharField("Titre", max_length=255)
    tache = models.ForeignKey(
        Tache, on_delete=models.CASCADE, related_name='sous_taches', verbose_name="Tâche parent"
    )
    responsable = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='projet_sous_taches', verbose_name="Responsable"
    )
    date_echeance = models.DateField("Échéance", blank=True, null=True)
    statut = models.CharField("Statut", max_length=10, choices=STATUT_CHOICES, default='a_faire')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'projet'
        ordering = ['created_at']
        verbose_name = "Sous-tâche"
        verbose_name_plural = "Sous-tâches"

    def __str__(self):
        return f"{self.titre} (sous-tâche de {self.tache.titre})"

    @property
    def est_en_retard(self):
        if self.statut == 'termine':
            return False
        return self.date_echeance and self.date_echeance < timezone.now().date()


# =============================================================================
# C. COMMENTAIRES
# =============================================================================

class CommentaireTache(models.Model):
    """Commentaire / discussion sur une tâche."""

    tache = models.ForeignKey(
        Tache, on_delete=models.CASCADE, related_name='commentaires', verbose_name="Tâche"
    )
    auteur = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='projet_commentaires', verbose_name="Auteur"
    )
    contenu = models.TextField("Contenu")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'projet'
        ordering = ['-created_at']
        verbose_name = "Commentaire"
        verbose_name_plural = "Commentaires"

    def __str__(self):
        return f"{self.auteur.username}: {self.contenu[:50]}..."


# =============================================================================
# D. PIÈCES JOINTES
# =============================================================================

class PieceJointe(models.Model):
    """Fichier attaché à une tâche ou un projet."""

    tache = models.ForeignKey(
        Tache, on_delete=models.CASCADE, null=True, blank=True,
        related_name='pieces_jointes', verbose_name="Tâche"
    )
    projet = models.ForeignKey(
        Projet, on_delete=models.CASCADE, null=True, blank=True,
        related_name='pieces_jointes', verbose_name="Projet"
    )
    fichier = models.FileField("Fichier", upload_to='projet/pieces_jointes/%Y/%m/')
    nom = models.CharField("Nom du fichier", max_length=255)
    type_fichier = models.CharField("Type", max_length=100, blank=True, default="")
    taille = models.PositiveIntegerField("Taille (octets)", default=0)
    uploaded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='projet_fichiers_uploades', verbose_name="Uploadé par"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'projet'
        ordering = ['-created_at']
        verbose_name = "Pièce jointe"
        verbose_name_plural = "Pièces jointes"

    def __str__(self):
        return self.nom


# =============================================================================
# E. NOTIFICATIONS
# =============================================================================

class NotificationProjet(models.Model):
    """Notification intelligente liée au module projets."""

    TYPE_CHOICES = [
        ('creation_tache', 'Création de tâche'),
        ('modification_tache', 'Modification de tâche'),
        ('retard_detecte', 'Retard détecté'),
        ('commentaire_ajoute', 'Commentaire ajouté'),
        ('rappel_echeance', 'Rappel avant échéance'),
        ('tache_terminee', 'Tâche terminée'),
        ('projet_termine', 'Projet terminé'),
        ('livrable_soumis', 'Livrable soumis'),
        ('livrable_valide', 'Livrable validé'),
        ('livrable_rejete', 'Livrable rejeté'),
        ('assignation', 'Assignation'),
        ('validation_requise', 'Validation requise'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='notifications_projet', verbose_name="Destinataire"
    )
    projet = models.ForeignKey(
        Projet, on_delete=models.CASCADE, null=True, blank=True,
        related_name='notifications', verbose_name="Projet"
    )
    tache = models.ForeignKey(
        Tache, on_delete=models.CASCADE, null=True, blank=True,
        related_name='notifications', verbose_name="Tâche"
    )
    type_notification = models.CharField("Type", max_length=30, choices=TYPE_CHOICES)
    titre = models.CharField("Titre", max_length=255)
    message = models.TextField("Message")
    lue = models.BooleanField("Lue", default=False)
    date_lecture = models.DateTimeField("Date de lecture", null=True, blank=True)
    metadata = models.JSONField("Données supplémentaires", default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'projet'
        ordering = ['-created_at']
        verbose_name = "Notification Projet"
        verbose_name_plural = "Notifications Projet"
        indexes = [
            models.Index(fields=['user', 'lue']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.titre} → {self.user.username}"

    def marquer_comme_lue(self):
        self.lue = True
        self.date_lecture = timezone.now()
        self.save(update_fields=['lue', 'date_lecture'])


# =============================================================================
# F. LIVRABLES
# =============================================================================

class Livrable(models.Model):
    """Document livrable avec validation et versioning."""

    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('soumis', 'Soumis'),
        ('valide', 'Validé'),
        ('rejete', 'Rejeté'),
    ]

    projet = models.ForeignKey(
        Projet, on_delete=models.CASCADE, related_name='livrables', verbose_name="Projet"
    )
    tache = models.ForeignKey(
        Tache, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='livrables', verbose_name="Tâche associée"
    )
    titre = models.CharField("Titre", max_length=255)
    description = models.TextField("Description", blank=True, default="")
    fichier = models.FileField("Fichier", upload_to='projet/livrables/%Y/%m/')
    version = models.PositiveIntegerField("Version", default=1)
    statut = models.CharField("Statut", max_length=10, choices=STATUT_CHOICES, default='brouillon')

    soumis_par = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='livrables_soumis', verbose_name="Soumis par"
    )
    valide_par = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='livrables_valides', verbose_name="Validé par"
    )
    commentaire_validation = models.TextField("Commentaire de validation", blank=True, default="")
    date_validation = models.DateTimeField("Date de validation", null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'projet'
        ordering = ['-version', '-created_at']
        verbose_name = "Livrable"
        verbose_name_plural = "Livrables"

    def __str__(self):
        return f"{self.titre} v{self.version} ({self.projet.titre})"


# =============================================================================
# G. WORKFLOW DE VALIDATION
# =============================================================================

class ValidationTache(models.Model):
    """Workflow de validation d'une tâche : soumise → validée / rejetée."""

    STATUT_CHOICES = [
        ('soumise', 'Soumise'),
        ('validee', 'Validée'),
        ('rejetee', 'Rejetée'),
    ]

    tache = models.ForeignKey(
        Tache, on_delete=models.CASCADE, related_name='validations', verbose_name="Tâche"
    )
    soumis_par = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='validations_soumises', verbose_name="Soumis par"
    )
    valide_par = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='validations_traitees', verbose_name="Traité par"
    )
    statut = models.CharField("Statut", max_length=10, choices=STATUT_CHOICES, default='soumise')
    commentaire = models.TextField("Commentaire", blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'projet'
        ordering = ['-created_at']
        verbose_name = "Validation de tâche"
        verbose_name_plural = "Validations de tâches"

    def __str__(self):
        return f"Validation {self.tache.titre} - {self.get_statut_display()}"


# =============================================================================
# H. HISTORIQUE / AUDIT TRAIL
# =============================================================================

class HistoriqueAction(models.Model):
    """Journal d'audit : toutes les actions sur projets et tâches."""

    ACTION_CHOICES = [
        ('creation', 'Création'),
        ('modification', 'Modification'),
        ('suppression', 'Suppression'),
        ('changement_statut', 'Changement de statut'),
        ('assignation', 'Assignation'),
        ('commentaire', 'Commentaire'),
        ('upload', 'Upload de fichier'),
        ('validation', 'Validation'),
        ('livrable', 'Action sur livrable'),
    ]

    projet = models.ForeignKey(
        Projet, on_delete=models.CASCADE, null=True, blank=True,
        related_name='historique', verbose_name="Projet"
    )
    tache = models.ForeignKey(
        Tache, on_delete=models.CASCADE, null=True, blank=True,
        related_name='historique', verbose_name="Tâche"
    )
    utilisateur = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='projet_historique_actions', verbose_name="Utilisateur"
    )
    action = models.CharField("Action", max_length=30, choices=ACTION_CHOICES)
    details = models.JSONField("Détails", default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'projet'
        ordering = ['-created_at']
        verbose_name = "Historique d'action"
        verbose_name_plural = "Historiques d'actions"
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['projet']),
            models.Index(fields=['tache']),
        ]

    def __str__(self):
        return f"{self.get_action_display()} par {self.utilisateur} - {self.created_at.strftime('%d/%m/%Y %H:%M')}"


# =============================================================================
# I. RÉUNIONS & RENDEZ-VOUS
# =============================================================================

class ReunionProjet(models.Model):
    """Réunion de suivi ou rendez-vous lié à un projet/tâche."""

    TYPE_CHOICES = [
        ('reunion_suivi', 'Réunion de suivi'),
        ('rendez_vous', 'Rendez-vous'),
        ('point_avancement', "Point d'avancement"),
        ('comite_pilotage', 'Comité de pilotage'),
    ]

    STATUT_CHOICES = [
        ('planifie', 'Planifié'),
        ('en_cours', 'En cours'),
        ('termine', 'Terminé'),
        ('annule', 'Annulé'),
    ]

    titre = models.CharField("Titre", max_length=255)
    type_reunion = models.CharField("Type", max_length=20, choices=TYPE_CHOICES, default='reunion_suivi')
    description = models.TextField("Description / Ordre du jour", blank=True, default="")
    lieu = models.CharField("Lieu", max_length=255, blank=True, default="")
    lien_visio = models.URLField("Lien visioconférence", blank=True, default="")

    date = models.DateField("Date")
    heure_debut = models.TimeField("Heure de début")
    heure_fin = models.TimeField("Heure de fin", blank=True, null=True)

    projet = models.ForeignKey(
        Projet, on_delete=models.CASCADE, null=True, blank=True,
        related_name='reunions', verbose_name="Projet"
    )
    tache = models.ForeignKey(
        Tache, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reunions', verbose_name="Tâche associée"
    )
    organisateur = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='reunions_organisees', verbose_name="Organisateur"
    )
    participants = models.ManyToManyField(
        User, related_name='reunions_invitees', blank=True, verbose_name="Participants"
    )
    statut = models.CharField("Statut", max_length=10, choices=STATUT_CHOICES, default='planifie')
    compte_rendu = models.TextField("Compte rendu", blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'projet'
        ordering = ['date', 'heure_debut']
        verbose_name = "Réunion"
        verbose_name_plural = "Réunions"
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['projet']),
        ]

    def __str__(self):
        return f"{self.get_type_reunion_display()} : {self.titre} ({self.date})"
