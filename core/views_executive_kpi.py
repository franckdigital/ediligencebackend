from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.utils import timezone
from django.db.models import Count, Avg, Q, Sum, F, FloatField, ExpressionWrapper
from django.db.models.functions import TruncMonth, Coalesce
from django.contrib.auth.models import User
from datetime import date, timedelta, time
from collections import defaultdict

from .models import (
    Courrier, Diligence, Presence, Tache,
    DemandeAbsence, DemandeConge, Direction, Service,
    Agent, UserProfile
)


HEURE_RETARD = time(8, 30)   # seuil de retard
DELAI_COURRIER_RETARD = 5    # jours avant qu'un courrier non traité soit considéré en retard


def safe_pct(num, denom):
    if not denom:
        return 0.0
    return round(num / denom * 100, 1)


class ExecutiveKPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        today = date.today()
        year = today.year
        month = today.month

        # ── Filtres optionnels ─────────────────────────────────────────────
        direction_id = request.query_params.get('direction_id')
        date_debut_str = request.query_params.get('date_debut')
        date_fin_str = request.query_params.get('date_fin')

        try:
            date_debut = date.fromisoformat(date_debut_str) if date_debut_str else date(year, 1, 1)
            date_fin   = date.fromisoformat(date_fin_str)   if date_fin_str   else today
        except ValueError:
            date_debut = date(year, 1, 1)
            date_fin   = today

        retard_date = today - timedelta(days=DELAI_COURRIER_RETARD)

        # ══════════════════════════════════════════════════════════════════
        # 1. KPI COURRIERS
        # ══════════════════════════════════════════════════════════════════
        c_qs = Courrier.objects.all()
        if direction_id:
            c_qs = c_qs.filter(service__sous_direction__direction_id=direction_id)

        # Volume global
        total_courriers = c_qs.count()
        recus_today     = c_qs.filter(sens='arrivee', date_reception=today).count()
        envoyes_today   = c_qs.filter(sens='depart', date_reception=today).count()
        traites_today   = c_qs.filter(date_traitement=today).count()
        en_attente_c    = c_qs.filter(statut__in=['nouveau', 'en_attente']).count()
        en_cours_c      = c_qs.filter(statut='en_cours').count()
        traites_c       = c_qs.filter(statut__in=['traite', 'termine']).count()
        archives_c      = c_qs.filter(statut='archive').count()
        en_retard_c     = c_qs.filter(
            statut__in=['nouveau', 'en_attente', 'en_cours'],
            date_reception__lte=retard_date
        ).count()
        urgents_retard  = c_qs.filter(
            statut__in=['nouveau', 'en_attente', 'en_cours'],
            niveau_urgence__in=['haute', 'critique'],
            date_reception__lte=retard_date
        ).count()
        critiques_nc    = c_qs.filter(
            statut__in=['nouveau', 'en_attente'],
            niveau_urgence='critique'
        ).count()

        # Taux
        taux_traites_c  = safe_pct(traites_c, total_courriers)
        taux_retard_c   = safe_pct(en_retard_c, total_courriers)

        # Par catégorie
        by_categorie = list(
            c_qs.values('categorie').annotate(total=Count('id')).order_by('-total')
        )

        # Par sens
        by_sens = list(
            c_qs.values('sens').annotate(total=Count('id'))
        )

        courriers_kpi = {
            'total': total_courriers,
            'recus_today': recus_today,
            'envoyes_today': envoyes_today,
            'traites_today': traites_today,
            'en_attente': en_attente_c,
            'en_cours': en_cours_c,
            'traites': traites_c,
            'archives': archives_c,
            'en_retard': en_retard_c,
            'urgents_retard': urgents_retard,
            'critiques_non_traites': critiques_nc,
            'taux_traites': taux_traites_c,
            'taux_retard': taux_retard_c,
            'by_categorie': by_categorie,
            'by_sens': by_sens,
        }

        # ══════════════════════════════════════════════════════════════════
        # 2. KPI DILIGENCES
        # ══════════════════════════════════════════════════════════════════
        d_qs = Diligence.objects.filter(
            created_at__date__gte=date_debut,
            created_at__date__lte=date_fin
        )
        if direction_id:
            d_qs = d_qs.filter(direction_id=direction_id)

        total_dil       = d_qs.count()
        en_attente_d    = d_qs.filter(statut='en_attente').count()
        en_cours_d      = d_qs.filter(statut='en_cours').count()
        en_correction_d = d_qs.filter(statut='en_correction').count()
        validation_d    = d_qs.filter(statut='demande_validation').count()
        terminees_d     = d_qs.filter(statut='termine').count()
        archivees_d     = d_qs.filter(statut='archivee').count()
        annulees_d      = d_qs.filter(statut='annule').count()

        en_retard_d = d_qs.filter(
            statut__in=['en_attente', 'en_cours', 'en_correction', 'demande_validation'],
            date_limite__lt=today,
            date_limite__isnull=False
        ).count()

        critiques_retard_d = d_qs.filter(
            statut__in=['en_attente', 'en_cours'],
            date_limite__lt=today - timedelta(days=3),
            date_limite__isnull=False
        ).count()

        avg_avancement = d_qs.aggregate(avg=Avg('pourcentage_avancement'))['avg'] or 0
        taux_completion_d = safe_pct(terminees_d, total_dil)
        taux_retard_d     = safe_pct(en_retard_d, total_dil)

        # Délai moyen de réalisation (diligences terminées avec date_limite)
        dil_terminees = d_qs.filter(statut='termine', date_limite__isnull=False, updated_at__isnull=False)
        delai_moyen_d = None
        if dil_terminees.exists():
            delais = []
            for dil in dil_terminees[:200]:
                delta = (dil.updated_at.date() - dil.created_at.date()).days
                delais.append(delta)
            delai_moyen_d = round(sum(delais) / len(delais), 1) if delais else None

        # Nombre moyen par agent
        nb_agents_actifs = User.objects.filter(diligences__in=d_qs).distinct().count()
        moy_dil_par_agent = round(total_dil / nb_agents_actifs, 1) if nb_agents_actifs else 0

        diligences_kpi = {
            'total': total_dil,
            'en_attente': en_attente_d,
            'en_cours': en_cours_d,
            'en_correction': en_correction_d,
            'demande_validation': validation_d,
            'terminees': terminees_d,
            'archivees': archivees_d,
            'annulees': annulees_d,
            'en_retard': en_retard_d,
            'critiques_retard': critiques_retard_d,
            'avg_avancement': round(float(avg_avancement), 1),
            'taux_completion': taux_completion_d,
            'taux_retard': taux_retard_d,
            'delai_moyen_jours': delai_moyen_d,
            'moy_par_agent': moy_dil_par_agent,
        }

        # ══════════════════════════════════════════════════════════════════
        # 3. KPI TÂCHES
        # ══════════════════════════════════════════════════════════════════
        t_qs = Tache.objects.filter(
            date_debut__gte=date_debut,
            date_debut__lte=date_fin
        )

        total_t     = t_qs.count()
        a_faire_t   = t_qs.filter(etat='a_faire').count()
        en_attente_t = t_qs.filter(etat='en_attente').count()
        en_cours_t  = t_qs.filter(etat='en_cours').count()
        terminees_t = t_qs.filter(etat='terminee').count()
        annulees_t  = t_qs.filter(etat='annulee').count()
        bloquees_t  = t_qs.filter(etat='en_attente', date_fin_prevue__lt=today, date_fin_prevue__isnull=False).count()

        en_retard_t = t_qs.filter(
            etat__in=['a_faire', 'en_attente', 'en_cours'],
            date_fin_prevue__lt=today,
            date_fin_prevue__isnull=False
        ).count()

        avg_avancement_t = t_qs.aggregate(avg=Avg('pourcentage_avancement'))['avg'] or 0
        taux_completion_t = safe_pct(terminees_t, total_t)
        taux_retard_t     = safe_pct(en_retard_t, total_t)

        # Par priorité
        haute_t   = t_qs.filter(priorite='haute').count()
        moyenne_t = t_qs.filter(priorite='moyenne').count()
        basse_t   = t_qs.filter(priorite='basse').count()

        taches_kpi = {
            'total': total_t,
            'a_faire': a_faire_t,
            'en_attente': en_attente_t,
            'en_cours': en_cours_t,
            'terminees': terminees_t,
            'annulees': annulees_t,
            'bloquees': bloquees_t,
            'en_retard': en_retard_t,
            'avg_avancement': round(float(avg_avancement_t), 1),
            'taux_completion': taux_completion_t,
            'taux_retard': taux_retard_t,
            'priorite_haute': haute_t,
            'priorite_moyenne': moyenne_t,
            'priorite_basse': basse_t,
        }

        # ══════════════════════════════════════════════════════════════════
        # 4. KPI PRÉSENCE (aujourd'hui)
        # ══════════════════════════════════════════════════════════════════
        p_today = Presence.objects.filter(date_presence=today)
        total_effectif = Agent.objects.filter(user__is_active=True).count()

        presents    = p_today.filter(statut='présent').count()
        absents     = p_today.filter(statut='absent').count()
        en_mission  = p_today.filter(statut='en mission').count()
        permission  = p_today.filter(statut='permission accordée').count()

        # Agents en retard : présents mais arrivée > HEURE_RETARD
        en_retard_p = p_today.filter(
            statut='présent',
            heure_arrivee__isnull=False,
            heure_arrivee__gt=HEURE_RETARD
        ).count()

        non_enregistres = max(0, total_effectif - p_today.count())

        taux_presence   = safe_pct(presents, total_effectif)
        taux_ponctualite = safe_pct(presents - en_retard_p, presents) if presents else 0

        # Présence sur la période (taux moyen mensuel)
        p_periode = Presence.objects.filter(
            date_presence__gte=date_debut,
            date_presence__lte=date_fin
        )
        jours_ouvrables = max(1, (date_fin - date_debut).days * 5 // 7)
        presence_kpi = {
            'total_effectif': total_effectif,
            'presents_today': presents,
            'absents_today': absents,
            'en_mission_today': en_mission,
            'permission_today': permission,
            'en_retard_today': en_retard_p,
            'non_enregistres': non_enregistres,
            'taux_presence': taux_presence,
            'taux_ponctualite': taux_ponctualite,
        }

        # ══════════════════════════════════════════════════════════════════
        # 5. KPI ABSENCES & CONGÉS
        # ══════════════════════════════════════════════════════════════════
        abs_qs = DemandeAbsence.objects.filter(
            date_debut__gte=date_debut,
            date_debut__lte=date_fin
        )
        total_absences      = abs_qs.count()
        absences_approuvees = abs_qs.filter(statut='approuve').count()
        absences_rejetees   = abs_qs.filter(statut='rejete').count()
        absences_en_attente = abs_qs.filter(statut='en_attente').count()

        cong_qs = DemandeConge.objects.filter(
            date_debut__gte=date_debut,
            date_debut__lte=date_fin
        )
        total_conges = cong_qs.count()
        conges_approuves = cong_qs.filter(statut='approuve').count()

        absences_conges_kpi = {
            'total_absences': total_absences,
            'absences_approuvees': absences_approuvees,
            'absences_rejetees': absences_rejetees,
            'absences_en_attente': absences_en_attente,
            'total_conges': total_conges,
            'conges_approuves': conges_approuves,
        }

        # ══════════════════════════════════════════════════════════════════
        # 6. TOP 10 AGENTS PERFORMANCE
        # ══════════════════════════════════════════════════════════════════
        top_agents = self._compute_top_agents(date_debut, date_fin, today)

        # ══════════════════════════════════════════════════════════════════
        # 7. CLASSEMENT DIRECTIONS
        # ══════════════════════════════════════════════════════════════════
        directions_rank = self._compute_directions_ranking(date_debut, date_fin, today)

        # ══════════════════════════════════════════════════════════════════
        # 8. ÉVOLUTION MENSUELLE 12 MOIS
        # ══════════════════════════════════════════════════════════════════
        monthly_evolution = self._compute_monthly_evolution(today)

        # ══════════════════════════════════════════════════════════════════
        # 9. KPI DÉCISIONNELS GLOBAUX
        # ══════════════════════════════════════════════════════════════════
        score_global = self._compute_global_score(
            taux_completion_d, taux_completion_t, taux_traites_c, taux_presence, taux_ponctualite
        )

        dossiers_critiques = en_retard_c + en_retard_d + en_retard_t
        dossiers_bloques   = bloquees_t + en_correction_d

        decisionnels_kpi = {
            'score_global': score_global,
            'taux_global_completion': round((taux_completion_d + taux_completion_t + taux_traites_c) / 3, 1),
            'taux_presence_global': taux_presence,
            'taux_ponctualite_global': taux_ponctualite,
            'dossiers_critiques': dossiers_critiques,
            'dossiers_bloques': dossiers_bloques,
            'dossiers_hors_delai': en_retard_c + en_retard_d + en_retard_t,
        }

        return Response({
            'generated_at': timezone.now().isoformat(),
            'periode': {'debut': date_debut.isoformat(), 'fin': date_fin.isoformat()},
            'courriers': courriers_kpi,
            'diligences': diligences_kpi,
            'taches': taches_kpi,
            'presence': presence_kpi,
            'absences_conges': absences_conges_kpi,
            'top_agents': top_agents,
            'directions_ranking': directions_rank,
            'monthly_evolution': monthly_evolution,
            'decisionnel': decisionnels_kpi,
        })

    # ──────────────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────────────

    def _compute_top_agents(self, date_debut, date_fin, today):
        """Score pondéré sur 100 pour chaque agent."""
        agents_data = []
        users = User.objects.filter(is_active=True).select_related('profile').prefetch_related('diligences')

        for user in users[:200]:  # limit for performance
            profile = getattr(user, 'profile', None)
            if not profile:
                continue

            # Diligences
            dil_qs   = Diligence.objects.filter(agents=user, created_at__date__gte=date_debut)
            dil_tot  = dil_qs.count()
            dil_done = dil_qs.filter(statut='termine').count()
            dil_retard = dil_qs.filter(
                statut__in=['en_attente', 'en_cours'],
                date_limite__lt=today,
                date_limite__isnull=False
            ).count()

            # Tâches
            tache_qs   = Tache.objects.filter(
                Q(responsable=user) | Q(agents=user),
                date_debut__gte=date_debut
            ).distinct()
            tache_tot  = tache_qs.count()
            tache_done = tache_qs.filter(etat='terminee').count()
            tache_retard = tache_qs.filter(
                etat__in=['a_faire', 'en_cours'],
                date_fin_prevue__lt=today,
                date_fin_prevue__isnull=False
            ).count()

            # Courriers
            courrier_qs   = Courrier.objects.filter(
                imputation_access__user=user,
                date_reception__gte=date_debut
            )
            courrier_tot  = courrier_qs.count()
            courrier_done = courrier_qs.filter(statut__in=['traite', 'termine']).count()

            # Présence
            p_qs   = Presence.objects.filter(agent__user=user, date_presence__gte=date_debut)
            p_pres  = p_qs.filter(statut='présent').count()
            p_total = p_qs.count() or 1
            p_retard = p_qs.filter(heure_arrivee__gt=HEURE_RETARD, statut='présent').count()

            # Calcul score
            s_presence    = safe_pct(p_pres, p_total)
            s_ponctualite = safe_pct(p_pres - p_retard, p_pres) if p_pres else 100
            s_dil         = safe_pct(dil_done, dil_tot) if dil_tot else 100
            s_tache       = safe_pct(tache_done, tache_tot) if tache_tot else 100
            s_courrier    = safe_pct(courrier_done, courrier_tot) if courrier_tot else 100
            s_delais      = max(0, 100 - safe_pct(dil_retard + tache_retard, max(1, dil_tot + tache_tot)) * 2)
            s_qualite     = 85  # valeur neutre (pas d'indicateur corrections en base)
            s_collab      = 75  # valeur neutre

            score = (
                s_presence    * 0.15 +
                s_ponctualite * 0.10 +
                s_dil         * 0.20 +
                s_tache       * 0.15 +
                s_courrier    * 0.15 +
                s_delais      * 0.15 +
                s_qualite     * 0.05 +
                s_collab      * 0.05
            )

            niveau = (
                'Excellent' if score >= 90 else
                'Très bon'  if score >= 80 else
                'Bon'       if score >= 70 else
                'Moyen'     if score >= 60 else
                'Faible'    if score >= 50 else
                'Critique'
            )

            nom = f"{user.first_name} {user.last_name}".strip() or user.username
            agents_data.append({
                'user_id': user.id,
                'nom': nom,
                'username': user.username,
                'role': profile.role if profile else '',
                'service': profile.service.nom if profile and profile.service else '',
                'score': round(score, 1),
                'niveau': niveau,
                'dil_total': dil_tot,
                'dil_terminees': dil_done,
                'tache_total': tache_tot,
                'tache_terminees': tache_done,
                'courrier_total': courrier_tot,
                'courrier_traites': courrier_done,
                'taux_presence': round(s_presence, 1),
                'taux_ponctualite': round(s_ponctualite, 1),
            })

        agents_data.sort(key=lambda x: x['score'], reverse=True)
        return agents_data[:10]

    def _compute_directions_ranking(self, date_debut, date_fin, today):
        directions = Direction.objects.all()
        result = []
        for d in directions:
            # Diligences de la direction
            dil_qs    = Diligence.objects.filter(direction=d, created_at__date__gte=date_debut)
            dil_tot   = dil_qs.count()
            dil_done  = dil_qs.filter(statut='termine').count()
            dil_retard = dil_qs.filter(
                statut__in=['en_attente', 'en_cours'],
                date_limite__lt=today,
                date_limite__isnull=False
            ).count()

            # Tâches des agents de la direction
            agents_ids = User.objects.filter(
                profile__service__sous_direction__direction=d
            ).values_list('id', flat=True)
            tache_qs   = Tache.objects.filter(
                Q(responsable_id__in=agents_ids) | Q(agents__in=agents_ids),
                date_debut__gte=date_debut
            ).distinct()
            tache_tot  = tache_qs.count()
            tache_done = tache_qs.filter(etat='terminee').count()

            # Présence (Agent.service → SousDirection → Direction)
            p_qs   = Presence.objects.filter(
                Q(agent__service__sous_direction__direction=d) |
                Q(agent__service__direction=d),
                date_presence__gte=date_debut
            )
            p_pres  = p_qs.filter(statut='présent').count()
            p_total = p_qs.count() or 1
            taux_p  = safe_pct(p_pres, p_total)

            # Score direction
            s_dil   = safe_pct(dil_done, dil_tot) if dil_tot else 0
            s_tache = safe_pct(tache_done, tache_tot) if tache_tot else 0
            score_d = round((s_dil * 0.4 + s_tache * 0.3 + taux_p * 0.3), 1)

            result.append({
                'direction_id': d.id,
                'nom': d.nom,
                'type': d.type_direction,
                'dil_total': dil_tot,
                'dil_terminees': dil_done,
                'dil_retard': dil_retard,
                'tache_total': tache_tot,
                'tache_terminees': tache_done,
                'taux_presence': taux_p,
                'taux_completion_dil': safe_pct(dil_done, dil_tot) if dil_tot else 0,
                'taux_completion_taches': safe_pct(tache_done, tache_tot) if tache_tot else 0,
                'score': score_d,
                'charge': dil_tot + tache_tot,
            })

        result.sort(key=lambda x: x['score'], reverse=True)
        return result

    def _compute_monthly_evolution(self, today):
        """Données des 12 derniers mois pour les graphiques de tendances."""
        months = []
        for i in range(11, -1, -1):
            y = today.year
            m = today.month - i
            while m <= 0:
                m += 12
                y -= 1
            first_day = date(y, m, 1)
            import calendar as cal
            last_day  = date(y, m, cal.monthrange(y, m)[1])

            label = first_day.strftime('%b %Y')

            c_recus     = Courrier.objects.filter(sens='arrivee', date_reception__gte=first_day, date_reception__lte=last_day).count()
            c_traites   = Courrier.objects.filter(date_traitement__gte=first_day, date_traitement__lte=last_day).count()
            d_crees     = Diligence.objects.filter(created_at__date__gte=first_day, created_at__date__lte=last_day).count()
            d_terminees = Diligence.objects.filter(statut='termine', updated_at__date__gte=first_day, updated_at__date__lte=last_day).count()
            t_terminees = Tache.objects.filter(etat='terminee', date_fin_effective__gte=first_day, date_fin_effective__lte=last_day).count()

            # Présence: taux moyen du mois
            p_qs      = Presence.objects.filter(date_presence__gte=first_day, date_presence__lte=last_day)
            p_pres    = p_qs.filter(statut='présent').count()
            p_total   = p_qs.count()
            taux_pres = safe_pct(p_pres, p_total) if p_total else 0

            months.append({
                'mois': label,
                'date': first_day.isoformat(),
                'courriers_recus': c_recus,
                'courriers_traites': c_traites,
                'diligences_creees': d_crees,
                'diligences_terminees': d_terminees,
                'taches_terminees': t_terminees,
                'taux_presence': taux_pres,
            })
        return months

    def _compute_global_score(self, taux_dil, taux_tache, taux_courrier, taux_presence, taux_ponctualite):
        score = (
            taux_dil        * 0.25 +
            taux_tache      * 0.20 +
            taux_courrier   * 0.20 +
            taux_presence   * 0.20 +
            taux_ponctualite * 0.15
        )
        return round(score, 1)
