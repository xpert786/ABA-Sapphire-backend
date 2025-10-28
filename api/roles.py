"""
Role definitions for the rolepermissions package.
"""

from rolepermissions.roles import AbstractUserRole


class SuperAdmin(AbstractUserRole):
    available_permissions = {
        'create_users': True,
        'edit_users': True,
        'delete_users': True,
        'view_all_users': True,
        'manage_sessions': True,
        'view_all_sessions': True,
        'manage_schedules': True,
        'view_reports': True,
        'system_admin': True,
    }


class Admin(AbstractUserRole):
    available_permissions = {
        'create_users': True,
        'edit_users': True,
        'delete_users': False,
        'view_all_users': True,
        'manage_sessions': True,
        'view_all_sessions': True,
        'manage_schedules': True,
        'view_reports': True,
    }


class BCBA(AbstractUserRole):
    available_permissions = {
        'create_users': False,
        'edit_users': False,
        'delete_users': False,
        'view_all_users': False,
        'manage_sessions': True,
        'view_assigned_sessions': True,
        'manage_schedules': False,
        'view_reports': True,
        'supervise_rbt': True,
    }


class RBT(AbstractUserRole):
    available_permissions = {
        'create_users': False,
        'edit_users': False,
        'delete_users': False,
        'view_all_users': False,
        'manage_sessions': False,
        'view_assigned_sessions': True,
        'manage_schedules': False,
        'view_reports': False,
        'log_session_data': True,
        'start_end_sessions': True,
    }


class Client(AbstractUserRole):
    available_permissions = {
        'create_users': False,
        'edit_users': False,
        'delete_users': False,
        'view_all_users': False,
        'manage_sessions': False,
        'view_assigned_sessions': True,
        'manage_schedules': False,
        'view_reports': False,
        'view_own_data': True,
        'upload_documents': True,
    }
