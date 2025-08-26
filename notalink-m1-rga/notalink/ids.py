import ulid
def new_id() -> str:
    return ulid.new().str.lower()
