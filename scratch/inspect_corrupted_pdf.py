import os

path = "data/raw/challenge_resources/original/other/PSI-39/PSI-39_Analyzed Data_FLEX-1248_Summary.pdf"
with open(path, "rb") as f:
    header = f.read(64)
    f.seek(0, 2)
    size = f.tell()

print(f"File size: {size} bytes")
print(f"First 64 bytes: {header}")
print(f"First 64 hex: {header.hex()}")
