from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, Http404
from .forms import CSVUploadForm
from .models import PodcastGeneration
import os
import csv
import io
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator


# Importa tu función de procesamiento de audio
from .podcast_logic import generate_podcast_audio # <--- IMPORTANTE: Importa tu función aquí

@login_required
def upload_csv(request):
    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            podcast_instance = form.save(commit=False) # Guarda la instancia pero no el archivo aún

            csv_file_obj = request.FILES['csv_file']

            # Define una ruta temporal para el CSV subido dentro de MEDIA_ROOT
            temp_csv_upload_dir = os.path.join(settings.MEDIA_ROOT, 'temp_csv_uploads')
            os.makedirs(temp_csv_upload_dir, exist_ok=True)

            # Guarda el archivo CSV en una ubicación temporal para que tu script pueda leerlo
            temp_csv_filename = FileSystemStorage().get_available_name(csv_file_obj.name)
            temp_csv_path = os.path.join(temp_csv_upload_dir, temp_csv_filename)

            with open(temp_csv_path, 'wb+') as destination:
                for chunk in csv_file_obj.chunks():
                    destination.write(chunk)

            try:
                # Llama a tu función de procesamiento de audio con la ruta del CSV temporal
                # Esta función ahora devuelve la RUTA COMPLETA del audio generado
                full_audio_output_path = generate_podcast_audio(temp_csv_path)

                if full_audio_output_path:
                    # Convierte la ruta completa a una ruta relativa para almacenar en el modelo
                    # Esto asume que full_audio_output_path ya está dentro de settings.MEDIA_ROOT
                    relative_audio_path = os.path.relpath(full_audio_output_path, settings.MEDIA_ROOT)
                    podcast_instance.audio_file.name = relative_audio_path # Asigna la ruta relativa
                    podcast_instance.processed = True
                    podcast_instance.save() # Ahora sí guarda la instancia con la ruta del audio

                    # Elimina el archivo CSV temporal después de procesar
                    os.remove(temp_csv_path)

                    return redirect('download_audio', pk=podcast_instance.pk)
                else:
                    # Si generate_podcast_audio no devuelve una ruta (por ejemplo, si no se generó audio)
                    os.remove(temp_csv_path) # Limpia el CSV temporal
                    return render(request, 'generator/upload.html', {'form': form, 'error_message': 'No se pudo generar el audio a partir del CSV proporcionado. Verifique el contenido.'})


            except Exception as e:
                # Manejo de errores durante el procesamiento del audio
                print(f"Error al generar el audio: {e}")
                # Asegúrate de limpiar el archivo CSV temporal incluso si hay un error
                if os.path.exists(temp_csv_path):
                    os.remove(temp_csv_path)
                return render(request, 'generator/upload.html', {'form': form, 'error_message': f'Error al procesar el archivo CSV: {e}. Asegúrate de que el formato sea correcto y las credenciales de Google Cloud estén bien configuradas.'})

    else:
        form = CSVUploadForm()
    return render(request, 'generator/upload.html', {'form': form})

@login_required
def download_audio(request, pk):
    podcast_instance = get_object_or_404(PodcastGeneration, pk=pk)
    if not podcast_instance.audio_file:
        raise Http404("El archivo de audio no ha sido generado o no existe.")

    file_path = podcast_instance.audio_file.path # Obtiene la ruta física del archivo
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="audio/mpeg")
            response['Content-Disposition'] = 'attachment; filename=' + os.path.basename(file_path)
            return response
    raise Http404("El archivo de audio no existe o fue movido.")

@login_required
def audio_list(request):
    audios = PodcastGeneration.objects.filter(processed=True).order_by('-uploaded_at')
    return render(request, 'generator/audio_list.html', {'audios': audios})
