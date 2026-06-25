"""
Seed complet — Docteur MEDI KOUASSI, Directeur des Études et Analyses
Laboratoire National d'Essais, de la Métrologie et de l'Analyse (LANEMA)
Ministère du Commerce, de l'Industrie et de l'Artisanat de Côte d'Ivoire

Usage:
    python manage.py seed_medi
    python manage.py seed_medi --reset   (supprime d'abord les données existantes)
"""
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.utils import timezone


def dummy_file(name, content_text):
    content = f"%PDF-1.4\n%% {content_text}\n%% LANEMA — Seed data".encode()
    return ContentFile(content, name=name)


class Command(BaseCommand):
    help = "Seed données complètes Dr MEDI / LANEMA / MCIA"

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Supprimer les données du seed avant de recréer")

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("=== SEED DR MEDI / LANEMA ==="))
        self._structure()
        self._users()
        self._courriers()
        self._diligences()
        self._conges_absences()
        self._reunions_rdv()
        self._projets_taches()
        self._ged()
        self._personnel()
        self.stdout.write(self.style.SUCCESS("\n=== SEED TERMINÉ ==="))
        self.stdout.write(f"  Connexion Dr Medi : dr.medi / Lanema2024!")

    # ── 1. Structure ────────────────────────────────────────────
    def _structure(self):
        from core.models import Direction, SousDirection, Service
        self.stdout.write("  → Structure organisationnelle…")

        self.ministere, _ = Direction.objects.get_or_create(
            nom="Ministère du Commerce, de l'Industrie et de l'Artisanat",
            defaults={"type_direction": "cabinet",
                      "description": "Ministère en charge du commerce, de l'industrie et de l'artisanat de Côte d'Ivoire"}
        )
        self.cabinet, _ = Direction.objects.get_or_create(
            nom="Cabinet du Ministre du Commerce et de l'Industrie",
            defaults={"type_direction": "cabinet",
                      "description": "Cabinet ministériel — coordination et communication"}
        )
        self.dg, _ = Direction.objects.get_or_create(
            nom="Direction Générale du Commerce et de la Consommation",
            defaults={"type_direction": "direction_generale",
                      "description": "DGCC — coordination des directions techniques"}
        )
        self.lanema, _ = Direction.objects.get_or_create(
            nom="LANEMA — Laboratoire National d'Essais, de la Métrologie et de l'Analyse",
            defaults={"type_direction": "direction",
                      "description": "Laboratoire officiel de contrôle qualité de Côte d'Ivoire"}
        )

        self.sd_analyses, _ = SousDirection.objects.get_or_create(
            nom="Direction des Études et Analyses",
            direction=self.lanema,
            defaults={"description": "Études, recherches et analyses de laboratoire"}
        )
        self.sd_qualite, _ = SousDirection.objects.get_or_create(
            nom="Direction du Contrôle Qualité",
            direction=self.lanema,
            defaults={"description": "Contrôle et certification de la qualité des produits"}
        )
        self.sd_admin, _ = SousDirection.objects.get_or_create(
            nom="Direction Administrative et Financière",
            direction=self.lanema,
            defaults={"description": "Ressources humaines, budget et logistique"}
        )

        self.svc_labo, _ = Service.objects.get_or_create(
            nom="Service Laboratoire Chimique",
            sous_direction=self.sd_analyses,
            defaults={"description": "Analyses chimiques et microbiologiques"}
        )
        self.svc_etudes, _ = Service.objects.get_or_create(
            nom="Service Études et Recherche",
            sous_direction=self.sd_analyses,
            defaults={"description": "Recherche appliquée et veille scientifique"}
        )
        self.svc_certif, _ = Service.objects.get_or_create(
            nom="Service Certification",
            sous_direction=self.sd_qualite,
            defaults={"description": "Certification des produits et laboratoires"}
        )

        self.stdout.write(self.style.SUCCESS("    ✓ 4 directions + 3 sous-directions + 3 services"))

    # ── 2. Utilisateurs ─────────────────────────────────────────
    def _users(self):
        from core.models import UserProfile, Site
        self.stdout.write("  → Comptes utilisateurs…")

        site, _ = Site.objects.get_or_create(
            nom="LANEMA — Siège Abidjan",
            defaults={"type_site": "siege", "ville": "Abidjan",
                      "adresse": "Rue du Commerce, Plateau, Abidjan"}
        )

        def make(username, first, last, email, role, dir_=None, sd=None, svc=None, staff=False):
            u, created = User.objects.get_or_create(
                username=username,
                defaults={"first_name": first, "last_name": last,
                          "email": email, "is_staff": staff, "is_active": True}
            )
            if created:
                u.set_password("Lanema2024!")
                u.save()
            p, _ = UserProfile.objects.get_or_create(user=u)
            p.role = role
            p.direction = dir_ or self.lanema
            p.sous_direction = sd
            p.service = svc
            p.site = site
            p.save()
            return u

        self.medi       = make("dr.medi",     "Medi",        "KOUASSI",  "medi.kouassi@lanema.ci",   "DIRECTEUR", self.lanema, self.sd_analyses)
        self.agent1     = make("aya.kone",     "Aya",         "KONÉ",     "aya.kone@lanema.ci",        "AGENT",     self.lanema, self.sd_analyses, self.svc_labo)
        self.agent2     = make("jean.brou",    "Jean",        "BROU",     "jean.brou@lanema.ci",       "AGENT",     self.lanema, self.sd_analyses, self.svc_etudes)
        self.agent3     = make("fatou.diallo", "Fatou",       "DIALLO",   "fatou.diallo@lanema.ci",    "AGENT",     self.lanema, self.sd_qualite,  self.svc_certif)
        self.secretaire = make("sec.lanema",   "Marie-Louise","ADOU",     "secretariat@lanema.ci",     "SECRETAIRE",self.lanema, self.sd_admin)
        self.dg_user    = make("dg.lanema",    "Pascal",      "GNAGNE",   "dg@lanema.ci",              "DIRECTEUR", self.lanema)
        self.admin      = make("admin.lanema", "Admin",       "LANEMA",   "admin@lanema.ci",           "ADMIN",     self.lanema, staff=True)

        self.stdout.write(self.style.SUCCESS("    ✓ 7 utilisateurs  (mdp : Lanema2024!)"))

    # ── 3. Courriers ────────────────────────────────────────────
    def _courriers(self):
        from core.models import Courrier, CourrierImputation, CourrierInstruction
        self.stdout.write("  → Courriers…")
        today = date.today()

        data = [
            ("LANEMA-ARR-001-2026", "arrivee", "ordinaire", "en_cours",   "Demande",    "Demande d'analyse de conformité — produits cosmétiques",                    "Entreprise BEAUTY AFRICA SARL",             "Dr MEDI — Direction des Analyses",     today-timedelta(10)),
            ("LANEMA-ARR-002-2026", "arrivee", "ordinaire", "traite",     "Invitation", "Invitation — Forum Qualité Abidjan 2026",                                   "Chambre de Commerce CCI-CI",                "Directeur LANEMA",                     today-timedelta(15)),
            ("LANEMA-ARR-003-2026", "arrivee", "confidentiel","en_attente","Réclamation","Réclamation — résultats d'analyse lot N°2025-089",                         "Groupe PHARMACI SA",                        "Direction des Analyses LANEMA",        today-timedelta(5)),
            ("LANEMA-ARR-004-2026", "arrivee", "ordinaire", "nouveau",    "Demande",    "Demande certification ISO 17025 — renouvellement 2026",                     "Accréditation Africa Bureau",               "Direction LANEMA",                     today-timedelta(2)),
            ("LANEMA-ARR-005-2026", "arrivee", "ordinaire", "traite",     "Autre",      "Note circulaire — procédures contrôle qualité des importations",            "Direction Générale du Commerce",            "Toutes directions techniques MCIA",    today-timedelta(20)),
            ("LANEMA-DEP-001-2026", "depart",  "ordinaire", "traite",     "Autre",      "Rapport d'analyse — lot cosmétiques BEAUTY AFRICA",                         "Dr MEDI KOUASSI, Directeur",                "BEAUTY AFRICA SARL",                   today-timedelta(7)),
            ("LANEMA-DEP-002-2026", "depart",  "ordinaire", "traite",     "Autre",      "Avis technique — conformité produits alimentaires lot 2026-003",            "LANEMA — Direction des Analyses",           "Direction Générale du Commerce",       today-timedelta(12)),
            ("LANEMA-DEP-003-2026", "depart",  "ordinaire", "nouveau",    "Autre",      "Convocation — réunion technique métrologie légale",                         "Dr MEDI KOUASSI, Directeur",                "Chefs de service LANEMA",              today-timedelta(1)),
            ("LANEMA-DEP-004-2026", "depart",  "ordinaire", "traite",     "Autre",      "Rapport mensuel d'activités — Direction Études et Analyses, Juin 2026",     "Direction des Études et Analyses LANEMA",   "Direction Générale LANEMA",            today-timedelta(30)),
            ("LANEMA-DEP-005-2026", "depart",  "ordinaire", "en_cours",   "Demande",    "Demande de dotation réactifs laboratoire Q3 2026",                          "Dr MEDI KOUASSI",                           "Direction Administrative et Financière",today-timedelta(3)),
        ]

        self.courriers = []
        for ref, sens, type_c, statut, cat, objet, exped, dest, date_rec in data:
            c, created = Courrier.objects.get_or_create(
                reference=ref,
                defaults=dict(sens=sens, type_courrier=type_c, statut=statut,
                              categorie=cat, objet=objet, expediteur=exped,
                              destinataire=dest, date_reception=date_rec,
                              service=self.svc_etudes)
            )
            if created:
                c.fichier_joint.save(f"{ref}.pdf", dummy_file(f"{ref}.pdf", objet), save=True)
                CourrierImputation.objects.get_or_create(
                    courrier=c, user=self.medi, access_type="edit",
                    defaults={"granted_by": self.admin}
                )
            self.courriers.append(c)

        instructions = ["urgent", "examen_reponse", "attribution", "information", "classer_archiver"]
        for i, c in enumerate(self.courriers[:5]):
            CourrierInstruction.objects.get_or_create(
                courrier=c, creee_par=self.medi,
                defaults={"instructions": instructions[i],
                          "commentaire": f"Traitement requis — {c.objet[:60]}"}
            )

        self.stdout.write(self.style.SUCCESS(f"    ✓ {len(self.courriers)} courriers (5 arrivée + 5 départ)"))

    # ── 4. Diligences ───────────────────────────────────────────
    def _diligences(self):
        from core.models import Diligence
        self.stdout.write("  → Diligences…")
        today = date.today()

        items = [
            dict(reference_courrier="LANEMA-ARR-001-2026",
                 objet="Analyse conformité produits cosmétiques BEAUTY AFRICA",
                 instructions="Analyses physico-chimiques et microbiologiques. Rapport sous 15 jours.",
                 statut="en_cours", categorie="URGENT", domaine="representations",
                 date_limite=today+timedelta(5), pourcentage_avancement=60,
                 type_diligence="courrier",
                 agents=[self.agent1], services=[self.svc_labo]),
            dict(reference_courrier="LANEMA-ARR-002-2026",
                 objet="Préparation communication Forum Qualité Abidjan 2026",
                 instructions="Présentation 20 slides sur activités LANEMA.",
                 statut="en_cours", categorie="NORMAL", domaine="communication",
                 date_limite=today+timedelta(20), pourcentage_avancement=30,
                 type_diligence="courrier",
                 agents=[self.agent2], services=[self.svc_etudes]),
            dict(reference_courrier="LANEMA-ARR-003-2026",
                 objet="Traitement réclamation PHARMACI — révision lot 2025-089",
                 instructions="Analyser réclamation, vérifier protocoles, préparer réponse officielle.",
                 statut="demande_validation", categorie="URGENT", domaine="representations",
                 date_limite=today+timedelta(2), pourcentage_avancement=90,
                 type_diligence="courrier",
                 agents=[self.medi, self.agent1], services=[self.svc_labo]),
            dict(reference_courrier="LANEMA-DEP-004-2026",
                 objet="Rapport mensuel d'activités — Juin 2026",
                 instructions="Consolider statistiques d'analyses, taux conformité et activités direction.",
                 statut="termine", categorie="NORMAL", domaine="budget",
                 date_limite=today-timedelta(5), pourcentage_avancement=100,
                 type_diligence="courrier",
                 agents=[self.agent2], services=[self.svc_etudes]),
            dict(reference_courrier="LANEMA-DEP-005-2026",
                 objet="Besoins réactifs laboratoire Q3 2026",
                 instructions="Inventaire stocks actuels et projection besoins Q3.",
                 statut="en_attente", categorie="NORMAL", domaine="budget",
                 date_limite=today+timedelta(10), pourcentage_avancement=0,
                 type_diligence="courrier",
                 agents=[self.agent1, self.agent2], services=[self.svc_labo]),
            dict(reference_courrier="DIL-SPONT-001-2026",
                 objet="Mise à jour manuel qualité LANEMA — révision annuelle",
                 instructions="Réviser procédures, intégrer nouvelles normes ISO, soumettre pour validation.",
                 statut="en_cours", categorie="NORMAL", domaine="autre",
                 date_limite=today+timedelta(45), pourcentage_avancement=20,
                 type_diligence="spontanee",
                 agents=[self.medi, self.agent2, self.agent3], services=[self.svc_certif]),
            dict(reference_courrier="DIL-SPONT-002-2026",
                 objet="Formation — nouvelles techniques d'analyse spectrométrique",
                 instructions="Organiser session de formation interne 3 jours. Programme et supports.",
                 statut="en_attente", categorie="NORMAL", domaine="formation",
                 date_limite=today+timedelta(30), pourcentage_avancement=0,
                 type_diligence="spontanee",
                 agents=[self.agent1, self.agent2], services=[self.svc_labo, self.svc_etudes]),
        ]

        self.diligences = []
        for d in items:
            agents  = d.pop("agents")
            services = d.pop("services")
            dil, created = Diligence.objects.get_or_create(
                reference_courrier=d["reference_courrier"],
                defaults={**d, "direction": self.lanema}
            )
            if created:
                dil.agents.set(agents)
                dil.services_concernes.set(services)
                dil.fichier_joint.save(
                    f"dil_{dil.id}.pdf",
                    dummy_file(f"dil_{dil.id}.pdf", d["objet"]),
                    save=True
                )
            self.diligences.append(dil)

        self.stdout.write(self.style.SUCCESS(f"    ✓ {len(self.diligences)} diligences"))

    # ── 5. Congés & Absences ────────────────────────────────────
    def _conges_absences(self):
        from core.models import DemandeConge, DemandeAbsence
        self.stdout.write("  → Congés et Absences…")
        today = date.today()
        now   = timezone.now()

        conges = [
            dict(demandeur=self.medi,       type_conge="annuel",
                 date_debut=today+timedelta(30), date_fin=today+timedelta(44),
                 motif="Congé annuel de repos été 2026",
                 adresse_conge="Résidence Cocody-Riviera, Abidjan",
                 telephone_conge="0700112233", statut="approuve",
                 matricule="MCIA-LAB-001", emploi="Directeur des Études et Analyses",
                 fonction="Directeur", directeur=self.dg_user),
            dict(demandeur=self.agent1,     type_conge="maladie",
                 date_debut=today-timedelta(5), date_fin=today-timedelta(2),
                 motif="Indisposition médicale avec ordonnance",
                 adresse_conge="Yopougon Selmer, Abidjan",
                 telephone_conge="0757884455", statut="approuve",
                 matricule="MCIA-LAB-002", emploi="Technicienne de laboratoire",
                 fonction="Agent technique", directeur=self.medi),
            dict(demandeur=self.agent2,     type_conge="formation",
                 date_debut=today+timedelta(10), date_fin=today+timedelta(14),
                 motif="Formation spectrométrie de masse — Dakar, Sénégal",
                 adresse_conge="Hôtel Terrou-Bi, Dakar, Sénégal",
                 telephone_conge="0506771234", statut="en_attente",
                 matricule="MCIA-LAB-003", emploi="Chargé d'études",
                 fonction="Agent technique", directeur=self.medi),
            dict(demandeur=self.secretaire, type_conge="maternite",
                 date_debut=today+timedelta(60), date_fin=today+timedelta(144),
                 motif="Congé de maternité",
                 adresse_conge="Abobo Anador, Abidjan",
                 telephone_conge="0787654321", statut="approuve",
                 matricule="MCIA-LAB-004", emploi="Secrétaire de direction",
                 fonction="Secrétaire", directeur=self.medi),
        ]
        for c in conges:
            DemandeConge.objects.get_or_create(
                demandeur=c["demandeur"], date_debut=c["date_debut"], defaults=c
            )

        absences = [
            dict(demandeur=self.medi,   type_absence="administrative",
                 date_debut=now-timedelta(days=3), date_fin=now-timedelta(days=3)+timedelta(hours=4),
                 duree_heures=4,
                 motif="Réunion interministérielle — Ministère du Commerce",
                 statut="approuve", directeur=self.dg_user),
            dict(demandeur=self.agent1, type_absence="medicale",
                 date_debut=now-timedelta(days=10), date_fin=now-timedelta(days=10)+timedelta(hours=3),
                 duree_heures=3,
                 motif="Consultation médicale spécialisée",
                 statut="approuve", directeur=self.medi),
            dict(demandeur=self.agent3, type_absence="mission",
                 date_debut=now+timedelta(days=7), date_fin=now+timedelta(days=9),
                 duree_heures=48,
                 motif="Mission de contrôle qualité — Bouaké",
                 statut="en_attente", directeur=self.medi),
            dict(demandeur=self.agent2, type_absence="formation",
                 date_debut=now+timedelta(days=15), date_fin=now+timedelta(days=15)+timedelta(hours=8),
                 duree_heures=8,
                 motif="Séminaire veille scientifique UEMOA",
                 statut="en_attente", directeur=self.medi),
        ]
        for a in absences:
            DemandeAbsence.objects.get_or_create(
                demandeur=a["demandeur"], date_debut=a["date_debut"], defaults=a
            )

        self.stdout.write(self.style.SUCCESS(f"    ✓ {len(conges)} congés + {len(absences)} absences"))

    # ── 6. Réunions & Rendez-vous ───────────────────────────────
    def _reunions_rdv(self):
        from core.models import Reunion, ReunionPresence, RendezVous
        self.stdout.write("  → Réunions et Rendez-vous…")
        now = timezone.now()

        reunions = [
            dict(intitule="Coordination mensuelle — Direction des Analyses",
                 description="Point mensuel sur analyses en cours, résultats et planification",
                 date_debut=now+timedelta(days=3, hours=8), date_fin=now+timedelta(days=3, hours=10),
                 lieu="Salle de conférence LANEMA — 2ème étage",
                 type_reunion="presentiel", statut="prevu", organisateur=self.medi),
            dict(intitule="Comité technique — Révision procédures ISO 17025",
                 description="Révision procédures accréditation et préparation audit externe",
                 date_debut=now+timedelta(days=7, hours=9), date_fin=now+timedelta(days=7, hours=12),
                 lieu="Salle ISO LANEMA",
                 type_reunion="presentiel", statut="prevu", organisateur=self.medi),
            dict(intitule="Réunion d'urgence — Réclamation PHARMACI",
                 description="Analyse réclamation résultats lot 2025-089",
                 date_debut=now-timedelta(days=2)+timedelta(hours=9),
                 date_fin=now-timedelta(days=2)+timedelta(hours=11),
                 lieu="Bureau du Directeur — Bâtiment A",
                 type_reunion="presentiel", statut="termine", organisateur=self.medi),
            dict(intitule="Webinaire — Nouvelles méthodes d'analyse toxicologique",
                 description="Formation en ligne organisée par le réseau AFRIQUE QUALITÉ",
                 date_debut=now+timedelta(days=14, hours=10),
                 date_fin=now+timedelta(days=14, hours=13),
                 lieu="En ligne — Zoom", type_reunion="en_ligne", statut="prevu",
                 organisateur=self.agent2),
        ]

        for r in reunions:
            reunion, created = Reunion.objects.get_or_create(intitule=r["intitule"], defaults=r)
            if created:
                reunion.participants.set([self.medi, self.agent1, self.agent2, self.agent3])
                ReunionPresence.objects.get_or_create(
                    reunion=reunion, participant=self.medi,
                    defaults={"present": True}
                )

        # Rendez-vous
        rdvs = [
            dict(objet="Réception délégation BEAUTY AFRICA — discussion résultats analyse",
                 date_debut=now+timedelta(days=2, hours=10),
                 date_fin=now+timedelta(days=2, hours=11),
                 lieu="Salle de réunion LANEMA",
                 visiteur_nom="KONAN", visiteur_prenoms="Yves",
                 visiteur_fonction="PDG", visiteur_telephone="0777112233",
                 visiteur_type="entreprise", statut="prevu",
                 organisateur=self.medi, responsable=self.medi),
            dict(objet="Entretien expert ONUDI — évaluation programme métrologie légale",
                 date_debut=now+timedelta(days=5, hours=14),
                 date_fin=now+timedelta(days=5, hours=15, minutes=30),
                 lieu="Bureau Dr MEDI",
                 visiteur_nom="KEITA", visiteur_prenoms="Ibrahim",
                 visiteur_fonction="Expert métrologie", visiteur_telephone="+22520312050",
                 visiteur_type="ministere", statut="prevu",
                 organisateur=self.medi, responsable=self.medi),
            dict(objet="Consultation partenariat CERTIQUA France — accord de coopération technique",
                 date_debut=now-timedelta(days=5)+timedelta(hours=9),
                 date_fin=now-timedelta(days=5)+timedelta(hours=11),
                 lieu="Visioconférence — Zoom",
                 visiteur_nom="DUPONT", visiteur_prenoms="Claire",
                 visiteur_fonction="Directrice Coopération", visiteur_telephone="+33144234567",
                 visiteur_type="entreprise", statut="effectue",
                 organisateur=self.medi, responsable=self.medi),
        ]

        for r in rdvs:
            RendezVous.objects.get_or_create(objet=r["objet"], defaults=r)

        self.stdout.write(self.style.SUCCESS(f"    ✓ {len(reunions)} réunions + {len(rdvs)} rendez-vous"))

    # ── 7. Projets & Tâches ─────────────────────────────────────
    def _projets_taches(self):
        from projet.models import Projet, Tache as ProjetTache
        from core.models import Tache as CoreTache
        self.stdout.write("  → Projets et Tâches…")
        today = date.today()

        projets_data = [
            dict(titre="Accréditation ISO 17025 — Renouvellement 2026",
                 description="Processus de renouvellement de l'accréditation ISO/CEI 17025. Révision documentaire, audits internes et évaluation externe.",
                 date_debut=today-timedelta(60), date_fin_prevue=today+timedelta(120),
                 statut="en_cours", responsable=self.medi, direction=self.lanema),
            dict(titre="Modernisation équipements laboratoire chimique",
                 description="Acquisition et mise en service de 3 spectromètres de masse et 2 chromatographes HPLC.",
                 date_debut=today-timedelta(30), date_fin_prevue=today+timedelta(180),
                 statut="en_cours", responsable=self.medi, direction=self.lanema),
            dict(titre="Programme de formation continue des techniciens 2026",
                 description="Plan annuel de formation des 12 techniciens de laboratoire sur les nouvelles méthodes analytiques.",
                 date_debut=today, date_fin_prevue=today+timedelta(365),
                 statut="planifie", responsable=self.agent2, direction=self.lanema),
            dict(titre="Digitalisation des rapports d'analyse LANEMA",
                 description="Migration rapports papier vers système électronique intégré avec signature numérique.",
                 date_debut=today-timedelta(90), date_fin_prevue=today+timedelta(90),
                 statut="en_cours", responsable=self.medi, direction=self.lanema),
        ]

        self.projets = []
        for p in projets_data:
            proj, created = Projet.objects.get_or_create(
                titre=p["titre"],
                defaults={**p, "created_by": self.medi}
            )
            if created:
                proj.equipe.add(self.medi, self.agent1, self.agent2, self.agent3)
            self.projets.append(proj)

        taches_projet = [
            dict(projet=self.projets[0], titre="Audit interne pré-accréditation",
                 description="Réaliser l'audit interne avant évaluation COFRAC",
                 statut="en_cours", priorite="haute", responsable=self.agent2,
                 date_debut=today, date_fin_prevue=today+timedelta(15)),
            dict(projet=self.projets[0], titre="Révision du manuel qualité",
                 description="Mettre à jour tous les documents qualité selon ISO 17025:2017",
                 statut="termine", priorite="haute", responsable=self.medi,
                 date_debut=today-timedelta(30), date_fin_prevue=today-timedelta(10)),
            dict(projet=self.projets[0], titre="Formation auditeurs internes",
                 description="Former 4 agents comme auditeurs internes ISO 17025",
                 statut="a_faire", priorite="moyenne", responsable=self.agent1,
                 date_debut=today+timedelta(20), date_fin_prevue=today+timedelta(25)),
            dict(projet=self.projets[1], titre="Appel d'offres équipements",
                 description="Rédiger et publier l'appel d'offres pour les équipements",
                 statut="termine", priorite="haute", responsable=self.medi,
                 date_debut=today-timedelta(25), date_fin_prevue=today-timedelta(15)),
            dict(projet=self.projets[1], titre="Évaluation offres fournisseurs",
                 description="Analyser les offres reçues et sélectionner les fournisseurs",
                 statut="en_cours", priorite="haute", responsable=self.medi,
                 date_debut=today-timedelta(10), date_fin_prevue=today+timedelta(10)),
            dict(projet=self.projets[3], titre="Cartographie des processus",
                 description="Documenter tous les processus de génération de rapports d'analyse",
                 statut="termine", priorite="moyenne", responsable=self.agent2,
                 date_debut=today-timedelta(80), date_fin_prevue=today-timedelta(60)),
            dict(projet=self.projets[3], titre="Module signature électronique",
                 description="Intégrer la signature électronique qualifiée dans le système de rapports",
                 statut="en_cours", priorite="haute", responsable=self.agent2,
                 date_debut=today-timedelta(20), date_fin_prevue=today+timedelta(40)),
        ]

        for t in taches_projet:
            task, created = ProjetTache.objects.get_or_create(
                projet=t["projet"], titre=t["titre"], defaults=t
            )
            if created:
                task.agents_assignes.add(t["responsable"])

        # Tâches Core (planning personnel)
        core_taches = [
            dict(titre="Valider rapport mensuel d'analyses — Juin 2026",
                 description="Relire, corriger et signer le rapport mensuel avant transmission à la DG",
                 etat="en_cours", priorite="haute", responsable=self.medi,
                 date_debut=today, date_fin_prevue=today+timedelta(2)),
            dict(titre="Note de service — sécurité laboratoire",
                 description="Mettre à jour consignes de sécurité suite nouveaux équipements",
                 etat="a_faire", priorite="moyenne", responsable=self.medi,
                 date_debut=today, date_fin_prevue=today+timedelta(15)),
            dict(titre="Préparer présentation Forum Qualité 2026",
                 description="Slides sur activités LANEMA et résultats 2025-2026",
                 etat="en_cours", priorite="moyenne", responsable=self.agent2,
                 date_debut=today, date_fin_prevue=today+timedelta(20)),
            dict(titre="Inventaire réactifs et consommables laboratoire",
                 description="Comptage complet et mise à jour base de données stocks",
                 etat="a_faire", priorite="moyenne", responsable=self.agent1,
                 date_debut=today, date_fin_prevue=today+timedelta(7)),
            dict(titre="Rapport réclamation PHARMACI — lot 2025-089",
                 description="Rapport détaillé sur la vérification du lot avec conclusions",
                 etat="terminee", priorite="haute", responsable=self.medi,
                 date_debut=today-timedelta(10), date_fin_prevue=today-timedelta(3)),
        ]

        for t in core_taches:
            CoreTache.objects.get_or_create(titre=t["titre"], defaults=t)

        self.stdout.write(self.style.SUCCESS(f"    ✓ {len(self.projets)} projets + {len(taches_projet)+len(core_taches)} tâches"))

    # ── 8. GED ──────────────────────────────────────────────────
    def _ged(self):
        from core.models import CategorieDocument, Document, DocumentAccess
        self.stdout.write("  → GED — Documents…")

        cats = {}
        for nom, desc in [
            ("Rapports d'analyses", "Rapports officiels d'analyses de laboratoire"),
            ("Documents Qualité", "Manuel qualité, procédures et instructions"),
            ("Documents Administratifs", "Courriers, notes, décisions officielles"),
            ("Formation et Compétences", "Supports de formation et certifications"),
        ]:
            cats[nom], _ = CategorieDocument.objects.get_or_create(nom=nom, defaults={"description": desc})

        docs = [
            dict(reference="LANEMA-RAP-2026-001",
                 titre="Rapport d'analyse — Cosmétiques BEAUTY AFRICA (Lot BA-2026-001)",
                 description="Analyse physico-chimique et microbiologique des produits cosmétiques",
                 categorie=cats["Rapports d'analyses"], statut="valide",
                 type_fichier="pdf", confidentialite="confidentiel",
                 auteur=self.medi, service=self.svc_labo,
                 mots_cles="analyse cosmétiques conformité laboratoire"),
            dict(reference="LANEMA-MQ-2026-001",
                 titre="Manuel Qualité LANEMA — Version 5.2 (ISO 17025:2017)",
                 description="Manuel qualité officiel conforme ISO/CEI 17025:2017",
                 categorie=cats["Documents Qualité"], statut="valide",
                 type_fichier="word", confidentialite="interne",
                 auteur=self.medi, service=self.svc_etudes,
                 mots_cles="qualité ISO 17025 manuel procédures"),
            dict(reference="LANEMA-PRC-LAB-005",
                 titre="Procédure — Manipulation réactifs dangereux (PRC-LAB-005)",
                 description="Procédure de sécurité pour manipulation et stockage des réactifs dangereux",
                 categorie=cats["Documents Qualité"], statut="diffuse",
                 type_fichier="pdf", confidentialite="interne",
                 auteur=self.agent1, service=self.svc_labo,
                 mots_cles="sécurité réactifs procédure chimie"),
            dict(reference="LANEMA-NS-2026-003",
                 titre="Note de service — Heures supplémentaires Q2 2026",
                 description="Note relative aux heures supplémentaires et compensations",
                 categorie=cats["Documents Administratifs"], statut="signe",
                 type_fichier="word", confidentialite="interne",
                 auteur=self.medi, service=self.svc_etudes,
                 mots_cles="RH heures supplémentaires note service"),
            dict(reference="LANEMA-RAP-2026-002",
                 titre="Rapport mensuel d'activités — Direction Analyses — Juin 2026",
                 description="Bilan mensuel des analyses réalisées, résultats et indicateurs",
                 categorie=cats["Rapports d'analyses"], statut="valide",
                 type_fichier="pdf", confidentialite="interne",
                 auteur=self.medi, service=self.svc_etudes,
                 mots_cles="rapport activités mensuel bilan statistiques"),
            dict(reference="LANEMA-FORM-2026-001",
                 titre="Support formation — Introduction spectrométrie de masse",
                 description="Présentation PowerPoint — formation interne techniciens laboratoire",
                 categorie=cats["Formation et Compétences"], statut="valide",
                 type_fichier="autre", confidentialite="interne",
                 auteur=self.agent2, service=self.svc_etudes,
                 mots_cles="formation spectrométrie laboratoire technique"),
            dict(reference="LANEMA-COFRAC-2023-001",
                 titre="Certificat accréditation COFRAC 2023 — LANEMA",
                 description="Certificat officiel d'accréditation ISO 17025 délivré par le COFRAC",
                 categorie=cats["Documents Qualité"], statut="archive",
                 type_fichier="scan", confidentialite="public",
                 auteur=self.admin, service=self.svc_certif,
                 mots_cles="accréditation COFRAC certificat ISO officiel"),
            dict(reference="LANEMA-AVIS-2026-001",
                 titre="Avis technique — Conformité alimentaire lot 2026-003",
                 description="Avis technique officiel LANEMA sur la conformité des produits alimentaires",
                 categorie=cats["Rapports d'analyses"], statut="signe",
                 type_fichier="pdf", confidentialite="public",
                 auteur=self.medi, service=self.svc_labo,
                 mots_cles="avis technique conformité alimentaire officiel"),
        ]

        for i, d in enumerate(docs):
            doc, created = Document.objects.get_or_create(reference=d["reference"], defaults=d)
            if created:
                doc.fichier.save(f"ged_{i+1}.pdf",
                                 dummy_file(f"ged_{i+1}.pdf", d["titre"]), save=True)
                DocumentAccess.objects.get_or_create(
                    document=doc, user=self.medi, defaults={"droit": "validation"}
                )
                DocumentAccess.objects.get_or_create(
                    document=doc, user=self.agent1, defaults={"droit": "lecture"}
                )

        self.stdout.write(self.style.SUCCESS(f"    ✓ {len(docs)} documents GED"))

    # ── 9. Personnel ────────────────────────────────────────────
    def _personnel(self):
        from core.models import FicheAgent, DocumentRH, MissionRH
        self.stdout.write("  → Fiches personnel…")
        today = date.today()

        fiches = [
            dict(user=self.medi, matricule="MCIA-LAB-001",
                 nom="KOUASSI", prenoms="Medi Emmanuel",
                 date_naissance=date(1975, 3, 15), lieu_naissance="Abidjan",
                 situation_matrimoniale="marie", nombre_enfants=3,
                 grade="Ingénieur de Recherche Principale",
                 emploi="Directeur des Études et Analyses",
                 fonction="Directeur",
                 date_prise_service=date(2005, 9, 1),
                 telephone="0700112233",
                 adresse="Cocody Riviera 4, Abidjan",
                 statut="actif", direction=self.lanema,
                 sous_direction=self.sd_analyses),
            dict(user=self.agent1, matricule="MCIA-LAB-002",
                 nom="KONÉ", prenoms="Aya Christelle",
                 date_naissance=date(1988, 7, 22), lieu_naissance="Bouaké",
                 situation_matrimoniale="celibataire", nombre_enfants=0,
                 grade="Technicien Supérieur de Laboratoire",
                 emploi="Technicienne de laboratoire chimique",
                 fonction="Agent technique",
                 date_prise_service=date(2015, 3, 1),
                 telephone="0757884455",
                 adresse="Yopougon Selmer, Abidjan",
                 statut="actif", direction=self.lanema,
                 sous_direction=self.sd_analyses, service=self.svc_labo),
            dict(user=self.agent2, matricule="MCIA-LAB-003",
                 nom="BROU", prenoms="Jean-Claude Kouamé",
                 date_naissance=date(1985, 11, 8), lieu_naissance="Abengourou",
                 situation_matrimoniale="marie", nombre_enfants=2,
                 grade="Ingénieur d'Études",
                 emploi="Chargé d'Études et de Recherche",
                 fonction="Agent technique",
                 date_prise_service=date(2012, 1, 15),
                 telephone="0506771234",
                 adresse="Marcory Résidentiel, Abidjan",
                 statut="actif", direction=self.lanema,
                 sous_direction=self.sd_analyses, service=self.svc_etudes),
            dict(user=self.secretaire, matricule="MCIA-LAB-004",
                 nom="ADOU", prenoms="Marie-Louise Adjoua",
                 date_naissance=date(1990, 5, 30), lieu_naissance="Abidjan",
                 situation_matrimoniale="marie", nombre_enfants=1,
                 grade="Agent Administratif Principal",
                 emploi="Secrétaire de Direction",
                 fonction="Secrétaire",
                 date_prise_service=date(2018, 6, 1),
                 telephone="0787654321",
                 adresse="Abobo Anador, Abidjan",
                 statut="actif", direction=self.lanema,
                 sous_direction=self.sd_admin),
        ]

        for f in fiches:
            FicheAgent.objects.get_or_create(user=f["user"], defaults=f)

        docs_rh = [
            dict(agent=self.medi, type_document="arrete",
                 titre="Arrêté de nomination — Directeur des Études et Analyses LANEMA",
                 reference="MCIA/DGA/ARR/2022/456", date_document=date(2022, 1, 10),
                 description="Nomination officielle au poste de Directeur des Études et Analyses",
                 created_by=self.admin),
            dict(agent=self.medi, type_document="diplome",
                 titre="Doctorat en Chimie Analytique — Université Félix Houphouët-Boigny",
                 reference="UFH/CHI/DOC/2004/089", date_document=date(2004, 7, 15),
                 description="Diplôme de Doctorat, mention Très Honorable avec Félicitations",
                 created_by=self.admin),
            dict(agent=self.medi, type_document="decision",
                 titre="Décision d'avancement — Corps Scientifique, Échelon 8",
                 reference="MCIA/RH/DEC/2023/234", date_document=date(2023, 4, 1),
                 description="Avancement au 8ème échelon du corps des ingénieurs de recherche",
                 created_by=self.admin),
            dict(agent=self.agent1, type_document="diplome",
                 titre="BTS Analyses Biologiques et Biochimiques — CAFOP Abidjan",
                 reference="CAFOP/ABB/2013/156", date_document=date(2013, 7, 8),
                 description="Brevet de Technicien Supérieur, mention Bien",
                 created_by=self.admin),
        ]

        for d in docs_rh:
            doc_rh, created = DocumentRH.objects.get_or_create(
                agent=d["agent"], titre=d["titre"], defaults=d
            )
            if created:
                doc_rh.fichier.save(
                    f"rh_{doc_rh.id}.pdf",
                    dummy_file(f"rh_{doc_rh.id}.pdf", d["titre"]), save=True
                )

        missions = [
            dict(agent=self.medi,   objet="Mission d'expertise — Contrôle qualité produits importés, Yamoussoukro",
                 destination="Yamoussoukro", date_debut=today-timedelta(45),
                 date_fin=today-timedelta(43), statut="terminee", vehicule=True,
                 type_vehicule="Véhicule de service"),
            dict(agent=self.agent3, objet="Mission de contrôle — Inspection entreprises agroalimentaires, Bouaké",
                 destination="Bouaké", date_debut=today+timedelta(7),
                 date_fin=today+timedelta(9), statut="validee", vehicule=True,
                 type_vehicule="Véhicule de service"),
        ]

        for m in missions:
            MissionRH.objects.get_or_create(agent=m["agent"], objet=m["objet"], defaults=m)

        self.stdout.write(self.style.SUCCESS(f"    ✓ {len(fiches)} fiches + {len(docs_rh)} docs RH + {len(missions)} missions"))
