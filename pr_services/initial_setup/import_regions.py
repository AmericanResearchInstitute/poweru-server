from __future__ import with_statement
import facade

def setup(machine):
    if not machine.options.has_key('region_csv_path'): return
    with open(machine.options['region_csv_path']) as csv_file:
        csv_str = csv_file.read()
    admin_token = machine.options['admin_token']
    csv = facade.models.CSVData.objects.create(text=csv_str,
        user=admin_token.user)
    machine.import_manager.import_regions(admin_token, csv)
