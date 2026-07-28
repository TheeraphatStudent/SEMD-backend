"""Entrypoint: builds the FastAPI app via the application factory and exposes
the dev/prod CLI. See application.py for app construction."""

import argparse

from application import create_application

app = create_application()


def main():
    """CLI entry point for running the FastAPI application."""
    parser = argparse.ArgumentParser(description='FastAPI Application CLI')
    parser.add_argument(
        'command',
        choices=['dev', 'prod'],
        help='Command to run: dev (development with auto-reload) or prod (production with uvicorn)'
    )
    parser.add_argument(
        '--host',
        default='0.0.0.0',
        help='Host to bind (default: 0.0.0.0)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=8000,
        help='Port to bind (default: 8000)'
    )

    args = parser.parse_args()

    if args.command == 'dev':
        import uvicorn
        print(f"🚀 Starting FastAPI in DEVELOPMENT mode on {args.host}:{args.port}")
        print("📝 Auto-reload enabled - watching for file changes")
        uvicorn.run(
            "main:app",
            host=args.host,
            port=args.port,
            reload=True,
            log_level="info"
        )
    elif args.command == 'prod':
        import uvicorn
        print(f"🚀 Starting FastAPI in PRODUCTION mode on {args.host}:{args.port}")
        uvicorn.run(
            "main:app",
            host=args.host,
            port=args.port,
            reload=False,
            workers=4,
            log_level="warning"
        )


if __name__ == "__main__":
    main()
