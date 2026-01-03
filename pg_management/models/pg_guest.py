from odoo import fields, models, api
from odoo.exceptions import ValidationError


class PGGuest(models.Model):
    _name = "pg.guest"
    _description = "PG Guest Profile"
    # _inherit = ["mail.thread"]  # Inheriting 'mail' module features

    name = fields.Char(
        string="Full Name", required=True, tracking=True
    )  # field enables the automatic logging of changes to that specific field.
    profile = fields.Binary()  # add profile image of guest
    gender_type = fields.Selection(
        [("male", "Male"), ("female", "Female"), ("other", "other")],
        string="Gender",
        required=True,
    )

    mobile = fields.Char(string="Mobile Number", required=True)
    email = fields.Char(string="Email-ID")

    # Address & KYC
    permanent_address_name = fields.Text(string="Permanent Address")
    id_proof_type = fields.Selection(
        [
            ("aadhar", "Aadhar Card"),
            ("pan", "PAN Card"),
            ("voter", "Voter ID"),
            ("passport", "Passport"),
        ],
        string="ID Proof Type",
        default="aadhar",
    )
    id_proof_number = fields.Char(string="ID Number")
    id_proof_image = fields.Binary(string="Upload ID Proof")

    # Work/Study Details
    occupation_type = fields.Selection(
        [("student", "Student"), ("worrking", "Working Professional")],
        string="Occupation",
    )
    organization_name = fields.Char(string="College/Office Name")

    # Emegency Contact
    emergency_contact_name = fields.Char(string="Guardian/Parent Name")
    emergency_contact_number = fields.Char(string="Guardian Mobile")
    relationship = fields.Char(string="Relationship (e.g Father)")

    active = fields.Boolean(default=True, string="Is Currently Staying?")

    filter_room_type = fields.Selection(
        [
            ("ac", "AC"),
            ("non_ac", "Non-AC"),
        ],
        string="Filter by Type",
    )

    filter_floor = fields.Selection(
        [
            ("0", "Ground Floor"),
            ("1", "1st Floor"),
            ("2", "2nd Floor"),
            ("3", "3rd Floor"),
        ],
        string="Filter by Floor",
    )

    # added Many2one relational field
    room_id = fields.Many2one(
        "pg.room",
        string="Allocated Room",
        # This domain dynamically checks the filter fields above
        domain="[('available_beds_num', '>', 0), ('room_type_value', '=', filter_room_type), ('floor_name', '=', filter_floor)]",
    )

    checkin_date = fields.Date(string="Check-in Date", default=fields.Date.today)

    # Logic to update 'Occupied Beds' in pg.room when guest is added
    @api.model_create_multi
    def create(self, val_list):
        guests = super(PGGuest, self).create(val_list)
        for guest in guests:
            if guest.room_id:
                guest.room_id.occupied_beds_num += 1
        return guests

    def write(self, vals):
        if "room_id" in vals:
            for guest in self:
                # Decrease count in old room
                if guest.room_id:
                    guest.room_id.occupied_beds_num -= 1
            res = super(PGGuest, self).write(vals)
            for guest in self:
                # Increase count in new room
                if guest.room_id:
                    guest.room_id.occupied_beds_num += 1
            return res
        return super(PGGuest, self).write(vals)

    @api.constrains('room_id')
    def _check_room_availability(self):
        for guest in self:
            if guest.room_id:
                if guest.room_id.available_beds_num <= 0:
                    raise ValidationError(
                        f"No beds available in room {guest.room_id.name}."
                    )
