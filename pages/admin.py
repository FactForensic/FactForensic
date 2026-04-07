from django.contrib import admin
from .models import GeopoliticalNews


@admin.register(GeopoliticalNews)
class GeopoliticalNewsAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "source_name",
        "bias_score",
        "objectivity_score",
        "published_at",
    )
    search_fields = ("title", "content")
