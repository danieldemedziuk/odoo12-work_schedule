# -*- coding: utf-8 -*-
{
    'name': 'Work schedule',
    'version': '1.0',
    'author': 'Daniel Demedziuk',
    'sequence': 110,
    'summary': 'Projects, Employees, Schedule',
    'company': 'Daniel Demedziuk',
    'description': """
Work schedule of employees
==================================
This module provides insight into employee involvement in company projects. Load the number of working hours on a project.
The module allows you to verify vacations and availability for new tasks. It allows for effective and convenient personnel management by observing the progress and project load of individual employees.

If you need help, contact the author of the module.

email: daniel.demedziuk@gmail.com
""",
    'website': 'website',
    'category': 'Tool',
    'depends': [
        'project', 
        'base', 
        'mail', 
        'hr_holidays', 
        'web_timeline'
    ],
    'data': [
        'views/work_schedule_view.xml',
        'views/server_action.xml',
        'security/work_schedule_security.xml',
        'security/ir.model.access.csv',
    ],
    'auto_install': False,
    'application': True,
    'installable': True,
}
