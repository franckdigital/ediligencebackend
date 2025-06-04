from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import F, ExpressionWrapper, DurationField, Sum, OuterRef, Subquery, Q
from django.db.models.functions import Cast
from django.contrib.auth.models import User
from core.models import Presence
from core.serializers import UserSerializer
from datetime import datetime, timedelta, date
from django.db.models.functions import ExtractWeek, ExtractMonth, ExtractYear
from django.db.models import Count

class PresenceStatsAPIView(APIView):
    """
    API endpoint: /api/stats/presence/
    Retourne pour chaque agent le cumul d'heures/jour, semaine, mois, année, avec nom/prénom/service/direction.
    Filtrable par période et service.
    """
    def get(self, request):
        start = request.GET.get('start')
        end = request.GET.get('end')
        service_id = request.GET.get('service')
        presences = Presence.objects.select_related('agent__profile', 'agent__profile__service', 'agent__profile__service__direction')
        if start:
            presences = presences.filter(date_presence__gte=start)
        if end:
            presences = presences.filter(date_presence__lte=end)
        if service_id:
            presences = presences.filter(agent__profile__service_id=service_id)
        # Annotate duration
        presences = presences.annotate(
            duration=ExpressionWrapper(
                (F('heure_depart') - F('heure_arrivee')),
                output_field=DurationField()
            )
        )
        # Build stats per agent
        stats = {}
        for p in presences:
            if not p.heure_arrivee or not p.heure_depart:
                continue
            uid = p.agent.id
            if uid not in stats:
                stats[uid] = {
                    'user_id': uid,
                    'last_name': p.agent.last_name,
                    'first_name': p.agent.first_name,
                    'service': getattr(p.agent.profile.service, 'nom', ''),
                    'direction': getattr(getattr(p.agent.profile.service, 'direction', None), 'nom', ''),
                    'hours_per_day': 0,
                    'hours_per_week': 0,
                    'hours_per_month': 0,
                    'hours_per_year': 0,
                    'dates': set(),
                    'weeks': set(),
                    'months': set(),
                    'years': set(),
                }
            # Compute duration in hours
            d = datetime.combine(date.min, p.heure_depart) - datetime.combine(date.min, p.heure_arrivee)
            hours = d.total_seconds() / 3600.0
            stats[uid]['hours_per_day'] += hours
            stats[uid]['dates'].add(p.date_presence)
            week = p.date_presence.isocalendar()[1]
            month = p.date_presence.month
            year = p.date_presence.year
            stats[uid]['weeks'].add((year, week))
            stats[uid]['months'].add((year, month))
            stats[uid]['years'].add(year)
        # Cumuls par période
        for s in stats.values():
            if s['dates']:
                s['hours_per_day'] = s['hours_per_day'] / len(s['dates'])
            s['hours_per_week'] = s['hours_per_day'] * 5  # approx (ou recalculer sur la base réelle)
            s['hours_per_month'] = s['hours_per_day'] * 22  # approx
            s['hours_per_year'] = s['hours_per_day'] * 260  # approx
            del s['dates'], s['weeks'], s['months'], s['years']
        return Response(list(stats.values()))
