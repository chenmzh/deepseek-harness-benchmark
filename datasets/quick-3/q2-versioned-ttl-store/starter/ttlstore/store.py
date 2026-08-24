class MissingKey(KeyError):
    pass


class VersionConflict(RuntimeError):
    pass


class VersionedTTLStore:
    def __init__(self, database, ttl=10):
        self.database = database
        self.ttl = ttl
        self.records = {}

    def put(self, key, value, request_id, now):
        record = {"key": key, "value": value, "version": 1, "expires_at": now + self.ttl}
        self.records[key] = record
        return record

    def get(self, key, now):
        return self.records.get(key)

    def compare_and_swap(self, key, expected_version, value, request_id, now):
        if key not in self.records:
            raise MissingKey(key)
        return self.put(key, value, request_id, now)

    def delete(self, key, expected_version, request_id, now):
        if key not in self.records:
            raise MissingKey(key)
        del self.records[key]
        return {"key": key, "version": expected_version, "deleted": True}

    def items(self, now):
        return list(self.records.values())
