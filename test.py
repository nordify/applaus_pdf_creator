import os
import webbrowser
from tkinter import Tk, filedialog, simpledialog
from PIL import Image, ExifTags
from fpdf import FPDF

def ask_files():
    Tk().withdraw()  # Versteckt das Hauptfenster
    file_paths = filedialog.askopenfilenames(title='Wähle die Fotos aus', filetypes=[("JPEG files", "*.jpg")])
    print(f"Gewählte Fotos: {file_paths}")
    return file_paths

def ask_input(prompt):
    Tk().withdraw()  # Versteckt das Hauptfenster
    return simpledialog.askstring("Eingabe", prompt)

def ask_save_location(default_name):
    Tk().withdraw()  # Versteckt das Hauptfenster
    output_path = filedialog.asksaveasfilename(title="Wähle den Speicherort für das PDF", defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")], initialfile=default_name)
    print(f"Speicherort für PDF: {output_path}")
    return output_path

def resize_image(image_path, max_size_kb):
    img = Image.open(image_path)
    img.thumbnail((800, 800))  # Verkleinern der Bildgröße
    img.save(image_path, optimize=True, quality=75)  # Reduziert die Dateigröße
    print(f"Bild {image_path} verkleinert")

def get_photo_date(photo_path):
    img = Image.open(photo_path)
    try:
        exif = {ExifTags.TAGS[k]: v for k, v in img._getexif().items() if k in ExifTags.TAGS}
        return exif.get('DateTime', '9999:99:99 99:99:99')  # Falls kein Datum gefunden wird, ein hoher Wert zur Sortierung
    except AttributeError:
        return '9999:99:99 99:99:99'  # Falls kein Exif-Tag vorhanden ist

def rename_photos(file_paths, aktennummer, dokumentenkürzel, dokumentenzahl):
    renamed_photos = []
    for count, photo in enumerate(file_paths):
        folder_path = os.path.dirname(photo)
        dst = f"{aktennummer}-{dokumentenkürzel}-{dokumentenzahl} Foto Nr. {count + 1}.jpg"
        src = photo
        dst = os.path.join(folder_path, dst)
        os.rename(src, dst)
        renamed_photos.append(dst)
    print(f"{len(renamed_photos)} Fotos umbenannt: {renamed_photos}")
    return renamed_photos

def create_pdf(file_paths, output_path, max_size_mb):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_margins(25, 20, 20)  # Setze die Ränder (links, oben, rechts)
    image_width = 165
    image_height = 110  # Anpassen der Bildhöhe
    text_gap = 1
    between_photos_gap = 3  # Weiteres Verringern des Abstands zwischen den Fotos

    for photo in file_paths:
        resize_image(photo, max_size_mb * 1024)  # Resize each photo

    for i in range(0, len(file_paths), 2):
        pdf.add_page()
        # First photo
        pdf.image(file_paths[i], 25, 20, image_width, image_height)
        pdf.set_xy(25, 20 + image_height + text_gap)
        pdf.set_font('Arial', 'B', 16)
        photo_name = os.path.basename(file_paths[i]).rsplit('.', 1)
        pdf.cell(0, 10, f"{photo_name}", align='L')
        # Second photo, if available
        if i + 1 < len(file_paths):
            y_position = 20 + image_height + text_gap + 10 + between_photos_gap
            pdf.image(file_paths[i + 1], 25, y_position, image_width, image_height)
            pdf.set_xy(25, y_position + image_height + text_gap)
            pdf.set_font('Arial', 'B', 16)
            photo_name = os.path.basename(file_paths[i + 1]).rsplit('.', 1)
            pdf.cell(0, 10, f"{photo_name}", align='L')

    pdf.output(output_path)
    print("PDF erzeugt und gespeichert unter:", output_path)

    # Öffne die PDF-Datei nach dem Erstellen
    webbrowser.open_new(output_path)

file_paths = ask_files()
aktennummer = ask_input("Gib die Aktennummer ein:")
dokumentenkürzel = ask_input("Gib das Dokumentenkürzel ein (GA, ST, PR):")
dokumentenzahl = ask_input("Gib die Dokumentenzahl ein:")
default_name = f"{aktennummer}-{dokumentenkürzel}-{dokumentenzahl} Fotos.pdf"
output_path = ask_save_location(default_name)
max_size_mb = 20  # Maximalgröße der PDF-Datei in MB
renamed_photos = rename_photos(file_paths, aktennummer, dokumentenkürzel, dokumentenzahl)
create_pdf(renamed_photos, output_path, max_size_mb)