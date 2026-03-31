import zipfile
import os

os.makedirs('unzipped_template', exist_ok=True)
with zipfile.ZipFile('template.hwpx', 'r') as z:
    z.extractall('unzipped_template')

os.makedirs('unzipped_test', exist_ok=True)
with zipfile.ZipFile('test_output.hwpx', 'r') as z:
    z.extractall('unzipped_test')
