"""Decode, orient and re-encode pixels; no metadata is copied to web derivatives."""
from dataclasses import dataclass
from io import BytesIO
import hashlib,warnings
from PIL import Image,ImageOps,UnidentifiedImageError
from .review_security import ReviewError
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIF=True
except ImportError:HEIF=False

@dataclass(frozen=True)
class ProcessedImage:
    original:bytes
    checksum:str
    mime:str
    width:int
    height:int
    variants:dict

class ImageProcessor:
    def __init__(self,max_bytes=10*1024*1024,max_pixels=24_000_000):self.max_bytes=max_bytes;self.max_pixels=max_pixels
    def process(self,data,filename=''):
        if not isinstance(data,bytes) or not 0<len(data)<=self.max_bytes:raise ReviewError(413,'image_size',{'image':'image'})
        signature=(data.startswith(b'\xff\xd8\xff') or data.startswith(b'\x89PNG\r\n\x1a\n') or data[:4]==b'RIFF' and data[8:12]==b'WEBP' or HEIF and data[4:8]==b'ftyp' and data[8:12] in (b'heic',b'heix',b'hevc',b'hevx',b'mif1',b'msf1'))
        if not signature:raise ReviewError(422,'image_type',{'image':'image'})
        try:
            with warnings.catch_warnings():
                warnings.simplefilter('error',Image.DecompressionBombWarning)
                with Image.open(BytesIO(data)) as image:
                    if image.format not in ('JPEG','PNG','WEBP','HEIF') or getattr(image,'n_frames',1)!=1 or image.width*image.height>self.max_pixels or max(image.size)>12000:raise ValueError()
                    image.verify()
                with Image.open(BytesIO(data)) as image:
                    image.load();oriented=ImageOps.exif_transpose(image).convert('RGB')
                    clean=Image.new('RGB',oriented.size);clean.paste(oriented)
                    variants={}
                    for label,max_width in [('small',320),('large',1200)]:
                        copy=clean.copy();copy.thumbnail((max_width,max_width),Image.Resampling.LANCZOS);out=BytesIO();copy.save(out,format='WEBP',quality=86,method=4)
                        variants[label]={'data':out.getvalue(),'width':copy.width,'height':copy.height,'mime':'image/webp'}
                    return ProcessedImage(data,hashlib.sha256(data).hexdigest(),Image.MIME.get(image.format,'image/heif'),clean.width,clean.height,variants)
        except (UnidentifiedImageError,OSError,ValueError,SyntaxError,Image.DecompressionBombError,Image.DecompressionBombWarning):raise ReviewError(422,'image_invalid',{'image':'image'}) from None
