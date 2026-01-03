from odoo import fields, models, api
from odoo.exceptions import UserError
from datetime import date


class PGContract(models.Model):
    _name = 'pg.contract'
    _description = 'PG Stay Contract'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Contract Reference", default='New', readonly=True)
    guest_id = fields.Many2one('pg.guest', required=True)
    room_id = fields.Many2one('pg.room', required=True, ondelete='restrict', tracking=True) # add tracking = True for chatter
    start_date = fields.Date(required=True, tracking=True)
    end_date = fields.Date(tracking=True)
    rent_amount = fields.Float(required=True, tracking=True)
    security_deposit = fields.Float()
    state = fields.Selection([
        ('draft', 'Draft'),
        ('running', 'Running'),
        ('closed', 'Closed'),
    ], default='draft', tracking=True)

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('pg.contract') or 'New'
        return super().create(vals)


    def action_start_contract(self):
        for rec in self:
            if rec.state != 'draft':
                continue  # prevent double execution

            room = rec.room_id

            if room.occupied_beds_num >= room.capacity:
                raise UserError("No beds available in this room.")

            # Update state
            rec.state = 'running'

            # Increase occupied beds safely
            room.occupied_beds_num += 1

            # Chatter message
            rec.message_post(
                body=f"✅ Contract started. Bed allocated in room {room.name}.",
                subtype_xmlid="mail.mt_note"
            )


    def action_close_contract(self):
        for rec in self:
            if rec.state != 'running':
                continue

            room = rec.room_id

            # Free the bed
            if room.occupied_beds_num > 0:
                room.occupied_beds_num -= 1

            rec.state = 'closed'

            rec.message_post(
                body=f"🔒 Contract closed. Bed released from room {room.name}.",
                subtype_xmlid="mail.mt_note"
            )



    def cron_rent_reminder(self):
        if date.today().day != 5:
            return

        contracts = self.search([
            ('state', '=', 'running')
        ])

        for contract in contracts:
            if contract.guest_id and contract.guest_id.email:
                contract.message_post(
                    subject="Monthly Rent Reminder",
                    body=f"""
                        Dear {contract.guest_id.name},<br/>
                        This is a reminder to pay your monthly rent of
                        <b>{contract.rent_amount}</b>.<br/><br/>
                        Thank you.
                    """,
                    partner_ids=[contract.guest_id.partner_id.id]
                )
