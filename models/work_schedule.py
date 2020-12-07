#!/usr/bin/env python
# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)


class work_schedule(models.Model):
    _name = 'work_schedule.model'
    _description = 'Work schedule Model'
    _order = 'state desc'

    @api.depends('project_id')
    def _get_name_fnc(self):
        for rec in self:
            rec.name = str(rec.employees_ids['x_user_id'] + ' / ' + rec.project_id['name'])

    active = fields.Boolean('Active', default=True, track_visibility="onchange", help="If the active field is set to False, it will allow you to hide the project without removing it.")
    name = fields.Char(compute="_get_name_fnc", type="char", store=True)
    type = fields.Selection([('0', 'Biuro'), ('1', 'Obiekt')], string='Miejsce wykonywania prac')
    project_id = fields.Many2one('account.analytic.account', string='Project', required=True)
    project_parent = fields.Char(compute='get_project_parent', type="char", string='Project parent', readonly=True, store=True)
    employees_ids = fields.Many2one('hr.employee', domain=([('x_production', '=', True)]), string="Employee", required=True)
    employee_id = fields.Char(compute='_get_employee_picture', readonly=True)
    image = fields.Html(compute="_get_employee_picture", string="Image", readonly=True)
    date_start = fields.Date(string='Date start', select=True, copy=False, required=True)
    date_end = fields.Date(string='Date stop', select=True, copy=False)
    duration = fields.Integer(compute='calc_duration', string='Duration (days)', default='0', store=True, readonly=True)
    notes = fields.Text(string='Note', help='A short note about schedule.')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
        ('done', 'Done'),
        ('cancel', 'Cancel'),
    ], string='Status', readonly=True, default='draft')

    @api.depends('project_id')
    def get_project_parent(self):
        for rec in self:
            if rec.project_id['manager_id']:
                rec.project_parent = rec.project_id['manager_id']['name']

    @api.depends('employees_ids')
    def _get_employee_picture(self):
        for rec in self:
            if rec.employees_ids['image']:
                rec.image = """
                            <div aria-atomic="true" class="o_field_image o_field_widget oe_avatar" name="image" data-original-title="" title="">
                                <img class='img img-fluid' name='image' src='/web/image/hr.employee/%s/image' border='1'>
                            </div>
                            """ % rec.employees_ids['id']

            else:
                rec.image = """
                            <div class="oe_form_field oe_form_field_html_text o_field_widget o_readonly_modifier oe_avatar" name="image" data-original-title="" title="">
                                 <img class="img img-fluid" name="image" src="/web/image/default_image.png" border="1">
                            </div>"""

            rec.employee_id = rec.employees_ids['x_user_id']

    def action_involvement_confirm(self):
        if self.employees_ids and self.project_id and self.date_start:
            self.ensure_one()
            self.write({'state': 'confirm'})

    def action_involvement_done(self):
        if self.employees_ids and self.project_id and self.date_start:
            self.ensure_one()
            self.write({'state': 'done'})

    def action_involvement_draft(self):
        if self.employees_ids and self.project_id and self.date_start:
            self.ensure_one()
            self.write({'state': 'draft'})

    def action_involvement_refuse(self):
        if self.employees_ids and self.project_id and self.date_start:
            self.ensure_one()
            self.write({'state': 'cancel'})

    @api.depends('date_start', 'date_end')
    def calc_duration(self):
        for rec in self:
            if rec.date_start and rec.date_end:
                date_format = "%Y-%m-%d"
                a = datetime.strptime(str(rec.date_start), date_format)
                b = datetime.strptime(str(rec.date_end), date_format)
                delta = b - a
                rec.duration = delta.days

    # def get_emp_timesheet(self):


# class hr_timesheets_lines(models.Model):
#     _name = 'hr_timesheets.lines'
#     _description = 'HR Timesheets Lines'
#     _inherit = ['hr_timesheet.sheet']
#
#     employee_id = fields.Many2one('hr_timesheet.sheet')
