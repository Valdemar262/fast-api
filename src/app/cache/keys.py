RESOURCE_PREFIX = "resource"
RESOURCE_LIST_PREFIX = f"{RESOURCE_PREFIX}:list"


def resource_key(resource_id: int) -> str:
    return f"{RESOURCE_PREFIX}:{resource_id}"


def resource_list_key(*, limit: int, offset: int) -> str:
    return f"{RESOURCE_LIST_PREFIX}:{limit}:{offset}"
