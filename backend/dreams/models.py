from collections import defaultdict
from dataclasses import dataclass, field

from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator
from django.db import models


@dataclass
class QualityConnection:
    """Represents a connection between two qualities."""

    quality_id: int
    quality_name: str
    shared_dream_ids: list[int]
    connection_strength: int  # Number of shared dreams

    def __post_init__(self) -> None:
        """Validate connection strength matches dream count."""
        if self.connection_strength != len(self.shared_dream_ids):
            self.connection_strength = len(self.shared_dream_ids)


@dataclass
class QualityStatistic:
    """Statistics for a single quality for word map visualization."""

    id: int
    name: str
    frequency: int  # Number of dreams this quality appears in
    total_connections: int  # Number of other qualities it co-occurs with
    top_connections: list[QualityConnection] = field(default_factory=list)
    all_dream_ids: list[int] = field(default_factory=list)


@dataclass
class QualityGraphNode:
    """A node in the quality graph."""

    quality_id: int
    quality_name: str
    frequency: int
    edges: dict[int, list[int]] = field(default_factory=dict)  # quality_id -> dream_ids

    def add_edge(self, other_quality_id: int, dream_id: int) -> None:
        """Add an edge to another quality via a dream."""
        if other_quality_id not in self.edges:
            self.edges[other_quality_id] = []
        self.edges[other_quality_id].append(dream_id)

    def get_connection_strength(self, other_quality_id: int) -> int:
        """Get the number of dreams connecting to another quality."""
        return len(self.edges.get(other_quality_id, []))


@dataclass
class QualityGraph:
    """Complete graph structure for quality co-occurrences."""

    nodes: dict[int, QualityGraphNode] = field(default_factory=dict)

    def add_node(self, quality_id: int, quality_name: str, frequency: int) -> None:
        """Add a node to the graph."""
        if quality_id not in self.nodes:
            self.nodes[quality_id] = QualityGraphNode(
                quality_id, quality_name, frequency
            )

    def add_edge(self, quality1_id: int, quality2_id: int, dream_id: int) -> None:
        """Add a bidirectional edge between two qualities."""
        if quality1_id in self.nodes:
            self.nodes[quality1_id].add_edge(quality2_id, dream_id)
        if quality2_id in self.nodes:
            self.nodes[quality2_id].add_edge(quality1_id, dream_id)

    def get_statistics(self) -> list[QualityStatistic]:
        """Generate statistics for all qualities in the graph."""
        stats = []
        for node in self.nodes.values():
            # Build connections list
            connections = []
            for other_id, dream_ids in node.edges.items():
                if other_id in self.nodes:
                    other_node = self.nodes[other_id]
                    connections.append(
                        QualityConnection(
                            quality_id=other_id,
                            quality_name=other_node.quality_name,
                            shared_dream_ids=dream_ids,
                            connection_strength=len(dream_ids),
                        )
                    )

            # Sort by connection strength
            connections.sort(key=lambda c: c.connection_strength, reverse=True)

            stats.append(
                QualityStatistic(
                    id=node.quality_id,
                    name=node.quality_name,
                    frequency=node.frequency,
                    total_connections=len(node.edges),
                    top_connections=connections[:5],  # Top 5 connections
                )
            )

        return sorted(stats, key=lambda s: s.frequency, reverse=True)


class Quality(models.Model):
    """Model for dream qualities - single word descriptors unique per user."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, help_text="The user who owns this quality"
    )

    name = models.CharField(
        max_length=128,
        validators=[
            MinLengthValidator(2),
        ],
        help_text="A 128 character quality descriptor",
    )

    frequency = models.PositiveIntegerField(
        default=1, help_text="Number of dreams this quality appears in"
    )

    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Qualities"
        ordering = ["name"]  # Alphabetical ordering
        unique_together = [["user", "name"]]  # Each user has unique quality names
        indexes = [
            models.Index(fields=["user", "name"]),  # For lookups and autocomplete
            models.Index(fields=["user", "-frequency"]),  # For top qualities queries
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.user.username})"

    def save(self, *args, **kwargs):
        # Normalize to lowercase for consistency
        self.name = self.name.lower()
        super().save(*args, **kwargs)

    def update_frequency(self) -> None:
        """Update frequency count based on associated dreams."""
        # Use the reverse relation name from Dream.qualities
        self.frequency = Dream.objects.filter(qualities=self).count()
        self.save(update_fields=["frequency"])

    def get_connections(self) -> list[QualityConnection]:
        """
        Get all qualities that co-occur with this one as QualityConnection objects.
        Returns a list sorted by connection strength.
        """
        connections_dict: dict[int, list[int]] = defaultdict(list)

        # Get all dreams with this quality using the correct relation
        dreams = Dream.objects.filter(qualities=self).prefetch_related("qualities")

        for dream in dreams:
            for other_quality in dream.qualities.exclude(pk=self.pk):
                connections_dict[other_quality.pk].append(dream.pk)

        # Convert to QualityConnection objects
        connections = []
        for quality_id, dream_ids in connections_dict.items():
            try:
                other_quality = Quality.objects.get(pk=quality_id)
                connections.append(
                    QualityConnection(
                        quality_id=quality_id,
                        quality_name=other_quality.name,
                        shared_dream_ids=dream_ids,
                        connection_strength=len(dream_ids),
                    )
                )
            except Quality.DoesNotExist:
                continue

        return sorted(connections, key=lambda c: c.connection_strength, reverse=True)


class Dream(models.Model):
    """Model for storing dream journal entries."""

    # Primary key - Django creates 'id' automatically as BigAutoField
    # id = models.BigAutoField(primary_key=True) - this is implicit

    # Foreign key to User model
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, help_text="The user who owns this dream entry"
    )

    # Dream content
    description = models.TextField(blank=True, help_text="Description of the dream")

    # Dream qualities - many-to-many using default related_name (dream_set)
    qualities = models.ManyToManyField(
        Quality, blank=True, help_text="Single-word qualities describing this dream"
    )

    # Timestamps
    created = models.DateTimeField(
        auto_now_add=True, help_text="When the dream entry was first created"
    )
    updated = models.DateTimeField(
        auto_now=True, help_text="When the dream entry was last modified"
    )

    class Meta:
        ordering = ["-created"]  # Most recent dreams first
        indexes = [
            models.Index(fields=["user", "-created"]),  # For user's dreams listing
        ]

    def __str__(self) -> str:
        return f"Dream {self.pk} by {self.user.username} on {self.created.date()}"

    @classmethod
    def build_quality_graph(cls, user: User) -> QualityGraph:
        """
        Build a complete quality co-occurrence graph for a user.
        This is more efficient than iterating through qualities individually.
        """
        graph = QualityGraph()

        # First, add all quality nodes
        qualities = Quality.objects.filter(user=user)
        for quality in qualities:
            graph.add_node(quality.pk, quality.name, quality.frequency)

        # Then, fetch all dreams with their qualities in one query
        dreams = cls.objects.filter(user=user).prefetch_related("qualities")

        for dream in dreams:
            qualities = list(dream.qualities.all())
            # Only process if there are 2+ qualities
            if len(qualities) >= 2:
                for i, q1 in enumerate(qualities):
                    for q2 in qualities[i + 1 :]:
                        graph.add_edge(q1.pk, q2.pk, dream.pk)

        return graph

    @classmethod
    def get_quality_statistics(cls, user: User) -> list[QualityStatistic]:
        """
        Get quality statistics for word map visualization.
        Returns list of QualityStatistic objects sorted by frequency.
        """
        graph = cls.build_quality_graph(user)
        return graph.get_statistics()


class Image(models.Model):
    """Model for storing AI-generated images associated with dreams."""

    # Image generation status choices
    class GenerationStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        GENERATING = "generating", "Generating"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    # Foreign key to Dream model
    dream = models.ForeignKey(
        Dream,
        on_delete=models.CASCADE,
        related_name="images",
        help_text="The dream this image belongs to",
    )

    # GCS storage information
    gcs_path = models.CharField(
        max_length=512, help_text="Path to the image file in Google Cloud Storage"
    )

    # Generation metadata
    generation_prompt = models.TextField(
        help_text="The prompt used to generate this image"
    )

    generation_status = models.CharField(
        max_length=20,
        choices=GenerationStatus.choices,
        default=GenerationStatus.PENDING,
        help_text="Current status of image generation",
    )

    # Timestamp
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]  # Most recent images first
        indexes = [
            models.Index(fields=["dream", "-created"]),  # For dream's images listing
            models.Index(fields=["generation_status"]),  # For status queries
        ]

    def __str__(self) -> str:
        return f"Image for Dream {self.dream.pk} ({self.generation_status})"
