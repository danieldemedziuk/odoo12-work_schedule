#!/usr/bin/env python
# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError, ValidationError
import logging
import re

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
    type = fields.Selection([(0, 'Office'), (1, 'Facility')], default=0, string='Place of work')
    project_id = fields.Many2one('project.project', string='Project', required=True)
    project_parent = fields.Char(compute='get_project_parent', type="char", string='Project parent', readonly=True, store=True)
    employees_ids = fields.Many2one('hr.employee', string="Employee", required=True)
    employee_id = fields.Char(compute='_get_employee_picture', string="Name", readonly=True)
    image = fields.Html(compute="_get_employee_picture", string="Image", readonly=True)
    date_start = fields.Date(string='Date start', index=True, copy=False, required=True)
    date_end = fields.Date(string='Date stop', index=True, copy=False)
    duration = fields.Integer(compute='calc_duration', string='Duration (days)', default='0', store=True, readonly=True)
    notes = fields.Text(string='Note', help='A short note about schedule.')
    involvement_id = fields.Many2one('work_schedule.involvement', string='Involvement', copy=False)
    department = fields.Char(compute='_get_employee_picture', string="Department", readonly=True, store=True)
    holiday = fields.Many2one('hr.leave', string="Holiday")
    state = fields.Selection([('temp', 'Temporary'), ('regular', 'Regular')], default='regular', string='State', readonly=True)

    # state = fields.Selection([
    #     ('draft', 'Draft'),
    #     ('confirm', 'Confirm'),
    #     ('done', 'Done'),
    #     ('cancel', 'Cancel'),
    # ], string='State', readonly=True, default='draft')

    @api.constrains('employees_ids', 'project_id', 'date_start', 'date_end')
    def _add_record(self):
        for rec in self:
            if not rec.involvement_id:
                self.involvement_id = self.env["work_schedule.involvement"].create({
                    'name': rec.name,
                    'schedule_ids': rec.id,
                    'employee_id': rec.employees_ids.id,
                    'project_id': rec.project_id.id,
                    'date_start': rec.date_start,
                    'date_end': rec.date_end,
                })

            elif rec.employees_ids or rec.project_id or rec.date_start or rec.date_end:
                self.involvement_id.write({
                    'name': rec.name,
                    'schedule_ids': rec.id,
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
            if rec.employees_ids['department_id']:
                rec.department = rec.employees_ids['department_id']['name']
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

    @api.constrains('active')
    def _archive_project(self):
        for rec in self:
            if not rec.active:
                self.involvement_id.write({
                    'active': False,
                })
            if rec.active:
                self.involvement_id.write({
                    'active': True,
                })

    @api.depends('date_start', 'date_end')
    def calc_duration(self):
        for rec in self:
            if rec.date_start and rec.date_end:
                date_format = "%Y-%m-%d"
                a = datetime.strptime(str(rec.date_start), date_format)
                b = datetime.strptime(str(rec.date_end), date_format)
                delta = b - a
                rec.duration = delta.days + 1

    @api.one
    @api.constrains('date_start', 'date_end')
    def _check_availability(self):
        for rec in self:
            holiday_ids = rec.holiday.search([('employee_id', '=', rec.employees_ids.id)])

            for req in holiday_ids:
                if rec.date_end >= req['request_date_from'] and rec.date_start <= req['request_date_to'] and req['state'] == 'validate':
                    raise ValidationError(_("Warning! The employee is on leave at this time. Verify the employee's leave and select other dates."))

    @api.multi
    def set_default_fnc(self):
        for proj_id in self.env['project.project'].search([('active', '=', True)]):
            project_format = re.compile('.*.*-.*.*.*.*')
            if project_format.match(proj_id['name']):
                if not self.env['work_schedule.model'].search([('project_id', '=', proj_id.id)]):
                    vals = {
                        'project_id': proj_id.id,
                        'employees_ids': 1,
                        'date_start': '2020-12-31',
                        'date_end': '2021-01-01',
                        'notes': 'DEFAULT PROJECT',
                        'state': 'temp',
                    }

                    self.env['work_schedule.model'].create([vals])

        return {
            'name': 'Work schedule',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'timeline,tree,form',
            'res_model': 'work_schedule.model',
        }


class work_schedule_holidays(models.Model):
    _inherit = 'hr.leave'

    work_schedule_id = fields.Many2one('work_schedule.model', string="Work Schedule")

    @api.multi
    def action_approve(self):
        for rec in self:
            work_ids = rec.work_schedule_id.search([('employees_ids', '=', rec.employee_id.id)])

            for req in work_ids:
                if rec.request_date_from <= req['date_end'] and rec.request_date_to >= req['date_start']:
                    raise UserError(_("This employee is assigned to a project on these days in the schedule. Contact your manager or administrator with the error code. \n\nError code: Collision of leave with work schedule."))

        # if validation_type == 'both': this method is the first approval approval
        # if validation_type != 'both': this method calls action_validate() below
        if any(holiday.state != 'confirm' for holiday in self):
            raise UserError(_('Leave request must be confirmed ("To Approve") in order to approve it.'))

        current_employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        self.filtered(lambda hol: hol.validation_type == 'both').write({'state': 'validate1', 'first_approver_id': current_employee.id})
        self.filtered(lambda hol: not hol.validation_type == 'both').action_validate()
        if not self.env.context.get('leave_fast_create'):
            self.activity_update()
        return True


class work_schedule_involvement(models.Model):
    _name = 'work_schedule.involvement'
    _description = 'Work schedule Involvement'

    name = fields.Char(string='Name', type="char", store=True)
    active = fields.Boolean('Active', default=True, track_visibility="onchange", help="If the active field is set to False, it will allow you to hide the project without removing it.")
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    date_start = fields.Date(string='Date start', index=True, copy=False, required=True)
    date_end = fields.Date(string='Date stop', index=True, copy=False)
    project_id = fields.Many2one('project.project', string='Project', required=True)
    schedule_ids = fields.Many2one('work_schedule.model', string='Schedule model')
    status = fields.Selection([
        ('free', 'Free'),
        ('busy', 'Busy')
    ], default='free', compute='check_status')

    @api.multi
    def check_status(self):
        # self.ensure_one()
        data_lst = {}
        for rec in self:
            employees_set = rec.search([('employee_id', '=', rec['employee_id']['name'])], order="date_start asc")
            data_lst[rec['employee_id']['name']] = {}
            for item in employees_set:
                data_lst[item['employee_id']['name']][item['project_id']] = {}
                data_lst[item['employee_id']['name']][item['project_id']]['date_start'] = item['date_start']
                data_lst[item['employee_id']['name']][item['project_id']]['date_end'] = item['date_end']

        if data_lst:
            prev_name = ''
            for elem in data_lst.items():
                dict_dates = elem[1].values()
                prev_val = datetime

                for proj in elem[1].keys():
                    # for dates in dict_dates:
                    curr_involv = self.search([('employee_id', '=', elem[0]), ('project_id', '=', proj.id)])

                    if prev_name != elem[0] or prev_name == '':
                        prev_val = datetime.strptime('2000-01-01', "%Y-%m-%d").date()

                    start = datetime.strptime(str(curr_involv['date_start']), "%Y-%m-%d").date()

                    if curr_involv['date_end']:
                        end = datetime.strptime(str(curr_involv['date_end']), "%Y-%m-%d").date()
                    else:
                        end = datetime.strptime(str(curr_involv['date_start']), "%Y-%m-%d").date()

                    if (start <= prev_val) and (prev_val != '2000-01-01'):
                        # if self.search([('employee_id', '=', elem[0]), ('date_start', '=', start), ('date_end', '=', end)]):
                        #     curr_involv.status = 'busy'

                        # if self.search([('employee_id', '=', elem[0]), ('date_end', '=', prev_val)]):
                        #     curr_involv.status = 'busy'

                        if len(self.search([('employee_id', '=', elem[0]), ('date_start', '=', start), ('date_end', '=', end)])) == 1:
                            self.search([('employee_id', '=', elem[0]), ('date_start', '=', start), ('date_end', '=', end)]).status = 'busy'
                        else:
                            for item in self.search([('employee_id', '=', elem[0]), ('date_start', '=', start), ('date_end', '=', end)]):
                                item.status = 'busy'

                        if len(self.search([('employee_id', '=', elem[0]), ('date_end', '=', prev_val)])) == 1:
                            self.search([('employee_id', '=', elem[0]), ('date_end', '=', prev_val)]).status = 'busy'
                        else:
                            for item in self.search([('employee_id', '=', elem[0]), ('date_end', '=', prev_val)]):
                                item.status = 'busy'

                    elif start > prev_val:
                        curr_involv.status = 'free'

                    prev_val = end
                    prev_name = elem[0]
