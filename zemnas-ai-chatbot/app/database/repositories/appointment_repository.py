from sqlalchemy.orm import Session

from app.database.models import Appointment


def get_or_create_request(db: Session, lead_id: int) -> Appointment:
	appointment = (
		db.query(Appointment)
		.filter(Appointment.lead_id == lead_id, Appointment.status == "requested")
		.order_by(Appointment.created_at.desc())
		.first()
	)
	if appointment is None:
		appointment = Appointment(lead_id=lead_id, status="requested")
		db.add(appointment)
		db.commit()
		db.refresh(appointment)
	return appointment


def update_request(db: Session, appointment: Appointment, data: dict) -> Appointment:
	if data.get("preferred_date"):
		appointment.preferred_date = data["preferred_date"]
	if data.get("preferred_time"):
		appointment.preferred_time = data["preferred_time"]
	db.commit()
	db.refresh(appointment)
	return appointment
