import logging
import sys
from assimilator.vandelay import vandelay_import
from django.db.models import Count
from django.core.management.base import BaseCommand, CommandError
from optparse import make_option

def resolve_function(func_module_path):
    (module_name, func_name) = func_module_path.rsplit('.', 1)
    module = vandelay_import(module_name)
    if not hasattr(module, func_name):
        raise CommandError("Function {0} not found in {1} module".format(func_name, module_name))
    return getattr(module, func_name)

class Command(BaseCommand):
    args = "chooser.module.function appname.models.ModelName field1 field2 ... fieldN"
    help = "Eliminates duplicate models before migrating to a less specific unique_together constraint."
    option_list = BaseCommand.option_list + (
        make_option('--dry-run',
                    action='store_true',
                    dest='dry_run',
                    default=False,
                    help='Don\'t actually delete anything.'),
    )

    def handle(self, chooser, model, *new_cons_fields, **options):
        chooser_func = resolve_function(chooser)
        if chooser_func is None:
            raise CommandError("Unable to resolve {0}.".format(chooser))

        (module_name, klass_name) = model.rsplit('.', 1)
        app_name = module_name.split('.')[0]
        if module_name not in sys.modules:
            raise CommandError("You must add {0} to the INSTALLED_APPS list.".format(app_name))

        module = sys.modules[module_name]
        if not hasattr(module, klass_name):
            error = "{0} not found in {1}.".format(klass_name, module_name)
            if not module_name.endswith('.models'):
                error = "{0} Did you mean {1}.models.{2}?".format(error,
                                                                  app_name,
                                                                  klass_name)
            raise CommandError(error)

        klass = getattr(module, klass_name)

        observed_fields = set([f.name for f in klass._meta._fields()])
        expected_fields = set(new_cons_fields)
        missing_fields = expected_fields - observed_fields
        if len(missing_fields) > 0:
            raise CommandError("Model {0} is missing fields: {1}.".format(
                model, ", ".join(sorted(list(missing_fields)))))

        keys = (klass.objects.order_by(*new_cons_fields)
                .values(*new_cons_fields)
                .annotate(cnt=Count('pk'))
                .filter(cnt__gt=1))
        keys = list(keys)

        for key in keys:
            del key['cnt']
            rows = klass.objects.filter(**key)

            chosen = apply(chooser_func, [new_cons_fields, key, rows])
            for row in rows:
                if row != chosen:
                    logging.warning("Deleting row {0} because it duplicates {1}".format(row.pk, chosen.pk))
                    if options['dry_run'] == False:
                        row.delete()




