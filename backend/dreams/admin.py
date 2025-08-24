from django.contrib import admin
from .models import Dream, Quality


@admin.register(Dream)
class DreamAdmin(admin.ModelAdmin):
    list_display = ('get_title', 'user', 'created', 'updated')
    list_filter = ('created', 'updated', 'user')
    search_fields = ('description',)
    readonly_fields = ('created', 'updated')
    filter_horizontal = ('qualities',)
    
    def get_title(self, obj):
        """Display first 50 characters of description as title"""
        if obj.description:
            return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
        return '(No description)'
    get_title.short_description = 'Title'
    
    def get_queryset(self, request):
        """Only show dreams for the current user (except for superusers)"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)


@admin.register(Quality)
class QualityAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'frequency', 'created')
    list_filter = ('created', 'user', 'frequency')
    search_fields = ('name',)
    readonly_fields = ('frequency', 'created')
    
    def get_queryset(self, request):
        """Only show qualities for the current user (except for superusers)"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)
