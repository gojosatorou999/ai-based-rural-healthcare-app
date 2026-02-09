"""
Generate placeholder PWA icons for the Rural Telemedicine Platform
"""

from PIL import Image, ImageDraw, ImageFont
import os

# Create icons directory
icons_dir = 'static/icons'
os.makedirs(icons_dir, exist_ok=True)

# Icon sizes needed for PWA
sizes = [32, 72, 96, 128, 144, 152, 192, 384, 512]

# Colors matching the dark theme
bg_color = (10, 10, 10)  # --bg-primary
accent_color = (196, 255, 13)  # --primary (neon green)

def create_icon(size):
    """Create a simple icon with the app logo"""
    # Create image with dark background
    img = Image.new('RGB', (size, size), bg_color)
    draw = ImageDraw.Draw(img)
    
    # Draw a heartbeat icon shape
    # Draw a circle for the medical cross background
    circle_radius = size // 3
    circle_center = (size // 2, size // 2)
    
    # Draw circle
    draw.ellipse(
        [
            circle_center[0] - circle_radius,
            circle_center[1] - circle_radius,
            circle_center[0] + circle_radius,
            circle_center[1] + circle_radius
        ],
        fill=accent_color
    )
    
    # Draw a simple + symbol in the center
    line_width = max(2, size // 20)
    cross_size = circle_radius // 2
    
    # Vertical line
    draw.rectangle(
        [
            circle_center[0] - line_width,
            circle_center[1] - cross_size,
            circle_center[0] + line_width,
            circle_center[1] + cross_size
        ],
        fill=bg_color
    )
    
    # Horizontal line
    draw.rectangle(
        [
            circle_center[0] - cross_size,
            circle_center[1] - line_width,
            circle_center[0] + cross_size,
            circle_center[1] + line_width
        ],
        fill=bg_color
    )
    
    return img

# Generate all icon sizes
for size in sizes:
    icon = create_icon(size)
    icon.save(f'{icons_dir}/icon-{size}x{size}.png', 'PNG')
    print(f'Created icon-{size}x{size}.png')

# Create favicon
favicon = create_icon(32)
favicon.save('static/favicon.ico', 'ICO')
print('Created favicon.ico')

print('\n✅ All PWA icons generated successfully!')
