import sys
import zipfile
import traceback

with open("full_log.txt", "w", encoding="utf-8") as f:
    f.write("Starting script...\n")
    try:
        with zipfile.ZipFile('template.hwpx', 'r') as z:
            f.write("Files in template.hwpx:\n")
            for item in z.infolist():
                f.write(f"- {item.filename}\n")
            
            f.write("\n==== Contents/section0.xml ====\n")
            f.write(z.read('Contents/section0.xml').decode('utf-8')[:2000])
    except Exception as e:
        f.write("ERROR:\n")
        f.write(traceback.format_exc())
