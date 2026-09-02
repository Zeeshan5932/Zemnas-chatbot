from typing import Optional

from sqlalchemy.orm import Session

from app.database.repositories.appointment_repository import (
	get_or_create_request,
	update_request,
)


def request_appointment(
	db: Session,
	lead_id: int,
	date: Optional[str] = None,
	time: Optional[str] = None,
):
	appointment = get_or_create_request(db, lead_id)
	return update_request(
		db,
		appointment,
		{"preferred_date": date, "preferred_time": time},
	)
