#!/usr/bin/env python
# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)

class work_schedule(models.Model):
    _name = 'work_schedule.model'
    _description = 'Work schedule Model'
    _inherit = ['hr.employee']

    @api.depends('project_id')
    def _get_name_fnc(self):
        for rec in self:
            rec.name = str(rec.employees_ids['x_user_id'] + ' / ' + rec.project_id['name'])

    active = fields.Boolean('Active', default=True, track_visibility="onchange", help="If the active field is set to False, it will allow you to hide the project without removing it.")
    name = fields.Char(compute="_get_name_fnc", type="char", store=True)
    project_id = fields.Many2one('account.analytic.account', string='Project')
    project_parent = fields.Char(compute='get_project_parent', type="char", string='Project parent', readonly=True, store=True)
    employees_ids = fields.Many2one('hr.employee', domain=([('x_production', '=', True)]), string="Employee", required=True)
    emp_picture = fields.Binary(compute='_get_employee_picture', string="Picture", readonly=True)
    date_start = fields.Date(string='Date start', select=True, copy=False, required=True)
    date_end = fields.Date(string='Date stop', select=True, copy=False)
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
            if rec.project_id['x_manager_id']:
                rec.project_parent = rec.project_id['x_manager_id']['name']

    @api.depends('employees_ids')
    @api.model
    def _get_employee_picture(self):
        if self.employees_ids['image']:
            self.emp_picture = self.employees_ids['image']
