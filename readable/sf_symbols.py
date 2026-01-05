"""SF Symbols integration for macOS menu bar app."""

from AppKit import NSImage, NSImageSymbolConfiguration, NSBitmapImageRep, NSGraphicsContext
from pathlib import Path
import tempfile
import shutil
import atexit
from .logger import get_logger

logger = get_logger("readable.sf_symbols")


class SFSymbols:
    """Helper class for working with SF Symbols in rumps."""

    _temp_dir = Path(tempfile.gettempdir()) / "readable_icons"

    @classmethod
    def create_icon(cls, symbol_name: str, size: int = 16) -> str:
        """
        Create properly configured SF Symbol icon for menu bar.

        Args:
            symbol_name: SF Symbol name (e.g., "speaker.fill")
            size: Icon size in points (14-16 recommended for menu bar)

        Returns:
            Path to temporary icon file optimized for menu bar
        """
        try:
            # First create NSImage from SF Symbol
            image = NSImage.imageWithSystemSymbolName_accessibilityDescription_(
                symbol_name, None
            )

            if image is None:
                logger.warning(f"SF Symbol '{symbol_name}' not found")
                return None

            # Create symbol configuration for menu bar rendering
            # NSFontWeightUltraLight (1) matches delicate system menu bar icons
            # NSImageSymbolScaleMedium (2) is standard for menu bar
            weight = 1  # NSFontWeightUltraLight
            symbol_config = NSImageSymbolConfiguration.configurationWithPointSize_weight_scale_(
                float(size),  # Use actual size parameter (14-16 for menu bar)
                weight,       # NSFontWeightUltraLight - matches thin system icons
                2             # NSImageSymbolScaleMedium
            )

            # Apply configuration to the image
            image = image.imageWithSymbolConfiguration_(symbol_config)

            if image is None:
                logger.warning(f"Failed to apply configuration to SF Symbol '{symbol_name}'")
                return None

            # Set size explicitly for proper rendering
            image.setSize_((float(size), float(size)))

            # Create temporary directory for icons
            cls._temp_dir.mkdir(exist_ok=True)

            # Include weight in filename to avoid cache issues
            weight_names = {1: "ultralight", 2: "thin", 3: "light", 4: "regular", 5: "medium", 6: "semibold", 7: "bold"}
            weight_name = weight_names.get(weight, "regular")
            icon_path = cls._temp_dir / f"{symbol_name.replace('.', '_')}_{size}pt_{weight_name}.png"

            # Save as PNG if not already saved
            if not icon_path.exists():
                # Render at 2x for Retina displays (36x36 for 18pt, 32x32 for 16pt)
                retina_size = int(size * 2)

                # Create bitmap for Retina rendering
                bitmap = NSBitmapImageRep.alloc().initWithBitmapDataPlanes_pixelsWide_pixelsHigh_bitsPerSample_samplesPerPixel_hasAlpha_isPlanar_colorSpaceName_bytesPerRow_bitsPerPixel_(
                    None,           # Let system allocate data
                    retina_size,    # Width in pixels (2x for Retina)
                    retina_size,    # Height in pixels (2x for Retina)
                    8,              # Bits per sample
                    4,              # Samples per pixel (RGBA)
                    True,           # Has alpha channel
                    False,          # Not planar
                    "NSDeviceRGBColorSpace",
                    0,              # Bytes per row (0 = auto)
                    0               # Bits per pixel (0 = auto)
                )

                # Draw SF Symbol into bitmap context at Retina resolution
                NSGraphicsContext.saveGraphicsState()
                context = NSGraphicsContext.graphicsContextWithBitmapImageRep_(bitmap)
                NSGraphicsContext.setCurrentContext_(context)

                # Draw image scaled to Retina size
                image.drawInRect_fromRect_operation_fraction_(
                    ((0, 0), (retina_size, retina_size)),  # Destination rect
                    ((0, 0), (size, size)),                # Source rect
                    2,   # NSCompositingOperationCopy
                    1.0  # Full opacity
                )

                NSGraphicsContext.restoreGraphicsState()

                # Save as PNG
                png_data = bitmap.representationUsingType_properties_(
                    1,    # NSPNGFileType
                    None  # Default properties
                )
                png_data.writeToFile_atomically_(str(icon_path), True)

            return str(icon_path)

        except Exception as e:
            logger.error(f"Error creating SF Symbol icon: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return None

    @classmethod
    def cleanup(cls):
        """Clean up temporary icon files."""
        if cls._temp_dir.exists():
            try:
                shutil.rmtree(cls._temp_dir, ignore_errors=True)
            except Exception as e:
                logger.warning(f"Failed to clean up SF Symbol temp files: {e}")

    @staticmethod
    def get_symbol_image(symbol_name: str):
        """Get NSImage directly from SF Symbol name."""
        try:
            return NSImage.imageWithSystemSymbolName_accessibilityDescription_(
                symbol_name, None
            )
        except Exception as e:
            logger.error(f"Error getting SF Symbol: {e}")
            return None


# Common SF Symbols for the app
SYMBOLS = {
    # Main menu bar (speaker with sound waves - perfect for TTS!)
    "menu_bar": "speaker.wave.2",

    # Actions
    "read": "doc.text.fill",
    "play": "play.fill",
    "pause": "pause.fill",
    "skip": "forward.fill",

    # Settings
    "voice": "waveform.circle.fill",
    "speed": "gauge.with.dots.needle.bottom.50percent",

    # Status
    "idle": "moon.zzz.fill",
    "processing": "gearshape.fill",
    "playing": "play.circle.fill",
    "paused": "pause.circle.fill",
    "complete": "checkmark.circle.fill",
    "error": "xmark.circle.fill",

    # Utilities
    "stats": "chart.bar.fill",
    "clear": "trash.fill",
    "quit": "power",
}

# Register cleanup function to run on exit
atexit.register(SFSymbols.cleanup)
