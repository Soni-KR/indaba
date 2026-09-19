import argparse
import json


def main():
    parser = argparse.ArgumentParser(description="AEGIS defense and local evidence tools")
    sub = parser.add_subparsers(dest="command", required=True)
    serve = sub.add_parser("serve")
    serve.add_argument("--port", type=int, default=8080)
    evaluate = sub.add_parser("evaluate")
    evaluate.add_argument("--variants", nargs="+")
    evaluate.add_argument("--seeds", nargs="+", type=int, default=[0])
    evaluate.add_argument("--adaptive", action="store_true")
    evaluate.add_argument("--model-path")
    evaluate.add_argument("--model-url")
    evaluate.add_argument("--profile", choices=["stock", "schema"], default="stock")
    evaluate.add_argument("--scenarios", nargs="+")
    check = sub.add_parser("verify")
    check.add_argument("path")
    args = parser.parse_args()
    if args.command == "serve":
        import uvicorn

        uvicorn.run("aegis.app:app", host="127.0.0.1", port=args.port)
    elif args.command == "evaluate":
        from aegis.experiments import run

        run(args.variants, args.seeds, args.adaptive, args.model_path, args.model_url, args.profile, args.scenarios)
    else:
        from aegis.audit import verify

        print(json.dumps(verify(args.path), indent=2))


if __name__ == "__main__":
    main()
