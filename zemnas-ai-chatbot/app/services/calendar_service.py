class CalendarService:
	"""Integration boundary for a future calendar provider adapter."""

	def create_booking(self, *, date: str, time: str, metadata: dict) -> None:
		raise NotImplementedError("No calendar provider is configured")
