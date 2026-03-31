import zipfile
try:
    with zipfile.ZipFile('template.hwpx', 'r') as z:
        for name in ['Contents/section0.xml', 'Contents/header.xml']:
            with open(name.replace("/", "_") + ".txt", "w", encoding="utf-8") as f:
                f.write(z.read(name).decode('utf-8'))
    print("Extracted successfully.")
except Exception as e:
    print(e)
