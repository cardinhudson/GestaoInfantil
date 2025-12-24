"""Modelos SQLAlchemy
"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from db import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    roles = Column(String, default="child")  # 'child' ou 'validator'
    password_hash = Column(String, nullable=True)
    photo = Column(String, nullable=True)  # caminho para arquivo de foto (uploads/users/...)

    submitted_tasks = relationship("Task", back_populates="submitted_by", foreign_keys='Task.submitted_by_id')
    validated_tasks = relationship("Task", back_populates="validator", foreign_keys='Task.validator_id')


class Conversion(Base):
    __tablename__ = "conversions"
    id = Column(Integer, primary_key=True)
    money_per_point = Column(Float, default=0.5)  # R$ per point
    hours_per_point = Column(Float, default=0.1)  # hours per point


class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    points = Column(Float, nullable=False)  # valor em dinheiro ou horas, depende de conversion_type
    conversion_type = Column(String, nullable=False)  # 'money' or 'hours'

    child_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    submitted_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    validator_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    validated = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    validated_at = Column(DateTime, nullable=True)

    submitted_by = relationship("User", foreign_keys=[submitted_by_id], back_populates="submitted_tasks")
    validator = relationship("User", foreign_keys=[validator_id], back_populates="validated_tasks")


class Debit(Base):
    __tablename__ = "debits"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    points_deducted = Column(Integer, nullable=False)
    money_amount = Column(Float, nullable=True)
    hours_amount = Column(Float, nullable=True)
    reason = Column(Text, nullable=True)
    performed_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
