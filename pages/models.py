# pages/models.py
from django.db import models
from django.utils import timezone  # ADD THIS


class GeopoliticalNews(models.Model):
    CATEGORY_CHOICES = [
        ("BD", "Bangladesh"),
        ("World", "World"),
    ]

    title = models.CharField(max_length=500)
    source_name = models.CharField(max_length=255)
    url = models.URLField(max_length=800, unique=True)
    content = models.TextField()
    category = models.CharField(
        max_length=10, choices=CATEGORY_CHOICES, default="World"
    )
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    bias_score = models.FloatField(null=True, blank=True)
    objectivity_score = models.FloatField(null=True, blank=True)
    summary = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"[{self.category}] {self.title}"

    class Meta:
        ordering = ["-published_at"]
        verbose_name_plural = "Geopolitical News"
