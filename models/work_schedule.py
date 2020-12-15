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
            if rec.project_id:
                rec.name = str(rec.employees_ids['employee_id'] + ' / ' + rec.project_id['name'])

    active = fields.Boolean('Active', default=True, track_visibility="onchange", help="If the active field is set to False, it will allow you to hide the project without removing it.")
    name = fields.Char(compute="_get_name_fnc", type="char", store=True)
    type = fields.Selection([('0', 'Office'), ('1', 'Facility')], string='Place of work')
    project_id = fields.Many2one('project.project', string='Project', required=True)
    project_parent = fields.Char(compute='get_project_parent', type="char", string='Project parent', readonly=True, store=True)
    employees_ids = fields.Many2one('hr.employee', domain=([('x_production', '=', True)]), string="Employee", required=True)
    employee_id = fields.Char(compute='_get_employee_picture', readonly=True)
    image = fields.Html(compute="_get_employee_picture", string="Image", readonly=True)
    date_start = fields.Date(string='Date start', index=True, copy=False, required=True)
    date_end = fields.Date(string='Date stop', index=True, copy=False)
    duration = fields.Integer(compute='calc_duration', string='Duration (days)', default='0', store=True, readonly=True)
    notes = fields.Text(string='Note', help='A short note about schedule.')
    involvement_id = fields.Many2one('work_schedule.involvement', string='Involvement', copy=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
        ('done', 'Done'),
        ('cancel', 'Cancel'),
    ], string='State', readonly=True, default='draft')

    @api.constrains('employees_ids', 'project_id', 'date_start', 'date_end')
    def _add_record(self):
        for rec in self:
            if not rec.involvement_id:
                self.involvement_id = self.env["work_schedule.involvement"].create({
                    'name': rec.name,
                    'employee_id': rec.employees_ids.id,
                    'project_id': rec.project_id.id,
                    'date_start': rec.date_start,
                    'date_end': rec.date_end,
                })

            elif rec.employees_ids or rec.project_id or rec.date_start or rec.date_end:
                self.involvement_id.write({
                    'name': rec.name,
                    'employee_id': rec.employees_ids.id,
                    'project_id': rec.project_id.id,
                    'date_start': rec.date_start,
                    'date_end': rec.date_end,
                })

    @api.multi
    def unlink(self):
        resources = self.mapped('involvement_id')
        super(work_schedule, self).unlink()
        return resources.unlink()

    @api.depends('project_id')
    def get_project_parent(self):
        for rec in self:
            if rec.project_id['user_id']:
                rec.project_parent = rec.project_id['user_id']['name']

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

            rec.employee_id = rec.employees_ids['employee_id']

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


class work_schedule_holidays(models.Model):
    _inherit = 'hr.leave'


class work_schedule_involvement(models.Model):
    _name = 'work_schedule.involvement'

    name = fields.Char(string='Name', type="char", store=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    date_start = fields.Date(string='Date start', index=True, copy=False, required=True)
    date_end = fields.Date(string='Date stop', index=True, copy=False)
    project_id = fields.Many2one('project.project', string='Project', required=True)
    status = fields.Selection([
        ('free', 'Free'),
        ('busy', 'Busy')
    ], compute='check_status')

    @api.one
    def check_status(self):
        self.ensure_one()
        data_lst = {}

        for rec in self:
            employees_set = rec.search([('employee_id', '=', rec['employee_id']['name'])])
            data_lst[rec['employee_id']['name']] = {}
            for item in employees_set:
                data_lst[item['employee_id']['name']][item['project_id']] = {}
                data_lst[item['employee_id']['name']][item['project_id']]['date_start'] = item['date_start']
                data_lst[item['employee_id']['name']][item['project_id']]['date_end'] = item['date_end']

        if data_lst:
            for elem in iter(data_lst.items()):
                dict_dates = elem[1].values()
                prev_val = datetime.strptime('2000-01-01', "%Y-%m-%d").date()
                for x in dict_dates:
                    start = datetime.strptime(str(x['date_start']), "%Y-%m-%d").date()
                    end = datetime.strptime(str(x['date_end']), "%Y-%m-%d").date()

                    if (start < prev_val) and prev_val != '2000-01-01':
                        self.status = 'busy'

                    elif start > prev_val:
                        self.status = 'free'
                    prev_val = end
