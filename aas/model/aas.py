class AssetAdministrationShell:
    """
    Administration Shell

    LANG

    @:param security: TODO-add the security model
    @:param derived_from: TODO-what does this actually do?
    @:param asset: instance of Asset
    @:param view: instance of class: view, containing a list of referable items
    """
    def __init__(self, security, asset, referables):
        self.security = security  # ToDO
        self.derived_from = AssetAdministrationShell  # Check does that really work this way?
        self.asset = asset  # type: isinstance(Asset)
        self.view = View(referables)


class Asset:
    """
    Asset of the Administration Shell

    @:param asset_identification_model: instance of a submodel
    """
    def __init__(self, submodel):
        self.asset_identification_model = submodel  # type: isinstance(Submodel)


class View:
    """


    """
    def __init__(self, referables):
        self.contained_elements = referables  # type: list[referable]