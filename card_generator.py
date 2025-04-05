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
from PIL import Image, ImageDraw, ImageFont, ImageChops

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

def generate_smart_layout(n_symbols: int) -> List[Tuple[float, float, float]]:
    """
    Generate an optimized symbol layout that maximizes space usage.
    
    Uses a force-directed placement algorithm to position symbols efficiently.
    
    Args:
        n_symbols: Number of symbols to place
        
    Returns:
        List of (x_offset, y_offset, scale) tuples
    """
    import random
    import math
    
    # Size constraints
    min_scale = 0.15
    max_scale = 0.45
    
    # Determine base scale based on number of symbols
    if n_symbols <= 3:
        base_scale = 0.35
    elif n_symbols <= 5:
        base_scale = 0.30
    elif n_symbols <= 8:
        base_scale = 0.25
    else:
        base_scale = 0.20
    
    # Initialize positions with a simple approach
    positions = []
    
    # First place a center symbol if we have more than 3 symbols
    if n_symbols > 3:
        positions.append([0.5, 0.5, base_scale])
        remaining = n_symbols - 1
    else:
        remaining = n_symbols
    
    # Place remaining symbols in a circle
    radius = 0.35  # Distance from center as fraction of diameter
    for i in range(remaining):
        angle = 2 * math.pi * i / remaining
        x = 0.5 + radius * math.cos(angle)
        y = 0.5 + radius * math.sin(angle)
        scale = base_scale * 0.8  # Slightly smaller than center symbol
        positions.append([x, y, scale])
    
    # Now refine the placement with force-directed algorithm
    # Parameters
    iterations = 100
    repulsion = 0.01  # Symbol-to-symbol repulsion strength
    boundary = 0.02   # Boundary repulsion strength
    min_distance = 0.1  # Minimum preferred distance between symbols
    
    # Run optimization
    for _ in range(iterations):
        for i in range(len(positions)):
            force_x, force_y = 0, 0
            
            # Forces between symbols (repulsion)
            for j in range(len(positions)):
                if i == j:
                    continue
                
                # Get positions and sizes
                x1, y1, scale1 = positions[i]
                x2, y2, scale2 = positions[j]
                
                # Calculate distance
                dx = x1 - x2
                dy = y1 - y2
                distance = max(0.001, math.sqrt(dx*dx + dy*dy))
                
                # Calculate required distance based on symbol sizes
                required_distance = (scale1 + scale2) * 0.6
                
                # Apply force if too close
                if distance < required_distance:
                    force = repulsion * (required_distance - distance) / distance
                    force_x += dx * force
                    force_y += dy * force
            
            # Boundary force (keep symbols inside card)
            x, y, scale = positions[i]
            
            # Distance from edge
            edge_dist_left = x - scale*0.6
            edge_dist_right = 1.0 - x - scale*0.6
            edge_dist_top = y - scale*0.6
            edge_dist_bottom = 1.0 - y - scale*0.6
            
            # Apply inward force if too close to edge
            if edge_dist_left < 0.05:
                force_x += boundary * (0.05 - edge_dist_left) / max(0.001, edge_dist_left)
            if edge_dist_right < 0.05:
                force_x -= boundary * (0.05 - edge_dist_right) / max(0.001, edge_dist_right)
            if edge_dist_top < 0.05:
                force_y += boundary * (0.05 - edge_dist_top) / max(0.001, edge_dist_top)
            if edge_dist_bottom < 0.05:
                force_y -= boundary * (0.05 - edge_dist_bottom) / max(0.001, edge_dist_bottom)
            
            # Update position
            positions[i][0] += force_x
            positions[i][1] += force_y
            
            # Ensure positions stay within bounds
            positions[i][0] = max(positions[i][2]*0.6, min(1.0 - positions[i][2]*0.6, positions[i][0]))
            positions[i][1] = max(positions[i][2]*0.6, min(1.0 - positions[i][2]*0.6, positions[i][1]))
    
    # Optimize scaling - try to expand symbols to fill the card better
    can_expand = True
    expansion_iterations = 10
    
    while can_expand and expansion_iterations > 0:
        expansion_iterations -= 1
        can_expand = False
        
        # Try to expand each symbol slightly
        for i in range(len(positions)):
            old_scale = positions[i][2]
            
            # Don't exceed maximum scale
            if old_scale >= max_scale:
                continue
                
            # Try a slightly larger scale
            new_scale = min(max_scale, old_scale * 1.05)
            positions[i][2] = new_scale
            
            # Check for overlaps
            has_overlap = False
            for j in range(len(positions)):
                if i == j:
                    continue
                    
                x1, y1, scale1 = positions[i]
                x2, y2, scale2 = positions[j]
                
                distance = math.sqrt((x1-x2)**2 + (y1-y2)**2)
                min_req_distance = (scale1 + scale2) * 0.6
                
                if distance < min_req_distance:
                    has_overlap = True
                    break
            
            # Also check if it goes outside boundary
            x, y, scale = positions[i]
            if (x - scale*0.6 < 0.02 or x + scale*0.6 > 0.98 or 
                y - scale*0.6 < 0.02 or y + scale*0.6 > 0.98):
                has_overlap = True
            
            # If overlap, revert to old scale
            if has_overlap:
                positions[i][2] = old_scale
            else:
                can_expand = True  # We were able to expand something
    
    # Convert to tuples for final result
    return [(p[0], p[1], p[2]) for p in positions]

def create_circular_card(symbols: List[int],
                         images: Dict[int, Image.Image],
                         size: Tuple[int, int] = (800, 800),
                         background_color: Tuple[int, int, int] = (255, 255, 255),
                         border_color: Tuple[int, int, int] = (0, 0, 0),
                         border_width: int = 10,
                         layout: str = 'smart') -> Image.Image:
    """
    Create a circular Dobble card with the given symbols and images.
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
    if layout == 'smart':
        positions = generate_smart_layout(len(symbols))
    elif layout == 'grid':
        positions = generate_grid_layout(len(symbols))
    else:  # 'circle' is the default
        positions = generate_circular_layout(len(symbols))

    # Randomize rotation for each symbol
    positions_randomized = []
    for x, y, scale in positions:
        # Add random rotation, but more controlled jitter to preserve layout
        x_jitter = random.uniform(-0.02, 0.02)
        y_jitter = random.uniform(-0.02, 0.02)
        rotation = random.uniform(-25, 25)
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
    """
    # Force A4 for optimal layout with 4 cards per page
    page_size = A4
    page_width, page_height = page_size
    
    # Use fixed 4 cards per page in a 2x2 grid
    cards_per_page = 4
    
    # Calculate card dimensions for 2x2 grid with margins
    margin = 20
    
    # Important: Make card dimensions square to prevent oval distortion
    card_size = min((page_width - (3 * margin)) / 2, (page_height - (3 * margin)) / 2)
    card_width = card_size
    card_height = card_size
    
    # Card render size in pixels (for high quality)
    card_pixels = (1000, 1000)
    
    # Calculate number of pages needed
    n_pages = math.ceil(len(cards) / cards_per_page)
    
    # Create output file path
    output_file = os.path.join(output_dir, f"{job_id}.pdf")
    
    # Create a new PDF
    c = canvas.Canvas(output_file, pagesize=page_size)
    
    # Calculate positions for centered square cards in a 2x2 grid
    h_margin = (page_width - (2 * card_width)) / 3
    v_margin = (page_height - (2 * card_height)) / 3
    
    positions = [
        # x, y coordinates (ReportLab's origin is bottom-left)
        (h_margin, page_height - v_margin - card_height),              # Top left
        (2*h_margin + card_width, page_height - v_margin - card_height), # Top right
        (h_margin, v_margin),                                          # Bottom left
        (2*h_margin + card_width, v_margin)                            # Bottom right
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
            
            # Add the card to the PDF - use same width and height to keep aspect ratio
            c.drawImage(card_file, x, y, width=card_width, height=card_height, preserveAspectRatio=True)
            
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