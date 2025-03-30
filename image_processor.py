#!/usr/bin/env python3
import datetime
import os
import logging
import io
from typing import Dict, List, Tuple, Optional
from PIL import Image, ImageOps, ImageFilter, ImageEnhance
import requests
import cairosvg

# Set up logging
logger = logging.getLogger('dobble_generator')


def process_icons(symbol_to_file: Dict[int, str]) -> Dict[int, Image.Image]:
    """
    Process icon images for use in Dobble cards.

    Args:
        symbol_to_file: Dictionary mapping symbol IDs to file paths

    Returns:
        Dictionary mapping symbol IDs to processed PIL Image objects
    """
    processed_images = {}

    for symbol, file_path in symbol_to_file.items():
        try:
            # Load and process the image
            processed_image = load_and_process_image(file_path)
            if processed_image:
                processed_images[symbol] = processed_image
            else:
                logger.warning(f"Failed to process image: {file_path}")
        except Exception as e:
            logger.error(f"Error processing image {file_path}: {e}")

    return processed_images


def load_and_process_image(file_path: str) -> Optional[Image.Image]:
    """
    Load an image from a file and process it for use in Dobble cards.

    Args:
        file_path: Path to the image file

    Returns:
        Processed PIL Image object, or None if loading failed
    """
    try:
        # Check file extension
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()

        if ext == '.svg':
            # Handle SVG files using CairoSVG
            png_data = cairosvg.svg2png(url=file_path)
            img = Image.open(io.BytesIO(png_data))
        else:
            # Handle raster images
            img = Image.open(file_path)

        # Convert to RGBA mode
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        # Apply preprocessing
        img = preprocess_image(img)

        return img

    except Exception as e:
        logger.error(f"Error loading image {file_path}: {e}")
        return None


def preprocess_image(img: Image.Image) -> Image.Image:
    """
    Preprocess an image for use in Dobble cards.

    Args:
        img: PIL Image object

    Returns:
        Processed PIL Image object
    """
    # Resize to a standard size (maintaining aspect ratio)
    img = resize_maintain_aspect(img, target_size=(400, 400))

    # Remove extra transparent border
    img = crop_transparent(img)

    # Add some padding around the image
    img = add_padding(img, padding_ratio=0.1)

    return img


def resize_maintain_aspect(img: Image.Image, target_size: Tuple[int, int]) -> Image.Image:
    """
    Resize an image to a target size while maintaining aspect ratio.

    Args:
        img: PIL Image object
        target_size: Tuple of (width, height) for the target size

    Returns:
        Resized PIL Image object
    """
    # Get current dimensions
    width, height = img.size

    # Calculate target width and height while maintaining aspect ratio
    if width > height:
        new_width = target_size[0]
        new_height = int(height * (new_width / width))
    else:
        new_height = target_size[1]
        new_width = int(width * (new_height / height))

    # Resize the image
    img_resized = img.resize((new_width, new_height), Image.LANCZOS)

    # Create a new blank image with the target size
    new_img = Image.new('RGBA', target_size, (0, 0, 0, 0))

    # Paste the resized image in the center of the new image
    paste_x = (target_size[0] - new_width) // 2
    paste_y = (target_size[1] - new_height) // 2
    new_img.paste(img_resized, (paste_x, paste_y), img_resized)

    return new_img


def crop_transparent(img: Image.Image) -> Image.Image:
    """
    Crop transparent borders around an image.

    Args:
        img: PIL Image object

    Returns:
        Cropped PIL Image object
    """
    # Get the alpha channel
    alpha = img.getchannel('A')

    # Get the bounding box of the non-transparent part
    bbox = alpha.getbbox()

    # If there's no bbox, return the original image
    if not bbox:
        return img

    # Crop to the bounding box
    return img.crop(bbox)


def add_padding(img: Image.Image, padding_ratio: float = 0.1) -> Image.Image:
    """
    Add padding around an image.

    Args:
        img: PIL Image object
        padding_ratio: Padding as a fraction of the image size

    Returns:
        Padded PIL Image object
    """
    # Calculate padding in pixels
    width, height = img.size
    padding_x = int(width * padding_ratio)
    padding_y = int(height * padding_ratio)

    # Create a new image with padding
    new_width = width + 2 * padding_x
    new_height = height + 2 * padding_y
    new_img = Image.new('RGBA', (new_width, new_height), (0, 0, 0, 0))

    # Paste the original image with padding
    new_img.paste(img, (padding_x, padding_y), img)

    return new_img


def download_icon(url: str, output_path: str) -> bool:
    """
    Download an icon from a URL.

    Args:
        url: URL of the icon
        output_path: Path where the downloaded icon should be saved

    Returns:
        True if download was successful, False otherwise
    """
    try:
        # Send a GET request to download the icon
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()

        # Save the icon to the output path
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return True

    except Exception as e:
        logger.error(f"Error downloading icon from {url}: {e}")
        return False


def create_placeholder_icon(output_path: str, text: str = '', size: Tuple[int, int] = (200, 200)) -> bool:
    """
    Create a placeholder icon with optional text.

    Args:
        output_path: Path where the placeholder icon should be saved
        text: Text to display on the placeholder
        size: Size of the placeholder in pixels

    Returns:
        True if creation was successful, False otherwise
    """
    try:
        # Create a blank image
        img = Image.new('RGBA', size, (200, 200, 200, 255))

        # Add some visual elements to make it look like a placeholder
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(img)

        # Draw a border
        border_width = 5
        draw.rectangle([0, 0, size[0] - 1, size[1] - 1], outline=(150, 150, 150), width=border_width)

        # Draw diagonal lines
        draw.line([(0, 0), (size[0], size[1])], fill=(150, 150, 150), width=border_width)
        draw.line([(0, size[1]), (size[0], 0)], fill=(150, 150, 150), width=border_width)

        # Add text if provided
        if text:
            # Try to use a system font
            try:
                # Use a reasonable default font size
                font_size = size[0] // 10
                font = ImageFont.truetype("Arial", font_size)
            except:
                # If that fails, use the default font
                font = ImageFont.load_default()

            # Calculate text position (centered)
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            text_x = (size[0] - text_width) // 2
            text_y = (size[1] - text_height) // 2

            # Draw the text
            draw.text((text_x, text_y), text, fill=(0, 0, 0), font=font)

        # Save the image
        img.save(output_path, format='PNG')

        return True

    except Exception as e:
        logger.error(f"Error creating placeholder icon: {e}")
        return False


def create_icon_set(set_name: str, icons: List[bytes], output_dir: str) -> bool:
    """
    Create an icon set from a list of icon data.

    Args:
        set_name: Name of the icon set
        icons: List of icon data (bytes)
        output_dir: Directory where the icon set should be saved

    Returns:
        True if creation was successful, False otherwise
    """
    try:
        # Create the output directory
        os.makedirs(output_dir, exist_ok=True)

        # Save each icon
        for i, icon_data in enumerate(icons):
            output_path = os.path.join(output_dir, f"icon_{i:03d}.png")
            with open(output_path, 'wb') as f:
                f.write(icon_data)

        # Create metadata file
        import json
        metadata = {
            'name': set_name,
            'count': len(icons),
            'created_at': datetime.datetime.now().isoformat()
        }

        with open(os.path.join(output_dir, 'metadata.json'), 'w') as f:
            json.dump(metadata, f)

        return True

    except Exception as e:
        logger.error(f"Error creating icon set: {e}")
        return False