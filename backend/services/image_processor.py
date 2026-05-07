from PIL import Image
import io

def crop_image_from_bounding_box(image_bytes: bytes, bbox: dict) -> bytes:
    """
    Crops an image based on normalized bounding box coordinates.
    
    Args:
        image_bytes: The original image bytes.
        bbox: A dict containing 'ymin', 'xmin', 'ymax', 'xmax' as floats between 0.0 and 1.0.
        
    Returns:
        The cropped image bytes, or original image bytes if cropping fails.
    """
    if not bbox:
        return image_bytes
        
    try:
        img = Image.open(io.BytesIO(image_bytes))
        width, height = img.size
        
        xmin = bbox.get('xmin', 0.0)
        ymin = bbox.get('ymin', 0.0)
        xmax = bbox.get('xmax', 1.0)
        ymax = bbox.get('ymax', 1.0)
        
        left = int(xmin * width)
        top = int(ymin * height)
        right = int(xmax * width)
        bottom = int(ymax * height)
        
        # Ensure coordinates are within bounds
        left = max(0, min(left, width))
        right = max(0, min(right, width))
        top = max(0, min(top, height))
        bottom = max(0, min(bottom, height))
        
        if right <= left or bottom <= top:
            return image_bytes # Invalid bbox
            
        cropped_img = img.crop((left, top, right, bottom))
        
        out_io = io.BytesIO()
        cropped_img.save(out_io, format=img.format or "JPEG")
        return out_io.getvalue()
    except Exception as e:
        print(f"Error cropping image: {e}")
        return image_bytes
