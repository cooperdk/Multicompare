import math
from PIL import Image, ImageDraw, ImageFilter

def create_gradient(width, height, start_color, end_color):
    """Creates a vertical linear gradient image."""
    base = Image.new('RGBA', (width, height), start_color)
    top = Image.new('RGBA', (width, height), end_color)
    mask = Image.new('L', (width, height))
    mask_data = []
    for y in range(height):
        mask_data.extend([int(255 * (y / height))] * width)
    mask.putdata(mask_data)
    base.paste(top, (0, 0), mask)
    return base

def generate_icon_image(size=512):
    """
    Generates the application icon in memory.
    Args:
        size (int): The dimension (width/height) of the icon.
    Returns:
        PIL.Image: The generated icon.
    """
    # Scale factor (internal resolution vs output)
    # We render at 2x size for anti-aliasing, then resize down
    render_size = size * 2
    W, H = render_size, render_size
    canvas = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    
    # --- GEOMETRY ---
    SHIFT_X = int(-50 * (render_size / 2048))
    SHIFT_Y = int(-50 * (render_size / 2048))
    
    cx = (W // 2) + SHIFT_X
    cy = (H // 2) + SHIFT_Y
    
    # Scale constants based on render_size relative to original 2048 logic
    s = render_size / 2048
    
    bg_margin = int(100 * s)
    bg_radius = int(450 * s)
    lens_radius = int(674 * s)
    lens_bbox = (cx - lens_radius, cy - lens_radius, cx + lens_radius, cy + lens_radius)

    METAL_COLOR = (235, 235, 235) 
    INNER_DARK  = (40, 40, 40)
    
    # --- A. BACKGROUND ---
    bg_grad = create_gradient(W, H, (60, 60, 60), (20, 20, 20))
    mask = Image.new('L', (W, H), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.rounded_rectangle((bg_margin, bg_margin, W-bg_margin, H-bg_margin), radius=bg_radius, fill=255)
    
    body = Image.new('RGBA', (W, H), (0,0,0,0))
    body.paste(bg_grad, (0,0), mask)
    draw_body = ImageDraw.Draw(body)
    draw_body.rounded_rectangle((bg_margin, bg_margin, W-bg_margin, H-bg_margin), radius=bg_radius, outline=(80,80,80), width=int(20*s))
    canvas.alpha_composite(body)

    # --- B. METAL OBJECT ---
    metal_layer = Image.new('RGBA', (W, H), (0,0,0,0))
    draw_metal = ImageDraw.Draw(metal_layer)
    
    handle_width = int(200 * s)
    handle_len = int(950 * s)
    offset = int(handle_len * 0.707)
    
    h_end_x = cx + offset
    h_end_y = cy + offset
    
    # Handle
    draw_metal.line([(cx, cy), (h_end_x, h_end_y)], fill=METAL_COLOR, width=handle_width)
    r_cap = handle_width // 2
    draw_metal.ellipse((h_end_x - r_cap, h_end_y - r_cap, h_end_x + r_cap, h_end_y + r_cap), fill=METAL_COLOR)

    # Ring
    draw_metal.ellipse(lens_bbox, fill=METAL_COLOR)
    
    # --- C. SHADOW ---
    shadow_layer = Image.new('RGBA', (W, H), (0,0,0,0))
    silhouette = metal_layer.split()[3]
    shadow_fill = Image.new('RGBA', (W, H), (0,0,0,160))
    shadow_layer.paste(shadow_fill, (0,0), mask=silhouette)
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(int(50*s)))
    
    shifted_shadow = Image.new('RGBA', (W, H), (0,0,0,0))
    shifted_shadow.paste(shadow_layer, (int(30*s), int(30*s)))
    
    canvas.alpha_composite(shifted_shadow)
    canvas.alpha_composite(metal_layer)

    # --- D. GLASS ---
    gap = int(40 * s)
    inner_bbox = (lens_bbox[0]+gap, lens_bbox[1]+gap, lens_bbox[2]-gap, lens_bbox[3]-gap)
    draw_cv = ImageDraw.Draw(canvas)
    draw_cv.ellipse(inner_bbox, fill=INNER_DARK)

    glass_gap = int(40 * s)
    g_bbox = (inner_bbox[0]+glass_gap, inner_bbox[1]+glass_gap, inner_bbox[2]-glass_gap, inner_bbox[3]-glass_gap)
    
    left_img = create_gradient(W, H, (0, 150, 255), (0, 80, 200))
    left_mask = Image.new('L', (W, H), 0)
    d_lm = ImageDraw.Draw(left_mask)
    d_lm.chord(g_bbox, 90, 270, fill=255)
    
    glass_layer = Image.new('RGBA', (W, H), (0,0,0,0))
    glass_layer.paste(left_img, (0,0), left_mask)

    right_img = create_gradient(W, H, (255, 180, 0), (255, 100, 0))
    right_mask = Image.new('L', (W, H), 0)
    d_rm = ImageDraw.Draw(right_mask)
    d_rm.chord(g_bbox, 270, 90, fill=255)
    
    glass_layer.paste(right_img, (0,0), right_mask)
    canvas.alpha_composite(glass_layer)

    draw_cv.line((cx, g_bbox[1], cx, g_bbox[3]), fill=INNER_DARK, width=int(20*s))

    # --- E. GLOSS ---
    gloss = Image.new('RGBA', (W, H), (0,0,0,0))
    d_gloss = ImageDraw.Draw(gloss)
    gl_x = g_bbox[0] + int(100*s)
    gl_y = g_bbox[1] + int(50*s)
    d_gloss.ellipse((gl_x, gl_y, W - gl_x + (SHIFT_X*2), cy), fill=(255, 255, 255, 40))
    
    lens_mask = Image.new('L', (W, H), 0)
    d_lens_mask = ImageDraw.Draw(lens_mask)
    d_lens_mask.ellipse(g_bbox, fill=255)
    
    final_gloss = Image.new('RGBA', (W, H), (0,0,0,0))
    final_gloss.paste(gloss, (0,0), lens_mask)
    canvas.alpha_composite(final_gloss)

    # Resize to requested output size (High Quality)
    return canvas.resize((size, size), Image.Resampling.LANCZOS)