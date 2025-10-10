#!/usr/bin/env python3

#  IRIS URLScan.io Module Source Code
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

import iris_urlscan_module.IrisURLScanConfig as interface_conf
from iris_urlscan_module.urlscan_handler.urlscan_handler import URLScanHandler


class IrisURLScanInterface(IrisModuleInterface):
    name = "IrisURLScanInterface"
    _module_name = interface_conf.module_name
    _module_description = interface_conf.module_description
    _interface_version = interface_conf.interface_version
    _module_version = interface_conf.module_version
    _pipeline_support = interface_conf.pipeline_support
    _pipeline_info = interface_conf.pipeline_info
    _module_configuration = interface_conf.module_configuration
    _module_type = IrisModuleTypes.module_processor

    def register_hooks(self, module_id: int):
        self.module_id = module_id
        module_conf = self.module_dict_conf

        if module_conf.get('urlscan_on_create_hook_enabled'):
            status = self.register_to_hook(module_id, iris_hook_name='on_postload_ioc_create')
            if status.is_failure():
                self.log.error(status.get_message())
                self.log.error(status.get_data())
            else:
                self.log.info("Successfully registered on_postload_ioc_create hook")
        else:
            self.deregister_from_hook(module_id=self.module_id, iris_hook_name='on_postload_ioc_create')

        if module_conf.get('urlscan_on_update_hook_enabled'):
            status = self.register_to_hook(module_id, iris_hook_name='on_postload_ioc_update')
            if status.is_failure():
                self.log.error(status.get_message())
                self.log.error(status.get_data())
            else:
                self.log.info("Successfully registered on_postload_ioc_update hook")
        else:
            self.deregister_from_hook(module_id=self.module_id, iris_hook_name='on_postload_ioc_update')

        if module_conf.get('urlscan_manual_hook_enabled'):
            status = self.register_to_hook(module_id, iris_hook_name='on_manual_trigger_ioc',
                                           manual_hook_name='Get URLScan.io insight')
            if status.is_failure():
                self.log.error(status.get_message())
                self.log.error(status.get_data())
            else:
                self.log.info("Successfully registered on_manual_trigger_ioc hook")
        else:
            self.deregister_from_hook(module_id=self.module_id, iris_hook_name='on_manual_trigger_ioc')

    def hooks_handler(self, hook_name: str, hook_ui_name: str, data: any):
        self.log.info(f'Received {hook_name}')

        if hook_name in ['on_postload_ioc_create', 'on_postload_ioc_update', 'on_manual_trigger_ioc']:
            return self._handle_ioc_enrichment(data=data, hook_name=hook_name)

        return InterfaceStatus.I2Error(data=data, logs=list(self.message_queue))

    def _handle_ioc_enrichment(self, data, hook_name):
        try:
            self.log.info(f"Processing IOC enrichment for hook {hook_name}")

            if isinstance(data, list):
                if not data:
                    return InterfaceStatus.I2Error(data=data, logs=["Empty data list provided"])
                ioc_obj = data[0]
            else:
                ioc_obj = data

            if hasattr(ioc_obj, 'ioc_value'):
                ioc_value = ioc_obj.ioc_value
                ioc_type = getattr(ioc_obj.ioc_type, 'type_name', '').lower() if hasattr(ioc_obj, 'ioc_type') else ''
                case_id = getattr(self, 'case_id', None) or self._get_case_id_from_session()
            elif isinstance(ioc_obj, dict):
                ioc_value = ioc_obj.get('ioc_value')
                ioc_type = ioc_obj.get('ioc_type_name', '').lower()
                case_id = ioc_obj.get('case_id') or getattr(self, 'case_id', None) or self._get_case_id_from_session()
            else:
                return InterfaceStatus.I2Error(data=data, logs=["Unknown data format provided"])

            if not ioc_value:
                return InterfaceStatus.I2Error(data=data, logs=["No IOC value provided"])

            api_key = self.module_dict_conf.get('urlscan_api_key')
            visibility = self.module_dict_conf.get('urlscan_visibility', 'unlisted')
            timeout = self.module_dict_conf.get('urlscan_timeout', 120)
            auto_create_notes = self.module_dict_conf.get('urlscan_auto_create_notes', True)

            if not api_key:
                return InterfaceStatus.I2Error(data=data, logs=["URLScan.io API key not configured"])

            urlscan_handler = URLScanHandler(
                api_key=api_key,
                visibility=visibility,
                timeout=timeout
            )

            detected_ioc_type = urlscan_handler.determine_ioc_type(ioc_value)

            if detected_ioc_type not in ['url', 'domain']:
                self.log.info(f"Skipping unsupported IOC type: {ioc_value} (type: {detected_ioc_type})")
                return InterfaceStatus.I2Success(data=data)

            self.log.info(f"Analyzing URL/Domain: {ioc_value} (detected type: {detected_ioc_type})")

            analysis_result = urlscan_handler.analyze_url(ioc_value)

            if not analysis_result.get('success'):
                error_msg = f"URLScan.io analysis failed: {analysis_result.get('error')}"
                self.log.error(error_msg)
                return InterfaceStatus.I2Error(data=data, logs=[error_msg])

            scan_data = analysis_result.get('data', {})
            intelligence_data = urlscan_handler.extract_intelligence_data(scan_data)
            screenshot_b64 = scan_data.get('screenshot_base64')

            enrichment_data = self._generate_enrichment_data(intelligence_data, detected_ioc_type, ioc_value)

            if auto_create_notes and case_id:
                try:
                    self._create_urlscan_note(
                        case_id=case_id,
                        ioc_value=ioc_value,
                        ioc_type=detected_ioc_type,
                        intelligence_data=intelligence_data,
                        screenshot_b64=screenshot_b64,
                        urlscan_handler=urlscan_handler
                    )
                except Exception as e:
                    self.log.error(f"Failed to create URLScan.io note: {str(e)}")

            self.log.info(f"Successfully enriched IOC {ioc_value} with URLScan.io data")

            return InterfaceStatus.I2Success(data=enrichment_data)

        except Exception as e:
            trace = traceback.format_exc()
            self.log.error(trace)
            return InterfaceStatus.I2Error(data=data, logs=[f"Unexpected error: {str(e)}"])

    def _generate_enrichment_data(self, intelligence_data: dict, ioc_type: str, ioc_value: str) -> dict:
        return {
            'source': 'URLScan.io',
            'data': {
                'overall_verdict': intelligence_data.get('overall_verdict', 'Unknown'),
                'final_url': intelligence_data.get('final_url', ioc_value),
                'domain': intelligence_data.get('domain', 'Unknown'),
                'title': intelligence_data.get('title', 'No title'),
                'ip_address': intelligence_data.get('ip_address', 'Unknown'),
                'country': intelligence_data.get('country', 'Unknown'),
                'city': intelligence_data.get('city', 'Unknown'),
                'asn': intelligence_data.get('asn', 'Unknown'),
                'server': intelligence_data.get('server', 'Unknown'),
                'domain_age': intelligence_data.get('domain_age', 'Unknown'),
                'brands': intelligence_data.get('brands', []),
                'technologies': intelligence_data.get('technologies', []),
                'screenshot_available': intelligence_data.get('screenshot_available', False),
                'scan_time': intelligence_data.get('scan_time', datetime.now().isoformat()),
                'ioc_type': ioc_type
            },
            'link': f"https://urlscan.io/search/#{ioc_value}",
            'timestamp': datetime.now().isoformat()
        }

    def _create_urlscan_note(self, case_id: int, ioc_value: str, ioc_type: str, intelligence_data: dict,
                           screenshot_b64: str, urlscan_handler: URLScanHandler):
        try:
            from app.datamgmt.case.case_notes_db import add_note
            from app.models import NoteDirectory
            from app import db
            from sqlalchemy import and_

            directory = NoteDirectory.query.filter(and_(
                NoteDirectory.case_id == case_id,
                NoteDirectory.name == "URLScan.io Reports"
            )).first()

            if not directory:
                directory = NoteDirectory(
                    name="URLScan.io Reports",
                    case_id=case_id
                )
                db.session.add(directory)
                db.session.commit()
                self.log.info(f"Created URLScan.io Reports directory for case {case_id}")

            markdown_report = urlscan_handler.format_report_markdown(
                url=ioc_value,
                intelligence_data=intelligence_data,
                screenshot_b64=screenshot_b64
            )

            current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
            note_title = f"URLScan.io Report - {ioc_type.upper()} - {current_date}"

            note = add_note(
                note_title=note_title,
                creation_date=datetime.now(),
                user_id=1,
                caseid=case_id,
                directory_id=directory.id,
                note_content=markdown_report
            )

            if note:
                self.log.info(f"Created URLScan.io note '{note_title}' for {ioc_type} {ioc_value} in case {case_id}")
            else:
                self.log.error(f"Failed to create URLScan.io note for {ioc_type} {ioc_value} in case {case_id}")

        except Exception as e:
            self.log.error(f"Error creating URLScan.io note: {str(e)}")

    def _get_case_id_from_session(self):
        try:
            from flask import g
            if hasattr(g, 'case_id'):
                return g.case_id
            return 1
        except:
            return 1

    def _sanitize_log_output(self, log_line):
        if isinstance(log_line, str) and self.module_dict_conf.get('urlscan_api_key'):
            return log_line.replace(self.module_dict_conf.get('urlscan_api_key'), '<api_key>')
        return log_line