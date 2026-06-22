from __future__ import annotations

import asyncio
from datetime import date
from pathlib import Path
import click

from .settings import Settings
from .models import ReportType
from .pipeline import NetPayRobotPipeline
from .crypto import encrypt_secret


@click.group()
def cli():
    pass


@cli.command()
@click.option('--report-type', type=click.Choice([r.value for r in ReportType]), required=True)
@click.option('--date-from', type=click.DateTime(formats=['%Y-%m-%d']), required=True)
@click.option('--date-to', type=click.DateTime(formats=['%Y-%m-%d']), required=True)
def run(report_type: str, date_from, date_to):
    settings = Settings()
    pipeline = NetPayRobotPipeline(settings)
    asyncio.run(pipeline.run(ReportType(report_type), date_from.date(), date_to.date()))


@cli.command()
@click.option('--file', 'file_path', type=click.Path(exists=True, dir_okay=False), required=True)
def validate(file_path: str):
    settings = Settings()
    pipeline = NetPayRobotPipeline(settings)
    pipeline.validate_file(Path(file_path))


@cli.command('encrypt-password')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True)
def encrypt_password(password: str):
    settings = Settings()
    print(encrypt_secret(password, settings.server_secret_key))


if __name__ == '__main__':
    cli()
