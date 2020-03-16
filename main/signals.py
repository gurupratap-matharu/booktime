import logging
from io import BytesIO

from django.core.files.base import ContentFile
from django.db.models.signals import pre_save
from django.dispatch import receiver
from PIL import Image

from .models import ProductImage

THUMBNAIL_SIZE = (300, 300)
logger = logging.getLogger(__name__)


@receiver(pre_save, sender=ProductImage)
def generate_thumbnail(sender, instance, **kwargs):
    logger.info("Generating thumbail for product {}".format(instance.product.id))
    image = Image.open(instance.image)
    image = image.convert("RGB")
    image.thumbail(THUMBNAIL_SIZE, Image.ANTIALIAS)

    temp_thumb = BytesIO()
    image.save(temp_thumb, "JPEG")
    temp_thumb.seek(0)

    # set save=False else it'll run in an infinite loop
    instance.thumbail.save(instance.image.name, ContentFile(temp_thumb.read()),
                           save=False)
    temp_thumb.close()
