with open("data/raw/challenge_resources/reports/resource_catalog.md", "r", encoding="utf-8") as f:
    lines = [f.readline() for _ in range(60)]

for idx, l in enumerate(lines, 1):
    print(f"{idx:2d}: {l.strip()}")
