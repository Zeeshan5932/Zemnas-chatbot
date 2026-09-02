from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey
)

from sqlalchemy.orm import declarative_base

from datetime import datetime


Base = declarative_base()


class Conversation(Base):

    __tablename__ = "conversations"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    session_id = Column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


class Message(Base):

    __tablename__ = "messages"

    id = Column(
        Integer,
        primary_key=True
    )

    session_id = Column(
        String(255),
        index=True,
        nullable=False
    )

    role = Column(
        String(50),
        nullable=False
    )

    content = Column(
        Text,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


class Lead(Base):

    __tablename__ = "leads"

    id = Column(
        Integer,
        primary_key=True
    )

    session_id = Column(
        String(255),
        unique=True,
        index=True
    )

    name = Column(
        String(255),
        nullable=True
    )

    email = Column(
        String(255),
        nullable=True
    )

    phone = Column(
        String(100),
        nullable=True
    )

    company_name = Column(
        String(255),
        nullable=True
    )

    service = Column(
        String(255),
        nullable=True
    )

    project_description = Column(
        Text,
        nullable=True
    )

    budget = Column(
        String(100),
        nullable=True
    )

    timeline = Column(
        String(100),
        nullable=True
    )

    status = Column(
        String(100),
        default="collecting"
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


class Appointment(Base):

    __tablename__ = "appointments"

    id = Column(
        Integer,
        primary_key=True
    )

    lead_id = Column(
        Integer,
        ForeignKey("leads.id")
    )

    preferred_date = Column(
        String(255),
        nullable=True
    )

    preferred_time = Column(
        String(255),
        nullable=True
    )

    status = Column(
        String(100),
        default="requested"
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )