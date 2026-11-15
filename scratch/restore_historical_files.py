import subprocess

files = [
    "backend/migrations/versions/0003_m43_sealing.py",
    "backend/migrations/versions/m43_sealing.sql"
]

for p in files:
    head_content = subprocess.check_output(["git", "show", f"HEAD:{p}"], text=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(head_content)
    print(f"Restored {p} to exact Git HEAD content.")

# Verify git diff on these two files is now completely clean
diff = subprocess.check_output(["git", "diff", "HEAD", "--", *files], text=True)
print("Git diff output (should be empty):", repr(diff))
assert diff == "", "Expected clean diff after restoration!"
print("Historical migration files successfully restored to pristine state!")
