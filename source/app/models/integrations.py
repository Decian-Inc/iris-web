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
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app import db


class IntegrationConfig(db.Model):
    """
    Model for storing integration configurations (SentinelOne, Velociraptor, etc.)
    """
    __tablename__ = 'integration_config'

    config_id = Column(Integer, primary_key=True)
    integration_type = Column(String(50), nullable=False, unique=True)
    enabled = Column(Boolean, nullable=False, default=False)
    config_data = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(String(255), nullable=True)
    updated_by = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)

    def __repr__(self):
        return f'<IntegrationConfig {self.integration_type}: enabled={self.enabled}>'

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'config_id': self.config_id,
            'integration_type': self.integration_type,
            'enabled': self.enabled,
            'config_data': self.config_data or {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by,
            'updated_by': self.updated_by,
            'description': self.description
        }