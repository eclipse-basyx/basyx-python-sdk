from typing import List
import enum


class ServiceSpecificationProfileEnum(str, enum.Enum):
    """
    Enumeration of all standardized Service Specification Profiles
    from the AAS Part 2 API Specification (IDTA-01002-3-1).
    Each profile is uniquely identified by its semantic URI.
    """

    # --- Asset Administration Shell (AAS) ---
    AAS_FULL = "https://admin-shell.io/aas/API/3/1/AssetAdministrationShellServiceSpecification/SSP-001"
    AAS_READ = "https://admin-shell.io/aas/API/3/1/AssetAdministrationShellServiceSpecification/SSP-002"

    # --- Submodel ---
    SUBMODEL_FULL = "https://admin-shell.io/aas/API/3/1/SubmodelServiceSpecification/SSP-001"
    SUBMODEL_VALUE = "https://admin-shell.io/aas/API/3/1/SubmodelServiceSpecification/SSP-002"
    SUBMODEL_READ = "https://admin-shell.io/aas/API/3/1/SubmodelServiceSpecification/SSP-003"

    # --- AASX File Server ---
    AASX_FILESERVER_FULL = "https://admin-shell.io/aas/API/3/1/AasxFileServerServiceSpecification/SSP-001"

    # --- AAS Registry ---
    AAS_REGISTRY_FULL = \
        "https://admin-shell.io/aas/API/3/1/AssetAdministrationShellRegistryServiceSpecification/SSP-001"
    AAS_REGISTRY_READ = \
        "https://admin-shell.io/aas/API/3/1/AssetAdministrationShellRegistryServiceSpecification/SSP-002"
    AAS_REGISTRY_BULK = \
        "https://admin-shell.io/aas/API/3/1/AssetAdministrationShellRegistryServiceSpecification/SSP-003"

    # --- Submodel Registry ---
    SUBMODEL_REGISTRY_FULL = "https://admin-shell.io/aas/API/3/1/SubmodelRegistryServiceSpecification/SSP-001"
    SUBMODEL_REGISTRY_READ = "https://admin-shell.io/aas/API/3/1/SubmodelRegistryServiceSpecification/SSP-002"
    SUBMODEL_REGISTRY_BULK = "https://admin-shell.io/aas/API/3/1/SubmodelRegistryServiceSpecification/SSP-003"

    # --- AAS Repository ---
    AAS_REPOSITORY_FULL = \
        "https://admin-shell.io/aas/API/3/1/AssetAdministrationShellRepositoryServiceSpecification/SSP-001"
    AAS_REPOSITORY_READ = \
        "https://admin-shell.io/aas/API/3/1/AssetAdministrationShellRepositoryServiceSpecification/SSP-002"
    AAS_REPOSITORY_BULK = \
        "https://admin-shell.io/aas/API/3/1/AssetAdministrationShellRepositoryServiceSpecification/SSP-003"

    # --- Submodel Repository ---
    SUBMODEL_REPOSITORY_FULL = "https://admin-shell.io/aas/API/3/1/SubmodelRepositoryServiceSpecification/SSP-001"
    SUBMODEL_REPOSITORY_READ = "https://admin-shell.io/aas/API/3/1/SubmodelRepositoryServiceSpecification/SSP-002"
    SUBMODEL_REPOSITORY_BULK = "https://admin-shell.io/aas/API/3/1/SubmodelRepositoryServiceSpecification/SSP-003"

    # --- Concept Description Repository ---
    CONCEPT_DESCRIPTION_REPOSITORY_FULL = \
        "https://admin-shell.io/aas/API/3/1/ConceptDescriptionRepositoryServiceSpecification/SSP-001"
    CONCEPT_DESCRIPTION_REPOSITORY_READ = \
        "https://admin-shell.io/aas/API/3/1/ConceptDescriptionRepositoryServiceSpecification/SSP-002"
    CONCEPT_DESCRIPTION_REPOSITORY_BULK = \
        "https://admin-shell.io/aas/API/3/1/ConceptDescriptionRepositoryServiceSpecification/SSP-003"

    # --- Discovery ---
    DISCOVERY_FULL = "https://admin-shell.io/aas/API/3/1/DiscoveryServiceSpecification/SSP-001"
    DISCOVERY_READ = "https://admin-shell.io/aas/API/3/1/DiscoveryServiceSpecification/SSP-002"


# TODO: Maybe remove this in spite of spec? Too complicated structure
class ServiceDescription:
    def __init__(self, profiles: List[ServiceSpecificationProfileEnum]):
        if not profiles:
            raise ValueError("At least one profile must be specified")
        self.profiles: List[ServiceSpecificationProfileEnum] = profiles

    def to_dict(self):
        return {"profiles": [p.value for p in self.profiles]}
