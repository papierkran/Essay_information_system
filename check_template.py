import zipfile, os, glob

base = r'C:\Users\WINNAS\Desktop\workfold\services\Essay_information_system'
files = glob.glob(os.path.join(base, '*.docx'))
print("Found:", files)
for f in files:
    z = zipfile.ZipFile(f)
    if 'docProps/app.xml' in z.namelist():
        print("app.xml:", z.read('docProps/app.xml').decode('utf-8'))
    if 'word/document.xml' in z.namelist():
        content = z.read('word/document.xml').decode('utf-8')
        print("document.xml length:", len(content))
        # Check for any title or filename hints
        import re
        titles = re.findall(r'w:t[^>]*>([^<]+)', content)
        print("Text content:", titles[:20])
    z.close()
