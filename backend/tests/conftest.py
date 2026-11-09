"""Opt-in, private PostgreSQL cluster; never migrates DATABASE_URL or TEST_DATABASE_URL."""
import os
from pathlib import Path
import secrets
import shutil
import socket
import subprocess
from uuid import uuid4

import pytest


def pytest_addoption(parser):
    parser.addoption("--run-postgres", action="store_true", default=False,
                     help="Create a private temporary PostgreSQL cluster for integration tests")
    parser.addoption("--pg-bin", default=None, help="Directory containing initdb and pg_ctl")


@pytest.fixture(scope="session")
def postgres_engines(request, tmp_path_factory):
    if not request.config.getoption("--run-postgres"):
        pytest.skip("PostgreSQL integration is opt-in: --run-postgres --pg-bin <directory>")
    import psycopg
    from psycopg import sql
    from sqlalchemy import URL
    from app.core.config import Settings
    from app.db.engine import create_db_engine

    supplied = request.config.getoption("--pg-bin") or os.environ.get("POSTGRES_BIN")
    found = shutil.which("initdb")
    binaries = Path(supplied) if supplied else Path(found).parent if found else None
    suffix = ".exe" if os.name == "nt" else ""
    if binaries is None or not all((binaries / (x + suffix)).is_file()
                                   for x in ["initdb", "pg_ctl"]):
        pytest.fail("PostgreSQL binaries unavailable; provide --pg-bin (no integration was run)")

    directory = tmp_path_factory.mktemp("flare_pg_private")
    cluster = directory / "cluster"
    password_file = directory / "password"
    password = secrets.token_urlsafe(32)
    password_file.write_text(password, encoding="utf-8")
    if os.name != "nt":
        password_file.chmod(0o600)
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    admin = "flare_fixture_migrator"
    app_user = "flare_fixture_app"
    database = "flare_test_" + uuid4().hex
    process_options = {"text": True, "timeout": 60}
    if os.name == "nt":
        process_options["creationflags"] = subprocess.CREATE_NO_WINDOW

    def run_pg(binary, *args):
        # A background server can inherit PIPE handles on Windows and prevent EOF.
        # Use a file so pg_ctl completion never waits for the server to exit.
        with (directory / "commands.log").open("a", encoding="utf-8") as output:
            result = subprocess.run([str(binaries / (binary + suffix)), *args],
                                    stdout=output, stderr=subprocess.STDOUT, **process_options)
        if result.returncode:
            # Never echo commands, credentials, connection strings or driver output.
            pytest.fail(f"Private PostgreSQL {binary} failed (exit {result.returncode})")

    engines = []
    try:
        try:
            run_pg("initdb", "-D", str(cluster), "-U", admin, "--auth=scram-sha-256",
                   "--pwfile=" + str(password_file), "--encoding=UTF8", "--locale=C")
        finally:
            password_file.unlink(missing_ok=True)
        run_pg("pg_ctl", "-D", str(cluster), "-l", str(directory / "server.log"),
               "-o", f"-h 127.0.0.1 -p {port}", "-w", "start")
        # This connection is to the newly initialized cluster, never an existing server.
        with psycopg.connect(host="127.0.0.1", port=port, user=admin, password=password,
                             dbname="postgres", autocommit=True, connect_timeout=5) as connection:
            connection.execute(sql.SQL("CREATE DATABASE {} OWNER {}").format(
                sql.Identifier(database), sql.Identifier(admin)))
            connection.execute(sql.SQL("CREATE ROLE {} LOGIN PASSWORD {} NOSUPERUSER NOCREATEDB NOCREATEROLE").format(
                sql.Identifier(app_user), sql.Literal(password)))
        for user in [admin, app_user]:
            url = URL.create("postgresql+psycopg", username=user, password=password,
                             host="127.0.0.1", port=port, database=database)
            settings = Settings(_env_file=None, database_url=None,
                                test_database_url=url.render_as_string(hide_password=False),
                                db_pool_size=1, db_max_overflow=0)
            engines.append(create_db_engine(settings, test=True))
        yield tuple(engines)
    finally:
        for engine in engines:
            engine.dispose()
        # Stop only the owned cluster; never use a service name or kill arbitrary processes.
        if (cluster / "postmaster.pid").exists():
            run_pg("pg_ctl", "-D", str(cluster), "-m", "fast", "-w", "stop")

