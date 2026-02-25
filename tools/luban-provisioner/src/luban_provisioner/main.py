import click
from luban_provisioner.commands.gitops import gitops
from luban_provisioner.commands.source import source
from luban_provisioner.commands.project import project
from luban_provisioner.commands.promote import promote
from luban_provisioner.commands.k8s import k8s
from luban_provisioner.commands.config import config
from luban_provisioner.commands.dagster import dagster

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
