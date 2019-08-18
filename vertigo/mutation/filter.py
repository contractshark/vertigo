from typing import List
from vertigo.mutation.mutation import Mutation


class MutationFilter:
    """ A mutation filter provides an interface to selectively filter test cases"""

    def apply(self, mutations: List[Mutation]) -> List[Mutation]:
        """ Apply this filter to a list of mutations

        :param mutations: The mutations to filter
        :return: The resulting list
        """
        raise NotImplementedError
