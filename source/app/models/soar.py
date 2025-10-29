#  IRIS Source Code
#  Copyright (C) 2025 - DFIR-IRIS
#  contact@dfir-iris.org
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 3 of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import BigInteger
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app import db


class SoarTemplate(db.Model):
    __tablename__ = 'soar_templates'

    template_id = Column(String(50), primary_key=True)
    template_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    vendor = Column(String(100), nullable=True)
    integration_type = Column(String(50), nullable=False)
    requires_approval = Column(Boolean, nullable=False, default=False)
    tags = Column(JSONB, nullable=True)
    allowed_target_types = Column(JSONB, nullable=True)
    parameter_schema = Column(JSONB, nullable=True)
    execution_function = Column(String(100), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    version = Column(String(20), nullable=False, default='1.0')
    created_by = Column(Integer, ForeignKey('user.id'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_by = Column(Integer, ForeignKey('user.id'), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    creator = relationship("User", foreign_keys=[created_by], backref="created_soar_templates")
    updater = relationship("User", foreign_keys=[updated_by], backref="updated_soar_templates")

    def __repr__(self):
        return f'<SoarTemplate {self.template_id}: {self.template_name}>'

    def to_dict(self):
        """Convert model to dictionary for API responses"""
        return {
            'template_id': self.template_id,
            'template_name': self.template_name,
            'description': self.description,
            'vendor': self.vendor,
            'integration_type': self.integration_type,
            'requires_approval': self.requires_approval,
            'tags': self.tags,
            'allowed_target_types': self.allowed_target_types,
            'parameter_schema': self.parameter_schema,
            'execution_function': self.execution_function,
            'is_active': self.is_active,
            'version': self.version,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_by': self.updated_by,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'creator_name': self.creator.name if self.creator else None,
            'updater_name': self.updater.name if self.updater else None
        }


class SoarJob(db.Model):
    __tablename__ = 'soar_jobs'

    # Primary job metadata
    job_id = Column(String(36), primary_key=True)  # UUID
    case_id = Column(Integer, ForeignKey('cases.case_id'), nullable=False)
    template_id = Column(String(50), nullable=False)
    template_name = Column(String(200), nullable=False)
    integration_type = Column(String(50), nullable=False)  # sentinelone, velociraptor, etc.

    # Execution details
    target = Column(String(255), nullable=False)
    status = Column(String(20), nullable=False)  # Running, Completed, Failed
    executor_id = Column(Integer, ForeignKey('user.id'), nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Results and metadata
    result_data = Column(JSONB, nullable=True)  # Full job execution results
    error_message = Column(Text, nullable=True)

    # Additional job parameters
    job_parameters = Column(JSONB, nullable=True)  # Store job-specific config
    comment = Column(Text, nullable=True)

    # Approval workflow fields
    requires_approval = Column(Boolean, nullable=False, default=False)
    approval_status = Column(String(20), nullable=True)  # Pending, Approved, Rejected
    approved_by = Column(Integer, ForeignKey('user.id'), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approval_comment = Column(Text, nullable=True)

    # Scheduling fields
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    schedule_type = Column(String(20), nullable=True)  # immediate, delayed, recurring
    schedule_params = Column(JSONB, nullable=True)  # Store schedule-specific parameters
    celery_task_id = Column(String(255), nullable=True)  # Celery task ID for scheduled jobs
    recurring_job_id = Column(String(36), nullable=True)  # UUID for recurring job series

    # Relationships
    case = relationship("Cases", backref="soar_jobs")
    executor = relationship("User", backref="executed_soar_jobs")
    approver = relationship("User", foreign_keys=[approved_by], backref="approved_soar_jobs")
    steps = relationship("SoarJobStep", backref="job", cascade="all, delete-orphan")
    artifacts = relationship("SoarJobArtifact", backref="job", cascade="all, delete-orphan")

    def __repr__(self):
        return f'<SoarJob {self.job_id}: {self.template_name} on {self.target}>'

    def to_dict(self):
        """Convert model to dictionary for API responses"""
        return {
            'job_id': self.job_id,
            'case_id': self.case_id,
            'template_id': self.template_id,
            'template_name': self.template_name,
            'integration_type': self.integration_type,
            'target': self.target,
            'status': self.status,
            'executor_id': self.executor_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'result_data': self.result_data,
            'error_message': self.error_message,
            'job_parameters': self.job_parameters,
            'comment': self.comment,
            'requires_approval': self.requires_approval,
            'approval_status': self.approval_status,
            'approved_by': self.approved_by,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'approval_comment': self.approval_comment,
            'approver_name': self.approver.name if self.approver else None,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'schedule_type': self.schedule_type,
            'schedule_params': self.schedule_params,
            'celery_task_id': self.celery_task_id,
            'recurring_job_id': self.recurring_job_id,
            'steps': [step.to_dict() for step in self.steps] if self.steps else [],
            'artifacts': [artifact.to_dict() for artifact in self.artifacts] if self.artifacts else []
        }


class SoarJobStep(db.Model):
    __tablename__ = 'soar_job_steps'

    step_id = Column(String(36), primary_key=True)
    job_id = Column(String(36), ForeignKey('soar_jobs.job_id'), nullable=False)
    step_name = Column(String(200), nullable=False)
    step_order = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    result_message = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)

    def __repr__(self):
        return f'<SoarJobStep {self.step_id}: {self.step_name}>'

    def to_dict(self):
        """Convert model to dictionary for API responses"""
        return {
            'step_id': self.step_id,
            'job_id': self.job_id,
            'step_name': self.step_name,
            'step_order': self.step_order,
            'status': self.status,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'result_message': self.result_message,
            'error_message': self.error_message
        }


class SoarJobArtifact(db.Model):
    __tablename__ = 'soar_job_artifacts'

    artifact_id = Column(String(36), primary_key=True)
    job_id = Column(String(36), ForeignKey('soar_jobs.job_id'), nullable=False)
    artifact_name = Column(String(255), nullable=False)
    artifact_type = Column(String(50), nullable=False)  # json, zip, txt, etc.
    file_path = Column(String(500), nullable=False)
    file_size = Column(BigInteger, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_downloadable = Column(Boolean, default=True)

    def __repr__(self):
        return f'<SoarJobArtifact {self.artifact_id}: {self.artifact_name}>'

    def to_dict(self):
        """Convert model to dictionary for API responses"""
        return {
            'artifact_id': self.artifact_id,
            'job_id': self.job_id,
            'artifact_name': self.artifact_name,
            'artifact_type': self.artifact_type,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_downloadable': self.is_downloadable,
            'name': self.artifact_name,  # For frontend compatibility
            'type': self.artifact_type,  # For frontend compatibility
            'size': f"{self.file_size / 1024:.1f} KB" if self.file_size else "Unknown",  # For frontend compatibility
            'url': f"/api/soar/jobs/{self.job_id}/artifacts/{self.artifact_id}/download"  # For frontend compatibility
        }