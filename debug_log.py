import zipfile

with open("my_log.txt", "w") as f:
    try:
        f.write("Opening zip...\n")
        with zipfile.ZipFile("template.hwpx", "r") as z:
            f.write(f"Zip files: {z.namelist()}\n")
            for name in ['Contents/section0.xml', 'Contents/header.xml']:
                f.write(f"Reading {name}...\n")
                if name in z.namelist():
                    content = z.read(name).decode("utf-8")
                    f.write(content[:2000] + "\n")
                else:
                    f.write(f"{name} not found.\n")
        f.write("Done.\n")
    except Exception as e:
        f.write(f"Error: {e}\n")
