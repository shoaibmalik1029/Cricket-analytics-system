from pathlib import Path
import shutil


def main():
    cache_dir = Path(".cricket_cache")
    if cache_dir.exists():
        shutil.rmtree(cache_dir)
        print(f"Removed stale cache: {cache_dir.resolve()}")
    else:
        print("No cache directory found.")
    print("Next FastAPI startup will rebuild analytics from the full Statsguru archive.")


if __name__ == "__main__":
    main()
