import click
from commands.gitops import gitops
from commands.source import source
from commands.project import project
from commands.promote import promote
from commands.k8s import k8s
from commands.config import config
from commands.dagster import dagster

@click.group()
def cli():
    """Luban Provisioner Tooling"""
    pass

cli.add_command(gitops)
cli.add_command(source)
cli.add_command(project)
cli.add_command(promote)
cli.add_command(k8s)
cli.add_command(config)
cli.add_command(dagster)

if __name__ == '__main__':
    cli()
