#  IRIS AbuseIPDB Module Source Code
#  Copyright (C) 2025 - Decian
#  contact@decian.org
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

import traceback
import ipaddress
from datetime import datetime

import iris_interface.IrisInterfaceStatus as InterfaceStatus
from iris_interface.IrisModuleInterface import IrisModuleInterface, IrisModuleTypes

import iris_abuseipdb_module.IrisAbuseIPDBConfig as interface_conf
from iris_abuseipdb_module.abuseipdb_handler.abuseipdb_handler import AbuseIPDBHandler


class IrisAbuseIPDBInterface(IrisModuleInterface):
    """
    Provide the interface between Iris and AbuseIPDB
    """
    name = "IrisAbuseIPDBInterface"
    _module_name = interface_conf.module_name
    _module_description = interface_conf.module_description
    _interface_version = interface_conf.interface_version
    _module_version = interface_conf.module_version
    _pipeline_support = interface_conf.pipeline_support
    _pipeline_info = interface_conf.pipeline_info
    _module_configuration = interface_conf.module_configuration
    _module_type = IrisModuleTypes.module_processor

    def register_hooks(self, module_id: int):
        """
        Registers all the hooks

        :param module_id: Module ID provided by IRIS
        :return: Nothing
        """
        self.module_id = module_id
        module_conf = self.module_dict_conf

        # Register IOC create hook
        if module_conf.get('abuseipdb_on_create_hook_enabled'):
            status = self.register_to_hook(module_id, iris_hook_name='on_postload_ioc_create')
            if status.is_failure():
                self.log.error(status.get_message())
                self.log.error(status.get_data())
            else:
                self.log.info("Successfully registered on_postload_ioc_create hook")
        else:
            self.deregister_from_hook(module_id=self.module_id, iris_hook_name='on_postload_ioc_create')

        # Register IOC update hook
        if module_conf.get('abuseipdb_on_update_hook_enabled'):
            status = self.register_to_hook(module_id, iris_hook_name='on_postload_ioc_update')
            if status.is_failure():
                self.log.error(status.get_message())
                self.log.error(status.get_data())
            else:
                self.log.info("Successfully registered on_postload_ioc_update hook")
        else:
            self.deregister_from_hook(module_id=self.module_id, iris_hook_name='on_postload_ioc_update')

        # Register manual trigger hook
        if module_conf.get('abuseipdb_manual_hook_enabled'):
            status = self.register_to_hook(module_id, iris_hook_name='on_manual_trigger_ioc',
                                           manual_hook_name='Get AbuseIPDB insight')
            if status.is_failure():
                self.log.error(status.get_message())
                self.log.error(status.get_data())
            else:
                self.log.info("Successfully registered on_manual_trigger_ioc hook")
        else:
            self.deregister_from_hook(module_id=self.module_id, iris_hook_name='on_manual_trigger_ioc')

    def hooks_handler(self, hook_name: str, hook_ui_name: str, data: any):
        """
        Handles hooks calls

        :param hook_name: Name of the hook
        :param hook_ui_name: Name of the hook for UI
        :param data: Hook data
        :return: Hook data
        """
        self.log.info(f'Received {hook_name}')

        if hook_name in ['on_postload_ioc_create', 'on_postload_ioc_update', 'on_manual_trigger_ioc']:
            return self._handle_ioc_enrichment(data=data, hook_name=hook_name)

        return InterfaceStatus.I2Error(data=data, logs=list(self.message_queue))

    def _handle_ioc_enrichment(self, data, hook_name):
        """
        Handle IOC enrichment with AbuseIPDB

        :param data: IOC data
        :param hook_name: Name of the hook being processed
        :return: Enriched IOC data
        """
        try:
            self.log.info(f"Processing IOC enrichment for hook {hook_name}")

            # Handle data format - IRIS can pass list, dict, or IOC model objects
            if isinstance(data, list):
                if not data:
                    return InterfaceStatus.I2Error(data=data, logs=["Empty data list provided"])
                ioc_obj = data[0]  # Take first IOC from list
            else:
                ioc_obj = data

            # Extract IOC information from different object types
            if hasattr(ioc_obj, 'ioc_value'):
                # SQLAlchemy model object
                ioc_value = ioc_obj.ioc_value
                ioc_type = getattr(ioc_obj.ioc_type, 'type_name', '').lower() if hasattr(ioc_obj, 'ioc_type') else ''
                # Get case_id from session context since IOC model may not have direct case_id
                case_id = getattr(self, 'case_id', None) or self._get_case_id_from_session()
            elif isinstance(ioc_obj, dict):
                # Dictionary format
                ioc_value = ioc_obj.get('ioc_value')
                ioc_type = ioc_obj.get('ioc_type_name', '').lower()
                case_id = ioc_obj.get('case_id') or getattr(self, 'case_id', None) or self._get_case_id_from_session()
            else:
                return InterfaceStatus.I2Error(data=data, logs=["Unknown data format provided"])

            if not ioc_value:
                return InterfaceStatus.I2Error(data=data, logs=["No IOC value provided"])

            # Only process IP addresses
            if not self._is_valid_ip(ioc_value):
                self.log.info(f"Skipping non-IP IOC: {ioc_value} (type: {ioc_type})")
                return InterfaceStatus.I2Success(data=data)

            # Get module configuration
            api_key = self.module_dict_conf.get('abuseipdb_api_key')
            max_age_days = self.module_dict_conf.get('abuseipdb_max_age_days', 90)
            auto_create_notes = self.module_dict_conf.get('abuseipdb_auto_create_notes', True)

            if not api_key:
                return InterfaceStatus.I2Error(data=data, logs=["AbuseIPDB API key not configured"])

            # Initialize AbuseIPDB handler
            abuseipdb_handler = AbuseIPDBHandler(api_key=api_key, max_age_days=max_age_days)

            # Query AbuseIPDB
            self.log.info(f"Querying AbuseIPDB for IP: {ioc_value}")
            check_result = abuseipdb_handler.check_ip(ioc_value)

            if not check_result.get('success'):
                error_msg = f"AbuseIPDB query failed: {check_result.get('error')}"
                self.log.error(error_msg)
                return InterfaceStatus.I2Error(data=data, logs=[error_msg])

            # Get reports for more detailed information
            reports_result = abuseipdb_handler.get_reports(ioc_value, per_page=25)

            # Generate enrichment data for IOC
            abuseipdb_data = check_result.get('data', {})
            enrichment_data = self._generate_enrichment_data(abuseipdb_data, ioc_value)

            # Create note with detailed report if enabled and we have a case_id
            if auto_create_notes and case_id:
                try:
                    self._create_abuseipdb_note(
                        case_id=case_id,
                        ioc_value=ioc_value,
                        check_data=check_result,
                        reports_data=reports_result,
                        abuseipdb_handler=abuseipdb_handler
                    )
                except Exception as e:
                    self.log.error(f"Failed to create AbuseIPDB note: {str(e)}")
                    # Don't fail the whole enrichment if note creation fails

            self.log.info(f"Successfully enriched IOC {ioc_value} with AbuseIPDB data")

            # Return enrichment data for IRIS to handle
            return InterfaceStatus.I2Success(data=enrichment_data)

        except Exception as e:
            trace = traceback.format_exc()
            self.log.error(trace)
            return InterfaceStatus.I2Error(data=data, logs=[f"Unexpected error: {str(e)}"])

    def _is_valid_ip(self, value: str) -> bool:
        """
        Check if a value is a valid IP address

        :param value: Value to check
        :return: True if valid IP, False otherwise
        """
        try:
            ipaddress.ip_address(value)
            return True
        except ValueError:
            return False

    def _generate_enrichment_data(self, abuseipdb_data: dict, ioc_value: str) -> dict:
        """
        Generate enrichment data structure for IOC

        :param abuseipdb_data: Raw AbuseIPDB response data
        :param ioc_value: The IOC value
        :return: Structured enrichment data
        """
        confidence = abuseipdb_data.get('abuseConfidencePercentage', 0)

        # Determine risk level
        if confidence >= 75:
            risk_level = "High"
        elif confidence >= 25:
            risk_level = "Medium"
        elif confidence > 0:
            risk_level = "Low"
        else:
            risk_level = "None"

        return {
            'source': 'AbuseIPDB',
            'data': {
                'abuse_confidence': confidence,
                'risk_level': risk_level,
                'total_reports': abuseipdb_data.get('totalReports', 0),
                'last_reported': abuseipdb_data.get('lastReportedAt'),
                'country': abuseipdb_data.get('countryName'),
                'country_code': abuseipdb_data.get('countryCode'),
                'isp': abuseipdb_data.get('isp'),
                'usage_type': abuseipdb_data.get('usageType'),
                'is_whitelisted': abuseipdb_data.get('isWhitelisted', False),
                'is_public': abuseipdb_data.get('isPublic', True),
                'domain': abuseipdb_data.get('domain')
            },
            'link': f"https://www.abuseipdb.com/check/{ioc_value}",
            'timestamp': datetime.now().isoformat()
        }

    def _create_abuseipdb_note(self, case_id: int, ioc_value: str, check_data: dict,
                              reports_data: dict, abuseipdb_handler: AbuseIPDBHandler):
        """
        Create a note in the case with AbuseIPDB report

        :param case_id: Case ID
        :param ioc_value: IOC value
        :param check_data: AbuseIPDB check result
        :param reports_data: AbuseIPDB reports result
        :param abuseipdb_handler: AbuseIPDB handler instance
        """
        try:
            # Import required modules for note creation
            from app.datamgmt.case.case_notes_db import add_note, add_note_group
            from app.models import NoteDirectory
            from app import db
            from sqlalchemy import and_

            # Check if "AbuseIPDB Reports" directory exists, create if not
            directory = NoteDirectory.query.filter(and_(
                NoteDirectory.case_id == case_id,
                NoteDirectory.name == "AbuseIPDB Reports"
            )).first()

            if not directory:
                directory = NoteDirectory(
                    name="AbuseIPDB Reports",
                    case_id=case_id
                )
                db.session.add(directory)
                db.session.commit()
                self.log.info(f"Created AbuseIPDB Reports directory for case {case_id}")

            # Generate markdown report
            markdown_report = abuseipdb_handler.format_report_markdown(
                ip_address=ioc_value,
                check_data=check_data,
                reports_data=reports_data
            )

            # Create note title with current date
            current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
            note_title = f"AbuseIPDB Report {current_date}"

            # Add the note
            note = add_note(
                note_title=note_title,
                creation_date=datetime.now(),
                user_id=1,  # System user
                caseid=case_id,
                directory_id=directory.id,
                note_content=markdown_report
            )

            if note:
                self.log.info(f"Created AbuseIPDB note '{note_title}' for IP {ioc_value} in case {case_id}")
            else:
                self.log.error(f"Failed to create AbuseIPDB note for IP {ioc_value} in case {case_id}")

        except Exception as e:
            self.log.error(f"Error creating AbuseIPDB note: {str(e)}")
            # Don't re-raise - we don't want note creation failure to break IOC enrichment

    def _get_case_id_from_session(self):
        """
        Get case_id from Flask session context

        :return: Case ID if available, otherwise 1 (default case)
        """
        try:
            from flask import g
            if hasattr(g, 'case_id'):
                return g.case_id
            # Fallback to default case if no session context
            return 1
        except:
            # If Flask context is not available, use default case
            return 1

    def _sanitize_log_output(self, log_line):
        """Sanitize log output to remove sensitive information"""
        if isinstance(log_line, str) and self.module_dict_conf.get('abuseipdb_api_key'):
            return log_line.replace(self.module_dict_conf.get('abuseipdb_api_key'), '<api_key>')
        return log_line