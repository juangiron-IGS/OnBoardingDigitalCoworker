import importlib

import pytest

PACKAGES = [
    "contracts",
    "services.case_service.domain",
    "services.case_service.application",
    "services.case_service.ports",
    "services.case_service.adapters",
    "web.api",
    "agents.common",
    "mcp_servers.common",
]


@pytest.mark.parametrize("name", PACKAGES)
def test_package_imports(name: str) -> None:
    assert importlib.import_module(name) is not None
