from itertools import combinations, permutations
import time

import uuid
import hashlib
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Set,
    Union
)


def uuid_to_sha256(uuid_str: str) -> str:
    """
    Converts a UUID string into a SHA-256 hash.

    Args:
        uuid_str (str): A valid UUID string.

    Returns:
        str: A hexadecimal string representing the SHA-256 hash of the UUID.

    Raises:
        ValueError: If the input string is not a valid UUID.
    """
    try:
        # This ensures the UUID is valid; if not, it raises a ValueError.
        uuid_obj = uuid.UUID(uuid_str)
    except ValueError:
        raise ValueError(f"Invalid UUID string: '{uuid_str}'")

    # Convert UUID to bytes, considering the hyphens.
    uuid_bytes = uuid_obj.bytes
    sha256_hash = hashlib.sha256(uuid_bytes).hexdigest()
    return sha256_hash


class Tags:
    """
    A class to manage a collection of unique tags.

    Attributes:
        tags (List[str]): A list of tags associated with an instance.
    """

    def __init__(self, tags: Optional[List[str]] = None):
        """
        Initializes the Tags object with an optional list of tags.

        Args:
            tags (Optional[List[str]]): An initial list of tags. Defaults to None.
        """
        self.tags: List[str] = tags if tags is not None else []

    def add_tag(self, tag: str):
        """
        Adds a new tag to the tags set if it's not already present.

        Args:
            tag (str): The tag to add.
        """
        self.tags.append(tag)

    def add_tags(self, tags: List[str]):
        """
        Adds a new tag to the tags set if it's not already present.

        Args:
            tag (str): The tag to add.
        """
        for tag in tags:
            self.add_tag(tag)

    def remove_tag(self, tag: str):
        """
        Removes a tag from the tags set if it exists.

        Args:
            tag (str): The tag to remove.
        """
        try:
            self.tags.remove(tag)
        except ValueError:
            pass

    def has_tag(self, tag: str) -> bool:
        """
        Checks if a tag is present in the tags set.

        Args:
            tag (str): The tag to check for.

        Returns:
        True if the tag is present, False otherwise.
        """
        return tag in self.tags

    def get_tags(self) -> List[str]:
        """
        Returns the list of tags.

        Returns:
            List[str]: A list of tags.
        """
        return self.tags

    def generate_powerset_with_permutations(self) -> List[List[str]]:
        """
        Generates the powerset of the given list, including all unique permutations
        of each subset.

        Returns:
            List[List[str]]: A list of lists, where each sublist is a unique permutation
            of elements representing a subset of the powerset.
        """
        # Generate the initial powerset
        result = [[]]
        for element in self.tags:
            new_subsets = [subset + [element] for subset in result]
            result.extend(new_subsets)

        # Generate all unique permutations for each subset in the powerset
        permuted_result = set()
        for subset in result:
            for perm in permutations(subset):
                permuted_result.add(perm)

        # Convert each tuple back to a list and sort the result by length and lexicographically
        final_result = [list(perm) for perm in sorted(
            permuted_result, key=lambda x: (len(x), x))]

        return final_result

    def priority_based_permutations(self) -> List[List[str]]:
        """
        Generates all permutations based on tag priority. This method focuses on generating permutations
        that include all tags (n elements) and, when n > 2, permutations with one less tag (n-1 elements),
        but only those permutations that start with the highest priority tag or the second highest priority tag are included.

        Returns:
            List[List[str]]: A list of permutations, where each permutation is a list of tags.

        Description:
            - The method first determines the length of the tag set (self.tags) and generates all combinations for that length (n) and n-1 when n > 2.
            - For each combination, it generates all possible permutations.
            - It then filters out those permutations that start with either the highest priority or the second highest priority tag.
            It is assumed that the tag list is already sorted in some manner to reflect their priority.
            - Finally, the method ensures each permutation in the result set is unique by removing any duplicates.

        Note:
            - This method assumes the first element in the `self.tags` list has the highest priority and the second element has the second highest priority.
            - The behavior of this method might not work as expected if there are fewer than two elements in the tag list, as it requires at least two elements to compare priorities.
        """
        result = []
        elements = self.tags
        n = len(elements)
        # Generate all permutations for n and n-1 elements when n > 2
        # Adjust range to include n-1 only if n > 2
        for i in range(n, n - 2 if n > 2 else n - 1, -1):
            for combination in combinations(elements, i):
                for perm in permutations(combination):
                    # Only add if starting with the highest priority element or the second highest
                    if perm[0] == elements[0] or perm[0] == elements[1]:
                        result.append(list(perm))

        # Eliminate duplicates
        final_result = []
        for item in result:
            if item not in final_result:
                final_result.append(item)

        return final_result

    def priority_based_permutations(self) -> List[List[str]]:
        """
        Generates all permutations based on tag priority. This method focuses on generating permutations
        that include all tags (n elements) and, when n > 2, permutations with one less tag (n-1 elements),
        but only those permutations that start with the highest priority tag or the second highest priority tag are included.

        Returns:
            List[List[str]]: A list of permutations, where each permutation is a list of tags.

        Description:
            - The method first determines the length of the tag set (self.tags) and generates all combinations for that length (n) and n-1 when n > 2.
            - For each combination, it generates all possible permutations.
            - It then filters out those permutations that start with either the highest priority or the second highest priority tag.
            It is assumed that the tag list is already sorted in some manner to reflect their priority.
            - Finally, the method ensures each permutation in the result set is unique by removing any duplicates.

        Note:
            - This method assumes the first element in the `self.tags` list has the highest priority and the second element has the second highest priority.
            - The behavior of this method might not work as expected if there are fewer than two elements in the tag list, as it requires at least two elements to compare priorities.
        """
        result = []
        elements = self.tags
        n = len(elements)
        # Generate all permutations for n and n-1 elements when n > 2
        # Adjust range to include n-1 only if n > 2
        for i in range(n, n - 2 if n > 2 else n - 1, -1):
            for combination in combinations(elements, i):
                for perm in permutations(combination):
                    # Only add if starting with the highest priority element or the second highest
                    if perm[0] == elements[0] or perm[0] == elements[1]:
                        result.append(list(perm))

        # Eliminate duplicates
        final_result = []
        for item in result:
            if item not in final_result:
                final_result.append(item)

        return final_result

    def priority_based_permutations(self) -> List[List[str]]:
        """
        Generates all permutations based on tag priority. This method focuses on generating permutations
        that include all tags (n elements) and, when n > 2, permutations with one less tag (n-1 elements),
        but only those permutations that start with the highest priority tag or the second highest priority tag are included.

        Additionally, when there are more than one tag, it includes permutations of single tags.

        Returns:
            List[List[str]]: A list of permutations, where each permutation is a list of tags.

        Description:
            - The method first determines the length of the tag set (self.tags) and generates all combinations for that length (n) and n-1 when n > 2.
            - For each combination, it generates all possible permutations.
            - It then filters out those permutations that start with either the highest priority or the second highest priority tag.
            It is assumed that the tag list is already sorted in some manner to reflect their priority.
            - Finally, the method ensures each permutation in the result set is unique by removing any duplicates.
            - If there are more than one tag, it also adds each tag as a single-element list to the result.

        Note:
            - This method assumes the first element in the `self.tags` list has the highest priority and the second element has the second highest priority.
            - The behavior of this method might not work as expected if there are fewer than two elements in the tag list, as it requires at least two elements to compare priorities.
        """
        result = []
        elements = self.tags
        n = len(elements)

        # Generate all permutations for n and n-1 elements when n > 2
        for i in range(n, n - 2 if n > 2 else n - 1, -1):
            for combination in combinations(elements, i):
                for perm in permutations(combination):
                    # Only add if starting with the highest priority element or the second highest
                    if perm[0] == elements[0] or perm[0] == elements[1]:
                        result.append(list(perm))

        # Eliminate duplicates
        final_result = []
        for item in result:
            if item not in final_result:
                final_result.append(item)

        # Add single elements if len(self.tags) > 1
        if len(self.tags) > 1:
            for element in self.tags:
                final_result.append([element])

        return final_result

    def to_filter(self, powerset: bool = True) -> Optional[Dict[str, Any]]:
        """
        Converts the metadata to a filter format, based on its tags.

        Args:
            powerset (bool): If True, generates filters based on the powerset of tags; otherwise, uses tag combinations.

        Returns:
            Optional[Dict[str, Any]]: A dictionary representing the filter criteria, or None if no tags are defined.
        """
        tags_filter = self.generate_powerset_with_permutations(
        ) if powerset else self.priority_based_permutations()
        if not self.get_tags():
            return None
        return {"tags": tags_filter}


class Metadata:
    """
    Represents metadata associated with a document, including IDs, tags, and temporal information.

    Attributes:
    - ids (str): Unique identifier for the metadata, generated from a SHA-256 hash.
    - splitter (str): A string used to split or differentiate metadata, default is 'default'.
    - related (bool): Indicates if the metadata is related to another entity.
    - valid_time (int): Duration in seconds for which the metadata is considered valid.
    - start_time (int): Timestamp marking the start of the metadata's validity.
    - tags (Tags): A `Tags` object containing tags associated with the metadata.
    """

    def __init__(
        self,
        ids: Optional[str] = None,
        splitter: str = "default",
        valid_time: Optional[int] = None,
        start_time: Optional[int] = None,
        related: bool = False,
        tags: Optional[List[str]] = None,
    ):
        self.ids = ids if ids is not None else uuid_to_sha256(
            str(uuid.uuid4()))
        self.splitter = splitter
        self.related = related
        self.valid_time = valid_time if valid_time is not None else -1
        self.start_time = start_time if start_time is not None else time.time()
        self.tags = Tags(tags)

    def get_ids(self) -> str:
        """
        Retrieves the unique identifier of the metadata.

        Returns:
            str: The unique identifier.
        """
        return self.ids

    def to_filter(self, powerset: bool = True) -> Optional[Dict[str, Any]]:
        return self.tags.to_filter(powerset)

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the metadata into a dictionary format.

        Returns:
            Dict[str, Any]: A dictionary representation of the metadata.
        """
        return {
            "ids": self.ids,
            "splitter": self.splitter,
            "valid_time": self.valid_time,
            "related": self.related,
            "start_time": self.start_time,
            "tags": self.tags.get_tags(),
        }


class Document:
    """
    Represents a document with content and associated metadata.

    Attributes:
        page_content (str): The content of the document.
        metadata (Metadata): The metadata associated with the document.
    """

    def __init__(self, page_content: str, metadata: Union[Dict[str, Any], Metadata] = None):
        self.page_content = page_content
        if isinstance(metadata, dict):
            self.metadata = Metadata(**metadata)
        elif isinstance(metadata, Metadata):
            self.metadata = metadata
        else:
            self.metadata = Metadata()

    def is_valid(self) -> bool:
        """
        Determines if the document is still valid based on its metadata's validity period.

        Returns:
            bool: True if the document is valid, False otherwise.
        """
        current_time = time.time()
        # Handle the case where valid_time is indefinite (-1).
        if self.metadata.valid_time == -1:
            return True

        return (self.metadata.start_time + self.metadata.valid_time) >= current_time

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the document into a dictionary format, including its content and metadata.

        Returns:
            Dict[str, Any]: A dictionary representation of the document.
        """
        return {"page_content": self.page_content, "metadata": self.metadata.to_dict()}
