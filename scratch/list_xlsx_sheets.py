import zipfile

path = "data/raw/challenge_resources/original/saffire/PSI-100/PSI-100_Raw Data_Saffire III Sample 1 Sensors.xlsx"
with zipfile.ZipFile(path) as z:
    for n in z.namelist():
        if "sheet" in n:
            print(n)
