from django.db import models

class PodcastGeneration(models.Model):
    csv_file = models.FileField(upload_to='csv_uploads/')
    audio_file = models.FileField(upload_to='generated_audios/', null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)

    def __str__(self):
        return f"Generación de podcast - {self.uploaded_at.strftime('%Y-%m-%d %H:%M')}"
