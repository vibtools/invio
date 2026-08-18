from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class CustomerRecord:
    """Provider-neutral customer data stored inside a Customer List.

    Email is mandatory. Name and country are optional explicit user-supplied
    metadata. Country is stored as an uppercase two-letter ASCII code when
    present; no country or name is inferred by this model.
    """

    email: str
    name: str = ""
    country: str = ""
    name_is_dynamic: bool = False

    def __post_init__(self) -> None:
        email = self.email.strip().lower()
        name = self.name.strip()
        country = self.country.strip().upper()
        name_is_dynamic = self.name_is_dynamic
        if not email:
            raise ValueError("Customer email is required.")
        if country and (len(country) != 2 or not country.isascii() or not country.isalpha()):
            raise ValueError("Customer country must be a two-letter code when provided.")
        if type(name_is_dynamic) is not bool:
            raise ValueError("Customer dynamic-name marker must be a boolean.")
        object.__setattr__(self, "email", email)
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "country", country)
        object.__setattr__(self, "name_is_dynamic", name_is_dynamic)


class _CustomerEmailList(list[str]):
    """Mutable compatibility view for the pre-P04 ``CustomerList.emails`` field.

    P04 changed the authoritative representation to ``CustomerRecord`` objects.
    The historical ``emails`` attribute was a mutable list, so returning a plain
    computed list would silently break callers that mutate it in place. This
    small list subclass mirrors every mutation back to the owning CustomerList
    while preserving name/country metadata for email values that remain present.
    """

    def __init__(self, owner: "CustomerList") -> None:
        self._owner = owner
        super().__init__(record.email for record in owner.customers)

    def _sync(self) -> None:
        existing: dict[str, deque[CustomerRecord]] = defaultdict(deque)
        for record in self._owner.customers:
            existing[record.email].append(record)

        rebuilt: list[CustomerRecord] = []
        normalized_values: list[str] = []
        for value in list.__iter__(self):
            normalized = CustomerRecord(str(value)).email
            normalized_values.append(normalized)
            if existing[normalized]:
                rebuilt.append(existing[normalized].popleft())
            else:
                rebuilt.append(CustomerRecord(normalized))

        # Keep the visible compatibility list normalized exactly like the domain
        # model, then publish the same ordering to the authoritative records.
        list.clear(self)
        list.extend(self, normalized_values)
        self._owner.customers = rebuilt

    def __setitem__(self, key, value) -> None:  # type: ignore[override]
        list.__setitem__(self, key, value)
        self._sync()

    def __delitem__(self, key) -> None:  # type: ignore[override]
        list.__delitem__(self, key)
        self._sync()

    def append(self, value: str) -> None:
        list.append(self, value)
        self._sync()

    def extend(self, values) -> None:  # type: ignore[override]
        list.extend(self, values)
        self._sync()

    def insert(self, index: int, value: str) -> None:
        list.insert(self, index, value)
        self._sync()

    def pop(self, index: int = -1) -> str:
        value = list.pop(self, index)
        self._sync()
        return value

    def remove(self, value: str) -> None:
        list.remove(self, value)
        self._sync()

    def clear(self) -> None:
        list.clear(self)
        self._sync()

    def reverse(self) -> None:
        list.reverse(self)
        self._sync()

    def sort(self, *args, **kwargs) -> None:
        list.sort(self, *args, **kwargs)
        self._sync()

    def __iadd__(self, values):
        list.__iadd__(self, values)
        self._sync()
        return self

    def __imul__(self, value: int):
        list.__imul__(self, value)
        self._sync()
        return self


@dataclass(slots=True, init=False)
class CustomerList:
    id: str
    name: str
    customers: list[CustomerRecord] = field(default_factory=list)

    def __init__(
        self,
        id: str,
        name: str,
        emails: list[str] | None = None,
        customers: list[CustomerRecord] | None = None,
    ) -> None:
        self.id = id
        self.name = name
        if customers is not None and emails is not None:
            raise ValueError("Provide customers or emails, not both.")
        if customers is not None:
            self.customers = [
                item if isinstance(item, CustomerRecord) else CustomerRecord(**item)  # type: ignore[arg-type]
                for item in customers
            ]
        else:
            self.customers = [CustomerRecord(email) for email in (emails or [])]

    @property
    def emails(self) -> list[str]:
        """Backward-compatible mutable email list view used by legacy callers."""
        return _CustomerEmailList(self)

    @emails.setter
    def emails(self, values: list[str]) -> None:
        # Assignment had replacement semantics before P04. Preserve metadata for
        # values that remain present while replacing the visible email ordering.
        proxy = _CustomerEmailList(self)
        list.clear(proxy)
        list.extend(proxy, values)
        proxy._sync()

    @property
    def count(self) -> int:
        return len(self.customers)
