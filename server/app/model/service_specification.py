from enum import Enum
from typing import List


class ServiceSpecificationProfileEnum(str, Enum):
    AAS_REGISTRY_FULL = "https://admin-shell.io/aas/API/3/1/AssetAdministrationShellRegistryServiceSpecification/SSP-001"  # noqa: E501
    AAS_REGISTRY_READ = "https://admin-shell.io/aas/API/3/1/AssetAdministrationShellRegistryServiceSpecification/SSP-002"  # noqa: E501
    SUBMODEL_REGISTRY_FULL = "https://admin-shell.io/aas/API/3/1/SubmodelRegistryServiceSpecification/SSP-001"
    SUBMODEL_REGISTRY_READ = "https://admin-shell.io/aas/API/3/1/SubmodelRegistryServiceSpecification/SSP-002"
    # TODO add other profiles


class ServiceDescription:
    def __init__(self, profiles: List[ServiceSpecificationProfileEnum]):
        if not profiles:
            raise ValueError("At least one profile must be specified")
        self.profiles = profiles

    def to_dict(self):
        return {"profiles": [p.value for p in self.profiles]}
