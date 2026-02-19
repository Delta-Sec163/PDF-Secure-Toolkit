from PIL import Image
img = Image.open("R.png")
img.save("icono_pdf.ico", format="ICO", sizes=[(64, 64)])