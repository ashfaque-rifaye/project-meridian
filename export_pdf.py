import os
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright
import fitz  # PyMuPDF

WORKSPACE = Path(r"D:\Projects\IBM Bob Hackathon 2.0\Project - X")
SLIDES_HTML = WORKSPACE / "slides.html"
OUTPUT_PDF = WORKSPACE / "Meridian_Executive_Pitch_Deck.pdf"
TEMP_DIR = WORKSPACE / ".meridian" / "pdf_slides"
TEMP_DIR.mkdir(parents=True, exist_ok=True)

def generate_pdf():
    print(f"Loading {SLIDES_HTML}...")
    file_url = SLIDES_HTML.as_uri()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # 16:9 ratio at high DPI (device_scale_factor=2 for razor sharp text/graphics)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=2
        )
        page = context.new_page()
        page.goto(file_url, wait_until="networkidle")
        time.sleep(1.0)

        # Inject CSS to make each slide fill the presentation screen cleanly without the floating HUD buttons
        # while keeping the elegant brand header, aurora glow, and slide layout
        page.evaluate("""() => {
            // Hide interactive controls not needed in a printed presentation
            const style = document.createElement('style');
            style.id = 'pdf-clean-style';
            style.innerHTML = `
                .hud-controls, .keyboard-hints, .deck-nav-buttons, #notesDrawer, #overviewModal {
                    display: none !important;
                }
                .slide-viewport {
                    padding: 20px 48px !important;
                }
                .slide-container {
                    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.12) !important;
                }
            `;
            document.head.appendChild(style);
        }""")

        total_slides = 6
        image_paths = []

        for i in range(total_slides):
            print(f"Capturing Slide {i+1} of {total_slides}...")
            # Trigger jumpToSlide in page
            page.evaluate(f"jumpToSlide({i})")
            time.sleep(0.7)  # allow transitions and aurora to settle

            img_path = TEMP_DIR / f"slide_{i+1:02d}.png"
            page.screenshot(path=str(img_path))
            image_paths.append(img_path)
            print(f"  -> Saved {img_path.name}")

        browser.close()

    print("\nAssembling into PDF with PyMuPDF...")
    doc = fitz.open()

    # 1920 x 1080 points landscape
    page_width = 1920
    page_height = 1080
    rect = fitz.Rect(0, 0, page_width, page_height)

    for img_path in image_paths:
        page = doc.new_page(width=page_width, height=page_height)
        page.insert_image(rect, filename=str(img_path))

    doc.save(str(OUTPUT_PDF), garbage=4, deflate=True)
    doc.close()

    pdf_size_mb = OUTPUT_PDF.stat().st_size / (1024 * 1024)
    print(f"\nSUCCESS! Generated PDF: {OUTPUT_PDF}")
    print(f"Total Pages: {total_slides}")
    print(f"File Size: {pdf_size_mb:.2f} MB")

if __name__ == "__main__":
    generate_pdf()
