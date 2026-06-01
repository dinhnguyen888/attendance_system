import logging
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).with_name(".env"))

from app.grpc.server import create_grpc_server


def main():
    logging.basicConfig(
        level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    server = create_grpc_server()
    server.add_insecure_port(f"[::]:{os.getenv('GRPC_PORT', '50051')}")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    main()
