#!/usr/bin/env python3

from enum import Enum


class MessagePerformative(Enum):
    """MessagePerformative enum class.
    Enumeration containing the possible message performative.
    """

    PROPOSE = 101
    ACCEPT = 102
    COMMIT = 103
    ASK_WHY = 104
    ARGUE = 105
    QUERY_REF = 106
    INFORM_WASTE_POS_ADD_REF = 107
    INFORM_WASTE_POS_REMOVE_REF = 108

    PROPOSE_WASTE = 201
    ACCEPT_WASTE = 202

    def __str__(self):
        """Returns the name of the enum item."""
        return "{0}".format(self.name)
