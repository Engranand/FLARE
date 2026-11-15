import zipfile

path = "data/raw/challenge_resources/original/psi_117/PSI-117_metadata_NEWID-13_Effect of External T.zip"
with zipfile.ZipFile(path) as z:
    for name in z.namelist():
        print(f"=== {name} ===")
        content = z.read(name).decode("utf-8", errors="replace")
        for line in content.splitlines()[:25]:
            print(" ", line)
