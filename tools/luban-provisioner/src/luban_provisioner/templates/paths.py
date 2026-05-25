import os

import click


def resolve_template_path(template_path: str) -> str:
    if os.path.exists(template_path):
        return template_path

    templates_root = _find_templates_root()
    if "/templates/" in template_path:
        tail = template_path.split("/templates/", 1)[1].lstrip("/")
        local_template = os.path.join(templates_root, tail)
        if os.path.exists(local_template):
            return local_template

    template_dirname = os.path.basename(template_path)
    local_template = os.path.join(templates_root, template_dirname)
    if os.path.exists(local_template):
        return local_template

    click.echo(f"Error: Template not found at {template_path}", err=True)
    raise FileNotFoundError(template_path)


def _find_templates_root() -> str:
    cur = os.getcwd()
    for _ in range(8):
        tool_templates = os.path.join(cur, "templates")
        if os.path.isdir(tool_templates) and os.path.isdir(
            os.path.join(cur, "src", "luban_provisioner")
        ):
            return tool_templates

        repo_templates = os.path.join(cur, "tools", "luban-provisioner", "templates")
        if os.path.isdir(repo_templates):
            return repo_templates

        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent

    return os.path.join(os.getcwd(), "tools", "luban-provisioner", "templates")
