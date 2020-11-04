#!/usr/bin/env python
# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)

class work_schedule(models.Model):
    _name = 'work_schedule.model'
    _description = 'Work schedule Model'
    _inherit = ['mail.thread', 'ir.needaction_mixin', 'project.task']

    def _get_name_fnc(self):
        res = {}
        for rec in self:
            name = rec.employee['name']
            res[rec.id] = name

        return res

    active = fields.Boolean('Active', default=True, help="If the active field is set to False, it will allow you to hide the project without removing it.")
    name = fields.Char(compute="_get_name_fnc", type="char", store=True)
    project = fields.Many2one('account.analytic.account', string='Project')
    employee = fields.Many2one('hr.employee', domain=([('x_production', '=', True)]), string="Employee", required=True)
    date_start = fields.Datetime(string='Date start', select=True, copy=False)
    date_end = fields.Datetime(string='Date stop', select=True, copy=False)
