import json
import re
from collections.abc import Mapping, Sequence
from typing import Any, cast

from dagster import Array, Field, Map, StringSource, _check as check
from dagster._cli.api import ExecuteRunArgs
from dagster._config import Permissive, Shape
from dagster._core.launcher import LaunchRunContext, ResumeRunContext
from dagster._core.storage.dagster_run import DagsterRun
from dagster._grpc.types import ResumeRunArgs
from dagster._serdes import ConfigurableClassData
from dagster_k8s.job import USER_DEFINED_K8S_CONFIG_KEY, DagsterK8sJobConfig, get_job_name_from_run_id
from dagster_k8s.launcher import K8sRunLauncher


class CodeLocationAwareK8sRunLauncher(K8sRunLauncher):
    def __init__(
        self,
        code_location_env: Mapping[str, Any] | None = None,
        inst_data: ConfigurableClassData | None = None,
        **kwargs: Any,
    ):
        self._code_location_env: Mapping[str, Any] = code_location_env or {}
        _validate_code_location_env(self._code_location_env)
        super().__init__(inst_data=inst_data, **kwargs)

    @classmethod
    def config_type(cls):
        base_config_type = DagsterK8sJobConfig.config_type_run_launcher()
        base_fields: Mapping[str, Field] | None = getattr(base_config_type, "fields", None)
        if not base_fields:
            return Permissive()

        code_location_env_schema = Field(
            Map(
                StringSource,
                Shape(
                    {
                        "env_config_maps": Field(Array(StringSource), is_required=False),
                        "env_secrets": Field(Array(StringSource), is_required=False),
                        "env_vars": Field(Array(StringSource), is_required=False),
                        "k8s_config": Field(Permissive(), is_required=False),
                    }
                ),
            ),
            is_required=False,
        )

        return Shape({**base_fields, "code_location_env": code_location_env_schema})

    @classmethod
    def from_config_value(cls, inst_data, config_value):
        return cls(inst_data=inst_data, **config_value)

    def _get_code_location_for_run(self, run: DagsterRun) -> str:
        code_location = run.tags.get("dagster/code_location")
        if code_location:
            return code_location
        if run.remote_job_origin:
            return run.remote_job_origin.repository_origin.code_location_origin.location_name
        return ""

    def _default_config_for_location(self, code_location: str) -> Mapping[str, Any] | None:
        return {
            "env_config_maps": [f"{code_location}-config"],
            "env_secrets": [f"{code_location}-secret"],
        }

    def _required_k8s_config_for_run(self, run: DagsterRun) -> Mapping[str, Any] | None:
        code_location = self._get_code_location_for_run(run)
        if not code_location:
            return None

        default = self._default_config_for_location(code_location) or {}
        explicit = cast(Mapping[str, Any], self._code_location_env.get(code_location) or {})

        env_from: list[Mapping[str, Any]] = []

        for cm in cast(Sequence[str], default.get("env_config_maps") or []):
            env_from.append({"configMapRef": {"name": cm}})

        for cm in cast(Sequence[str], explicit.get("env_config_maps") or []):
            env_from.append({"configMapRef": {"name": cm}})

        for secret in cast(Sequence[str], default.get("env_secrets") or []):
            env_from.append({"secretRef": {"name": secret}})

        for secret in cast(Sequence[str], explicit.get("env_secrets") or []):
            env_from.append({"secretRef": {"name": secret}})

        env_vars = cast(Sequence[str], default.get("env_vars") or []) + cast(
            Sequence[str], explicit.get("env_vars") or []
        )

        container_config: dict[str, Any] = {}
        if env_from:
            container_config["envFrom"] = env_from
        if env_vars:
            container_config["env"] = [_parse_env_var(e) for e in env_vars]

        k8s_config = cast(Mapping[str, Any] | None, explicit.get("k8s_config"))
        if k8s_config:
            merged = {**k8s_config}
            if container_config:
                existing = cast(Mapping[str, Any], merged.get("container_config") or {})
                merged["container_config"] = {**existing, **container_config}
            return merged

        if not container_config:
            return None

        return {"container_config": container_config}

    def _ensure_platform_k8s_config_tag(self, run: DagsterRun) -> DagsterRun:
        required_config = self._required_k8s_config_for_run(run)
        if not required_config:
            return run

        existing_raw = run.tags.get(USER_DEFINED_K8S_CONFIG_KEY)
        existing = {} if not existing_raw else cast(dict[str, Any], json.loads(existing_raw))

        merged = _merge_user_defined_k8s_config(existing, required_config)
        merged_raw = json.dumps(merged, sort_keys=True, separators=(",", ":"))

        if merged_raw == existing_raw:
            return run

        self._instance.add_run_tags(run.run_id, {USER_DEFINED_K8S_CONFIG_KEY: merged_raw})
        return run.with_tags({**run.tags, USER_DEFINED_K8S_CONFIG_KEY: merged_raw})

    def launch_run(self, context: LaunchRunContext) -> None:
        run = self._ensure_platform_k8s_config_tag(context.dagster_run)
        job_name = get_job_name_from_run_id(run.run_id)
        job_origin = check.not_none(run.job_code_origin)
        args = ExecuteRunArgs(
            job_origin=job_origin,
            run_id=run.run_id,
            instance_ref=self._instance.get_ref(),
            set_exit_code_on_failure=self.fail_pod_on_run_failure,
        ).get_command_args()
        self._launch_k8s_job_with_args(job_name, args, run)

    def resume_run(self, context: ResumeRunContext) -> None:
        run = self._ensure_platform_k8s_config_tag(context.dagster_run)
        job_name = get_job_name_from_run_id(
            run.run_id, resume_attempt_number=context.resume_attempt_number
        )
        job_origin = check.not_none(run.job_code_origin)
        args = ResumeRunArgs(
            job_origin=job_origin,
            run_id=run.run_id,
            instance_ref=self._instance.get_ref(),
            set_exit_code_on_failure=self.fail_pod_on_run_failure,
        ).get_command_args()
        self._launch_k8s_job_with_args(job_name, args, run)


def _parse_env_var(env_var: str) -> Mapping[str, str]:
    env_var = env_var.strip()
    if not env_var:
        raise ValueError("Invalid env var entry: empty string")

    name, _, value = env_var.partition("=")
    name = name.strip()
    if not name:
        raise ValueError(f"Invalid env var entry: {env_var!r}. Name cannot be empty.")
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
        raise ValueError(
            f"Invalid env var entry: {env_var!r}. Name must match [A-Za-z_][A-Za-z0-9_]*."
        )
    return {"name": name, "value": value}


def _validate_code_location_env(code_location_env: Mapping[str, Any]) -> None:
    for code_location, spec in code_location_env.items():
        if not isinstance(spec, Mapping):
            raise ValueError(
                f"Invalid code_location_env entry for {code_location!r}: expected mapping, got {type(spec).__name__}"
            )

        env_vars = spec.get("env_vars") or []
        if not isinstance(env_vars, Sequence) or isinstance(env_vars, (str, bytes)):
            raise ValueError(
                f"Invalid code_location_env.env_vars for {code_location!r}: expected list of strings"
            )

        for env_var in env_vars:
            if not isinstance(env_var, str):
                raise ValueError(
                    f"Invalid code_location_env.env_vars for {code_location!r}: expected string entries"
                )
            try:
                _parse_env_var(env_var)
            except ValueError as e:
                raise ValueError(
                    f"Invalid code_location_env.env_vars entry for {code_location!r}: {env_var!r}. {e}"
                ) from e


def _env_from_key(item: Mapping[str, Any]) -> tuple[str, str] | None:
    cm_ref = item.get("configMapRef") or item.get("config_map_ref")
    if isinstance(cm_ref, Mapping):
        name = cm_ref.get("name")
        if isinstance(name, str) and name:
            return ("configMapRef", name)

    secret_ref = item.get("secretRef") or item.get("secret_ref")
    if isinstance(secret_ref, Mapping):
        name = secret_ref.get("name")
        if isinstance(name, str) and name:
            return ("secretRef", name)

    return None


def _merge_env_from(
    platform: Sequence[Mapping[str, Any]], user: Sequence[Mapping[str, Any]]
) -> list[Mapping[str, Any]]:
    seen: set[tuple[str, str]] = set()
    merged: list[Mapping[str, Any]] = []

    def add(items: Sequence[Mapping[str, Any]]) -> None:
        for item in items:
            key = _env_from_key(item)
            if key and key in seen:
                continue
            if key:
                seen.add(key)
            merged.append(item)

    def sort_key(item: Mapping[str, Any]) -> str:
        key = _env_from_key(item)
        if not key:
            return ""
        return f"{key[0]}:{key[1]}"

    add(sorted(platform, key=sort_key))
    add(user)
    return merged


def _merge_env_vars(
    platform: Sequence[Mapping[str, str]], user: Sequence[Mapping[str, str]]
) -> list[Mapping[str, str]]:
    seen: set[str] = set()
    merged: list[Mapping[str, str]] = []

    for item in platform:
        name = item.get("name", "")
        if name and name not in seen:
            seen.add(name)
            merged.append(item)

    for item in user:
        name = item.get("name", "")
        if name and name not in seen:
            seen.add(name)
            merged.append(item)

    return merged


def _deep_merge_dicts(base: dict[str, Any], overlay: Mapping[str, Any]) -> dict[str, Any]:
    result = {**base}
    for k, v in overlay.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, Mapping):
            result[k] = _deep_merge_dicts(cast(dict[str, Any], result[k]), v)
        else:
            result[k] = v
    return result


def _merge_user_defined_k8s_config(
    existing: Mapping[str, Any], required: Mapping[str, Any]
) -> dict[str, Any]:
    merged: dict[str, Any] = {**existing}

    existing_container = cast(dict[str, Any], merged.get("container_config") or {})
    required_container = cast(Mapping[str, Any], required.get("container_config") or {})

    existing_env_from_raw = cast(
        Sequence[Mapping[str, Any]],
        existing_container.get("envFrom") or existing_container.get("env_from") or [],
    )
    required_env_from_raw = cast(
        Sequence[Mapping[str, Any]],
        required_container.get("envFrom") or required_container.get("env_from") or [],
    )

    existing_env_raw = cast(
        Sequence[Mapping[str, str]],
        existing_container.get("env") or [],
    )
    required_env_raw = cast(
        Sequence[Mapping[str, str]],
        required_container.get("env") or [],
    )

    merged_container: dict[str, Any] = {**existing_container}

    if required_env_from_raw:
        merged_container.pop("env_from", None)
        merged_container["envFrom"] = _merge_env_from(required_env_from_raw, existing_env_from_raw)

    if required_env_raw:
        merged_container["env"] = _merge_env_vars(required_env_raw, existing_env_raw)

    merged["container_config"] = merged_container

    for k, v in required.items():
        if k == "container_config":
            continue
        if k in merged and isinstance(merged[k], dict) and isinstance(v, Mapping):
            merged[k] = _deep_merge_dicts(cast(dict[str, Any], merged[k]), v)
        elif k not in merged:
            merged[k] = v

    return merged
