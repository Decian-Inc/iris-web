#  IRIS Source Code
#  Copyright (C) 2021 - Airbus CyberSecurity (SAS) - https://www.airbus-cyber-security.com
#
#  Licensed under the LGPL v3.0 - the "License";
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      https://www.gnu.org/licenses/lgpl-3.0.html
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from app import db


class MS365NotificationRecipient(db.Model):
    __tablename__ = 'ms365_notification_recipients'

    id = Column(Integer, primary_key=True)
    channel_type = Column(String(10), nullable=False)   # 'email' or 'teams'
    address = Column(Text, nullable=False)              # email address or encrypted webhook URL
    display_name = Column(String(255), nullable=True)
    enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    created_by = Column(String(255), nullable=True)