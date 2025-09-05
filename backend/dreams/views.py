import logging

from django.contrib.auth.models import User
from django.db.models import Q, QuerySet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from .models import Dream, Image, Quality
from .pagination import DynamicPageSizePagination
from .permissions import IsAuthenticatedAndIsOwnerOrIsPublic, IsAuthenticatedAndOwner
from .serializers import (
    DreamListSerializer,
    DreamSerializer,
    ImageSerializer,
    QualitySerializer,
    QualityStatisticSerializer,
)
from .services.prompt_service import PromptService
from .services.signed_url import signed_url_service


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
    ViewSet for Dream model with public sharing support.
    - Authenticated users can view public dreams OR their own dreams
    - Only owners can modify their dreams
    """

    permission_classes = [IsAuthenticatedAndIsOwnerOrIsPublic]
    pagination_class = DynamicPageSizePagination

    def _generate_gcs_path(self, dream: Dream) -> str:
        """Generate a unique GCS path for a dream image."""
        import uuid
        from datetime import datetime

        image_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return (
            f"users/{dream.user.pk}/dreams/{dream.pk}/images/{image_id}_{timestamp}.png"
        )

    def _create_and_queue_image(
        self, dream: Dream, prompt: str, source_image_id: int | None = None
    ) -> Image:
        """Create an Image record and queue it for generation.

        Args:
            dream: The Dream this image belongs to
            prompt: The generation prompt
            source_image_id: Optional ID of source image for alterations
        """
        # Generate unique GCS path
        gcs_path = self._generate_gcs_path(dream)

        # Create Image record with pending status
        dream_image = Image.objects.create(
            dream=dream,
            gcs_path=gcs_path,
            generation_prompt=prompt,
            generation_status=Image.GenerationStatus.PENDING,
        )

        # Queue the Celery task with optional source image ID
        from dream_journal.celery import app as celery_app

        # Pass source_image_id as second argument if provided
        task_args = [dream_image.pk]
        if source_image_id is not None:
            task_args.append(source_image_id)

        celery_app.send_task("dreams.tasks.generate_dream_image", args=task_args)

        return dream_image

    def get_queryset(self) -> QuerySet[Dream]:
        """
        Filter dreams to those owned by the user OR marked as public.
        Supports optional quality filtering via query parameter.
        """
        queryset = (
            Dream.objects.filter(Q(user=self.request.user) | Q(is_public=True))
            .prefetch_related("qualities")
            .distinct()
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

    @action(detail=False, methods=["get"])
    def astral_plane(self, request: Request) -> Response:
        """Get all public dreams anonymously for The Astral Plane."""
        queryset = Dream.objects.filter(is_public=True).prefetch_related("qualities")

        # Apply search if provided
        search_query = request.query_params.get("search")
        if search_query and search_query.strip():
            search_term = search_query.strip()
            queryset = queryset.filter(
                Q(description__icontains=search_term)
                | Q(qualities__name__icontains=search_term)
            ).distinct()

        # Apply pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def generate_image(self, request: Request, pk: str | None = None) -> Response:
        """Generate an AI image for this dream using Celery task queue."""
        dream = self.get_object()  # This already checks ownership via permissions

        try:
            # Create the prompt using PromptService
            prompt = PromptService.generate_image_prompt(dream)

            # Create and queue the image
            dream_image = self._create_and_queue_image(dream, prompt)

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

    @action(detail=True, methods=["post"], url_path=r"alter_image/(?P<image_id>\d+)")
    def alter_image(
        self, request: Request, pk: str | None = None, image_id: str | None = None
    ) -> Response:
        """Generate an altered version of a specific dream image with a custom prompt."""
        dream = self.get_object()  # This already checks ownership via permissions

        # Get the source image to alter
        try:
            source_image = dream.images.get(pk=image_id)
            if source_image.generation_status != Image.GenerationStatus.COMPLETED:
                return Response(
                    {"error": "Source image must be completed before alteration"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except Image.DoesNotExist:
            return Response(
                {"error": "Image not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Get required custom prompt from request
        user_prompt = request.data.get("prompt")
        if not user_prompt:
            return Response(
                {"error": "Custom prompt is required for image alteration"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Check if dream has been updated since the source image was created
            dream_updated_since_image = dream.updated > source_image.created

            # Generate the alteration prompt using PromptService
            alteration_prompt = PromptService.generate_alteration_prompt(
                user_prompt, dream, dream_updated_since_image
            )

            # Create and queue the altered image with source image reference
            dream_image = self._create_and_queue_image(
                dream, alteration_prompt, source_image_id=source_image.pk
            )

            return Response(
                {
                    "id": dream_image.pk,
                    "status": dream_image.generation_status,
                    "prompt": dream_image.generation_prompt,
                    "created": dream_image.created,
                    "source_image_id": source_image.pk,
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            return Response(
                {"error": f"Failed to start image alteration: {e!s}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["get"])
    def images(self, request: Request, pk: str | None = None) -> Response:
        """Get all images for this dream. Returns List[Image]."""
        dream = self.get_object()  # This already checks ownership

        # Serialize images
        serializer = ImageSerializer(dream.images.all(), many=True)
        data = serializer.data

        # Add signed URLs for completed images
        for i, image in enumerate(dream.images.all()):
            if image.generation_status == Image.GenerationStatus.COMPLETED:
                try:
                    data[i]["image_url"] = signed_url_service.get_signed_url(image)
                except Exception as e:
                    logging.error(
                        f"Failed to generate signed URL for image {image.id}: {e}"
                    )

        return Response(data)

    @action(detail=True, methods=["get"], url_path=r"images/(?P<image_id>\d+)")
    def image(
        self, request: Request, pk: str | None = None, image_id: str | None = None
    ) -> Response:
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
                data["image_url"] = signed_url_service.get_signed_url(dream_image)
            except Exception as e:
                logging.error(
                    f"Failed to generate signed URL for image {dream_image.id}: {e}"
                )

        return Response(data)
