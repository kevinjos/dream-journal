from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.request import Request
from django.contrib.auth.models import User
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from typing import Optional, Union
from .models import Dream, Quality
from .serializers import QualitySerializer
from .permissions import IsAuthenticatedAndOwner


class DreamQualityViewSet(viewsets.ViewSet):
    """
    ViewSet for managing qualities nested under dreams.
    
    Provides RESTful endpoints:
    - GET /api/dreams/{dream_id}/qualities/ - List dream's qualities
    - PUT /api/dreams/{dream_id}/qualities/{quality_id}/ - Add quality to dream  
    - DELETE /api/dreams/{dream_id}/qualities/{quality_id}/ - Remove quality from dream
    """
    permission_classes = [IsAuthenticatedAndOwner]
    
    def get_dream(self, dream_id: Union[int, str]) -> Dream:
        """Get dream owned by current user or raise 404."""
        user = self.request.user
        if not isinstance(user, User):
            raise PermissionError("Authentication required")
        
        return get_object_or_404(
            Dream.objects.filter(user=user),
            pk=dream_id
        )
    
    def get_quality(self, quality_id: Union[int, str]) -> Quality:
        """Get quality owned by current user or raise 404."""
        user = self.request.user
        if not isinstance(user, User):
            raise PermissionError("Authentication required")
        
        return get_object_or_404(
            Quality.objects.filter(user=user),
            pk=quality_id
        )
    
    def list(self, request: Request, dream_pk: Optional[Union[int, str]] = None) -> Response:
        """List all qualities for a specific dream."""
        if dream_pk is None:
            return Response({'error': 'Dream ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        dream = self.get_dream(dream_pk)
        qualities = dream.qualities.all().order_by('name')
        serializer = QualitySerializer(qualities, many=True, context={'request': request})
        return Response(serializer.data)
    
    def update(self, request: Request, dream_pk: Optional[Union[int, str]] = None, 
               pk: Optional[Union[int, str]] = None) -> Response:
        """Add a quality to a dream (PUT /dreams/{id}/qualities/{quality_id}/)."""
        if dream_pk is None:
            return Response({'error': 'Dream ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        if pk is None:
            return Response({'error': 'Quality ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        dream = self.get_dream(dream_pk)
        quality = self.get_quality(pk)
        
        # Add quality to dream if not already present
        if not dream.qualities.filter(pk=quality.pk).exists():
            dream.qualities.add(quality)
            quality.update_frequency()
        
        serializer = QualitySerializer(quality, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def destroy(self, request: Request, dream_pk: Optional[Union[int, str]] = None, 
                pk: Optional[Union[int, str]] = None) -> Response:
        """Remove a quality from a dream (DELETE /dreams/{id}/qualities/{quality_id}/)."""
        if dream_pk is None:
            return Response({'error': 'Dream ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        if pk is None:
            return Response({'error': 'Quality ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        dream = self.get_dream(dream_pk)
        quality = self.get_quality(pk)
        
        # Remove quality from dream if present
        if dream.qualities.filter(pk=quality.pk).exists():
            dream.qualities.remove(quality)
            
            # Update frequency and check if quality should be deleted
            new_frequency = Dream.objects.filter(qualities=quality).count()
            if new_frequency == 0:
                quality.delete()
            else:
                quality.frequency = new_frequency
                quality.save(update_fields=['frequency'])
        
        return Response(status=status.HTTP_204_NO_CONTENT)