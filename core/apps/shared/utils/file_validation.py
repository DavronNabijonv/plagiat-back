from pathlib import Path

from rest_framework import serializers

# BE-08: fayl limitlari barcha tekshiruv turlarida bir xil
# (TZ: Plagiat 20MB / SI 50MB nomuvofiqligi bartaraf etildi — yagona 50MB).
ALLOWED_EXTENSIONS = {'.pdf', '.doc', '.docx', '.txt'}
MAX_FILE_SIZE_MB = 50


def validate_upload(file):
    """Plagiat, SI va check_file yuklamalari uchun yagona validatsiya."""
    ext = Path(file.name).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise serializers.ValidationError(
            f"Qo'llab-quvvatlanmaydigan fayl turi: {ext or 'nomalum'}. "
            f"Ruxsat etilgan: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )
    if file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise serializers.ValidationError(
            f"Fayl hajmi {MAX_FILE_SIZE_MB} MB dan oshmasligi kerak"
        )
    return file
