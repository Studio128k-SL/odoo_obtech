from odoo import models

class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _run_wkhtmltopdf(self, bodies, report_ref=False, header=None, footer=None, landscape=False, specific_paperformat_args=None, set_viewport_size=False):
        if specific_paperformat_args is None:
            specific_paperformat_args = {}
        report = self._get_report(report_ref) if report_ref else None
        if report and report.report_name == 'rother.report_label_dymo_rother':
            specific_paperformat_args['--disable-smart-shrinking'] = ''
            specific_paperformat_args['--page-width'] = '62mm'
            specific_paperformat_args['--page-height'] = '30mm'
        return super()._run_wkhtmltopdf(bodies, report_ref=report_ref, header=header, footer=footer, landscape=landscape, specific_paperformat_args=specific_paperformat_args, set_viewport_size=set_viewport_size)