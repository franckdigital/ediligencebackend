"""
Management command: seed_lanema
Creates the full LANEMA organizational structure with realistic test data.

Usage:
    python manage.py seed_lanema          # full seed
    python manage.py seed_lanema --flush  # delete existing LANEMA data first
"""
import random
from datetime import date, timedelta, time, datetime
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction

from core.models import (
    Direction, SousDirection, Service, UserProfile, Agent, Bureau,
    Courrier, CourrierImputation, Diligence, Tache, Presence,
    DemandeConge, DemandeAbsence, FicheAgent, MissionRH,
    EvaluationRH, FormationRH, InscriptionFormationRH, DocumentRH,
)

# ─────────────────────────────────────────────────────────────────────────────
# LANEMA Abidjan coordinates (Plateau / Ministère du Commerce)
LAT, LON = '5.356389', '-4.008389'

# ─────────────────────────────────────────────────────────────────────────────
# Ivorian name pool
PRENOMS_H = [
    'Kouamé', 'Koffi', 'Konan', 'Kouassi', 'Yao', 'Jean-Baptiste',
    'Adama', 'Siaka', 'Ibrahim', 'Mamadou', 'Moussa', 'Drissa',
    'Bamba', 'Seydou', 'Lacina', 'N\'Guessan', 'Brou', 'Tchétrché',
    'Sié', 'Souleymane', 'Alassane', 'Clovis', 'Hermann', 'Franck',
    'Wilfried', 'Boris', 'Patrick', 'Eric', 'Serge', 'Landry',
]
PRENOMS_F = [
    'Adjoua', 'Akissi', 'Affoue', 'Aya', 'Bintou', 'Fatoumata',
    'Mariame', 'Aminata', 'Odette', 'Marie-Claude', 'Edwige',
    'Roseline', 'Célestine', 'Clarisse', 'Nathalie', 'Danielle',
    'Estelle', 'Grâce', 'Joëlle', 'Larissa',
]
NOMS = [
    'Koné', 'Traoré', 'Coulibaly', 'Bamba', 'Diallo', 'Ouattara',
    'Touré', 'Cissé', 'Keïta', 'Sanogo', 'Diarrassouba', 'Camara',
    'N\'Goran', 'Yao', 'Kouamé', 'Konan', 'Assi', 'Dje', 'Ehui',
    'Aboua', 'Gnagne', 'Boni', 'Tuo', 'Fofana', 'Diabaté', 'Doumbia',
    'Kouyaté', 'Dao', 'Séry', 'Bogui', 'Kimou', 'Lathro', 'Zié',
    'Gnamba', 'Okou', 'Dié', 'Niamké', 'Vroh', 'Yoboué', 'Agoh',
]

# ─────────────────────────────────────────────────────────────────────────────
# Full LANEMA organizational structure
LANEMA_ORG = [
    {
        'type': 'cabinet',
        'nom': 'Cabinet du Directeur Général',
        'sigle': 'CDG',
        'sous_dirs': [
            {
                'nom': 'Cabinet Direction Générale',
                'services': [
                    'Conseiller Technique',
                    'Chargé de Communication Institutionnelle',
                    'Chargé des Relations Publiques',
                    'Chargé de la Coopération Internationale',
                    'Secrétariat Général',
                ],
            },
        ],
    },
    {
        'type': 'direction_generale',
        'nom': 'Direction Générale',
        'sigle': 'DG',
        'sous_dirs': [
            {
                'nom': 'Direction Générale',
                'services': ['Directeur Général', 'Directeur Général Adjoint'],
            },
        ],
    },
    {
        'type': 'direction',
        'nom': 'Direction des Essais et Analyses de Laboratoire',
        'sigle': 'DEAL',
        'sous_dirs': [
            {
                'nom': 'Sous-Direction des Analyses Chimiques',
                'services': ['Chimie Organique', 'Chimie Minérale', 'Produits Pétroliers', 'Métaux Lourds', 'Analyses Toxicologiques'],
            },
            {
                'nom': 'Sous-Direction des Analyses Microbiologiques',
                'services': ['Microbiologie Alimentaire', 'Microbiologie des Eaux', 'Hygiène Alimentaire', 'Biologie Moléculaire'],
            },
            {
                'nom': 'Sous-Direction des Analyses Physico-Chimiques',
                'services': ['Analyses des Eaux', 'Sols et Sédiments', 'Air et Pollution', 'Produits Alimentaires'],
            },
            {
                'nom': 'Sous-Direction des Essais Techniques',
                'services': ['Matériaux de Construction', 'Essais Électriques', 'Essais Mécaniques', 'Essais Thermiques'],
            },
        ],
    },
    {
        'type': 'direction',
        'nom': 'Direction Nationale de la Métrologie',
        'sigle': 'DNM',
        'sous_dirs': [
            {
                'nom': 'Sous-Direction de la Métrologie Légale',
                'services': ['Vérification des Balances', 'Instruments de Pesage', 'Compteurs', 'Pompes à Carburant'],
            },
            {
                'nom': 'Sous-Direction de la Métrologie Industrielle',
                'services': ['Masse', 'Température', 'Pression', 'Volume', 'Dimension', 'Électricité'],
            },
            {
                'nom': 'Sous-Direction de l\'Étalonnage',
                'services': ['Étalonnage des Instruments', 'Maintenance des Équipements', 'Validation Métrologique'],
            },
        ],
    },
    {
        'type': 'direction',
        'nom': 'Direction Qualité et Accréditation',
        'sigle': 'DQA',
        'sous_dirs': [
            {
                'nom': 'Sous-Direction Assurance Qualité',
                'services': ['Management Qualité', 'Documentation Qualité', 'Gestion des Risques'],
            },
            {
                'nom': 'Sous-Direction Accréditation',
                'services': ['ISO/IEC 17025', 'Audits Internes', 'Certification'],
            },
            {
                'nom': 'Sous-Direction Amélioration Continue',
                'services': ['Indicateurs de Performance', 'Veille Normative', 'Satisfaction Client'],
            },
        ],
    },
    {
        'type': 'direction',
        'nom': 'Direction de la Recherche et de l\'Innovation',
        'sigle': 'DRI',
        'sous_dirs': [
            {
                'nom': 'Sous-Direction Recherche',
                'services': ['Recherche Chimique', 'Recherche Environnementale', 'Recherche Agroalimentaire'],
            },
            {
                'nom': 'Sous-Direction Innovation',
                'services': ['Développement des Méthodes', 'Intelligence Artificielle', 'Transformation Digitale'],
            },
        ],
    },
    {
        'type': 'direction',
        'nom': 'Direction de la Normalisation et de la Conformité',
        'sigle': 'DNC',
        'sous_dirs': [
            {
                'nom': 'Sous-Direction Normalisation',
                'services': ['Veille Normative', 'Élaboration des Référentiels'],
            },
            {
                'nom': 'Sous-Direction Contrôle de Conformité',
                'services': ['Inspection', 'Certification des Produits', 'Homologation'],
            },
        ],
    },
    {
        'type': 'direction',
        'nom': 'Direction Environnement et Sécurité Sanitaire',
        'sigle': 'DESS',
        'sous_dirs': [
            {
                'nom': 'Sous-Direction Analyses Environnementales',
                'services': ['Qualité de l\'Eau', 'Qualité de l\'Air', 'Déchets Industriels'],
            },
            {
                'nom': 'Sous-Direction Sécurité Alimentaire',
                'services': ['Contrôle Alimentaire', 'Résidus Chimiques', 'Contaminants'],
            },
        ],
    },
    {
        'type': 'direction',
        'nom': 'Direction des Systèmes d\'Information et de la Transformation Digitale',
        'sigle': 'DSITD',
        'sous_dirs': [
            {
                'nom': 'Sous-Direction Infrastructures Informatiques',
                'services': ['Réseaux', 'Systèmes', 'Sécurité Informatique'],
            },
            {
                'nom': 'Sous-Direction Développement',
                'services': ['Développement Applicatif', 'Base de Données', 'API et Interopérabilité'],
            },
            {
                'nom': 'Sous-Direction Support',
                'services': ['Assistance Utilisateurs', 'Maintenance', 'Formation Numérique'],
            },
            {
                'nom': 'Sous-Direction Data et IA',
                'services': ['Business Intelligence', 'Data Analytics', 'Intelligence Artificielle', 'Archivage Électronique'],
            },
        ],
    },
    {
        'type': 'direction',
        'nom': 'Direction Administrative et Financière',
        'sigle': 'DAF',
        'sous_dirs': [
            {
                'nom': 'Sous-Direction Administrative',
                'services': ['Courrier', 'Archives', 'Patrimoine'],
            },
            {
                'nom': 'Sous-Direction Financière',
                'services': ['Comptabilité', 'Budget', 'Trésorerie'],
            },
            {
                'nom': 'Sous-Direction Achats',
                'services': ['Marchés Publics', 'Approvisionnements', 'Gestion des Stocks'],
            },
        ],
    },
    {
        'type': 'direction',
        'nom': 'Direction des Ressources Humaines',
        'sigle': 'DRH',
        'sous_dirs': [
            {
                'nom': 'Sous-Direction Administration du Personnel',
                'services': ['Carrière', 'Paie', 'Discipline'],
            },
            {
                'nom': 'Sous-Direction Développement RH',
                'services': ['Formation', 'Évaluation', 'Recrutement'],
            },
            {
                'nom': 'Sous-Direction Santé et Bien-être',
                'services': ['Santé au Travail', 'Action Sociale'],
            },
        ],
    },
    {
        'type': 'direction',
        'nom': 'Direction Commerciale et Relation Client',
        'sigle': 'DCRC',
        'sous_dirs': [
            {
                'nom': 'Sous-Direction Développement Commercial',
                'services': ['Prospection', 'Marketing', 'Partenariats'],
            },
            {
                'nom': 'Sous-Direction Relation Client',
                'services': ['Accueil', 'Devis', 'Facturation'],
            },
            {
                'nom': 'Sous-Direction Communication',
                'services': ['Communication Digitale', 'Événementiel', 'Médias'],
            },
        ],
    },
    {
        'type': 'direction',
        'nom': 'Direction des Opérations',
        'sigle': 'DO',
        'sous_dirs': [
            {
                'nom': 'Sous-Direction Réception des Échantillons',
                'services': ['Enregistrement', 'Identification', 'Traçabilité'],
            },
            {
                'nom': 'Sous-Direction Planification',
                'services': ['Programmation', 'Affectation des Analyses'],
            },
            {
                'nom': 'Sous-Direction Livraison',
                'services': ['Validation des Rapports', 'Transmission des Résultats', 'Archivage'],
            },
        ],
    },
    {
        'type': 'direction',
        'nom': 'Direction Juridique et Audit',
        'sigle': 'DJA',
        'sous_dirs': [
            {
                'nom': 'Sous-Direction Juridique',
                'services': ['Contentieux', 'Contrats', 'Veille Juridique'],
            },
            {
                'nom': 'Sous-Direction Audit',
                'services': ['Audit Interne', 'Contrôle Interne', 'Conformité'],
            },
        ],
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# Performance profiles (used to generate realistic varied data)
PROFILES = {
    'excellent':   {'presence': 0.97, 'ponctualite': 0.98, 'completion': 0.95},
    'bon':         {'presence': 0.88, 'ponctualite': 0.85, 'completion': 0.82},
    'moyen':       {'presence': 0.75, 'ponctualite': 0.70, 'completion': 0.65},
    'faible':      {'presence': 0.58, 'ponctualite': 0.55, 'completion': 0.45},
}
PROFILE_WEIGHTS = ['excellent', 'excellent', 'bon', 'bon', 'bon', 'moyen', 'moyen', 'faible']

# Courrier content templates
OBJETS_COURRIER_ARRIVEE = [
    "Demande d'analyses de produits alimentaires",
    "Requête de certification de conformité",
    "Plainte relative à la qualité des produits",
    "Demande d'étalonnage d'instruments de mesure",
    "Notification d'inspection métrologique",
    "Demande de partenariat technique",
    "Rapport d'audit qualité externe",
    "Convocation à une réunion technique",
    "Invitation à une conférence internationale",
    "Demande d'accréditation ISO 17025",
    "Transmission de résultats d'analyses",
    "Demande d'homologation de produit",
    "Saisine pour contrôle de conformité",
    "Lettre de réclamation client",
    "Demande de devis analyses environnementales",
]
OBJETS_COURRIER_DEPART = [
    "Transmission de rapport d'analyse",
    "Réponse à la demande de certification",
    "Convocation à réunion de coordination",
    "Notification de résultats d'étalonnage",
    "Rapport d'inspection métrologique",
    "Réponse à réclamation client",
    "Proposition de partenariat technique",
    "Transmission de certificat de conformité",
    "Compte rendu de mission technique",
    "Note circulaire interne",
    "Rapport mensuel d'activités",
    "Transmission de rapport d'audit",
    "Convocation comité technique",
]
EXPEDITEURS_ARRIVEE = [
    "Ministère du Commerce", "Direction Générale du Commerce Intérieur",
    "Ministère de la Santé", "Direction des Industries Chimiques",
    "Chambre de Commerce de Côte d'Ivoire", "SODECI",
    "CIE", "PETROCI", "PALMCI", "SIR Abidjan",
    "Université Félix Houphouët-Boigny", "INSP",
    "Groupement des Industries Agroalimentaires", "NESTLE CI",
    "Unilever CI", "SGS Côte d'Ivoire", "Bureau Veritas CI",
    "Ambassade de France", "Union Européenne",
]

# Diligence templates
DIL_OBJETS = [
    "Analyser le rapport d'échantillons soumis par {}",
    "Préparer le certificat de conformité pour {}",
    "Traiter la réclamation de {} concernant les résultats",
    "Répondre à la demande d'accréditation de {}",
    "Effectuer l'inspection métrologique chez {}",
    "Rédiger le rapport d'audit qualité pour {}",
    "Préparer la proposition commerciale pour {}",
    "Valider les méthodes d'analyse demandées par {}",
    "Coordonner la mission technique avec {}",
    "Mettre à jour la documentation qualité suite à la demande de {}",
]

# Tâche templates
TACHE_TITRES = [
    "Mise à jour de la procédure d'analyse",
    "Préparation du rapport mensuel d'activité",
    "Formation du personnel sur les nouvelles méthodes",
    "Calibration des équipements de laboratoire",
    "Audit interne du système de management qualité",
    "Révision du manuel qualité",
    "Élaboration du plan de formation annuel",
    "Mise à jour de la base de données clients",
    "Préparation de la revue de direction",
    "Rédaction du rapport annuel",
    "Validation de nouvelles méthodes d'analyse",
    "Évaluation des prestataires",
    "Préparation de l'audit de renouvellement",
    "Suivi des indicateurs de performance",
    "Inventaire des réactifs et consommables",
    "Mise en place du système de traçabilité",
    "Formation ISO 17025",
    "Amélioration du processus de réception des échantillons",
    "Digitalisation des archives",
    "Mise à jour du système LIMS",
]


class Command(BaseCommand):
    help = 'Seed LANEMA organizational data with agents and comprehensive test data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush',
            action='store_true',
            help='Delete all existing LANEMA data before seeding',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        rng = random.Random(42)  # deterministic seed for reproducibility

        if options['flush']:
            self._flush_lanema_data()

        self.stdout.write(self.style.MIGRATE_HEADING('\n🏗  Creating LANEMA organizational structure…'))
        directions_map, sous_dirs_map, services_map = self._create_org(rng)

        self.stdout.write(self.style.MIGRATE_HEADING('\n👥  Creating users and agents…'))
        all_users_by_service = self._create_users(rng, directions_map, sous_dirs_map, services_map)

        # Flatten to get all users and directeur users
        all_agents = []
        dir_heads = {}     # direction_id → user
        subdir_heads = {}  # sous_direction_id → user
        for service_id, users in all_users_by_service.items():
            all_agents.extend(users)

        # Also collect the direction/sous-direction heads stored during creation
        dir_heads = getattr(self, '_dir_heads', {})
        subdir_heads = getattr(self, '_subdir_heads', {})

        self.stdout.write(self.style.MIGRATE_HEADING('\n📅  Generating presence data (90 days)…'))
        self._create_presence(rng, all_agents)

        self.stdout.write(self.style.MIGRATE_HEADING('\n✉️  Generating courriers…'))
        all_courriers = self._create_courriers(rng, directions_map, services_map, all_agents)

        self.stdout.write(self.style.MIGRATE_HEADING('\n📋  Generating diligences…'))
        self._create_diligences(rng, directions_map, services_map, all_agents, all_courriers)

        self.stdout.write(self.style.MIGRATE_HEADING('\n✅  Generating tâches…'))
        self._create_taches(rng, all_agents)

        self.stdout.write(self.style.MIGRATE_HEADING('\n🏥  Generating RH data…'))
        self._create_rh_data(rng, all_agents)

        self.stdout.write(self.style.MIGRATE_HEADING('\n📁  Generating demandes congés & absences…'))
        self._create_demandes(rng, all_agents)

        total = len(all_agents)
        self.stdout.write(self.style.SUCCESS(
            f'\n✅  LANEMA seed complete! Created {total} agents across '
            f'{len(directions_map)} directions, {len(sous_dirs_map)} sous-directions, '
            f'{len(services_map)} services.\n'
            f'   🔑 Default password for all accounts: Lanema2024!\n'
        ))

    # ──────────────────────────────────────────────────────────────────────────
    def _flush_lanema_data(self):
        self.stdout.write('  Flushing existing LANEMA data…')
        Direction.objects.filter(nom__icontains='LANEMA').delete()
        Direction.objects.filter(nom__in=[d['nom'] for d in LANEMA_ORG]).delete()
        User.objects.filter(username__startswith='lanema.').delete()

    # ──────────────────────────────────────────────────────────────────────────
    def _create_org(self, rng):
        directions_map = {}   # sigle → Direction
        sous_dirs_map  = {}   # (sigle, nom) → SousDirection
        services_map   = {}   # (sigle, sd_nom, svc_nom) → Service

        for dir_data in LANEMA_ORG:
            d, _ = Direction.objects.get_or_create(
                nom=dir_data['nom'],
                defaults={'type_direction': dir_data['type']},
            )
            sigle = dir_data['sigle']
            directions_map[sigle] = d
            self.stdout.write(f'  [{d.type_direction}] {d.nom}')

            for sd_data in dir_data.get('sous_dirs', []):
                sd, _ = SousDirection.objects.get_or_create(
                    nom=sd_data['nom'],
                    direction=d,
                )
                sous_dirs_map[(sigle, sd_data['nom'])] = sd

                for svc_nom in sd_data.get('services', []):
                    svc, _ = Service.objects.get_or_create(
                        nom=svc_nom,
                        sous_direction=sd,
                        defaults={'direction': d},
                    )
                    services_map[(sigle, sd_data['nom'], svc_nom)] = svc

        return directions_map, sous_dirs_map, services_map

    # ──────────────────────────────────────────────────────────────────────────
    def _pick_name(self, rng, gender=None):
        if gender is None:
            gender = rng.choice(['M', 'F'])
        pool = PRENOMS_H if gender == 'M' else PRENOMS_F
        return rng.choice(pool), rng.choice(NOMS), gender

    def _make_user(self, rng, username_base, prenom, nom, role, service, direction=None, sous_direction=None, profile=None):
        username = f'lanema.{username_base}'
        if User.objects.filter(username=username).exists():
            return User.objects.get(username=username)
        user = User.objects.create_user(
            username=username,
            password='Lanema2024!',
            first_name=prenom,
            last_name=nom,
            email=f'{username_base}@lanema.ci',
            is_active=True,
        )
        # Create or update UserProfile
        prof_data = {
            'role': role,
            'service': service,
        }
        if direction:
            prof_data['direction'] = direction
        if sous_direction:
            prof_data['sous_direction'] = sous_direction
        UserProfile.objects.filter(user=user).delete()
        UserProfile.objects.create(
            user=user,
            **prof_data,
            matricule=f'MAT-{username_base.upper()[:10]}',
        )
        return user

    def _create_users(self, rng, directions_map, sous_dirs_map, services_map):
        self._dir_heads = {}
        self._subdir_heads = {}
        all_users_by_service = {}

        # Counter for unique matricules
        counter = {'n': 1}

        def next_mat(prefix):
            n = counter['n']
            counter['n'] += 1
            return f'{prefix}-{n:04d}'

        for dir_data in LANEMA_ORG:
            sigle = dir_data['sigle']
            direction = directions_map[sigle]

            # Create direction head (DIRECTEUR / ADMIN for DG)
            prenom, nom, gender = self._pick_name(rng)
            role = 'ADMIN' if dir_data['type'] == 'direction_generale' else 'DIRECTEUR'
            slug = f'{sigle.lower()}.directeur'
            user_dir = self._make_user(
                rng, slug, prenom, nom, role,
                service=None, direction=direction,
            )
            self._dir_heads[direction.id] = user_dir

            for sd_data in dir_data.get('sous_dirs', []):
                sd = sous_dirs_map[(sigle, sd_data['nom'])]

                # Create sous-direction head
                prenom, nom, gender = self._pick_name(rng)
                sd_slug = f'{sigle.lower()}.sd.{sd.id}'
                role_sd = 'SOUS_DIRECTEUR' if dir_data['type'] == 'direction' else 'SUPERIEUR'
                user_sd = self._make_user(
                    rng, sd_slug, prenom, nom, role_sd,
                    service=None, direction=direction, sous_direction=sd,
                )
                self._subdir_heads[sd.id] = user_sd

                for svc_nom in sd_data.get('services', []):
                    svc = services_map[(sigle, sd_data['nom'], svc_nom)]
                    service_users = []

                    # Chef de service
                    prenom, nom, gender = self._pick_name(rng)
                    svc_slug = f'{sigle.lower()}.cs.{svc.id}'
                    user_cs = self._make_user(
                        rng, svc_slug, prenom, nom, 'CHEF_SERVICE',
                        service=svc, direction=direction, sous_direction=sd,
                    )
                    # Create Agent record for chef de service
                    agent_cs, _ = Agent.objects.get_or_create(
                        user=user_cs,
                        defaults={
                            'nom': nom.upper(),
                            'prenom': prenom,
                            'matricule': next_mat(sigle),
                            'poste': f'Chef de Service {svc_nom}',
                            'service': svc,
                        }
                    )
                    service_users.append(user_cs)

                    # 3 agents per service
                    for i in range(3):
                        prenom, nom, gender = self._pick_name(rng)
                        a_slug = f'{sigle.lower()}.ag.{svc.id}.{i}'
                        user_ag = self._make_user(
                            rng, a_slug, prenom, nom, 'AGENT',
                            service=svc, direction=direction, sous_direction=sd,
                        )
                        agent_ag, _ = Agent.objects.get_or_create(
                            user=user_ag,
                            defaults={
                                'nom': nom.upper(),
                                'prenom': prenom,
                                'matricule': next_mat(sigle),
                                'poste': f'Technicien {svc_nom}',
                                'service': svc,
                            }
                        )
                        service_users.append(user_ag)

                    all_users_by_service[svc.id] = service_users
                    self.stdout.write(f'    ✓ {svc_nom}: {len(service_users)} agents')

        return all_users_by_service

    # ──────────────────────────────────────────────────────────────────────────
    def _create_presence(self, rng, all_agents):
        today = date.today()
        start_date = today - timedelta(days=90)

        # Build list of working days
        working_days = []
        d = start_date
        while d <= today:
            if d.weekday() < 5:  # Monday–Friday
                working_days.append(d)
            d += timedelta(days=1)

        presence_bulk = []
        existing = set(Presence.objects.values_list('agent_id', 'date_presence'))

        for user in all_agents:
            try:
                agent = Agent.objects.get(user=user)
            except Agent.DoesNotExist:
                continue

            profile_name = rng.choice(PROFILE_WEIGHTS)
            prof = PROFILES[profile_name]
            # Store on user for later use in tâches/diligences scoring
            user._perf_profile = profile_name

            for work_day in working_days:
                if (agent.id, work_day) in existing:
                    continue

                roll = rng.random()
                if roll > prof['presence']:
                    # Absent
                    statut = rng.choice(['absent', 'en mission', 'permission accordée'])
                    presence_bulk.append(Presence(
                        agent=agent,
                        date_presence=work_day,
                        statut=statut,
                        latitude=LAT,
                        longitude=LON,
                        localisation_valide=False,
                    ))
                else:
                    # Présent — with possible lateness
                    if rng.random() > prof['ponctualite']:
                        # Late
                        h = rng.randint(8, 10)
                        m = rng.randint(31 if h == 8 else 0, 59)
                        arrivee = time(h, m)
                    else:
                        # On time
                        h = rng.randint(7, 8)
                        m = rng.randint(0, 29) if h == 8 else rng.randint(30, 59)
                        arrivee = time(h, m)

                    depart_h = rng.randint(16, 18)
                    depart_m = rng.randint(0, 59)
                    depart = time(depart_h, depart_m)

                    presence_bulk.append(Presence(
                        agent=agent,
                        date_presence=work_day,
                        heure_arrivee=arrivee,
                        heure_depart=depart,
                        statut='présent',
                        latitude=LAT,
                        longitude=LON,
                        localisation_valide=True,
                    ))

        Presence.objects.bulk_create(presence_bulk, ignore_conflicts=True)
        self.stdout.write(f'  Created {len(presence_bulk)} presence records')

    # ──────────────────────────────────────────────────────────────────────────
    def _create_courriers(self, rng, directions_map, services_map, all_agents):
        today = date.today()
        all_courriers = []
        ref_counter = {'n': Courrier.objects.count() + 1}

        def next_ref(sens, d):
            n = ref_counter['n']
            ref_counter['n'] += 1
            prefix = 'CA' if sens == 'arrivee' else 'CD'
            return f'LANEMA-{prefix}-{d.strftime("%Y%m")}-{n:04d}'

        for dir_data in LANEMA_ORG:
            sigle = dir_data['sigle']
            direction = directions_map[sigle]

            # Get services for this direction
            dir_services = [svc for (s, _, _), svc in services_map.items() if s == sigle]
            if not dir_services:
                continue

            dir_users = [u for u in all_agents
                         if hasattr(u, 'profile') and u.profile.direction == direction]
            if not dir_users:
                dir_users = all_agents[:5]

            # Generate 20 arrivée + 15 départ courriers per direction (over 3 months)
            for i in range(20):
                jours_ago = rng.randint(1, 90)
                date_rec = today - timedelta(days=jours_ago)
                service = rng.choice(dir_services)
                objet = rng.choice(OBJETS_COURRIER_ARRIVEE)
                expediteur = rng.choice(EXPEDITEURS_ARRIVEE)

                # Statut based on age
                if jours_ago > 30:
                    statut = rng.choice(['traite', 'termine', 'archive', 'archive'])
                elif jours_ago > 10:
                    statut = rng.choice(['traite', 'en_cours', 'en_attente'])
                else:
                    statut = rng.choice(['nouveau', 'en_attente', 'en_cours'])

                ref = next_ref('arrivee', date_rec)
                if Courrier.objects.filter(reference=ref).exists():
                    continue
                c = Courrier.objects.create(
                    reference=ref,
                    objet=objet,
                    expediteur=expediteur,
                    destinataire='Directeur Général LANEMA',
                    sens='arrivee',
                    date_reception=date_rec,
                    service=service,
                    statut=statut,
                    categorie=rng.choice(['Demande', 'Invitation', 'Réclamation', 'Autre']),
                    niveau_urgence=rng.choice(['normal', 'normal', 'normal', 'haute', 'critique']),
                    date_traitement=date_rec + timedelta(days=rng.randint(2, 10)) if statut in ['traite', 'termine'] else None,
                )
                all_courriers.append(c)

                # Imputer to some agents
                for u in rng.sample(dir_users[:min(len(dir_users), 5)], min(2, len(dir_users))):
                    CourrierImputation.objects.get_or_create(
                        courrier=c, user=u,
                        defaults={'access_type': 'view', 'granted_by': dir_users[0]},
                    )

            for i in range(15):
                jours_ago = rng.randint(1, 90)
                date_rec = today - timedelta(days=jours_ago)
                service = rng.choice(dir_services)
                objet = rng.choice(OBJETS_COURRIER_DEPART)
                dest = rng.choice(EXPEDITEURS_ARRIVEE)

                statut = rng.choice(['traite', 'termine']) if jours_ago > 5 else rng.choice(['en_cours', 'nouveau'])
                ref = next_ref('depart', date_rec)
                if Courrier.objects.filter(reference=ref).exists():
                    continue
                c = Courrier.objects.create(
                    reference=ref,
                    objet=objet,
                    expediteur='LANEMA',
                    destinataire=dest,
                    sens='depart',
                    date_reception=date_rec,
                    service=service,
                    statut=statut,
                    categorie=rng.choice(['Demande', 'Invitation', 'Autre']),
                    niveau_urgence=rng.choice(['normal', 'normal', 'haute']),
                    date_traitement=date_rec + timedelta(days=rng.randint(1, 5)) if statut in ['traite', 'termine'] else None,
                )
                all_courriers.append(c)

        self.stdout.write(f'  Created {len(all_courriers)} courriers')
        return all_courriers

    # ──────────────────────────────────────────────────────────────────────────
    def _create_diligences(self, rng, directions_map, services_map, all_agents, all_courriers):
        today = date.today()
        dil_count = 0

        # Get DG user as créateur
        dg_user = User.objects.filter(username='lanema.dg.directeur').first() or all_agents[0]

        for dir_data in LANEMA_ORG:
            sigle = dir_data['sigle']
            direction = directions_map[sigle]

            dir_users = [u for u in all_agents
                         if hasattr(u, 'profile') and u.profile.direction == direction]
            if not dir_users:
                continue

            dir_courriers = [c for c in all_courriers
                             if c.service and c.service.sous_direction and
                             c.service.sous_direction.direction == direction]

            # 8–12 diligences per direction
            for i in range(rng.randint(8, 12)):
                jours_ago = rng.randint(5, 85)
                date_creation = today - timedelta(days=jours_ago)
                date_limite = date_creation + timedelta(days=rng.randint(5, 30))
                assigned = rng.sample(dir_users, min(rng.randint(1, 3), len(dir_users)))

                # Performance-aware statut
                if date_limite < today:
                    p_names = [getattr(u, '_perf_profile', 'moyen') for u in assigned]
                    avg_profile = p_names[0] if p_names else 'moyen'
                    if avg_profile == 'excellent':
                        statut = rng.choice(['termine', 'termine', 'archivee'])
                    elif avg_profile == 'bon':
                        statut = rng.choice(['termine', 'en_cours', 'en_correction'])
                    elif avg_profile == 'moyen':
                        statut = rng.choice(['en_cours', 'en_attente', 'termine'])
                    else:
                        statut = rng.choice(['en_attente', 'en_cours'])
                else:
                    statut = rng.choice(['en_attente', 'en_cours', 'en_cours', 'demande_validation', 'termine'])

                if statut == 'termine':
                    avancement = 100
                elif statut == 'demande_validation':
                    avancement = rng.randint(85, 99)
                elif statut == 'en_correction':
                    avancement = rng.randint(60, 85)
                elif statut == 'en_cours':
                    avancement = rng.randint(20, 80)
                else:
                    avancement = rng.randint(0, 20)

                expediteur = rng.choice(EXPEDITEURS_ARRIVEE)
                objet = rng.choice(DIL_OBJETS).format(expediteur)

                ref = f'DIL-{sigle}-{date_creation.strftime("%d%m%Y")}-{dil_count + 1:03d}'
                dil = Diligence.objects.create(
                    reference_courrier=ref,
                    type_diligence=rng.choice(['courrier', 'spontanee']),
                    objet=objet,
                    expediteur=expediteur,
                    statut=statut,
                    domaine=rng.choice(['formation', 'logistique', 'budget', 'communication', 'atelier', 'evenements', 'autre']),
                    categorie=rng.choice(['NORMAL', 'URGENT', 'BASSE']),
                    date_limite=date_limite,
                    pourcentage_avancement=avancement,
                    direction=direction,
                )
                dil.agents.set(assigned)
                dil_count += 1

        self.stdout.write(f'  Created {dil_count} diligences')

    # ──────────────────────────────────────────────────────────────────────────
    def _create_taches(self, rng, all_agents):
        today = date.today()
        tache_count = 0

        for user in all_agents:
            profile_name = getattr(user, '_perf_profile', rng.choice(PROFILE_WEIGHTS))
            prof = PROFILES[profile_name]
            n_taches = rng.randint(3, 6)

            for i in range(n_taches):
                jours_ago = rng.randint(10, 80)
                date_debut = today - timedelta(days=jours_ago)
                duree = rng.randint(5, 25)
                date_fin_prevue = date_debut + timedelta(days=duree)

                if date_fin_prevue < today:
                    if rng.random() < prof['completion']:
                        etat = 'terminee'
                        date_fin_effective = date_fin_prevue + timedelta(days=rng.randint(-2, 3))
                        avancement = 100
                    else:
                        etat = rng.choice(['en_cours', 'en_attente'])
                        date_fin_effective = None
                        avancement = rng.randint(20, 70)
                else:
                    etat = rng.choice(['a_faire', 'en_cours', 'en_cours'])
                    date_fin_effective = None
                    avancement = rng.randint(0, 60)

                Tache.objects.create(
                    titre=rng.choice(TACHE_TITRES),
                    description=f'Tâche assignée dans le cadre des activités du service.',
                    responsable=user,
                    etat=etat,
                    priorite=rng.choice(['basse', 'moyenne', 'moyenne', 'haute']),
                    date_debut=date_debut,
                    date_fin_prevue=date_fin_prevue,
                    date_fin_effective=date_fin_effective if etat == 'terminee' else None,
                    pourcentage_avancement=avancement,
                )
                tache_count += 1

        self.stdout.write(f'  Created {tache_count} tâches')

    # ──────────────────────────────────────────────────────────────────────────
    def _create_rh_data(self, rng, all_agents):
        today = date.today()
        admin_user = User.objects.filter(is_superuser=True).first() or all_agents[0]

        # Create shared formations (available to all)
        formations = []
        formation_titles = [
            ('ISO/IEC 17025 – Exigences pour les laboratoires', 24),
            ('Métrologie et traçabilité des mesures', 16),
            ('Management de la qualité ISO 9001', 16),
            ('Techniques d\'analyse chimique avancée', 32),
            ('Hygiène et sécurité au laboratoire', 8),
            ('Informatique et gestion de données (LIMS)', 24),
            ('Communication et rédaction administrative', 16),
            ('Leadership et management d\'équipe', 24),
            ('Anglais technique', 40),
            ('Accréditation et conformité réglementaire', 16),
        ]
        for title, duree in formation_titles:
            date_form = today - timedelta(days=rng.randint(30, 300))
            f, _ = FormationRH.objects.get_or_create(
                titre=title,
                defaults={
                    'date_debut': date_form,
                    'date_fin': date_form + timedelta(days=duree // 8),
                    'duree_heures': duree,
                    'lieu': rng.choice(['LANEMA Abidjan', 'CFPA', 'ECCA', 'INPHB', 'Paris – LNE']),
                    'organisateur': rng.choice(['LANEMA', 'OIEA', 'OIML', 'ISO', 'AFNOR', 'LNE']),
                    'statut': 'terminee',
                    'created_by': admin_user,
                }
            )
            formations.append(f)

        evaluation_count = fiche_count = mission_count = doc_count = inscr_count = 0

        for idx, user in enumerate(all_agents):
            profile_name = getattr(user, '_perf_profile', 'bon')
            prof = PROFILES[profile_name]

            # --- Fiche Agent ---
            birth_year = rng.randint(1975, 1998)
            birthday = date(birth_year, rng.randint(1, 12), rng.randint(1, 28))
            service = getattr(user.profile, 'service', None) if hasattr(user, 'profile') else None
            direction = getattr(user.profile, 'direction', None) if hasattr(user, 'profile') else None
            sous_dir = getattr(user.profile, 'sous_direction', None) if hasattr(user, 'profile') else None

            mat = f'FA-LAN-{user.id:06d}'
            if not FicheAgent.objects.filter(user=user).exists() and not FicheAgent.objects.filter(matricule=mat).exists():
                FicheAgent.objects.create(
                    user=user,
                    matricule=mat,
                    nom=user.last_name.upper(),
                    prenoms=user.first_name,
                    grade=rng.choice(['Ingénieur', 'Technicien Supérieur', 'Technicien', 'Agent de Maîtrise', 'Cadre']),
                    emploi=rng.choice(['Laborantin', 'Ingénieur d\'Études', 'Technicien d\'Analyses', 'Chargé de Projets', 'Gestionnaire']),
                    fonction=f"Agent - {service.nom if service else 'LANEMA'}",
                    direction=direction,
                    service=service,
                    sous_direction=sous_dir,
                    date_prise_service=birthday + timedelta(days=365 * rng.randint(2, 10)),
                    date_naissance=birthday,
                    lieu_naissance=rng.choice(['Abidjan', 'Bouaké', 'Yamoussoukro', 'San-Pédro', 'Daloa', 'Korhogo', 'Man']),
                    situation_matrimoniale=rng.choice(['celibataire', 'marie', 'marie', 'divorce']),
                    nombre_enfants=rng.randint(0, 5),
                    telephone=f'+225 07 {rng.randint(10,99)} {rng.randint(10,99)} {rng.randint(10,99)}',
                    email_professionnel=f'{user.username}@lanema.ci',
                    adresse=f'Lot {rng.randint(1,500)}, {rng.choice(["Cocody", "Plateau", "Marcory", "Yopougon", "Abobo", "Adjamé"])}, Abidjan',
                    statut='actif',
                    contact_urgence_nom=f'{rng.choice(PRENOMS_H)} {rng.choice(NOMS)}',
                    contact_urgence_tel=f'+225 05 {rng.randint(10,99)} {rng.randint(10,99)} {rng.randint(10,99)}',
                )
                fiche_count += 1

            # --- Évaluations (2 années) ---
            evaluateur = admin_user
            for yr in [2024, 2025]:
                note = rng.gauss(
                    {'excellent': 17, 'bon': 14, 'moyen': 11, 'faible': 7}[profile_name],
                    1.5
                )
                note = max(0, min(20, note))
                if note >= 16:
                    mention = 'excellent'
                elif note >= 14:
                    mention = 'tres_bien'
                elif note >= 12:
                    mention = 'bien'
                elif note >= 10:
                    mention = 'satisfaisant'
                else:
                    mention = 'insuffisant'

                if not EvaluationRH.objects.filter(agent=user, annee=yr).exists():
                    EvaluationRH.objects.create(
                        agent=user,
                        evaluateur=evaluateur,
                        annee=yr,
                        periode='Annuelle',
                        note_globale=round(note, 1),
                        mention=mention,
                        ponctualite=round(rng.gauss(note, 1), 1),
                        assiduite=round(rng.gauss(note, 1), 1),
                        competence=round(rng.gauss(note, 1), 1),
                        initiative=round(rng.gauss(note, 1), 1),
                        travail_equipe=round(rng.gauss(note, 1), 1),
                        rendement=round(rng.gauss(note, 1), 1),
                        appreciation=f'Agent {mention.replace("_", " ")}. Donne satisfaction dans ses fonctions.',
                        objectifs_atteints='Réalisation des analyses assignées dans les délais.',
                        objectifs_prochaine_periode='Améliorer les délais de rendu des résultats.',
                    )
                    evaluation_count += 1

            # --- Missions (1–2 par agent) ---
            n_missions = rng.randint(0, 2)
            for m_i in range(n_missions):
                date_m = today - timedelta(days=rng.randint(10, 280))
                duree_m = rng.randint(2, 7)
                statut_m = rng.choice(['terminee', 'terminee', 'validee', 'archivee'])
                MissionRH.objects.create(
                    agent=user,
                    objet=rng.choice([
                        "Participation à une conférence internationale sur la métrologie",
                        "Mission de contrôle métrologique en région",
                        "Formation technique à l'étranger",
                        "Audit qualité chez un client industriel",
                        "Réunion de normalisation à Genève",
                        "Inspection sur site – Bouaké",
                        "Accompagnement expert ONU – accréditation",
                    ]),
                    destination=rng.choice(['Bouaké', 'Abidjan', 'Genève', 'Paris', 'Dakar', 'San-Pédro', 'Yamoussoukro']),
                    date_debut=date_m,
                    date_fin=date_m + timedelta(days=duree_m),
                    vehicule=rng.choice([True, False]),
                    frais_alloues=rng.choice([50000, 100000, 150000, 200000, 250000]),
                    ordre_mission_num=f'OM-{date_m.year}-{rng.randint(1000,9999)}',
                    statut=statut_m,
                )
                mission_count += 1

            # --- Inscriptions formations (2–3 par agent) ---
            chosen_formations = rng.sample(formations, min(rng.randint(2, 3), len(formations)))
            for form in chosen_formations:
                if not InscriptionFormationRH.objects.filter(formation=form, agent=user).exists():
                    statut_insc = rng.choice(['certifie', 'certifie', 'present', 'absent'])
                    note_insc = rng.uniform(10, 20) if statut_insc == 'certifie' else None
                    InscriptionFormationRH.objects.create(
                        formation=form,
                        agent=user,
                        statut=statut_insc,
                        note=round(note_insc, 1) if note_insc else None,
                        observations='Participation satisfaisante.' if statut_insc != 'absent' else 'Agent absent sans motif.',
                    )
                    inscr_count += 1

            # --- Documents RH (3 par agent) ---
            doc_types = rng.sample(['arrete', 'decision', 'affectation', 'promotion', 'contrat', 'diplome', 'acte'], 3)
            for dt in doc_types:
                date_d = today - timedelta(days=rng.randint(365, 365 * 5))
                DocumentRH.objects.create(
                    agent=user,
                    type_document=dt,
                    titre={
                        'arrete': "Arrêté de nomination",
                        'decision': "Décision d'avancement",
                        'affectation': "Lettre d'affectation au LANEMA",
                        'promotion': "Décision de promotion de grade",
                        'contrat': "Contrat de travail LANEMA",
                        'diplome': "Diplôme d'ingénieur ou BTS",
                        'acte': "Acte de naissance",
                    }.get(dt, "Document administratif"),
                    reference=f'{dt.upper()[:3]}-{date_d.year}-{rng.randint(100,9999)}',
                    date_document=date_d,
                    signataire=rng.choice(['Directeur Général', 'Ministre du Commerce', 'DRH LANEMA']),
                    description='Document archivé dans le dossier RH.',
                    created_by=admin_user,
                )
                doc_count += 1

        self.stdout.write(f'  Created {fiche_count} fiches agents, {evaluation_count} évaluations, '
                          f'{mission_count} missions, {inscr_count} inscriptions formations, {doc_count} documents RH')

    # ──────────────────────────────────────────────────────────────────────────
    def _create_demandes(self, rng, all_agents):
        today = date.today()
        conge_count = abs_count = 0

        for user in all_agents:
            profile_name = getattr(user, '_perf_profile', 'bon')
            # More absences for faible/moyen profiles
            n_conges  = {'excellent': 1, 'bon': 1, 'moyen': 2, 'faible': 3}[profile_name]
            n_absences = {'excellent': 0, 'bon': 1, 'moyen': 2, 'faible': 4}[profile_name]

            for c_i in range(n_conges):
                start = today - timedelta(days=rng.randint(10, 300))
                duree = rng.randint(5, 21)
                statut = rng.choice(['approuve', 'approuve', 'rejete', 'en_attente'])
                DemandeConge.objects.create(
                    demandeur=user,
                    matricule=f'MAT-{user.username[-6:].upper()}',
                    emploi='Technicien LANEMA',
                    fonction='Agent',
                    type_conge=rng.choice(['annuel', 'maladie', 'exceptionnel']),
                    date_debut=start,
                    date_fin=start + timedelta(days=duree),
                    nombre_jours=duree,
                    motif=rng.choice([
                        "Congé annuel réglementaire",
                        "Raisons familiales impérieuses",
                        "Maladie avec certificat médical",
                        "Congé maternité",
                    ]),
                    adresse_conge=f'Abidjan, Quartier {rng.choice(["Cocody", "Marcory", "Yopougon"])}',
                    telephone_conge=f'+225 07 {rng.randint(10,99)} {rng.randint(10,99)} {rng.randint(10,99)}',
                    statut=statut,
                )
                conge_count += 1

            for a_i in range(n_absences):
                start = today - timedelta(days=rng.randint(5, 60))
                duree_h = rng.choice([2, 3, 4, 8])
                statut = rng.choice(['approuve', 'approuve', 'rejete', 'en_attente'])
                DemandeAbsence.objects.create(
                    demandeur=user,
                    matricule=f'MAT-{user.username[-6:].upper()}',
                    emploi='Technicien LANEMA',
                    fonction='Agent',
                    type_absence=rng.choice(['medicale', 'personnelle', 'familiale', 'administrative']),
                    date_debut=timezone.make_aware(datetime.combine(start, time(8, 0))),
                    date_fin=timezone.make_aware(datetime.combine(start, time(8 + duree_h, 0))),
                    duree_heures=duree_h,
                    motif=rng.choice([
                        "Rendez-vous médical",
                        "Démarche administrative urgente",
                        "Raison familiale",
                    ]),
                    statut=statut,
                )
                abs_count += 1

        self.stdout.write(f'  Created {conge_count} demandes congé, {abs_count} demandes absence')
