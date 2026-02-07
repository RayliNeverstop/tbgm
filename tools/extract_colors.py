from collections import Counter
import sys

try:
    from PIL import Image
except ImportError:
    print("Pillow not installed. Please install it with 'pip install Pillow'")
    sys.exit(1)

def get_dominant_colors(image_path, num_colors=5):
    try:
        image = Image.open(image_path)
        image = image.convert('RGB')
        image = image.resize((100, 100))
        pixels = list(image.getdata())
        
        # Filter for Gold-ish colors (Red > Blue, Green > Blue)
        # Gold is roughly R=High, G=Med-High, B=Low.
        filtered_pixels = []
        for r, g, b in pixels:
            # Skip dark/white
            if (r+g+b)/3 > 240 or (r+g+b)/3 < 40:
                continue
            
            # Gold heuristic: R > B and G > B (Yellowish)
            # Also R usually > G for gold/orange, or R ~= G for Yellow.
            if r > b + 30 and g > b + 30:
                filtered_pixels.append((r, g, b))
            
        if not filtered_pixels:
            print("No gold-like colors found.")
            return []
            
        counts = Counter(filtered_pixels)
        return counts.most_common(num_colors)
    except Exception as e:
        print(f"Error: {e}")
        return []

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_colors.py <image_path>")
        sys.exit(1)
        
    colors = get_dominant_colors(sys.argv[1], num_colors=10)
    print("Dominant Brand Colors (RGB):")
    for color, count in colors:
        print(f"RGB{color} - Hex: #{color[0]:02x}{color[1]:02x}{color[2]:02x} (Count: {count})")
