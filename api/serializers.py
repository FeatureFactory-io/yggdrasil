"""DRF serializers for graph API."""

from rest_framework import serializers

from graph.models import ChangeSet, Element, Package, Relationship, Stereotype


class StereotypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stereotype
        fields = "__all__"


class PackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = "__all__"


class ElementSerializer(serializers.ModelSerializer):
    stereotype_name = serializers.CharField(source="stereotype.name", read_only=True)

    class Meta:
        model = Element
        fields = [
            "id", "name", "stereotype", "stereotype_name", "package", "properties",
            "owner", "source", "confidence", "valid_from", "valid_to", "recorded_at",
            "created_at", "updated_at",
        ]
        read_only_fields = ["valid_from", "valid_to", "recorded_at", "created_at", "updated_at"]


class RelationshipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Relationship
        fields = "__all__"
        read_only_fields = ["valid_from", "valid_to", "recorded_at", "created_at", "updated_at"]


class ChangeSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChangeSet
        fields = "__all__"


class TraverseQuerySerializer(serializers.Serializer):
    from_id = serializers.IntegerField()
    depth = serializers.IntegerField(default=3, min_value=1, max_value=10)
    as_of = serializers.DateTimeField(required=False)
