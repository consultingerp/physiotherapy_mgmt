from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
import pdb


class PartnerRelatedFields(models.AbstractModel):
    _name = "physiotherapy.fields"
    _description = "Fields related with partner to be used on physiotherapy"

    active = fields.Boolean(default=True)
    partner_id = fields.Many2one("res.partner", "Partner", required=True)
    create_date = fields.Datetime(default=lambda self: fields.Datetime.now())
    company_id = fields.Many2one('res.company', string='Company', index=True,
                                 default=lambda self: self.env.user.company_id.id)

    # Partner related fields
    birth_date = fields.Date(related='partner_id.birth_date')
    gender = fields.Selection(related='partner_id.gender')
    civil_state = fields.Selection(related='partner_id.civil_state')
    allergies = fields.Char(related='partner_id.allergies')
    function = fields.Char(related='partner_id.function')
    style_of_life = fields.Char(related='partner_id.style_of_life')
    sport_practice = fields.Boolean(related='partner_id.sport_practice')
    sport_id = fields.Many2one(related='partner_id.sport_id')
    sport_periodicity = fields.Selection(related='partner_id.sport_periodicity')
    personal_history_id = fields.Many2many(related='partner_id.personal_history_id')
    familiar_history_id = fields.Many2many(related='partner_id.familiar_history_id')

    @api.multi
    def unlink(self):
        """
        Ensure that the templates can't be deleted
        """
        template_id = self.env.ref("physiotherapy_mgmt.template_%s" % self._table)
        is_template = template_id.id == self.id

        if is_template:
            raise ValidationError(_('Template record can\'t be deleted!!'))
        return super().unlink()


class ResPartner(models.Model):
    _inherit = 'res.partner'

    treatment_ids = fields.One2many('partner.treatment', 'partner_id', "Treatments")
    treatment_count = fields.Integer(compute='count_treatments')
    treatment_history_ids = fields.One2many('treatment.history', 'partner_id', "Treatment Histories")
    physiotherapy_partner = fields.Boolean("Physiotherapy Partner")

    # IMPORTANT (physiotherapy.fields): Each of the next fields that need to be appearing on treatments
    # NEEDED: repeat on physiotherapy.fields model
    birth_date = fields.Date('Date of Birth')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string="Gender")
    civil_state = fields.Selection([('single', 'Single'), ('married', 'Married')], string="Civil State")
    allergies = fields.Char("Allergies")
    style_of_life = fields.Char("Style of life")
    sport_practice = fields.Boolean("Practice Sports??")
    sport_id = fields.Many2one("partner.sport", "Sport practice")
    sport_periodicity = fields.Selection([('two', '1 - 2 per week'),
                                          ('five', '2 - 5 per week'),
                                          ('seven', '6 or more')], string="Periodicity")
    personal_history_id = fields.Many2many("personal.history",  'personal_history_rel', 'partner_id',
                                           'personal_history_id', string="Personal history")
    familiar_history_id = fields.Many2many("familiar.history",  'familiar_history_rel', 'partner_id',
                                           'familiar_history_id', string="Familiar history")

    @api.model
    def create(self, values):
        self.check_physiotherapy(values)
        return super().create(values)

    @api.multi
    def write(self, values):
        self.check_physiotherapy(values)
        return super().write(values)

    def check_physiotherapy(self, values):
        """
        Method to mark what partners are physiotherapy patients also.
        """
        s1 = set(values.keys())
        # Get all physiotherapy fields and remove no needed standard fields
        treatment_fields = set(self.env['physiotherapy.fields'].fields_get().keys())
        s2 = treatment_fields.difference(['__last_update',
                                          'active',
                                          'id',
                                          'company_id',
                                          'create_date',
                                          'display_name',
                                          'function',
                                          'partner_id'])
        res = s1.intersection(s2)
        if res:
            values['physiotherapy_partner'] = True

    @api.multi
    def count_treatments(self):
        if self.treatment_ids:
            self.treatment_count = len(self.treatment_ids.ids)

    @api.multi
    def action_make_treatment(self):
        action = self.env.ref('physiotherapy_mgmt.action_treatment_form').read()[0]
        action['context'] = {'search_default_partner_id': self.id}
        if len(self.treatment_ids) == 1:
            action['res_id'] = self.treatment_ids.id
            action['target'] = 'current'
            action['view_mode'] = 'form'
            del action['views']
        return action
