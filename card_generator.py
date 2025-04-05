#!/usr/bin/env python3

import os
import logging
import math
import random
from typing import List, Dict, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont
import cairo
from reportlab.lib.pagesizes import A4, A5, A6, LETTER
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# Set up logging
logger = logging.getLogger('dobble_generator')

# Card size constants
CARD_SIZES = {
    'A4': A4,
    'A5': A5,
    'A6': A6,
    'LETTER': LETTER,
}

# Commonly used circular layouts
# In card_generator.py
# Update the CIRCULAR_LAYOUTS constant

CIRCULAR_LAYOUTS = {
    # symbols_per_card: [(x_offset, y_offset, scale), ...]
    8: [
        (0.5, 0.5, 0.35),   # Center (slightly smaller)
        (0.5, 0.22, 0.20),  # Top
        (0.78, 0.28, 0.20), # Top-right
        (0.82, 0.5, 0.20),  # Right
        (0.78, 0.72, 0.20), # Bottom-right
        (0.5, 0.78, 0.20),  # Bottom
        (0.22, 0.72, 0.20), # Bottom-left
        (0.18, 0.5, 0.20),  # Left
        (0.22, 0.28, 0.20), # Top-left
    ],
    7: [
        (0.5, 0.5, 0.35),   # Center
        (0.5, 0.22, 0.22),  # Top
        (0.78, 0.35, 0.22), # Top-right
        (0.78, 0.65, 0.22), # Bottom-right
        (0.5, 0.78, 0.22),  # Bottom
        (0.22, 0.65, 0.22), # Bottom-left
        (0.22, 0.35, 0.22), # Top-left
    ],
    6: [
        (0.5, 0.5, 0.30),   # Center
        (0.5, 0.22, 0.22),  # Top
        (0.78, 0.35, 0.22), # Top-right
        (0.78, 0.65, 0.22), # Bottom-right
        (0.5, 0.78, 0.22),  # Bottom
        (0.22, 0.5, 0.22),  # Left
    ],
    5: [
        (0.5, 0.5, 0.35),   # Center
        (0.5, 0.22, 0.25),  # Top
        (0.78, 0.5, 0.25),  # Right
        (0.65, 0.78, 0.25), # Bottom-right
        (0.35, 0.78, 0.25), # Bottom-left
    ],
    4: [
        (0.5, 0.3, 0.30),   # Top
        (0.7, 0.6, 0.30),   # Right
        (0.5, 0.75, 0.30),  # Bottom
        (0.3, 0.6, 0.30),   # Left
    ],
    3: [
        (0.5, 0.25, 0.35),  # Top
        (0.7, 0.7, 0.35),   # Bottom-right
        (0.3, 0.7, 0.35),   # Bottom-left
    ],
}

def generate_circular_layout(n_symbols: int) -> List[Tuple[float, float, float]]:
    """
    Generate a circular layout for the given number of symbols.
    Returns a list of (x_offset, y_offset, scale) tuples.
    """
    if n_symbols in CIRCULAR_LAYOUTS:
        return CIRCULAR_LAYOUTS[n_symbols]

    # For other numbers, generate a circular layout
    layout = []

    # One symbol in the center if more than 3 symbols
    if n_symbols > 3:
        layout.append((0.5, 0.5, 0.35))  # Center symbol, slightly smaller
        remaining = n_symbols - 1
    else:
        remaining = n_symbols

    # Place remaining symbols in a circle
    radius = 0.28  # Reduced radius to keep symbols further from edge
    angle_step = 2 * math.pi / remaining
    
    # Scale based on number of symbols
    if remaining <= 6:
        scale = 0.22
    else:
        scale = 0.20  # Smaller for more symbols
    
    for i in range(remaining):
        angle = i * angle_step
        x = 0.5 + radius * math.cos(angle)
        y = 0.5 + radius * math.sin(angle)
        layout.append((x, y, scale))

    return layout

def generate_grid_layout(n_symbols: int) -> List[Tuple[float, float, float]]:
    """
    Generate a grid layout for the given number of symbols.
    Returns a list of (x_offset, y_offset, scale) tuples.
    """
    # Calculate grid dimensions
    cols = math.ceil(math.sqrt(n_symbols))
    rows = math.ceil(n_symbols / cols)

    # Calculate scale based on grid
    scale = 0.9 / max(cols, rows)

    # Generate grid positions
    layout = []
    for i in range(n_symbols):
        row = i // cols
        col = i % cols

        # Calculate position (centered in cell)
        x = (col + 0.5) / cols
        y = (row + 0.5) / rows

        layout.append((x, y, scale))

    return layout

def create_circular_card(symbols: List[int],
                         images: Dict[int, Image.Image],
                         size: Tuple[int, int] = (800, 800),
                         background_color: Tuple[int, int, int] = (255, 255, 255),
                         border_color: Tuple[int, int, int] = (0, 0, 0),
                         border_width: int = 10,
                         layout: str = 'circle') -> Image.Image:
    """
    Create a circular Dobble card with the given symbols and images.

    Args:
        symbols: List of symbol IDs to place on the card
        images: Dictionary mapping symbol IDs to PIL Image objects
        size: Size of the card in pixels (width, height)
        background_color: Background color as RGB tuple
        border_color: Border color as RGB tuple
        border_width: Width of the border in pixels
        layout: Layout type ('circle' or 'grid')

    Returns:
        PIL Image of the rendered card
    """
    # Create a blank card with the given background color
    card = Image.new('RGBA', size, background_color)
    draw = ImageDraw.Draw(card)

    # Calculate circle parameters
    center = (size[0] // 2, size[1] // 2)
    radius = min(size) // 2 - border_width // 2
    inner_radius = radius - border_width  # For clipping images

    # Create a circular mask for clipping symbols
    mask = Image.new('L', size, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse(
        [(center[0] - inner_radius, center[1] - inner_radius),
         (center[0] + inner_radius, center[1] + inner_radius)],
        fill=255
    )

    # Draw a circular border
    draw.ellipse(
        [(center[0] - radius, center[1] - radius),
         (center[0] + radius, center[1] + radius)],
        outline=border_color,
        width=border_width
    )

    # Select the appropriate layout
    if layout == 'grid':
        positions = generate_grid_layout(len(symbols))
    else:  # 'circle' is the default
        positions = generate_circular_layout(len(symbols))

    # Randomize the position of each symbol (within its assigned zone)
    positions_randomized = []
    for x, y, scale in positions:
        # Reduce jitter to keep symbols more centered in their zones
        x_jitter = random.uniform(-0.03, 0.03)
        y_jitter = random.uniform(-0.03, 0.03)
        # Add some random rotation
        rotation = random.uniform(-20, 20)
        positions_randomized.append((x + x_jitter, y + y_jitter, scale, rotation))

    # Place each symbol on the card
    for i, symbol in enumerate(symbols):
        if i >= len(positions_randomized):
            logger.warning(f"Not enough positions for all symbols on card")
            break

        # Get the image for this symbol
        if symbol not in images:
            logger.warning(f"No image found for symbol {symbol}")
            continue

        img = images[symbol]

        # Get position and scale for this symbol
        x, y, scale, rotation = positions_randomized[i]

        # Calculate pixel position
        px = int(x * size[0])
        py = int(y * size[1])

        # Scale the image
        scaled_size = int(min(size) * scale)
        img_scaled = img.resize((scaled_size, scaled_size), Image.LANCZOS)

        # Rotate the image
        img_rotated = img_scaled.rotate(rotation, resample=Image.BICUBIC, expand=False)

        # Create a temporary image for this symbol
        temp = Image.new('RGBA', size, (0, 0, 0, 0))
        
        # Calculate paste position (centered on the point)
        paste_x = px - img_rotated.width // 2
        paste_y = py - img_rotated.height // 2

        # Paste the image onto the temporary image
        temp.paste(img_rotated, (paste_x, paste_y), img_rotated)
        
        # Apply the circular mask to clip the symbol
        r, g, b, a = temp.split()
        a = ImageChops.multiply(a, mask)
        temp = Image.merge('RGBA', (r, g, b, a))

        # Composite this symbol onto the card
        card = Image.alpha_composite(card, temp)

    return card


def create_square_card(symbols: List[int],
                       images: Dict[int, Image.Image],
                       size: Tuple[int, int] = (800, 800),
                       background_color: Tuple[int, int, int] = (255, 255, 255),
                       border_color: Tuple[int, int, int] = (0, 0, 0),
                       border_width: int = 10,
                       layout: str = 'circle') -> Image.Image:
    """
    Create a square Dobble card with the given symbols and images.

    Args:
        symbols: List of symbol IDs to place on the card
        images: Dictionary mapping symbol IDs to PIL Image objects
        size: Size of the card in pixels (width, height)
        background_color: Background color as RGB tuple
        border_color: Border color as RGB tuple
        border_width: Width of the border in pixels
        layout: Layout type ('circle' or 'grid')

    Returns:
        PIL Image of the rendered card
    """
    # Create a blank card with the given background color
    card = Image.new('RGBA', size, background_color)
    draw = ImageDraw.Draw(card)

    # Draw a square border
    border_rect = [
        border_width // 2,
        border_width // 2,
        size[0] - border_width // 2,
        size[1] - border_width // 2
    ]
    draw.rectangle(border_rect, outline=border_color, width=border_width)

    # Select the appropriate layout
    if layout == 'grid':
        positions = generate_grid_layout(len(symbols))
    else:  # 'circle' is the default
        positions = generate_circular_layout(len(symbols))

    # Randomize the position of each symbol (within its assigned zone)
    positions_randomized = []
    for x, y, scale in positions:
        # Add some random variation to position (±10%)
        x_jitter = random.uniform(-0.05, 0.05)
        y_jitter = random.uniform(-0.05, 0.05)
        # Add some random rotation
        rotation = random.uniform(-30, 30)
        positions_randomized.append((x + x_jitter, y + y_jitter, scale, rotation))

    # Place each symbol on the card
    for i, symbol in enumerate(symbols):
        if i >= len(positions_randomized):
            logger.warning(f"Not enough positions for all symbols on card")
            break

        # Get the image for this symbol
        if symbol not in images:
            logger.warning(f"No image found for symbol {symbol}")
            continue

        img = images[symbol]

        # Get position and scale for this symbol
        x, y, scale, rotation = positions_randomized[i]

        # Calculate pixel position
        px = int(x * size[0])
        py = int(y * size[1])

        # Scale the image
        scaled_size = int(min(size) * scale)
        img_scaled = img.resize((scaled_size, scaled_size), Image.LANCZOS)

        # Rotate the image
        img_rotated = img_scaled.rotate(rotation, resample=Image.BICUBIC, expand=False)

        # Calculate paste position (centered on the point)
        paste_x = px - img_rotated.width // 2
        paste_y = py - img_rotated.height // 2

        # Paste the image onto the card
        card.paste(img_rotated, (paste_x, paste_y), img_rotated)

    return card


def create_cards_pdf(job_id: str,
                   cards: List[List[int]],
                   images: Dict[int, Image.Image],
                   output_dir: str,
                   card_shape: str = 'circle',
                   card_size: str = 'A4',
                   layout: str = 'circle',
                   cards_per_page: int = 4) -> str:
    """
    Create a PDF with multiple Dobble cards, optimized for A4 with 4 cards per page.

    Args:
        job_id: Unique ID for the job
        cards: List of cards, where each card is a list of symbol IDs
        images: Dictionary mapping symbol IDs to PIL Image objects
        output_dir: Directory where the PDF should be saved
        card_shape: Shape of the cards ('circle' or 'square')
        card_size: Size of the cards (e.g., 'A4', 'A5')
        layout: Layout of symbols on the cards ('circle' or 'grid')
        cards_per_page: Number of cards to place on each page (1, 2, 4, or 9)

    Returns:
        Path to the generated PDF file
    """
    # Force A4 for optimal layout with 4 cards per page
    page_size = A4
    page_width, page_height = page_size
    
    # Use fixed 4 cards per page in a 2x2 grid
    cards_per_page = 4
    
    # Calculate card dimensions for 2x2 grid with margins
    margin = 20
    card_width = (page_width - (3 * margin)) / 2
    card_height = (page_height - (3 * margin)) / 2
    
    # Card render size in pixels (for high quality)
    card_pixels = (1000, 1000)
    
    # Calculate number of pages needed
    n_pages = math.ceil(len(cards) / cards_per_page)
    
    # Create output file path
    output_file = os.path.join(output_dir, f"{job_id}.pdf")
    
    # Create a new PDF
    c = canvas.Canvas(output_file, pagesize=page_size)
    
    # 2x2 grid positions
    positions = [
        # x, y coordinates (ReportLab's origin is bottom-left)
        (margin, page_height - margin - card_height),                    # Top left
        (margin + card_width + margin/2, page_height - margin - card_height),  # Top right
        (margin, margin),                                               # Bottom left
        (margin + card_width + margin/2, margin)                         # Bottom right
    ]
    
    # Generate each page
    for page in range(n_pages):
        # Get the cards for this page
        page_cards = cards[page * cards_per_page: min((page + 1) * cards_per_page, len(cards))]
        
        # Place each card on the page
        for i, card_symbols in enumerate(page_cards):
            if i >= len(positions):
                break
                
            # Get position for this card
            x, y = positions[i]
            
            # Create the card image
            if card_shape == 'square':
                card_img = create_square_card(card_symbols, images, card_pixels, layout=layout)
            else:  # 'circle' is the default
                card_img = create_circular_card(card_symbols, images, card_pixels, layout=layout)
            
            # Save the card image temporarily
            card_file = os.path.join(output_dir, f"{job_id}_card_{page}_{i}.png")
            card_img.save(card_file, format='PNG')
            
            # Add the card to the PDF
            c.drawImage(card_file, x, y, width=card_width, height=card_height)
            
            # Add a small card number for reference
            c.setFont("Helvetica", 8)
            c.drawString(x + 5, y + 5, f"Card #{page * cards_per_page + i + 1}")
            
            # Delete the temporary file
            os.remove(card_file)
        
        # Finish the page
        c.showPage()
    
    # Save the PDF
    c.save()
    
    return output_file


def generate_cards(job_id: str,
                   cards: List[List[int]],
                   images: Dict[int, Image.Image],
                   output_dir: str,
                   card_shape: str = 'circle',
                   card_size: str = 'A4',
                   layout: str = 'circle',
                   cards_per_page: int = 4,
                   export_png: bool = True) -> Tuple[str, List[str]]:
    """
    Generate Dobble cards and save as PDF and optionally PNG.

    Args:
        job_id: Unique ID for the job
        cards: List of cards, where each card is a list of symbol IDs
        images: Dictionary mapping symbol IDs to PIL Image objects
        output_dir: Directory where the files should be saved
        card_shape: Shape of the cards ('circle' or 'square')
        card_size: Size of the cards (e.g., 'A4', 'A5')
        layout: Layout of symbols on the cards ('circle' or 'grid')
        cards_per_page: Number of cards to place on each page (1, 2, 4, or 9)
        export_png: Whether to also export individual card images as PNG

    Returns:
        Tuple of (PDF path, list of PNG paths)
    """
    # Create PDF with optimized settings
    pdf_path = create_cards_pdf(
        job_id,
        cards,
        images,
        output_dir,
        card_shape,
        card_size,
        layout,
        cards_per_page
    )

    # Export individual cards as PNG if requested
    png_paths = []
    if export_png:
        for i, card_symbols in enumerate(cards):
            # Create the card image
            if card_shape == 'square':
                card_img = create_square_card(card_symbols, images, (800, 800), layout=layout)
            else:  # 'circle' is the default
                card_img = create_circular_card(card_symbols, images, (800, 800), layout=layout)

            # Save the card image
            png_path = os.path.join(output_dir, f"{job_id}_card_{i}.png")
            card_img.save(png_path, format='PNG')
            png_paths.append(png_path)

    return pdf_path, png_paths