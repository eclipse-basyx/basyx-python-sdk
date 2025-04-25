from typing import List
from enum import Enum

class ServiceSpecificationProfileEnum(str, Enum):
    AAS_REGISTRY_FULL = "https://adminshell.io/aas/API/3/0/AssetAdministrationShellRegistryServiceSpecification/SSP-001"
    AAS_REGISTRY_READ = "https://adminshell.io/aas/API/3/0/AssetAdministrationShellRegistryServiceSpecification/SSP-002"
    SUBMODEL_REGISTRY_FULL = "https://adminshell.io/aas/API/3/0/SubmodelRegistryServiceSpecification/SSP-001"
    SUBMODEL_REGISTRY_READ = "https://adminshell.io/aas/API/3/0/SubmodelRegistryServiceSpecification/SSP-002"
    #TODO add other profiles


class ServiceDescription:
    def __init__(self, profiles: List[ServiceSpecificationProfileEnum]):
        if not profiles:
            raise ValueError("At least one profile must be specified")
        self.profiles = profiles

    def to_dict(self):
        return {
            "profiles": [p.value for p in self.profiles]
        }