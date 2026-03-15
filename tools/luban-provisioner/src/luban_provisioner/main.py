import warnings
warnings.filterwarnings(
    "ignore",
    message=r"urllib3 .* doesn't match a supported version!",
    category=Warning,
)
import click
from luban_provisioner.commands.gitops import gitops
from luban_provisioner.commands.source import source
from luban_provisioner.commands.project import project
from luban_provisioner.commands.promote import promote
from luban_provisioner.commands.config import config
from luban_provisioner.commands.dagster import dagster
from luban_provisioner.commands.infra import infra

@click.group()
def cli():
    """Luban Provisioner Tooling"""
    pass

cli.add_command(gitops)
cli.add_command(source)
cli.add_command(project)
cli.add_command(promote)
cli.add_command(config)
cli.add_command(dagster)
cli.add_command(infra)

if __name__ == '__main__':
    cli()
