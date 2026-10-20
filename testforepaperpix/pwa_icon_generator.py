#!/usr/bin/env python3

"""
Icon Generation Script for EpaperPix PWA
Requires: Pillow (PIL)
Usage: python generate_icons.py source-icon.png
"""

import sys
import os
from PIL import Image, ImageDraw
import argparse

def create_directories(icon_dir, splash_dir):
    """Create necessary directories if they don't exist."""
    os.makedirs(icon_dir, exist_ok=True)
    os.makedirs(splash_dir, exist_ok=True)

def resize_and_save(source_image, size, output_path):
    """Resize image and save to specified path."""
    resized = source_image.resize((size, size), Image.Resampling.LANCZOS)
    resized.save(output_path, optimize=True)

def create_splash_screen(source_image, width, height, icon_size, output_path, bg_color='#dc2626'):
    """Create a splash screen with centered icon on colored background."""
    # Create background
    splash = Image.new('RGB', (width, height), bg_color)
    
    # Resize source icon
    icon = source_image.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
    
    # Calculate center position
    x = (width - icon_size) // 2
    y = (height - icon_size) // 2
    
    # Paste icon onto background
    if icon.mode == 'RGBA':
        splash.paste(icon, (x, y), icon)
    else:
        splash.paste(icon, (x, y))
    
    # Save as JPEG
    splash.convert('RGB').save(output_path, 'JPEG', quality=85, optimize=True)

def create_social_media_image(source_image, width, height, output_path, bg_color='#dc2626'):
    """Create social media image with icon centered on background."""
    # Create background
    social_img = Image.new('RGB', (width, height), bg_color)
    
    # Calculate icon size (proportional to image size)
    icon_size = min(width, height) // 3
    icon = source_image.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
    
    # Calculate center position
    x = (width - icon_size) // 2
    y = (height - icon_size) // 2
    
    # Paste icon
    if icon.mode == 'RGBA':
        social_img.paste(icon, (x, y), icon)
    else:
        social_img.paste(icon, (x, y))
    
    social_img.save(output_path, 'PNG', optimize=True)

def create_favicon_ico(source_image, output_path):
    """Create favicon.ico with multiple sizes."""
    sizes = [16, 32, 48]
    images = []
    
    for size in sizes:
        resized = source_image.resize((size, size), Image.Resampling.LANCZOS)
        # Convert to P mode for better ICO compatibility
        if resized.mode != 'P':
            resized = resized.convert('P', palette=Image.ADAPTIVE, colors=256)
        images.append(resized)
    
    # Save as ICO
    images[0].save(output_path, format='ICO', sizes=[(img.width, img.height) for img in images])

def generate_icons(source_path):
    """Main function to generate all PWA icons and splash screens."""
    if not os.path.exists(source_path):
        print(f"Error: Source icon '{source_path}' not found.")
        return False
    
    # Setup directories
    icon_dir = "wwwroot/images/icons"
    splash_dir = "wwwroot/images/splash"
    create_directories(icon_dir, splash_dir)
    
    # Load source image
    try:
        source_image = Image.open(source_path)
        print(f"Generating PWA icons from {source_path}...")
        
        # Ensure source image is in RGBA mode for transparency support
        if source_image.mode != 'RGBA':
            source_image = source_image.convert('RGBA')
            
    except Exception as e:
        print(f"Error loading source image: {e}")
        return False
    
    # Generate standard PWA icons
    icon_sizes = [
        (16, "favicon-16x16.png"),
        (32, "favicon-32x32.png"),
        (72, "icon-72x72.png"),
        (96, "icon-96x96.png"),
        (128, "icon-128x128.png"),
        (144, "icon-144x144.png"),
        (152, "icon-152x152.png"),
        (192, "icon-192x192.png"),
        (384, "icon-384x384.png"),
        (512, "icon-512x512.png")
    ]
    
    for size, filename in icon_sizes:
        resize_and_save(source_image, size, os.path.join(icon_dir, filename))
    
    # Generate Apple Touch Icons
    apple_icons = [
        (152, "apple-touch-icon-152x152.png"),
        (167, "apple-touch-icon-167x167.png"),
        (180, "apple-touch-icon-180x180.png")
    ]
    
    for size, filename in apple_icons:
        resize_and_save(source_image, size, os.path.join(icon_dir, filename))
    
    # Copy 180x180 as default apple-touch-icon
    source_180 = os.path.join(icon_dir, "apple-touch-icon-180x180.png")
    target_default = os.path.join(icon_dir, "apple-touch-icon.png")
    if os.path.exists(source_180):
        import shutil
        shutil.copy2(source_180, target_default)
    
    # Generate Microsoft Tile Icons
    ms_icons = [
        (70, "ms-icon-70x70.png"),
        (144, "ms-icon-144x144.png"),
        (150, "ms-icon-150x150.png"),
        (310, "ms-icon-310x310.png")
    ]
    
    for size, filename in ms_icons:
        resize_and_save(source_image, size, os.path.join(icon_dir, filename))
    
    # Generate additional icons for shortcuts
    resize_and_save(source_image, 96, os.path.join(icon_dir, "upload-96x96.png"))
    resize_and_save(source_image, 96, os.path.join(icon_dir, "images-96x96.png"))
    
    # Generate social media icons
    create_social_media_image(source_image, 1200, 630, os.path.join(icon_dir, "og-image.png"))
    create_social_media_image(source_image, 1200, 600, os.path.join(icon_dir, "twitter-image.png"))
    
    # Generate favicon.ico
    create_favicon_ico(source_image, "wwwroot/favicon.ico")
    
    print("Generating iOS splash screens...")
    
    # iOS Splash Screens (portrait only)
    splash_configs = [
        # (width, height, icon_size, filename)
        (640, 1136, 200, "apple-splash-640-1136.jpg"),      # iPhone SE, 5s
        (750, 1334, 200, "apple-splash-750-1334.jpg"),      # iPhone 6s, 7, 8
        (1242, 2208, 300, "apple-splash-1242-2208.jpg"),    # iPhone 6s Plus, 7 Plus, 8 Plus
        (1125, 2436, 300, "apple-splash-1125-2436.jpg"),    # iPhone X, XS, 11 Pro
        (828, 1792, 250, "apple-splash-828-1792.jpg"),      # iPhone XR, 11
        (1242, 2688, 350, "apple-splash-1242-2688.jpg"),    # iPhone XS Max, 11 Pro Max
        (1170, 2532, 300, "apple-splash-1170-2532.jpg"),    # iPhone 12, 12 Pro, 13, 13 Pro
        (1080, 1920, 300, "apple-splash-1080-1920.jpg"),    # Generic Android
        (1536, 2048, 400, "apple-splash-1536-2048.jpg"),    # iPad
        (1668, 2388, 400, "apple-splash-1668-2388.jpg"),    # iPad Pro 10.5"
        (2048, 2732, 500, "apple-splash-2048-2732.jpg"),    # iPad Pro 12.9"
    ]
    
    for width, height, icon_size, filename in splash_configs:
        create_splash_screen(source_image, width, height, icon_size, 
                           os.path.join(splash_dir, filename))
    
    print("Icon generation complete!")
    print("")
    print(f"Generated icons in: {icon_dir}")
    print(f"Generated splash screens in: {splash_dir}")
    print("")
    print("To test your PWA:")
    print("1. Run the application: dotnet run")
    print("2. Open Chrome/Edge and navigate to your site")
    print("3. Open DevTools > Application > Manifest")
    print("4. Check 'Add to Home Screen' functionality")
    print("")
    print("For icon validation, use: https://realfavicongenerator.net/favicon_checker")
    
    return True

def main():
    parser = argparse.ArgumentParser(
        description="Generate PWA icons and splash screens from a source image",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_icons.py icon.png
  python generate_icons.py path/to/source-icon.png

Requirements:
  - Source icon should be at least 512x512px for best results
  - Pillow library: pip install Pillow
        """
    )
    
    parser.add_argument('source_icon', 
                       help='Path to source icon file (PNG recommended, at least 512x512px)')
    
    if len(sys.argv) == 1:
        parser.print_help()
        return
    
    args = parser.parse_args()
    
    # Validate source image
    if not os.path.exists(args.source_icon):
        print(f"Error: Source icon '{args.source_icon}' not found.")
        print(f"Usage: {sys.argv[0]} <source-icon.png>")
        print("Source icon should be at least 512x512px")
        sys.exit(1)
    
    # Check if Pillow is installed
    try:
        from PIL import Image
    except ImportError:
        print("Error: Pillow library is required.")
        print("Install it with: pip install Pillow")
        sys.exit(1)
    
    # Generate icons
    success = generate_icons(args.source_icon)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()