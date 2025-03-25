# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime

from typing import List, Dict, Optional,Iterable, Set

from .base import AdministrativeInformation
from . import descriptor
from . import base
from .base import Reference
import re


class SubmodelDescriptor(descriptor.Descriptor):

    def __init__(self, id_: base.Identifier, endpoints: List[descriptor.Endpoint],
                 administration: Optional[base.AdministrativeInformation] = None,
                 id_short: Optional[base.NameType]=None, semantic_id: Optional[base.Reference]=None,
                 supplemental_semantic_id: Iterable[base.Reference] = ()):

        super().__init__()
        self.id: base.Identifier = id_
        self.endpoints: List[descriptor.Endpoint] = endpoints
        self.administration: Optional[base.AdministrativeInformation] = administration
        self.id_short: Optional[base.NameType] = id_short
        self.semantic_id: Optional[base.Reference] = semantic_id
        self.supplemental_semantic_id: base.ConstrainedList[base.Reference] = \
            base.ConstrainedList(supplemental_semantic_id)
