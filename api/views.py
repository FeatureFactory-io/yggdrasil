"""DRF viewsets and traversal endpoint."""

from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.serializers import (
    ChangeSetSerializer,
    ElementSerializer,
    PackageSerializer,
    RelationshipSerializer,
    StereotypeSerializer,
    TraverseQuerySerializer,
)
from graph.models import ChangeSet, Element, Package, Relationship, Stereotype
from graph.services import apply_changeset, traverse_from


class StereotypeViewSet(viewsets.ModelViewSet):
    queryset = Stereotype.objects.all()
    serializer_class = StereotypeSerializer
    permission_classes = [IsAuthenticated]


class PackageViewSet(viewsets.ModelViewSet):
    queryset = Package.objects.all()
    serializer_class = PackageSerializer
    permission_classes = [IsAuthenticated]


class ElementViewSet(viewsets.ModelViewSet):
    queryset = Element.objects.filter(valid_to__isnull=True)
    serializer_class = ElementSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(valid_from=timezone.now(), source="manual")


class RelationshipViewSet(viewsets.ModelViewSet):
    queryset = Relationship.objects.filter(valid_to__isnull=True)
    serializer_class = RelationshipSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(valid_from=timezone.now(), source="manual")


class ChangeSetViewSet(viewsets.ModelViewSet):
    queryset = ChangeSet.objects.all()
    serializer_class = ChangeSetSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=["post"])
    def approve_high_confidence(self, request, pk=None):
        changeset = self.get_object()
        applied = apply_changeset(changeset, min_confidence=0.8)
        return Response({"applied": applied, "status": changeset.status})


class TraverseView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = TraverseQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        nodes = traverse_from(
            element_id=data["from_id"],
            depth=data.get("depth", 3),
            as_of=data.get("as_of"),
        )
        return Response({"nodes": nodes})


class HealthView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        from django.conf import settings

        return Response({"status": "ok", "revision": settings.GIT_REVISION})
