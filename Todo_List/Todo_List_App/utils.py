from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile

def resize_image(image, size=(800, 800)):
    img = Image.open(image)
    img.thumbnail(size, Image.LANCZOS)

    output = BytesIO()
    
    format = img.format
    
    if format.upper() == 'JPEG':
        quality = 85
        img.save(output, format=format, quality=quality)
    elif format.upper() == 'PNG':
        img.save(output, format=format, optimize=True)
    else:
        img.save(output, format=format)
    
    output.seek(0)
    
    new_file_name = f"{image.name.split('.')[0]}.{format.lower()}"
    
    return ContentFile(output.read(), name=new_file_name)
