from app.signals import analyze_image

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m app.cli <image>")
        sys.exit(1)
    res = analyze_image(sys.argv[1])
    print(f"Verdict: {res['verdict_label']}  (score {res['score']}/100)")
    for r in res["reasons"]:
        print(f"  - {r}")
    print("Signals:")
    for k, v in res["signals"].items():
        mark = "WARN" if v.get("score", 0) > 40 else "ok"
        print(f"  [{mark:>4}] {k}: {v.get('score')}/100")
