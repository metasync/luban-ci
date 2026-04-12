from .dbt import make_dbt_resource
from .starrocks import make_starrocks_resource

resources = {
    "dbt": make_dbt_resource(),
    "starrocks": make_starrocks_resource(),
}
