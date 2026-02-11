import click
from commands.gitops import gitops
from commands.source import source
from commands.project import project
from commands.promote import promote
from commands.k8s import k8s

@click.group()
def cli():
    """Luban Provisioner Tooling"""
    pass

cli.add_command(gitops)
cli.add_command(source)
cli.add_command(project)
cli.add_command(promote)
cli.add_command(k8s)

if __name__ == '__main__':
    cli()
