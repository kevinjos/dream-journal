from django.contrib.auth.models import User
from django.db.models import Q, QuerySet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from .models import Dream, Image, Quality
from .pagination import DynamicPageSizePagination
from .permissions import IsAuthenticatedAndOwner
from .serializers import (
    DreamListSerializer,
    DreamSerializer,
    ImageSerializer,
    QualitySerializer,
    QualityStatisticSerializer,
)
from .services.image_generation import image_service


class QualityViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Quality model with user-scoped access.
    Users can only see and modify their own qualities.
    """

    serializer_class = QualitySerializer
    permission_classes = [IsAuthenticatedAndOwner]

    def perform_create(self, serializer: QualitySerializer) -> None:
        """Save the quality with the authenticated user."""
        serializer.save(user=self.request.user)

    def get_queryset(self) -> QuerySet[Quality]:
        """
        Filter qualities to only those owned by the requesting user.
        This ensures users cannot even see other users' qualities in list views.
        """
        return Quality.objects.filter(user=self.request.user).order_by("name")

    @action(detail=True, methods=["get"])
    def connections(self, request: Request) -> Response:
        """Get all connections for a specific quality."""
        quality = self.get_object()  # This already checks ownership
        connections = quality.get_connections()

        # Convert to serializable format
        connections_data = [
            {
                "quality_id": conn.quality_id,
                "quality_name": conn.quality_name,
                "shared_dream_ids": conn.shared_dream_ids,
                "connection_strength": conn.connection_strength,
            }
            for conn in connections
        ]

        return Response(connections_data)

    @action(detail=False, methods=["get"])
    def statistics(self, request: Request) -> Response:
        """Get quality statistics for word map visualization."""
        user = request.user
        if not isinstance(user, User):
            return Response(
                {"error": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        stats = Dream.get_quality_statistics(user)
        serializer = QualityStatisticSerializer(stats, many=True)
        return Response(serializer.data)


class DreamViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Dream model with user-scoped access.
    Users can only see and modify their own dreams.
    """

    permission_classes = [IsAuthenticatedAndOwner]
    pagination_class = DynamicPageSizePagination

    def get_queryset(self) -> QuerySet[Dream]:
        """
        Filter dreams to only those owned by the requesting user.
        Supports optional quality filtering via query parameter.
        """
        queryset = Dream.objects.filter(user=self.request.user).prefetch_related(
            "qualities"
        )

        # Filter by quality if quality query parameter is provided
        quality_id = self.request.query_params.get("quality")
        if quality_id:
            try:
                quality_id_int = int(quality_id)
                # Filter dreams that have this quality and belong to the user
                queryset = queryset.filter(
                    qualities__id=quality_id_int, qualities__user=self.request.user
                ).distinct()
            except (ValueError, TypeError):
                # Invalid quality ID format, return empty queryset
                queryset = queryset.none()

        # Filter by search query if search parameter is provided
        search_query = self.request.query_params.get("search")
        if search_query and search_query.strip():
            search_term = search_query.strip()
            # Search in dream description and quality names
            queryset = queryset.filter(
                Q(description__icontains=search_term)
                | Q(qualities__name__icontains=search_term)
            ).distinct()

        return queryset

    def get_serializer_class(self) -> type:
        """Use lightweight serializer for list views."""
        if self.action == "list":
            return DreamListSerializer
        return DreamSerializer

    def perform_create(self, serializer: DreamSerializer) -> None:
        """Save the dream with the authenticated user."""
        serializer.save(user=self.request.user)

    def perform_update(self, serializer: DreamSerializer) -> None:
        """Update the dream (user is already set on the instance)."""
        serializer.save()

    @action(detail=False, methods=["get"])
    def quality_graph(self, request: Request) -> Response:
        """Get the complete quality graph for the user."""
        user = request.user
        if not isinstance(user, User):
            return Response(
                {"error": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        graph = Dream.build_quality_graph(user)

        # Convert graph to serializable format
        graph_data = {
            "nodes": [
                {
                    "id": node.quality_id,
                    "name": node.quality_name,
                    "frequency": node.frequency,
                    "edges": {str(k): v for k, v in node.edges.items()},
                }
                for node in graph.nodes.values()
            ]
        }

        return Response(graph_data)

    @action(detail=True, methods=["post"])
    def generate_image(self, request: Request) -> Response:
        """Generate an AI image for this dream."""
        dream = self.get_object()  # This already checks ownership via permissions

        # Get optional custom prompt from request
        custom_prompt = request.data.get("prompt")

        try:
            # Generate image using the service
            dream_image = image_service.generate_image_for_dream(dream, custom_prompt)

            return Response(
                {
                    "id": dream_image.pk,
                    "status": dream_image.generation_status,
                    "prompt": dream_image.generation_prompt,
                    "created": dream_image.created,
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            return Response(
                {"error": f"Failed to start image generation: {e!s}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["get"])
    def images(self, request: Request) -> Response:
        """Get all images for this dream. Returns List[Image]."""
        dream = self.get_object()  # This already checks ownership

        # Serialize images
        serializer = ImageSerializer(dream.images.all(), many=True)
        data = serializer.data

        # Add signed URLs for completed images
        for i, image in enumerate(dream.images.all()):
            if image.generation_status == Image.GenerationStatus.COMPLETED:
                try:
                    data[i]["image_url"] = image_service.get_signed_url(image)
                except Exception:
                    pass  # Skip URL if generation fails

        return Response(data)

    @action(detail=True, methods=["get"], url_path=r"images/(?P<image_id>\d+)")
    def image(self, request: Request, image_id: str) -> Response:
        """Get a specific image for this dream. Returns Image."""
        dream = self.get_object()  # This already checks ownership

        try:
            dream_image = dream.images.get(pk=image_id)
        except Image.DoesNotExist:
            return Response(
                {"error": "Image not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Serialize the image
        serializer = ImageSerializer(dream_image)
        data = serializer.data

        # Add signed URL if image is completed
        if dream_image.generation_status == Image.GenerationStatus.COMPLETED:
            try:
                data["image_url"] = image_service.get_signed_url(dream_image)
            except Exception:
                pass  # Skip URL if generation fails

        return Response(data)
