import os
import uuid
import mimetypes
from datetime import datetime
from typing import Optional, Tuple
from fastapi import UploadFile
from PIL import Image
import io
from slugify import slugify

# Define allowed image mime types
ALLOWED_IMAGE_TYPES = [
    "image/jpeg", 
    "image/png", 
    "image/gif", 
    "image/webp", 
    "image/svg+xml", 
    "image/bmp", 
    "image/tiff"
]

def is_valid_image(file: UploadFile) -> bool:
    """Check if the uploaded file is a valid image."""
    content_type = file.content_type
    return content_type in ALLOWED_IMAGE_TYPES

async def save_upload_file(
    upload_file: UploadFile, 
    folder: str = "uploads", 
    convert_to_webp: bool = True
) -> Tuple[bool, str, Optional[str], Optional[int], Optional[str]]:
    """
    Save an uploaded file to the specified folder.
    
    Args:
        upload_file: The uploaded file
        folder: The folder to save the file in
        convert_to_webp: Whether to convert images to WebP format
        
    Returns:
        Tuple containing:
        - Success status (bool)
        - Error message if any (str)
        - File path if successful (str or None)
        - File size in bytes (int or None)
        - MIME type (str or None)
    """
    try:
        # Create folder if it doesn't exist
        os.makedirs(f"static/{folder}", exist_ok=True)
        
        # Get file content
        contents = await upload_file.read()
        
        # Get original filename and extension
        original_filename = upload_file.filename
        if not original_filename:
            return False, "Filename is empty", None, None, None
        
        # Generate a unique filename
        filename_without_ext = slugify(os.path.splitext(original_filename)[0])
        unique_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Check if it's an image and should be converted to WebP
        mime_type = upload_file.content_type
        if convert_to_webp and mime_type in ALLOWED_IMAGE_TYPES:
            try:
                # Open the image using PIL
                image = Image.open(io.BytesIO(contents))
                
                # Convert to RGB if it's RGBA (WebP doesn't support alpha in some implementations)
                if image.mode == 'RGBA':
                    # Create a white background
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    # Paste the image on the background
                    background.paste(image, mask=image.split()[3])
                    image = background
                elif image.mode != 'RGB':
                    image = image.convert('RGB')
                
                # Generate WebP filename
                filename = f"{filename_without_ext}_{timestamp}_{unique_id}.webp"
                file_path = f"static/{folder}/{filename}"
                
                # Save as WebP with 85% quality
                image.save(file_path, 'WEBP', quality=85)
                
                # Get file size
                file_size = os.path.getsize(file_path)
                
                # Update mime type
                mime_type = "image/webp"
                
                return True, "", file_path, file_size, mime_type
            except Exception as e:
                # If conversion fails, save the original file
                print(f"WebP conversion failed: {str(e)}")
        
        # For non-images or if conversion fails, save the original file
        extension = os.path.splitext(original_filename)[1]
        filename = f"{filename_without_ext}_{timestamp}_{unique_id}{extension}"
        file_path = f"static/{folder}/{filename}"
        
        # Write the file
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        return True, "", file_path, file_size, mime_type
    except Exception as e:
        return False, str(e), None, None, None

def get_file_url(file_path: str, base_url: Optional[str] = None) -> str:
    """
    Convert a file path to a URL.
    
    Args:
        file_path: The file path
        base_url: The base URL of the server
        
    Returns:
        The file URL
    """
    if not file_path.startswith("static/"):
        return file_path
    
    # Remove 'static/' from the beginning of the path
    url_path = file_path[7:]
    
    # If base_url is provided, use it, otherwise use relative path
    if base_url:
        if base_url.endswith('/'):
            return f"{base_url}static/{url_path}"
        else:
            return f"{base_url}/static/{url_path}"
    else:
        return f"/static/{url_path}"
