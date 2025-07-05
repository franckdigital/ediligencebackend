from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

class SetFingerprintView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        fingerprint_hash = request.data.get('fingerprint_hash')
        if not fingerprint_hash:
            return Response({'detail': 'fingerprint_hash manquant'}, status=status.HTTP_400_BAD_REQUEST)
        user.profile.empreinte_hash = fingerprint_hash
        user.profile.save()
        return Response({'detail': 'Empreinte enregistrée'}, status=status.HTTP_200_OK)

class VerifyFingerprintView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        fingerprint_hash = request.data.get('fingerprint_hash')
        if not fingerprint_hash:
            return Response({'detail': 'fingerprint_hash manquant'}, status=status.HTTP_400_BAD_REQUEST)
        if user.profile.empreinte_hash == fingerprint_hash:
            return Response({'detail': 'Empreinte reconnue'}, status=status.HTTP_200_OK)
        else:
            return Response({'detail': 'Empreinte non reconnue'}, status=status.HTTP_401_UNAUTHORIZED)
