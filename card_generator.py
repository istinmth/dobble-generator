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
CIRCULAR_LAYOUTS = {
    # symbols_per_card: [(x_offset, y_offset, scale), ...]
    8: [
        (0.5, 0.5, 0.5),  # Center
        (0.5, 0.15, 0.25),  # Top
        (0.85, 0.25, 0.25),  # Top-right
        (0.9, 0.5, 0.25),  # Right
        (0.85, 0.75, 0.25),  # Bottom-right
        (0.5, 0.85, 0.25),  # Bottom
        (0.15, 0.75, 0.25),  # Bottom-left
        (0.1, 0.5, 0.25),  # Left
        (0.15, 0.25, 0.25),  # Top-left
    ],
    7: [
        (0.5, 0.5, 0.5),  # Center
        (0.5, 0.15, 0.25),  # Top
        (0.85, 0.3, 0.25),  # Top-right
        (0.85, 0.7, 0.25),  # Bottom-right
        (0.5, 0.85, 0.25),  # Bottom
        (0.15, 0.7, 0.25),  # Bottom-left
        (0.15, 0.3, 0.25),  # Top-left
    ],
    6: [
        (0.5, 0.5, 0.45),  # Center
        (0.5, 0.15, 0.25),  # Top
        (0.85, 0.35, 0.25),  # Top-right
        (0.85, 0.65, 0.25),  # Bottom-right
        (0.5, 0.85, 0.25),  # Bottom
        (0.15, 0.5, 0.25),  # Left
    ],
    5: [
        (0.5, 0.5, 0.45),  # Center
        (0.5, 0.15, 0.3),  # Top
        (0.85, 0.5, 0.3),  # Right
        (0.65, 0.85, 0.3),  # Bottom-right
        (0.35, 0.85, 0.3),  # Bottom-left
    ],
    4: [
        (0.5, 0.3, 0.4),  # Top
        (0.75, 0.6, 0.4),  # Right
        (0.5, 0.8, 0.4),  # Bottom
        (0.25, 0.6, 0.4),  # Left
    ],
    3: [
        (0.5, 0.25, 0.45),  # Top
        (0.75, 0.7, 0.45),  # Bottom-right
        (0.25, 0.7, 0.45),  # Bottom-left
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

    # One symbol in the center, bigger than the others
    layout.append((0.5, 0.5, 0.4))

    # The rest arranged in a circle
    if n_symbols > 1:
        radius = 0.35  # Distance from center
        angle_step = 2 * math.pi / (n_symbols - 1)
        scale = min(0.25, 1.0 / n_symbols)  # Adjust scale based on number of symbols

        for i in range(n_symbols - 1):
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

    # Draw a circular border
    center = (size[0] // 2, size[1] // 2)
    radius = min(size) // 2 - border_width // 2
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
                     cards_per_page: int = 1) -> str:
    """
    Create a PDF with multiple Dobble cards.

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
    # Determine page size
    page_size = CARD_SIZES.get(card_size.upper(), A4)
    page_width, page_height = page_size

    # Determine card size based on cards_per_page
    if cards_per_page == 1:
        card_width, card_height = page_width * 0.9, page_height * 0.9
        cards_layout = [(0.5, 0.5)]  # One card centered
    elif cards_per_page == 2:
        card_width, card_height = page_width * 0.9, page_height * 0.45
        cards_layout = [(0.5, 0.25), (0.5, 0.75)]  # Two cards stacked
    elif cards_per_page == 4:
        card_width, card_height = page_width * 0.45, page_height * 0.45
        cards_layout = [(0.25, 0.25), (0.75, 0.25), (0.25, 0.75), (0.75, 0.75)]  # 2x2 grid
    elif cards_per_page == 9:
        card_width, card_height = page_width * 0.3, page_height * 0.3
        cards_layout = [
            (0.17, 0.17), (0.5, 0.17), (0.83, 0.17),
            (0.17, 0.5), (0.5, 0.5), (0.83, 0.5),
            (0.17, 0.83), (0.5, 0.83), (0.83, 0.83)
        ]  # 3x3 grid
    else:
        # Default to one card per page
        card_width, card_height = page_width * 0.9, page_height * 0.9
        cards_layout = [(0.5, 0.5)]  # One card centered

    # Determine card size in pixels (for rendering)
    card_pixels = (800, 800)

    # Calculate number of pages needed
    n_pages = math.ceil(len(cards) / cards_per_page)

    # Create output file path
    output_file = os.path.join(output_dir, f"{job_id}.pdf")

    # Create a new PDF
    c = canvas.Canvas(output_file, pagesize=page_size)

    # Generate each page
    for page in range(n_pages):
        # Get the cards for this page
        page_cards = cards[page * cards_per_page: (page + 1) * cards_per_page]

        # Place each card on the page
        for i, card_symbols in enumerate(page_cards):
            if i >= len(cards_layout):
                break

            # Get position for this card
            card_x, card_y = cards_layout[i]

            # Convert to absolute coordinates
            x = card_x * page_width - card_width / 2
            y = page_height - (card_y * page_height + card_height / 2)  # ReportLab coordinates start from bottom

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
                   cards_per_page: int = 1,
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
    # Create PDF
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