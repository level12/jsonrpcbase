from typing import Optional, Any, List


# Type of `obj` should be anything that has the __getitem__ method
def get_path(obj: Any, path: List[str]) -> Optional[Any]:
    """
    Get a nested value by a series of keys inside some nested indexable
    containers, returning None if the path does not exist, avoiding any errors.
    Args:
        obj: any indexable (has __getitem__ method) obj
        path: list of accessors, such as dict keys or list indexes
    Examples:
        get_path([{'x': {'y': 1}}], [0, 'x', 'y']) -> 1
    """
    for key in path:
        try:
            obj = obj[key]
        except Exception:
            return None
    return obj
