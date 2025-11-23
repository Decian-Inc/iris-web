#  IRIS Source Code
#  Copyright (C) 2021 - Airbus CyberSecurity (SAS)
#  ir@cyberactionlab.net
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

import datetime

import traceback
from flask import Blueprint
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask import send_file
from flask import make_response
from flask_login import current_user
from flask_wtf import FlaskForm
from marshmallow import ValidationError
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

from app import ac_current_user_has_permission
from app.datamgmt.client.client_db import create_client
from app.datamgmt.client.client_db import create_contact
from app.datamgmt.client.client_db import delete_client
from app.datamgmt.client.client_db import delete_contact
from app.datamgmt.client.client_db import get_client
from app.datamgmt.client.client_db import get_client_api
from app.datamgmt.client.client_db import get_client_cases
from app.datamgmt.client.client_db import get_client_contact
from app.datamgmt.client.client_db import get_client_contacts
from app.datamgmt.client.client_db import get_client_list
from app.datamgmt.client.client_db import update_client
from app.datamgmt.client.client_db import update_contact
from app.datamgmt.exceptions.ElementExceptions import ElementInUseException
from app.datamgmt.exceptions.ElementExceptions import ElementNotFoundException
from app.datamgmt.manage.manage_attribute_db import get_default_custom_attributes
from app.datamgmt.manage.manage_users_db import add_user_to_customer
from app.forms import AddCustomerForm
from app.forms import ContactForm
from app.iris_engine.utils.tracker import track_activity
from app.models.authorization import Permissions
from app.schema.marshables import ContactSchema
from app.schema.marshables import CustomerSchema
from app.util import ac_api_requires
from app.util import ac_api_requires_client_access
from app.util import ac_requires_client_access
from app.util import ac_requires
from app.util import page_not_found
from app.util import response_error
from app.util import response_success

manage_customers_blueprint = Blueprint(
    'manage_customers',
    __name__,
    template_folder='templates'
)


# CONTENT ------------------------------------------------
@manage_customers_blueprint.route('/manage/customers')
@ac_requires(Permissions.customers_read, no_cid_required=True)
def manage_customers(caseid, url_redir):
    if url_redir:
        return redirect(url_for('manage_customers.manage_customers', cid=caseid))

    form = AddCustomerForm()

    # Return default page of case management
    return render_template('manage_customers.html', form=form)


@manage_customers_blueprint.route('/manage/customers/list')
@ac_api_requires(Permissions.customers_read)
def list_customers():
    user_is_server_administrator = ac_current_user_has_permission(Permissions.server_administrator)
    client_list = get_client_list(current_user_id=current_user.id,
                                  is_server_administrator=user_is_server_administrator)

    return response_success("", data=client_list)


@manage_customers_blueprint.route('/manage/customers/<int:client_id>', methods=['GET'])
@ac_api_requires(Permissions.customers_read)
@ac_api_requires_client_access()
def view_customer(client_id):

    customer = get_client_api(client_id)

    customer['contacts'] = ContactSchema().dump(get_client_contacts(client_id), many=True)

    return response_success(data=customer)


@manage_customers_blueprint.route('/manage/customers/<int:client_id>/view', methods=['GET'])
@ac_requires(Permissions.customers_read, no_cid_required=True)
@ac_requires_client_access()
def view_customer_page(client_id, caseid, url_redir):
    if url_redir:
        return redirect(url_for('manage_customers.manage_customers', cid=caseid))

    customer = get_client_api(client_id)
    if not customer:
        return page_not_found(None)

    form = FlaskForm()
    contacts = get_client_contacts(client_id)
    contacts = ContactSchema().dump(contacts, many=True)

    return render_template('manage_customer_view.html', customer=customer, form=form, contacts=contacts)


@manage_customers_blueprint.route('/manage/customers/<int:client_id>/contacts/add/modal', methods=['GET'])
@ac_requires(Permissions.customers_write, no_cid_required=True)
@ac_requires_client_access()
def customer_add_contact_modal(client_id, caseid, url_redir):
    if url_redir:
        return redirect(url_for('manage_customers.manage_customers', cid=caseid))

    form = ContactForm()

    return render_template('modal_customer_add_contact.html', form=form, contact=None)


@manage_customers_blueprint.route('/manage/customers/<int:client_id>/contacts/<int:contact_id>/modal', methods=['GET'])
@ac_requires(Permissions.customers_read, no_cid_required=True)
@ac_requires_client_access()
def customer_edit_contact_modal(client_id, contact_id, caseid, url_redir):
    if url_redir:
        return redirect(url_for('manage_customers.manage_customers', cid=caseid))

    contact = get_client_contact(client_id, contact_id)
    if not contact:
        return response_error(f"Invalid Contact ID {contact_id}")

    form = ContactForm()
    form.contact_name.render_kw = {'value': contact.contact_name}
    form.contact_email.render_kw = {'value':  contact.contact_email}
    form.contact_mobile_phone.render_kw = {'value': contact.contact_mobile_phone}
    form.contact_work_phone.render_kw = {'value': contact.contact_work_phone}
    form.contact_note.data = contact.contact_note
    form.contact_role.render_kw = {'value':  contact.contact_role}

    return render_template('modal_customer_add_contact.html', form=form, contact=contact)


@manage_customers_blueprint.route('/manage/customers/<int:client_id>/contacts/<int:contact_id>/update', methods=['POST'])
@ac_api_requires(Permissions.customers_write)
@ac_api_requires_client_access()
def customer_update_contact(client_id, contact_id):

    if not request.is_json:
        return response_error("Invalid request")

    if not get_client(client_id):
        return response_error(f"Invalid Customer ID {client_id}")

    try:

        contact = update_contact(request.json, contact_id, client_id)

    except ValidationError as e:
        return response_error(msg='Error update contact', data=e.messages)

    except Exception as e:
        print(traceback.format_exc())
        return response_error(f'An error occurred during contact update. {e}')

    track_activity(f"Updated contact {contact.contact_name}", ctx_less=True)

    # Return the customer
    contact_schema = ContactSchema()
    return response_success("Added successfully", data=contact_schema.dump(contact))


@manage_customers_blueprint.route('/manage/customers/<int:client_id>/contacts/add', methods=['POST'])
@ac_api_requires(Permissions.customers_write)
@ac_api_requires_client_access()
def customer_add_contact(client_id):

    if not request.is_json:
        return response_error("Invalid request")

    if not get_client(client_id):
        return response_error(f"Invalid Customer ID {client_id}")

    try:

        contact = create_contact(request.json, client_id)

    except ValidationError as e:
        return response_error(msg='Error adding contact', data=e.messages)

    except Exception as e:
        print(traceback.format_exc())
        return response_error(f'An error occurred during contact addition. {e}')

    track_activity(f"Added contact {contact.contact_name}", ctx_less=True)

    # Return the customer
    contact_schema = ContactSchema()
    return response_success("Added successfully", data=contact_schema.dump(contact))


@manage_customers_blueprint.route('/manage/customers/<int:client_id>/cases', methods=['GET'])
@ac_api_requires(Permissions.customers_read)
@ac_api_requires_client_access()
def get_customer_case_stats(client_id):

    cases = get_client_cases(client_id)
    cases_list = []

    now = datetime.date.today()
    cases_stats = {
        'cases_last_month': 0,
        'cases_last_year': 0,
        'open_cases': 0,
        'last_year': now.year - 1,
        'last_month': now.month - 1,
        'cases_rolling_week': 0,
        'cases_current_month': 0,
        'cases_current_year': 0,
        'ratio_year': 0,
        'ratio_month': 0,
        'average_case_duration': 0,
        'cases_total': len(cases)
    }

    last_month_start = datetime.date.today() - datetime.timedelta(days=30)
    last_month_end = datetime.date(now.year, now.month, 1)

    last_year_start = datetime.date(now.year - 1, 1, 1)
    last_year_end = datetime.date(now.year - 1, 12, 31)
    this_year_start = datetime.date(now.year, 1, 1)
    this_month_start = datetime.date(now.year, now.month, 1)

    for case in cases:
        cases_list.append(case._asdict())
        if now - datetime.timedelta(days=7) <= case.open_date <= now:
            cases_stats['cases_rolling_week'] += 1

        if this_month_start <= case.open_date <= now:
            cases_stats['cases_current_month'] += 1

        if this_year_start <= case.open_date <= now:
            cases_stats['cases_current_year'] += 1

        if last_month_start < case.open_date < last_month_end:
            cases_stats['cases_last_month'] += 1

        if last_year_start <= case.open_date <= last_year_end:
            cases_stats['cases_last_year'] += 1

        if case.close_date is None:
            cases_stats['open_cases'] += 1

        if cases_stats['cases_last_year'] == 0:
            st = 1
            et = cases_stats['cases_current_year'] + 1
        else:
            st = cases_stats['cases_last_year']
            et = cases_stats['cases_current_year']

        cases_stats['ratio_year'] = ((et - st)/(st)) * 100

        if cases_stats['cases_last_month'] == 0:
            st = 1
            et = cases_stats['cases_current_month'] + 1
        else:
            st = cases_stats['cases_last_month']
            et = cases_stats['cases_current_month']

        cases_stats['ratio_month'] = ((et - st)/(st)) * 100

        if (case.close_date is not None) and (case.open_date is not None):
            cases_stats['average_case_duration'] += (case.close_date - case.open_date).days

    if cases_stats['cases_total'] > 0 and cases_stats['open_cases'] > 0 and cases_stats['average_case_duration'] > 0:
        cases_stats['average_case_duration'] = cases_stats['average_case_duration'] / (cases_stats['cases_total'] - cases_stats['open_cases'])

    cases = {
        'cases': cases_list,
        'stats': cases_stats
    }

    return response_success(data=cases)


@manage_customers_blueprint.route('/manage/customers/update/<int:client_id>/modal', methods=['GET'])
@ac_requires(Permissions.customers_read, no_cid_required=True)
@ac_requires_client_access()
def view_customer_modal(client_id, caseid, url_redir):
    if url_redir:
        return redirect(url_for('manage_customers.manage_customers', cid=caseid))

    form = AddCustomerForm()
    customer = get_client(client_id)
    if not customer:
        return response_error("Invalid Customer ID")

    form.customer_name.render_kw = {'value': customer.name}
    form.customer_description.data = customer.description
    form.customer_sla.data = customer.sla

    return render_template("modal_add_customer.html", form=form, customer=customer,
                           attributes=customer.custom_attributes)


@manage_customers_blueprint.route('/manage/customers/update/<int:client_id>', methods=['POST'])
@ac_api_requires(Permissions.customers_write)
@ac_api_requires_client_access()
def view_customers(client_id):
    if not request.is_json:
        return response_error("Invalid request")

    try:
        client = update_client(client_id, request.json)

    except ElementNotFoundException:
        return response_error('Invalid Customer ID')

    except ValidationError as e:
        return response_error("", data=e.messages)

    except Exception as e:
        print(traceback.format_exc())
        return response_error(f'An error occurred during Customer update. {e}')

    client_schema = CustomerSchema()
    return response_success("Customer updated", client_schema.dump(client))


@manage_customers_blueprint.route('/manage/customers/add/modal', methods=['GET'])
@ac_requires(Permissions.customers_read, no_cid_required=True)
def add_customers_modal(caseid, url_redir):
    if url_redir:
        return redirect(url_for('manage_customers.manage_customers', cid=caseid))
    form = AddCustomerForm()
    attributes = get_default_custom_attributes('client')
    return render_template("modal_add_customer.html", form=form, customer=None, attributes=attributes)


@manage_customers_blueprint.route('/manage/customers/add', methods=['POST'])
@ac_api_requires(Permissions.customers_write)
def add_customers():
    if not request.is_json:
        return response_error("Invalid request")

    try:
        client = create_client(request.json)
    except ValidationError as e:
        return response_error(msg='Error adding customer', data=e.messages)
    except Exception as e:
        print(traceback.format_exc())
        return response_error(f'An error occurred during customer addition. {e}')

    track_activity(f"Added customer {client.name}", ctx_less=True)

    # Associate the created customer with the current user
    add_user_to_customer(current_user.id, client.client_id)

    # Return the customer
    client_schema = CustomerSchema()
    return response_success("Added successfully", data=client_schema.dump(client))


@manage_customers_blueprint.route('/manage/customers/delete/<int:client_id>', methods=['POST'])
@ac_api_requires(Permissions.customers_write)
@ac_api_requires_client_access()
def delete_customers(client_id):
    try:

        delete_client(client_id)

    except ElementNotFoundException:
        return response_error('Invalid Customer ID')

    except ElementInUseException:
        return response_error('Cannot delete a referenced customer')

    except Exception:
        return response_error('An error occurred during customer deletion')

    track_activity(f"Deleted Customer with ID {client_id}", ctx_less=True)

    return response_success("Deleted successfully")


@manage_customers_blueprint.route('/manage/customers/<int:client_id>/contacts/<int:contact_id>/delete', methods=['POST'])
@ac_api_requires(Permissions.customers_write)
@ac_api_requires_client_access()
def delete_contact_route(client_id, contact_id):
    try:

        delete_contact(contact_id)

    except ElementNotFoundException:
        return response_error('Invalid contact ID')

    except ElementInUseException:
        return response_error('Cannot delete a referenced contact')

    except Exception:
        return response_error('An error occurred during contact deletion')

    track_activity(f"Deleted Customer with ID {contact_id}", ctx_less=True)

    return response_success("Deleted successfully")


def generate_customer_activity_report(client_id):
    """
    Generate a professional PDF report for customer activity using Decian Ironclad design.
    Includes consistent blue/black/white color palette, styled tables, and KPI summary.
    """

    # ─────────────────────────── DATA ───────────────────────────
    customer = get_client_api(client_id)
    if not customer:
        return None

    cases_data = get_client_cases(client_id)

    now = datetime.date.today()
    last_month_start = now - datetime.timedelta(days=30)
    past_month_cases = [c for c in cases_data if c.open_date >= last_month_start]

    total_cases = len(cases_data)
    recent_cases = len(past_month_cases)
    open_cases = len([c for c in cases_data if c.close_date is None])

    # ─────────────────────────── PDF SETUP ───────────────────────────
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=50, bottomMargin=40)

    styles = getSampleStyleSheet()

    # Custom brand colors
    DARK_BLUE = colors.HexColor("#0E1F44")
    LIGHT_BLUE = colors.HexColor("#D9E3F0")
    BLACK = colors.HexColor("#000000")

    # ─────────────────────────── STYLES ───────────────────────────
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontSize=20,
        textColor=DARK_BLUE,
        alignment=1,
        spaceAfter=20
    )

    section_header = ParagraphStyle(
        "SectionHeader",
        parent=styles["Heading2"],
        fontSize=14,
        textColor=DARK_BLUE,
        spaceBefore=10,
        spaceAfter=10
    )

    normal = ParagraphStyle(
        "NormalText",
        parent=styles["Normal"],
        fontSize=10,
        textColor=BLACK,
        leading=14
    )

    bold = ParagraphStyle(
        "BoldText",
        parent=styles["Normal"],
        fontSize=10,
        textColor=BLACK,
        leading=14
    )
    bold.fontName = "Helvetica-Bold"

    # ─────────────────────────── CONTENT ───────────────────────────
    story = []
    story.append(Paragraph("Customer Activity Report", title_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph(f"<b>{customer['customer_name']}</b> (#{customer['customer_id']})", bold))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        f"Report Generated: {now.strftime('%B %d, %Y')}<br/>"
        f"Period: Past 30 days ({last_month_start.strftime('%B %d, %Y')} - {now.strftime('%B %d, %Y')})",
        normal
    ))
    story.append(Spacer(1, 20))

    # ─────────────────────────── CUSTOMER OVERVIEW ───────────────────────────
    story.append(Paragraph("Customer Overview", section_header))
    overview_data = [
        ["Customer Name:", customer["customer_name"]],
        ["Customer ID:", f"#{customer['customer_id']}"],
        ["Description:", customer.get("customer_description", "N/A")],
        ["SLA:", customer.get("customer_sla", "N/A")]
    ]
    overview_table = Table(overview_data, colWidths=[1.5 * inch, 4.5 * inch])
    overview_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), LIGHT_BLUE),
        ("TEXTCOLOR", (0, 0), (-1, -1), BLACK),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(overview_table)
    story.append(Spacer(1, 20))

    # ─────────────────────────── CASE SUMMARY KPI BLOCKS ───────────────────────────
    story.append(Paragraph("Cases Summary – Past 30 Days", section_header))
    kpi_data = [
        [
            Paragraph("<b>Total Cases (All Time)</b>", normal),
            Paragraph("<b>Cases Opened (Past 30 Days)</b>", normal),
            Paragraph("<b>Currently Open Cases</b>", normal)
        ],
        [
            Paragraph(str(total_cases), bold),
            Paragraph(str(recent_cases), bold),
            Paragraph(str(open_cases), bold)
        ]
    ]
    kpi_table = Table(kpi_data, colWidths=[2 * inch, 2 * inch, 2 * inch])
    kpi_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), LIGHT_BLUE),
        ("TEXTCOLOR", (0, 0), (-1, -1), BLACK),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 20))

    # ─────────────────────────── RECENT CASES TABLE ───────────────────────────
    if past_month_cases:
        story.append(Paragraph("Cases Opened in Past 30 Days", section_header))
        case_data = [["Case Name", "Open Date", "Case ID", "Owner"]]

        for case in past_month_cases:
            case_data.append([
                case.case_name,
                case.open_date.strftime('%Y-%m-%d'),
                f"#{case.case_id}",
                case.case_owner
            ])

        case_table = Table(case_data, colWidths=[3 * inch, 1.2 * inch, 1 * inch, 1.3 * inch])
        case_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), DARK_BLUE),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("TEXTCOLOR", (0, 1), (-1, -1), BLACK),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(case_table)
    else:
        story.append(Paragraph("No cases opened in the past 30 days.", normal))
    story.append(Spacer(1, 30))

    # ─────────────────────────── FOOTER ───────────────────────────
    footer_text = Paragraph(
        '<para align="center">'
        '<font size="9" color="#0E1F44">'
        'This report was generated automatically by Decian Ironclad Case Management System.'
        '</font></para>',
        styles["Normal"]
    )
    story.append(footer_text)

    # ─────────────────────────── BUILD PDF ───────────────────────────
    doc.build(story)
    buffer.seek(0)
    return buffer


@manage_customers_blueprint.route('/manage/customers/<int:client_id>/report/download', methods=['GET'])
@ac_requires(Permissions.customers_read, no_cid_required=True)
@ac_requires_client_access()
def download_customer_report(client_id, caseid, url_redir):
    """Download customer activity report as PDF"""
    if url_redir:
        return redirect(url_for('manage_customers.manage_customers', cid=caseid))

    try:
        pdf_buffer = generate_customer_activity_report(client_id)
        if not pdf_buffer:
            return response_error("Could not generate report - customer not found")

        customer = get_client_api(client_id)
        filename = f"customer_{client_id}_{customer['customer_name'].replace(' ', '_')}_activity_report.pdf"

        track_activity(f"Downloaded customer activity report for {customer['customer_name']}", ctx_less=True)

        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )

    except Exception as e:
        print(traceback.format_exc())
        return response_error(f"Error generating report: {str(e)}")


@manage_customers_blueprint.route('/manage/customers/<int:client_id>/report/preview', methods=['GET'])
@ac_requires(Permissions.customers_read, no_cid_required=True)
@ac_requires_client_access()
def preview_customer_report(client_id, caseid, url_redir):
    """Preview customer activity report in browser"""
    if url_redir:
        return redirect(url_for('manage_customers.manage_customers', cid=caseid))

    try:
        pdf_buffer = generate_customer_activity_report(client_id)
        if not pdf_buffer:
            return response_error("Could not generate report - customer not found")

        customer = get_client_api(client_id)
        filename = f"customer_{client_id}_{customer['customer_name'].replace(' ', '_')}_activity_report.pdf"

        track_activity(f"Previewed customer activity report for {customer['customer_name']}", ctx_less=True)

        response = make_response(pdf_buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename="{filename}"'
        return response

    except Exception as e:
        print(traceback.format_exc())
        return response_error(f"Error generating report: {str(e)}")
