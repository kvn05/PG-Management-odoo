from odoo import api, fields, models


class PGRoom(models.Model):
    _name = "pg.room"
    _description = "PG Room Details"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Room Number/Name", required=True)
    floor_name = fields.Selection(
        [
            ("0", "Ground Floor"),
            ("1", "1st Floor"),
            ("2", "2nd Floor"),
            ("3", "3rd Floor"),
        ],
        string="Floor",
        default="0",
    )

    room_type_value = fields.Selection(
        [("ac", "AC"), ("non_ac", "Non-AC")], string="Room Type", default="non_ac"
    )

    capacity = fields.Integer(
        string="Total Beds", default=1, help="e.g., 2 for 2-sharing"
    )
    occupied_beds_num = fields.Integer(string="Occupied Beds", default=0)

    # Logic to calculate availability
    available_beds_num = fields.Integer(
        string="Available Beds", compute="_compute_availability", store=True
    )

    rent_amount = fields.Float(string="Monthly Rent per Bed", required=True)
    facilities = fields.Text(string="Facilities (e.g. Balcony, Attached Bath)")

    state = fields.Selection([
            ('available', 'Available'),
            ('occupied', 'Occupied'),
            ('maintenance', 'Maintenance'),
    ], string="Status", compute="_compute_state", default='available', tracking=True)

    # add contract count fields
    contract_count = fields.Integer(
        string="Contracts",
        compute="_compute_contract_count"
    )

    @api.depends("capacity", "occupied_beds_num")
    def _compute_availability(self):
        for record in self:
            record.available_beds_num = record.capacity - record.occupied_beds_num

    @api.depends('capacity','occupied_beds_num','state')
    def _compute_state(self):
        for room in self:
            if room.state == 'maintenance':
                continue
            if room.occupied_beds_num >= room.capacity:
                room.state = 'occupied'
            else:
                room.state = 'available'


    """
    add one2many relational field - notice 'guest_ids' not id
    pg.guest = comodel_name
    room_id = inverse name
    this links many pg.guest records to one room_id
    """
    guest_ids = fields.One2many("pg.guest", "room_id", string="Current Guests")

    # Method for Object Button
    def action_set_to_maintenance(self):
        for record in self:
            record.state = 'maintenance'
            # Optional: Add a log message
            record.message_post(body="Room has been moved to Maintenance status.")

    def action_set_to_available(self):
        for record in self:
            record.state = 'available'

    def _compute_contract_count(self):
        for room in self:
            room.contract_count = self.env['pg.contract'].search_count([
                ('room_id', '=', room.id)
            ])

    def action_view_contracts(self):
        self.ensure_one()
        return {
            'name': 'Contracts',
            'type': 'ir.actions.act_window',
            'res_model': 'pg.contract',
            'view_mode': 'list,form',
            'domain': [('room_id', '=', self.id)],
            'context': {
                'default_room_id': self.id
            }
        }
    