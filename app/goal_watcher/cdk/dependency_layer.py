"""Lambda dependency layer construct built from uv.lock."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

import jsii
from aws_cdk import BundlingOptions, FileSystem, ILocalBundling, aws_lambda as lambda_
from constructs import Construct


class DependencyLayer(lambda_.LayerVersion):
    """Lambda layer that bundles Python runtime dependencies from uv.lock.

    Uses ``uv export`` to generate a requirements.txt from the lock file, then
    installs them via pip inside the Lambda bundling Docker image. Local bundling
    only generates the requirements file; Docker handles the actual pip install so
    packages are compiled for the correct Lambda runtime/architecture.
    """

    BUILD_DIR = (Path(__file__).parents[3] / "build").resolve()
    LOCK_FILE = (Path(__file__).parents[3] / "uv.lock").resolve()

    def __init__(
        self,
        scope: Construct,
        id: str,  # noqa: A002
        runtime: lambda_.Runtime,
        architecture: lambda_.Architecture,
        dependency_group: str | None = None,
        **kwargs: Any,
    ) -> None:
        lambda_bundling_runtime = lambda_.Runtime(
            f"{runtime.name}:latest-{architecture.name}",
            runtime.family,
        )

        self.BUILD_DIR.mkdir(exist_ok=True)
        if not (self.BUILD_DIR / ".gitignore").exists():
            with (self.BUILD_DIR / ".gitignore").open("w") as f:
                f.write("*\n")

        super().__init__(
            scope,
            id,
            code=lambda_.Code.from_asset(
                str(self.BUILD_DIR),
                asset_hash=FileSystem.fingerprint(
                    str(self.LOCK_FILE),
                ),
                bundling=BundlingOptions(
                    image=lambda_bundling_runtime.bundling_image,
                    local=self.Bundler(dependency_group),
                    command=[
                        "pip3",
                        "install",
                        "-r",
                        str(self.requirements_file(dependency_group).name),
                        "-t",
                        "/asset-output/python",
                    ],
                ),
            ),
            compatible_runtimes=[runtime],
            compatible_architectures=[architecture],
            **kwargs,
        )

    @classmethod
    def requirements_file(cls, dependency_group: str | None = None) -> Path:
        """Return the path to the generated requirements file."""
        return (
            cls.BUILD_DIR / f"requirements_{dependency_group}.txt"
            if dependency_group
            else cls.BUILD_DIR / "requirements.txt"
        )

    @jsii.implements(ILocalBundling)
    class Bundler:
        """Local bundler that generates requirements.txt via uv export."""

        def __init__(self, dependency_group: str | None = None):
            self.dependency_group = dependency_group

        def try_bundle(self, *_args: Any, **_kwargs: Any) -> bool:
            uv_path = shutil.which("uv")
            if not uv_path:
                raise RuntimeError(
                    "uv command not found. Ensure uv is installed and in PATH.",
                )

            cmd = [
                uv_path,
                "export",
                "--format",
                "requirements.txt",
                "--no-dev",
                "--output-file",
                str(DependencyLayer.requirements_file(self.dependency_group)),
                "--frozen",
                "--quiet",
            ] + (["--group", self.dependency_group] if self.dependency_group else [])

            subprocess.run(cmd, check=True)  # noqa: S603
            return False  # local step only generates requirements file; Docker does the pip install
