from rest_framework import serializers
from django.contrib.auth.models import User
from typing import Any, Dict
from .models import Dream, Quality, QualityStatistic, QualityConnection


class QualitySerializer(serializers.ModelSerializer):
    """Serializer for Quality model."""
    
    class Meta:
        model = Quality
        fields = ['id', 'name', 'frequency', 'created']
        read_only_fields = ['id', 'frequency', 'created']
    
    def create(self, validated_data: Dict[str, Any]) -> Quality:
        """Create a quality for the authenticated user."""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class QualityConnectionSerializer(serializers.Serializer):
    """Serializer for QualityConnection dataclass."""
    quality_id = serializers.IntegerField()
    quality_name = serializers.CharField()
    shared_dream_ids = serializers.ListField(child=serializers.IntegerField())
    connection_strength = serializers.IntegerField()


class QualityStatisticSerializer(serializers.Serializer):
    """Serializer for QualityStatistic dataclass."""
    id = serializers.IntegerField()
    name = serializers.CharField()
    frequency = serializers.IntegerField()
    total_connections = serializers.IntegerField()
    top_connections = QualityConnectionSerializer(many=True)
    all_dream_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )


class DreamSerializer(serializers.ModelSerializer):
    """Serializer for Dream model."""
    qualities = QualitySerializer(many=True, read_only=True)
    quality_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    quality_names = serializers.ListField(
        child=serializers.CharField(max_length=128),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Dream
        fields = ['id', 'description', 'qualities', 'quality_ids', 'quality_names', 'created', 'updated']
        read_only_fields = ['id', 'created', 'updated']
    
    def create(self, validated_data: Dict[str, Any]) -> Dream:
        """Create a dream for the authenticated user."""
        quality_ids = validated_data.pop('quality_ids', [])
        quality_names = validated_data.pop('quality_names', [])
        validated_data['user'] = self.context['request'].user
        
        dream = Dream.objects.create(**validated_data)
        
        # Handle quality names - create new qualities or get existing ones
        user_qualities = []
        if quality_names:
            for name in quality_names:
                name = name.strip().lower()
                if name:  # Skip empty names
                    quality, created = Quality.objects.get_or_create(
                        name=name,
                        user=self.context['request'].user
                    )
                    user_qualities.append(quality)
        
        # Handle quality IDs - existing qualities
        if quality_ids:
            existing_qualities = Quality.objects.filter(
                id__in=quality_ids,
                user=self.context['request'].user
            )
            user_qualities.extend(existing_qualities)
        
        # Set all qualities
        if user_qualities:
            dream.qualities.set(user_qualities)
        
        return dream
    
    def update(self, instance: Dream, validated_data: Dict[str, Any]) -> Dream:
        """Update a dream and its qualities."""
        quality_ids = validated_data.pop('quality_ids', None)
        quality_names = validated_data.pop('quality_names', None)
        
        # Update dream fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update qualities if provided
        user_qualities = []
        
        # Handle quality names - create new qualities or get existing ones
        if quality_names is not None:
            for name in quality_names:
                name = name.strip().lower()
                if name:  # Skip empty names
                    quality, created = Quality.objects.get_or_create(
                        name=name,
                        user=self.context['request'].user
                    )
                    user_qualities.append(quality)
        
        # Handle quality IDs - existing qualities
        elif quality_ids is not None:
            existing_qualities = Quality.objects.filter(
                id__in=quality_ids,
                user=self.context['request'].user
            )
            user_qualities.extend(existing_qualities)
        
        # Set all qualities if any were provided
        if quality_names is not None or quality_ids is not None:
            instance.qualities.set(user_qualities)
        
        return instance


class DreamListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for dream lists."""
    qualities = QualitySerializer(many=True, read_only=True)
    
    class Meta:
        model = Dream
        fields = ['id', 'description', 'qualities', 'created']
        read_only_fields = ['id', 'created']