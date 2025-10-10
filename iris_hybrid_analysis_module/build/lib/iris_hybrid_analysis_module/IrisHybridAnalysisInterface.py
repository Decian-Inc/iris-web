#  IRIS Hybrid Analysis Module Source Code
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

import iris_hybrid_analysis_module.IrisHybridAnalysisConfig as interface_conf
from iris_hybrid_analysis_module.hybrid_analysis_handler.hybrid_analysis_handler import HybridAnalysisHandler


class IrisHybridAnalysisInterface(IrisModuleInterface):
    """
    Provide the interface between Iris and Hybrid Analysis
    """
    name = "IrisHybridAnalysisInterface"
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
        if module_conf.get('hybrid_analysis_on_create_hook_enabled'):
            status = self.register_to_hook(module_id, iris_hook_name='on_postload_ioc_create')
            if status.is_failure():
                self.log.error(status.get_message())
                self.log.error(status.get_data())
            else:
                self.log.info("Successfully registered on_postload_ioc_create hook")
        else:
            self.deregister_from_hook(module_id=self.module_id, iris_hook_name='on_postload_ioc_create')

        # Register IOC update hook
        if module_conf.get('hybrid_analysis_on_update_hook_enabled'):
            status = self.register_to_hook(module_id, iris_hook_name='on_postload_ioc_update')
            if status.is_failure():
                self.log.error(status.get_message())
                self.log.error(status.get_data())
            else:
                self.log.info("Successfully registered on_postload_ioc_update hook")
        else:
            self.deregister_from_hook(module_id=self.module_id, iris_hook_name='on_postload_ioc_update')

        # Register manual trigger hook
        if module_conf.get('hybrid_analysis_manual_hook_enabled'):
            status = self.register_to_hook(module_id, iris_hook_name='on_manual_trigger_ioc',
                                           manual_hook_name='Get Hybrid Analysis insight')
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
        Handle IOC enrichment with Hybrid Analysis

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

            # Get module configuration
            api_key = self.module_dict_conf.get('hybrid_analysis_api_key')
            environment_id = self.module_dict_conf.get('hybrid_analysis_environment_id', 120)
            max_reports = self.module_dict_conf.get('hybrid_analysis_max_reports', 10)
            auto_create_notes = self.module_dict_conf.get('hybrid_analysis_auto_create_notes', True)

            if not api_key:
                return InterfaceStatus.I2Error(data=data, logs=["Hybrid Analysis API key not configured"])

            # Initialize Hybrid Analysis handler
            ha_handler = HybridAnalysisHandler(
                api_key=api_key,
                environment_id=environment_id,
                max_reports=max_reports
            )

            # Determine IOC type and perform appropriate search
            detected_ioc_type = ha_handler.determine_ioc_type(ioc_value)

            self.log.info(f"Analyzing IOC: {ioc_value} (detected type: {detected_ioc_type})")

            # Perform search based on IOC type
            if detected_ioc_type == 'hash':
                search_result = ha_handler.search_hash(ioc_value)
            elif detected_ioc_type in ['domain', 'url']:
                search_result = ha_handler.search_terms(ioc_value, detected_ioc_type)
            elif detected_ioc_type == 'email':
                # Email addresses can be searched as terms
                search_result = ha_handler.search_terms(ioc_value, 'email')
            else:
                self.log.info(f"Skipping unsupported IOC type: {ioc_value} (type: {detected_ioc_type})")
                return InterfaceStatus.I2Success(data=data)

            if not search_result.get('success'):
                error_msg = f"Hybrid Analysis query failed: {search_result.get('error')}"
                self.log.error(error_msg)
                return InterfaceStatus.I2Error(data=data, logs=[error_msg])

            # Get detailed reports and MITRE data for relevant results
            report_summaries = []
            mitre_data = []

            search_data = search_result.get('data', [])
            if search_data:
                # Get detailed reports for top results
                for result in search_data[:3]:  # Limit to top 3 for performance
                    job_id = result.get('job_id')
                    if job_id:
                        # Get report summary
                        summary = ha_handler.get_report_summary(job_id)
                        if summary.get('success'):
                            report_summaries.append(summary)

                        # Get MITRE ATT&CK data
                        mitre = ha_handler.get_mitre_attack(job_id)
                        if mitre.get('success'):
                            mitre_data.append(mitre)

            # Generate enrichment data for IOC
            enrichment_data = self._generate_enrichment_data(search_result, detected_ioc_type, ioc_value)

            # Create note with detailed report if enabled and we have a case_id
            if auto_create_notes and case_id:
                try:
                    self._create_hybrid_analysis_note(
                        case_id=case_id,
                        ioc_value=ioc_value,
                        ioc_type=detected_ioc_type,
                        search_data=search_result,
                        report_summaries=report_summaries,
                        mitre_data=mitre_data,
                        ha_handler=ha_handler
                    )
                except Exception as e:
                    self.log.error(f"Failed to create Hybrid Analysis note: {str(e)}")
                    # Don't fail the whole enrichment if note creation fails

            self.log.info(f"Successfully enriched IOC {ioc_value} with Hybrid Analysis data")

            # Return enrichment data for IRIS to handle
            return InterfaceStatus.I2Success(data=enrichment_data)

        except Exception as e:
            trace = traceback.format_exc()
            self.log.error(trace)
            return InterfaceStatus.I2Error(data=data, logs=[f"Unexpected error: {str(e)}"])

    def _generate_enrichment_data(self, search_result: dict, ioc_type: str, ioc_value: str) -> dict:
        """
        Generate enrichment data structure for IOC

        :param search_result: Hybrid Analysis search results
        :param ioc_type: Type of IOC
        :param ioc_value: The IOC value
        :return: Structured enrichment data
        """
        search_data = search_result.get('data', [])

        if not search_data:
            return {
                'source': 'Hybrid Analysis',
                'data': {
                    'total_reports': 0,
                    'malicious_count': 0,
                    'suspicious_count': 0,
                    'clean_count': 0,
                    'overall_verdict': 'not_found',
                    'risk_level': 'Unknown',
                    'ioc_type': ioc_type
                },
                'link': f"https://www.hybrid-analysis.com/search?query={ioc_value}",
                'timestamp': datetime.now().isoformat()
            }

        # Analyze results
        total_reports = len(search_data)
        malicious_count = sum(1 for r in search_data if r.get('verdict') == 'malicious')
        suspicious_count = sum(1 for r in search_data if r.get('verdict') == 'suspicious')
        clean_count = sum(1 for r in search_data if r.get('verdict') == 'no specific threat')

        # Determine overall verdict and risk level
        if malicious_count > 0:
            overall_verdict = 'malicious'
            risk_level = 'High'
        elif suspicious_count > 0:
            overall_verdict = 'suspicious'
            risk_level = 'Medium'
        elif clean_count > 0:
            overall_verdict = 'clean'
            risk_level = 'Low'
        else:
            overall_verdict = 'unknown'
            risk_level = 'Unknown'

        # Get average threat score
        threat_scores = [r.get('threat_score', 0) for r in search_data if r.get('threat_score') is not None]
        avg_threat_score = sum(threat_scores) / len(threat_scores) if threat_scores else 0

        return {
            'source': 'Hybrid Analysis',
            'data': {
                'total_reports': total_reports,
                'malicious_count': malicious_count,
                'suspicious_count': suspicious_count,
                'clean_count': clean_count,
                'overall_verdict': overall_verdict,
                'risk_level': risk_level,
                'average_threat_score': round(avg_threat_score, 2),
                'ioc_type': ioc_type,
                'analysis_environments': list(set(r.get('environment_description', 'Unknown') for r in search_data)),
                'file_types': list(set(r.get('type_short', 'Unknown') for r in search_data if r.get('type_short'))),
                'latest_analysis': max([r.get('analysis_start_time', '') for r in search_data], default='')
            },
            'link': f"https://www.hybrid-analysis.com/search?query={ioc_value}",
            'timestamp': datetime.now().isoformat()
        }

    def _create_hybrid_analysis_note(self, case_id: int, ioc_value: str, ioc_type: str, search_data: dict,
                                   report_summaries: list, mitre_data: list, ha_handler: HybridAnalysisHandler):
        """
        Create a note in the case with Hybrid Analysis report

        :param case_id: Case ID
        :param ioc_value: IOC value
        :param ioc_type: IOC type
        :param search_data: Search results
        :param report_summaries: Detailed report summaries
        :param mitre_data: MITRE ATT&CK data
        :param ha_handler: Hybrid Analysis handler instance
        """
        try:
            # Import required modules for note creation
            from app.datamgmt.case.case_notes_db import add_note, add_note_group
            from app.models import NoteDirectory
            from app import db
            from sqlalchemy import and_

            # Check if "Hybrid Analysis Reports" directory exists, create if not
            directory = NoteDirectory.query.filter(and_(
                NoteDirectory.case_id == case_id,
                NoteDirectory.name == "Hybrid Analysis Reports"
            )).first()

            if not directory:
                directory = NoteDirectory(
                    name="Hybrid Analysis Reports",
                    case_id=case_id
                )
                db.session.add(directory)
                db.session.commit()
                self.log.info(f"Created Hybrid Analysis Reports directory for case {case_id}")

            # Generate markdown report
            markdown_report = ha_handler.format_report_markdown(
                ioc_value=ioc_value,
                ioc_type=ioc_type,
                search_data=search_data,
                report_summaries=report_summaries,
                mitre_data=mitre_data
            )

            # Create note title with current date
            current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
            note_title = f"Hybrid Analysis Report - {ioc_type.upper()} - {current_date}"

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
                self.log.info(f"Created Hybrid Analysis note '{note_title}' for {ioc_type} {ioc_value} in case {case_id}")
            else:
                self.log.error(f"Failed to create Hybrid Analysis note for {ioc_type} {ioc_value} in case {case_id}")

        except Exception as e:
            self.log.error(f"Error creating Hybrid Analysis note: {str(e)}")
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
        if isinstance(log_line, str) and self.module_dict_conf.get('hybrid_analysis_api_key'):
            return log_line.replace(self.module_dict_conf.get('hybrid_analysis_api_key'), '<api_key>')
        return log_line