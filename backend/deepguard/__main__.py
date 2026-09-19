"""DeepGuard CLI.

Usage:
    python -m deepguard analyze image.jpg
    python -m deepguard match selfie.jpg id.jpg
    python -m deepguard liveness face.jpg
    python -m deepguard ocr document.jpg
    python -m deepguard serve --port 8765
"""

from __future__ import annotations

import sys
import json
import argparse


def cmd_analyze(args):
    from deepguard.core import analyze_image
    result = analyze_image(args.image)
    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print(f"Verdict: {result['verdict_label']}  (score {result['score']}/100)")
        for r in result.get("reasons", []):
            print(f"  - {r}")
        print("Signals:")
        for k, v in result.get("signals", {}).items():
            mark = "WARN" if v.get("score", 0) > 40 else "ok"
            print(f"  [{mark:>4}] {k}: {v.get('score')}/100")


def cmd_match(args):
    from deepguard.face import match_faces
    result = match_faces(args.selfie, args.id_photo, model=args.model)
    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        status = "MATCH" if result.get("match") else "NO MATCH"
        print(f"{status}  (distance: {result.get('distance', '?')}, model: {result.get('model', '?')})")


def cmd_liveness(args):
    from deepguard.liveness import detect_liveness
    result = detect_liveness(args.image)
    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        status = "LIVE" if result.get("is_live") else "SPOOF"
        print(f"{status}  (score: {result.get('score', '?')})")
        for check, detail in result.get("checks", {}).items():
            print(f"  {check}: {detail}")


def cmd_ocr(args):
    from deepguard.ocr import extract_text
    result = extract_text(args.image)
    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print(f"Extracted text:\n{result.get('raw_text', '')}")
        if result.get("mrz"):
            print(f"\nMRZ: {json.dumps(result['mrz'], indent=2)}")


def cmd_serve(args):
    import uvicorn
    from deepguard.api import app
    uvicorn.run(app, host="0.0.0.0", port=args.port, reload=args.reload)


def main():
    parser = argparse.ArgumentParser(prog="deepguard", description="DeepGuard KYC CLI")
    sub = parser.add_subparsers(dest="command")

    p_analyze = sub.add_parser("analyze", help="Forensic image analysis")
    p_analyze.add_argument("image", help="Path to image")
    p_analyze.add_argument("--json", action="store_true")
    p_analyze.set_defaults(func=cmd_analyze)

    p_match = sub.add_parser("match", help="Face matching")
    p_match.add_argument("selfie", help="Path to selfie")
    p_match.add_argument("id_photo", help="Path to ID photo")
    p_match.add_argument("--model", help="Face model")
    p_match.add_argument("--json", action="store_true")
    p_match.set_defaults(func=cmd_match)

    p_liveness = sub.add_parser("liveness", help="Liveness detection")
    p_liveness.add_argument("image", help="Path to face image")
    p_liveness.add_argument("--json", action="store_true")
    p_liveness.set_defaults(func=cmd_liveness)

    p_ocr = sub.add_parser("ocr", help="OCR text extraction")
    p_ocr.add_argument("image", help="Path to document")
    p_ocr.add_argument("--json", action="store_true")
    p_ocr.set_defaults(func=cmd_ocr)

    p_serve = sub.add_parser("serve", help="Start API server")
    p_serve.add_argument("--port", type=int, default=8765)
    p_serve.add_argument("--reload", action="store_true")
    p_serve.set_defaults(func=cmd_serve)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()
