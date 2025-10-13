#  IRIS AlienVault OTX Module Source Code
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
from datetime import datetime

import iris_interface.IrisInterfaceStatus as InterfaceStatus
from iris_interface.IrisModuleInterface import IrisModuleInterface, IrisModuleTypes

import iris_otx_module.IrisOTXConfig as interface_conf
from iris_otx_module.otx_handler.otx_handler import OTXHandler


class IrisOTXInterface(IrisModuleInterface):
    """
    Provide the interface between Iris and AlienVault OTX
    """
    name = "IrisOTXInterface"
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
        if module_conf.get('otx_on_create_hook_enabled'):
            status = self.register_to_hook(module_id, iris_hook_name='on_postload_ioc_create')
            if status.is_failure():
                self.log.error(status.get_message())
                self.log.error(status.get_data())
            else:
                self.log.info("Successfully registered on_postload_ioc_create hook")
        else:
            self.deregister_from_hook(module_id=self.module_id, iris_hook_name='on_postload_ioc_create')

        # Register IOC update hook
        if module_conf.get('otx_on_update_hook_enabled'):
            status = self.register_to_hook(module_id, iris_hook_name='on_postload_ioc_update')
            if status.is_failure():
                self.log.error(status.get_message())
                self.log.error(status.get_data())
            else:
                self.log.info("Successfully registered on_postload_ioc_update hook")
        else:
            self.deregister_from_hook(module_id=self.module_id, iris_hook_name='on_postload_ioc_update')

        # Register manual trigger hook
        if module_conf.get('otx_manual_hook_enabled'):
            status = self.register_to_hook(module_id, iris_hook_name='on_manual_trigger_ioc',
                                           manual_hook_name='Get AlienVault OTX insight')
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
        Handle IOC enrichment with AlienVault OTX

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

            # OTX supports multiple IOC types, so we'll determine what type it is
            self.log.info(f"Processing IOC: {ioc_value} (type: {ioc_type})")

            # Get module configuration
            api_key = self.module_dict_conf.get('otx_api_key')
            auto_create_notes = self.module_dict_conf.get('otx_auto_create_notes', True)

            if not api_key:
                return InterfaceStatus.I2Error(data=data, logs=["AlienVault OTX API key not configured"])

            # Initialize OTX handler
            otx_handler = OTXHandler(api_key=api_key)

            # Query OTX
            self.log.info(f"Querying AlienVault OTX for IOC: {ioc_value}")
            otx_result = otx_handler.query_indicator(ioc_value)

            if 'error' in otx_result:
                error_msg = f"OTX query failed: {otx_result.get('error')}"
                self.log.warning(error_msg)
                # Don't fail completely for unsupported IOCs, just log and continue
                if 'Unsupported indicator type' in otx_result.get('error', ''):
                    self.log.info(f"Skipping unsupported IOC type: {ioc_value}")
                    return InterfaceStatus.I2Success(data=data)
                return InterfaceStatus.I2Error(data=data, logs=[error_msg])

            # Generate enrichment data for IOC
            enrichment_data = self._generate_enrichment_data(otx_result, ioc_value)

            # Create note with detailed report if enabled and we have a case_id
            if auto_create_notes and case_id:
                try:
                    self._create_otx_note(
                        case_id=case_id,
                        ioc_value=ioc_value,
                        otx_data=otx_result,
                        otx_handler=otx_handler
                    )
                except Exception as e:
                    self.log.error(f"Failed to create OTX note: {str(e)}")
                    # Don't fail the whole enrichment if note creation fails

            self.log.info(f"Successfully enriched IOC {ioc_value} with OTX data")

            # Return enrichment data for IRIS to handle
            return InterfaceStatus.I2Success(data=enrichment_data)

        except Exception as e:
            trace = traceback.format_exc()
            self.log.error(trace)
            return InterfaceStatus.I2Error(data=data, logs=[f"Unexpected error: {str(e)}"])

    def _generate_enrichment_data(self, otx_data: dict, ioc_value: str) -> dict:
        """
        Generate enrichment data structure for IOC

        :param otx_data: Raw OTX response data
        :param ioc_value: The IOC value
        :return: Structured enrichment data
        """
        general = otx_data.get('general', {})
        pulse_info = general.get('pulse_info', {})
        pulse_count = pulse_info.get('count', 0)

        # Determine risk level based on pulse count and reputation
        reputation = general.get('reputation', 0)
        if pulse_count >= 10 or reputation < -5:
            risk_level = "High"
        elif pulse_count >= 5 or reputation < 0:
            risk_level = "Medium"
        elif pulse_count > 0:
            risk_level = "Low"
        else:
            risk_level = "None"

        return {
            'source': 'AlienVault OTX',
            'data': {
                'pulse_count': pulse_count,
                'risk_level': risk_level,
                'reputation': reputation,
                'country': general.get('country_name'),
                'country_code': general.get('country_code'),
                'city': general.get('city'),
                'asn': general.get('asn'),
                'indicator_type': otx_data.get('indicator_type')
            },
            'link': f"https://otx.alienvault.com/indicator/{otx_data.get('indicator_type', 'ip')}/{ioc_value}",
            'timestamp': datetime.now().isoformat()
        }

    def _create_otx_note(self, case_id: int, ioc_value: str, otx_data: dict, otx_handler: OTXHandler):
        """
        Create a note in the case with OTX report

        :param case_id: Case ID
        :param ioc_value: IOC value
        :param otx_data: OTX query result
        :param otx_handler: OTX handler instance
        """
        try:
            # Import required modules for note creation
            from app.datamgmt.case.case_notes_db import add_note, add_note_group
            from app.models import NoteDirectory
            from app import db
            from sqlalchemy import and_

            # Check if "AlienVault OTX Reports" directory exists, create if not
            directory = NoteDirectory.query.filter(and_(
                NoteDirectory.case_id == case_id,
                NoteDirectory.name == "AlienVault OTX Reports"
            )).first()

            if not directory:
                directory = NoteDirectory(
                    name="AlienVault OTX Reports",
                    case_id=case_id
                )
                db.session.add(directory)
                db.session.commit()
                self.log.info(f"Created AlienVault OTX Reports directory for case {case_id}")

            # Generate markdown report
            markdown_report = otx_handler.format_report_markdown(
                indicator=ioc_value,
                otx_data=otx_data
            )

            # Create note title with current date
            current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
            note_title = f"AlienVault OTX Report {current_date}"

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
                self.log.info(f"Created OTX note '{note_title}' for IOC {ioc_value} in case {case_id}")
            else:
                self.log.error(f"Failed to create OTX note for IOC {ioc_value} in case {case_id}")

        except Exception as e:
            self.log.error(f"Error creating OTX note: {str(e)}")
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
        if isinstance(log_line, str) and self.module_dict_conf.get('otx_api_key'):
            return log_line.replace(self.module_dict_conf.get('otx_api_key'), '<api_key>')
        return log_line