import uuid
from sqlalchemy.types import TypeDecorator, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


class GUID(TypeDecorator):
    """Platform-independent GUID type. Uses PostgreSQL UUID natively, stores as string on other DBs."""

    impl = String
    cache_ok = True

    @property
    def python_type(self):
        return str

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return uuid.UUID(str(value)) if isinstance(value, str) else value
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        return str(value)
