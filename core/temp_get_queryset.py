    def get_queryset(self):
        user = self.request.user
        role = user.profile.role

        if role in ['ADMIN', 'superadmin', 'Administrateur']:
            return Diligence.objects.all()

        if role == 'DIRECTEUR' and user.profile.service:
            # Le directeur voit toutes les diligences de sa direction
            direction = user.profile.service.direction
            return Diligence.objects.filter(
                Q(direction=direction) |
                Q(services_concernes__direction=direction) |
                Q(agents__profile__service__direction=direction)
            ).distinct()

        if role == 'SECRETAIRE' and user.profile.service:
            # La secrétaire voit les diligences de son service
            return Diligence.objects.filter(
                Q(services_concernes__in=[user.profile.service]) |
                Q(agents=user)
            ).distinct()

        if role == 'SUPERIEUR' and user.profile.service:
            # Le supérieur voit les diligences de son service
            return Diligence.objects.filter(
                services_concernes=user.profile.service
            ).distinct()

        # Les agents voient leurs propres diligences
        return Diligence.objects.filter(agents=user)
