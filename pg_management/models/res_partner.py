from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner' # Standard Odoo inheritance

    is_pg_tenant = fields.Boolean(string="Is PG Tenant?", default=False)
    pg_id_proof = fields.Char(string="Aadhar/PAN Number")
