from sqlalchemy.orm import Session

from app.database.models import Lead


def get_or_create_lead(

    db: Session,

    session_id: str

):

    lead = (

        db.query(Lead)

        .filter(
            Lead.session_id
            == session_id
        )

        .first()
    )


    if not lead:

        lead = Lead(

            session_id=session_id,

            status="collecting"
        )


        db.add(
            lead
        )


        db.commit()


        db.refresh(
            lead
        )


    return lead


def update_lead(

    db: Session,

    session_id: str,

    data: dict

):

    lead = get_or_create_lead(

        db=db,

        session_id=session_id
    )


    allowed_fields = [

        "name",

        "email",

        "phone",

        "company_name",

        "service",

        "project_description",

        "budget",

        "timeline",

        "appointment_requested",

        "appointment_date",

        "appointment_time",

        "status"
    ]


    for key, value in data.items():

        if (

            key in allowed_fields

            and value is not None

        ):

            setattr(

                lead,

                key,

                value
            )


    db.commit()


    db.refresh(
        lead
    )


    return lead